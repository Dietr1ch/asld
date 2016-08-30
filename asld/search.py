import os
import gc

from sys import stdout
from copy import copy
from time import time
from shutil import get_terminal_size

import psutil

from rdflib.term import URIRef, Literal, BNode

from asld.graph import ASLDGraph
from asld.query.direction import Direction
from asld.query.query import Query
from asld.query.state import State
from asld.query.transition import Transition

from asld.utils.heap import Heap
from asld.utils.color_print import Color
from asld.utils.async_timeout_pool import AsyncTimeOutPool




# Default limits
# ==============
_L_ANS = 1000
_L_TIME = 30*60
_L_TRIPLES = 1e5


# Output Helpers
# ==============
term_size = get_terminal_size((80, 20))

tty = stdout.isatty()
def clearLine():
    if tty:
        print("\r\033[K", end="")

def rP(s, i=0):
    print("%*s" % (term_size.columns+9*i, s))


def printPath(path):
    for n in path:
        if n.parent:  # has previous transition
            rP("%s    " % n.str_p(), 1)
        rP("%-69s: %21s" % (n.str_n(), n.str_q()), 2)



_proc_self = psutil.Process(os.getpid())
def getMemory():
    """ Returns memory usage in MB (after calling the GC) """
    gc.collect()
    return _proc_self.memory_info().rss/1024/1024


class ASLDSearch:

    class NodeState:
        """Search Node, a (Node, State) pair"""

        def __init__(self,
                     node,
                     state:  State,
                     parent,
                     P:      URIRef,
                     t:      Transition,
                     d:      Direction,
                     g=float("inf")):
            assert node.__class__ is URIRef  or  node.__class__ is Literal or  node.__class__ is BNode, "node.__class__ == '%s' is not URIRef or Literal or BNode" % node.__class__

            self.n = node
            self.q = state

            # Path data
            self.parent = parent

            self.P = P
            self.t = t
            self.d = d

            # Node cost
            self.g = g


        def __lt__(self, other):
            return self.n < other.n

        def __eq__(self, other):
            return self.n == other.n  and  self.q == other.q

        def __hash__(self):
            return hash(self.n)^(hash(self.q)+1)


        def str_n(self):
            if isinstance(self.n, URIRef):
                return Color.GREEN(self.n)
            return Color.RED(self.n)

        def str_p(self):
            # Forward
            st = "--"
            nd = "->"

            if self.d == Direction.backward:
                st = "<-"
                nd = "--"

            return "%s(%s)%s" % (st, Color.YELLOW(self.P), nd)

        def str_q(self):
            return Color.YELLOW(self.q.name)


        def __str__(self):
            return "(%21s: %s)" % (self.str_q(), self.str_n())

        def __repr__(self):
            return str(self)

        def default(self, o):
            pass



    class Stats:
        class Snapshot:

            def __init__(self, snap=None):
                self.wallClock = 0
                self.batch = 0

                self.memory = 0

                # Search
                self.goals = 0       # Goals found
                self.expansions = 0  # Expansions done

                # DB
                self.triples = 0     # Triples on the Main DB

                # Last request
                self.requestTriples = 0
                self.requestTime    = 0
                self.requestAccTime = 0
                self.requestIRI = ""

            def __str__(self) -> str:
                return "%5d (%3d) %7.2fs> goals: %3d; |Req|: %4d, t(Req): %5.2fs;  |DB| = %6d;  Mem:%.1fMB" % (self.expansions, self.batch, self.wallClock, self.goals, self.requestTriples, self.requestTime, self.triples, self.memory)

            def __repr__(self):
                return str(self)

            def json(self) -> dict:
                return {
                    "wallClock": self.wallClock,
                    "batchID": self.batch,

                    "memory": self.memory,

                    "goalsFound": self.goals,
                    "expansions": self.expansions,

                    "triples": self.triples,

                    "requestTriples":   self.requestTriples,
                    "requestTime":      self.requestTime,
                    "requestTotalTime": self.requestAccTime,
                    "requestIRI":       self.requestIRI
                }

            def __lt__(self, o):
                return self.requestTime < o.requestTime


        def __init__(self, s):
            self.status = ASLDSearch.Stats.Snapshot()
            self.history = []
            self.search = s
            self.t0 = time()
            self.g = s.g
            self.snap()

        def _marks(self):
            self.t0 = time()

        def __str__(self) -> str:
            return "LastStatus: %s" % str(self.status)
        def __repr__(self) -> str:
            return str(self)


        def snap(self):
            self.status.memory = getMemory()
            self.status.triples = len(self.g)
            self.status.wallClock = time()-self.t0
            self.history.append(copy(self.status))

        def goal(self):
            self.status.goals += 1

        def batch(self):
            self.status.batch += 1

        def expand(self, iri, lG, t):
            """ Marks an expansion """
            self.status.expansions += 1
            self.status.requestIRI = str(iri)
            self.status.requestTriples = lG
            self.status.requestTime = t
            self.status.requestAccTime += t
            self.snap()



    def __init__(self, queryAutomaton: Query):
        self.query = queryAutomaton
        self.g = None
        self.stats = None
        self._reset()

    def _reset(self):
        """ Clears all search info and call the GC """
        self.g = ASLDGraph()
        self.stats = ASLDSearch.Stats(self.g)
        self._setup_search()
        gc.collect()

    def _setup_search(self):
        self.open   = Heap()
        self.closed = set()
        self.states = {}

        n0 = self.query.startNode
        q0 = self.query.startState
        ns = ASLDSearch.NodeState(n0, q0, None, None, None, None)
        self.states[(n0, q0)] = ns

        self.startNS   = ns
        self.startNS.g = 0



    def _get(self, n, q, parent, P, t, d):
        """
        Gets the *Unique* NodeState for a (node, state) pair.
        It builds new NodeStates as needed.
        """
        if (n, q) not in self.states:
            if P is None  or  t is None  or  d is None:
                raise Exception("First get MUST init the new NodeState")
            self.states[(n, q)] = ASLDSearch.NodeState(n,q, parent, P,t,d)

        return self.states[(n, q)]


    def _pop(self):
        (_, ns) = self.open.pop()
        return ns

    def _enqueue(self, ns):
        # Put cns on open
        k = (ns.g + ns.q.h, -ns.g)
        self.open.push(k, ns)

        if ns.q.accepts(ns.n):
            self.stats.goal()
            return ns
        return None


    def _getPath(self, ns):
        path = []
        while ns is not None:
            path.append(ns)
            ns = ns.parent
        path.reverse()
        return path


    def _reach(self, ns, P, cN,cQ, t, d):
        """
        Reaches (cN, cQ) from ns using t on direction d
        Updates target node if it's reached in a better way
        """

        if not t(P):
            return None  # Predicate not allowed by t

        if not cQ(cN):
            return None  # Destination Node not allowed by q

        cns = self._get(cN,cQ, parent=ns, P=P, t=t, d=d)
        if cns in self.closed:
            return None  # target node already expanded

        # Reach
        newCost = ns.g + 1
        if newCost >= cns.g:
            return None  # Nothing to see here...

        # Update child
        cns.parent = ns

        cns.g = newCost

        cns.P = P
        cns.t = t
        cns.d = d

        # Enqueue child
        return self._enqueue(cns)

    def _expand(self, ns):
        """
        Reaches all the neighborhood.
        It prefers Forward Transitions as they may bring data
          for computing the backward transitions.

        REVIEW: It may be better to force tie breaking on the heap
        """

        goalsFound = []

        for t in ns.q.next_transitions_f:
            for _,P,O in self.g.query(ns.n):
                g = self._reach(ns, P, cN=O,cQ=t.dst, t=t, d=Direction.forward)
                if g:
                    goalsFound.append(g)

        for t in ns.q.next_transitions_b:
            for S,P,_ in self.g.query(None, None, ns.n):
                g = self._reach(ns, P, cN=S,cQ=t.dst, t=t, d=Direction.backward)
                if g:
                    goalsFound.append(g)

        return goalsFound


    def _paths(self):
        """Performs search using a single process"""
        # Initialize search
        _t0_search = time()
        self._enqueue(self.startNS)

        # Empty open...
        self.stats._marks()  # Adjust stats clock
        while self.open:
            _t0_localExpand = time()

            # Extract a single top-F node
            self.stats.batch()
            ns = self._pop()

            if ns in self.closed:
                if __debug__:
                    Color.RED.print("Discarding a closed node found on open")
                continue

            # Blocking load
            (_, incr) = self.g.loadB(ns.n)

            # Local expand
            goalsFound = self._expand(ns)
            for g in goalsFound:
                yield self._getPath(g)

            _t_localExpand = time() - _t0_localExpand
            self.stats.expand(ns.n, incr, _t_localExpand)

            clearLine()
            print(" Sync expanded (%5.2fs) %s" % (_t_localExpand, ns))

        _t_search = time() - _t0_search
        clearLine()
        Color.BLUE.print("Search took %4.2fs" % _t_search)
        Color.GREEN.print("Open was emptied, there are no more paths")


    def _extractTopF(self, batchSize):
        # Extract at most batchSize from top-f nodes
        (topF, _) = self.open.peekKey()  # key: (f, -g)

        rdy = []
        pnd = []
        gls = []
        expansions = 0


        # Build top Slice
        # ===============
        f = topF
        pendingExpansions = 0
        while self.open  and  (batchSize==0 or expansions<batchSize):
            (f, _) = self.open.peekKey()
            if f>topF:
                break

            ns = self._pop()
            if ns in self.closed:
                if __debug__:
                    Color.RED.print("Discarding a closed node found on open")
                continue
            self.closed.add(ns)


            expansions += 1
            pendingExpansions += 1

            if tty:
                clearLine()
                print("  expansions (%4d): " % pendingExpansions, end="")
                print("#"*pendingExpansions, end="")

            # Goal Check
            # ==========
            # REVIEW: allow blocking goal check
            if ns.q.accepts(ns.n):
                gls.append(ns)

            # Add to batch
            if isinstance(ns.n, URIRef):
                if ns not in self.g.loaded:
                    pnd.append(ns)
                else:
                    rdy.append(ns)  # It will make sense on query re-runs over local data (ensures optimal order)
            else:
                rdy.append(ns)

        return (rdy, pnd, gls, pendingExpansions)


    def paths(self, parallelRequests=40, batchSize=160,
              limit_time=_L_TIME, limit_ans=_L_ANS, limit_triples=_L_TRIPLES):
        """
        Performs search using parallel requests to expand top-f value NodeStates

        Reaching limits causes the search to stop doing requests, but it may
          find a few answers more with whats left.
        """
        deadline = None
        if limit_time:
            deadline = time() + limit_time

        # Initialize search
        _t0_search = time()
        self._enqueue(self.startNS)
        pool = AsyncTimeOutPool(parallelRequests, timeout=25)

        answers = 0
        requestsAllowed = True

        # Empty open...
        while self.open:
            # Limits check
            if requestsAllowed:
                if answers>limit_ans:
                    clearLine()
                    Color.YELLOW.print("Reached the %d-goal-limit (%d)" % (limit_ans, answers))
                    requestsAllowed = False
                if len(self.g) > limit_triples:
                    clearLine()
                    Color.YELLOW.print("Reached the %d-triples limit (%d)" % (limit_triples, len(self.g)))
                    requestsAllowed = False
                if deadline and time() > deadline:
                    clearLine()
                    Color.YELLOW.print("Reached the %ds time limit" % (limit_time))
                    requestsAllowed = False

            (rdy, pnd, _, pendingExpansions) = self._extractTopF(batchSize)
            self.stats.batch()


            # Local expand (no requests are needed)
            # ============
            # Blocking goal check will ruin this, also, goal states should rank further
            if rdy:
                _t0_localExpansions = time()
                expansionsDone = 0
                for ns in rdy:
                    expansionsDone += 1
                    pendingExpansions -= 1
                    if tty:
                        print("\r  local expansions (%4d): " % pendingExpansions, end="")
                        print("[%s" % ("#"*expansionsDone), end="")
                        print("%s]" % ("."*pendingExpansions), end="")

                    # Expand nodes
                    # Early declare goals (Unless we implement blocking filters :c)
                    _t0_localExpand = time()
                    goalsFound = self._expand(ns)
                    for g in goalsFound:
                        answers += 1
                        yield self._getPath(g)

                    self.stats.expand(ns.n, 0, time()-_t0_localExpand)

                _t_end = time()
                _t_localExpansions = _t_end - _t0_localExpansions

                clearLine()
                print(" Sync expanded (%4.2fs) %3d nodes" % (_t_localExpansions, len(rdy)))


            # Parallel expand
            # ===============
            if requestsAllowed and pnd:
                newTriples = 0
                _t0_parallelExpand = time()
                requests = [(ns.n, i, ns.q._next_P(), ns.q.hasBackwardTransition()) for (i, ns) in enumerate(pnd)]

                clearLine()
                Color.BLUE.print("Mapping %d requests:" % len(pnd))

                requestsFullfilled = 0
                requestsCorrectlyFullfilled = 0
                for reqAns in pool.map(ASLDGraph.pure_loadB, requests):
                    requestsFullfilled += 1
                    pendingExpansions -= 1
                    # Use answers as they become available
                    # Using the main thread seems better as it avoids most sync

                    # Unpack and recover the NodeState (was not copied around)
                    assert isinstance(reqAns, ASLDGraph.RequestAnswer)
                    reqGraph = reqAns.g
                    t = reqAns.reqTime
                    iri = reqAns.iri
                    ns = pnd[reqAns.index]
                    assert ns not in self.g.loaded, "No loads should be issued to loaded NodeStates (%s)" % ns
                    self.stats.expand(iri, len(reqGraph), t)


                    # Report progress
                    if tty:
                        print("\r  || expansions (%4d): " % pendingExpansions, end="")
                        print("[%s" % ("#"*requestsFullfilled), end="")
                        print("%s]" % ("."*pendingExpansions), end="")


                    # Finish expansion on the node
                    self.g.loaded.add(ns)

                    if len(reqGraph) == 0:
                        # Nothing was obtained, nothing to do
                        clearLine()
                        Color.RED.print("Request for '%s' failed" % iri)
                        continue
                    requestsCorrectlyFullfilled += 1

                    # Add new data
                    newTriples += len(reqGraph)
                    for spo in reqGraph:
                        self.g.add(spo)

                    # Expand node
                    goalsFound = self._expand(ns)
                    for g in goalsFound:
                        answers += 1
                        yield self._getPath(g)

                _t_end = time()
                _t_parallelExpand = _t_end - _t0_parallelExpand

                clearLine()
                print("Async expanded %3d nodes on %4.2fs" % (requestsCorrectlyFullfilled, _t_parallelExpand))

        _t_end = time()
        _t_search = time() - _t0_search

        clearLine()
        Color.BLUE.print("Search took %4.2fs" % _t_search)
        Color.GREEN.print("\nOpen was emptied, there are no more paths")
        pool.close()

    def run(self, parallelRequests=40,
            limit_time=_L_TIME, limit_ans=_L_ANS):
        """Intended only for interactive CLI use"""
        term_size = get_terminal_size((80, 20))  # Update CLI width

        r = []
        if self.closed:
            self._setup_search()

        _t0 = time()
        try:
            answers = 0
            self.stats._marks()  # Adjust stats clock
            for p in self.paths(parallelRequests, parallelRequests):
                r.append(p)
                print()
                printPath(p)

                answers += 1
                if answers >= limit_ans:
                    Color.BLUE.print("Reached the %d-Answer limit" % limit_ans)
                    break
                if time()-_t0 >= limit_time:
                    Color.BLUE.print("Reached the %.2fs time limit" % limit_time)
                    break

        except KeyboardInterrupt:
            Color.BLUE.print("\nTerminating search.")
        #except Exception as e:
            #Color.RED.print("Terminated Search.run on: %s" % e)
        t = time() - _t0
        Color.GREEN.print("\nSearch took %.2fs. Gathered %d triples and got back %d paths." % (t, len(self.g), len(r)))
        return (r, answers, time()-_t0)

    @classmethod
    def _native_path(cls, path):
        """
        Builds a simplified path representation using native types
        It's serializable (=
        """
        _path = []
        for n in path:

            transition = None
            if n.parent:
                d = ""
                if n.d is Direction.forward:
                    d = ">"
                else:
                    d = "<"
                transition = {
                    "P": str(n.P),
                    "d": d
                }

            step = {
                "transition": transition,
                "state": n.q.name,
                "node": str(n.n)
            }
            _path.append(step)

        return _path

    def test(self, parallelRequests=40,
             limit_time=_L_TIME, limit_ans=_L_ANS, limit_triples=_L_TRIPLES):
        """ Non-interactive runs """
        if limit_time is None:
            limit_time = float("inf")
        elif limit_time <= 0:
            limit_time = float("inf")

        self._reset()

        _ans = []
        _t0 = time()
        try:

            self.stats._marks()  # Adjust stats clock
            for path in self.paths(parallelRequests, parallelRequests,
                                   limit_time=limit_time,
                                   limit_ans=limit_ans,
                                   limit_triples=limit_triples):
                _ans.append(path)

        except KeyboardInterrupt:
            Color.BLUE.print("\nTerminating search.")
        #except Exception as e:
            #Color.RED.print("Terminated Search.test on: %s" % e)
        t = time() - _t0

        ans = [ASLDSearch._native_path(path) for path in _ans]

        Color.GREEN.print("\nSearch took %.2fs. Gathered %d triples and got back %d paths." % (t, len(self.g), len(ans)))

        with open("last-db", 'w') as f:
            for s, p, o in self.g.g:
                f.write("%-50s  (%50s)  %50s\n" % (s, p, o))
        with open("last-ans", 'w') as f:
            for p in _ans:
                f.write("%s\n" % p)

        return {
            "Paths": ans,
            "PathCount": len(ans),
            "StatsHistory": [h.json() for h in self.stats.history],
            "Time": t
        }
