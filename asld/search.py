"""
Search

A search, with it's own query and database
"""
import os
import gc

from sys import stdout
from copy import copy
from time import time
from shutil import get_terminal_size
from json import dump
from enum import Enum

import psutil

from rdflib.term import URIRef, Literal, BNode

from asld.graph import ASLDGraph
from asld.query.query import Query
from asld.query.state import State
from asld.query.transition import Transition, Direction

from asld.utils.heap import Heap
from asld.utils.color_print import Color
from asld.utils.async_timeout_pool import AsyncTimeOutPool


INFTY = float("inf")

DUMP_DATA = True

# Default limits
# ==============
_L_ANS = 1000
_L_TIME = 30*60
_L_TRIPLES = 1e5


# Output Helpers
# ==============
TERM_SIZE = get_terminal_size((80, 20))

IS_TTY = stdout.isatty()
def clearLine():
    """
    Clears current line on TTYs
    """
    if IS_TTY:
        print("\r\033[K", end="")

def rP(s, i=0):
    """
    Prints string to the right of the TTY.

    Accepts an optional offset to account for escape sequences
    """
    print("%*s" % (TERM_SIZE.columns+9*i, s))


def printPath(path):
    """
    Pretty prints a path on the Right of the TTY
    """
    if IS_TTY:
        for n in path:
            if n.parent:  # has previous transition
                rP("%s    " % n.str_p(), 1)
            rP("%-69s: %21s" % (n.str_n(), n.str_q()), 2)



_proc_self = psutil.Process(os.getpid())
def getMemory():
    """ Returns memory usage in MB (after calling the GC) """
    gc.collect()
    return _proc_self.memory_info().rss/1024/1024


def valid_node(node):
    """ Checks whether an object is a valid RDF Node """
    c = node.__class__
    return c is URIRef  or  c is Literal  or  c is BNode



class Algorithm(Enum):
    """
    Sets up the algorithm used for the search
    """
    AStar    = 0
    Dijkstra = 1
    DFS      = 2

    @classmethod
    def parse(cls, alg: str):
        """
        String -> Algorithm enum
        """
        alg = alg.lower()

        if alg == "a*":
            return Algorithm.AStar
        elif "astar".startswith(alg):
            return Algorithm.AStar

        elif "dijkstra".startswith(alg):
            return Algorithm.Dijkstra
        elif "bfs".startswith(alg):
            return Algorithm.Dijkstra

        elif "dfs".startswith(alg):
            return Algorithm.DFS

        return Algorithm.AStar

    @classmethod
    def to_string(cls, alg):
        """ Alg enum -> string """
        if alg == Algorithm.AStar:
            return "AStar"
        elif alg == Algorithm.Dijkstra:
            return "Dijkstra"
        elif alg == Algorithm.DFS:
            return "DFS"

        return "(Alg)"

class ASLDSearch:
    """
    Search

    Holds:
      - query:  Query
      - g:      ASLDGraph
      - stats:  ASLDSearch.Stats

      - open:   Heap<NodeState>
      - closed: Set<NodeState>
      - states: (Node, State) -> NodeState

      - Setup:
         - w:           Weight to use on the heuristic
         - quick_goal:  Use quick goal declaration
    """
    # pylint: disable=too-many-instance-attributes

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
            # pylint: disable=too-many-arguments

            assert valid_node(node), "%s not a valid node" % node

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
            return hash(self.n) ^ (hash(self.q)+1)


        def str_n(self):
            """Pretty prints the Node"""
            if isinstance(self.n, URIRef):
                return Color.GREEN(self.n)
            return Color.RED(self.n)

        def str_p(self):
            """Pretty prints the Predicate"""
            # Forward
            st = "--"
            nd = "->"

            if self.d == Direction.backward:
                st = "<-"
                nd = "--"

            return "%s(%s)%s" % (st, Color.YELLOW(self.P), nd)

        def str_q(self):
            """Pretty prints the State"""
            return Color.YELLOW(self.q.name)


        def __str__(self):
            return "(%21s: %-90s)" % (self.str_q(), self.str_n())

        def __repr__(self):
            return str(self)

        def default(self, o):
            pass

        def isGoal(self):
            """Checks if the state is a goal"""
            return self.q.accepts(self.n)

        def SPARQL_query(self):
            """
            Returns the SPARQL query to expand this NodeState
            """
            return self.q.SPARQL_query(self.n)


    class Stats:
        """
        Manages the series of statistics for a search run
        """

        class Snapshot:
            """
            Statistics of a currently running search
            """
            # pylint: disable=too-many-instance-attributes,too-few-public-methods

            def __init__(self):
                self.wallClock = 0
                self.batch = 0

                self.memory = 0

                # Search
                self.goals = 0       # Goals found
                self.expansions = 0  # Expansions done
                self.local_expansions = 0
                self.remote_expansions = 0

                # DB
                self.triples = 0  # Triples on the Main DB

                # Last request
                self.requestTriples = 0
                self.requestTime    = 0
                self.requestAccTime = 0
                self.requestIRI = ""

            def __str__(self) -> str:
                # pylint: disable=line-too-long
                return "%5d (%3d) %7.2fs> goals: %3d; |Req|: %4d, t(Req): %5.2fs;  |DB| = %6d;  Mem:%.1fMB" % (self.expansions, self.batch, self.wallClock, self.goals, self.requestTriples, self.requestTime, self.triples, self.memory)

            def __repr__(self) -> str:
                return str(self)

            def json(self) -> dict:
                """
                Returns the json object representation of the Snapshot
                """
                return {

                    "wallClock": self.wallClock,
                    "batchID": self.batch,

                    "memory": self.memory,

                    "goals_found": self.goals,
                    "expansions": self.expansions,
                    "local_expansions": self.local_expansions,
                    "remote_expansions": self.remote_expansions,

                    "triples": self.triples,

                    "requestTriples":   self.requestTriples,
                    "requestTime":      self.requestTime,
                    "requestTotalTime": self.requestAccTime,
                    "requestIRI":       self.requestIRI
                }

            def __lt__(self, o) -> bool:
                return self.requestTime < o.requestTime


        def __init__(self, s):
            self.status = ASLDSearch.Stats.Snapshot()
            self.history = []
            self.search = s
            self.t0 = time()
            self.g = s.g
            self.snap()

        def tick(self):
            """Start timing"""
            self.t0 = time()

        def __str__(self) -> str:
            return "LastStatus: %s" % str(self.status)

        def __repr__(self) -> str:
            return str(self)


        def snap(self):
            """Adds a new stats snapshot to the history"""
            self.status.memory = getMemory()
            self.status.triples = len(self.g)
            self.status.wallClock = time()-self.t0
            self.history.append(copy(self.status))

        def goal(self):
            """Count another goal found"""
            self.status.goals += 1

        def batch(self):
            """Count another batch"""
            self.status.batch += 1

        def expand(self, iri, lG, t, local):
            """ Marks an expansion """
            self.status.expansions += 1
            if local:
                self.status.local_expansions += 1
            else:
                self.status.remote_expansions += 1
            self.status.requestIRI = str(iri)
            self.status.requestTriples = lG
            self.status.requestTime = t
            self.status.requestAccTime += t
            self.snap()

        def expansions(self):
            """Expansions performed"""
            return self.status.expansions

        def db_triples(self):
            """Triples stored on the search's DB"""
            return self.status.triples

        def memory(self):
            """Memory used"""
            return self.status.memory

        def wallClock(self):
            """Time executing"""
            return self.status.wallClock



    def __init__(self, queryAutomaton: Query, quick_goal=True, alg=Algorithm.AStar):
        # Search setup
        self.query = queryAutomaton
        self.g = None
        self.stats = None
        self._reset()

        # Options
        self.alg = alg
        self.quick_goal = quick_goal

        # Search
        self.open   = Heap()
        self.closed = set()
        self.states = {}
        self.startNS = None

        if self.quick_goal:
            Color.BLUE.print("Using quick goal declaration")
            self._advanceHeuristic()
        else:
            Color.BLUE.print("Using regular goal declaration")

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

    def _advanceHeuristic(self):
        """
        Shift heuristic to avoid computing best children on every expansion
        """
        for s in self.query.states.values():
            h = INFTY

            # pylint: disable=protected-access
            for ns in s._next():
                if ns._h < h:
                    h = ns._h
            s.h = h
        Color.GREEN.print("Queue-Skipping Heuristic:")
        for s in self.query.states.values():
            Color.GREEN.print("  * %s" % s)


    def _get(self, n, q, parent, P, t, d):
        """
        Gets the *Unique* NodeState for a (node, state) pair.
        It builds new NodeStates as needed.
        """
        # pylint: disable=too-many-arguments

        if (n, q) not in self.states:
            if P is None  or  t is None  or  d is None:
                raise Exception("First get MUST init the new NodeState")
            self.states[(n, q)] = ASLDSearch.NodeState(n,q, parent, P,t,d)

        return self.states[(n, q)]


    def _pop(self):
        (_, ns) = self.open.pop()
        return ns


    @classmethod
    def getPath(cls, ns):
        """
        Retrieves a path by following parent nodes

        Assumes that no loops exist
        """
        path = []
        while ns is not None:
            path.append(ns)
            ns = ns.parent
        path.reverse()
        return path


    def _enqueue(self, ns):
        """
        Adds a NodeState to Open

        This function sets the priority used which defines the algorithm's
          behavior.

        DFS can be implemented with only a stack, but loop prevention requires
          similar overhead.
        BFS could also be lighter (no tie-breaking), but on the web, CPU use
          is negligible when considering the communication delay.
        """
        if   self.alg == Algorithm.AStar:
            # Least f
            # Tie break towards greater g
            k = (ns.g + ns.q.h, -ns.g)
        elif self.alg == Algorithm.Dijkstra:
            # Least g
            # Tie break towards lower h
            #k = (ns.g, ns.q.h)
            k = (ns.g, 0)
        elif self.alg == Algorithm.DFS:
            # Most g
            # Tie break towards lower h
            #k = (-ns.g, ns.q.h)
            k = (-ns.g, 0)

        if ns.q.h < INFTY:
            # quick_goal marks useless expansions with h=INFTY
            self.open.push(k, ns)

        if self.quick_goal and ns.isGoal():
            return ns

        return None

    def _reach(self, ns, P, cN,cQ, t, d):
        """
        Reaches (cN, cQ) from ns using t on direction d
        Updates target node if it's reached in a better way
        """
        # pylint: disable=too-many-arguments


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
        Reaches all the neighborhood and does early goal check.

        It prefers Forward Transitions as they may bring data
          for computing the backward transitions.

        REVIEW: It may be better to force tie breaking on the heap
        """

        goalsFound = []
        if not self.quick_goal:
            if ns.isGoal():
                goalsFound = [ns]

        for t in ns.q.next_transitions_f:
            for _,P,O in self.g.query(ns.n):
                g = self._reach(ns, P, cN=O,cQ=t.dst, t=t, d=Direction.forward)
                if g and self.quick_goal:
                    goalsFound.append(g)

        for t in ns.q.next_transitions_b:
            for S,P,_ in self.g.query(None, None, ns.n):
                g = self._reach(ns, P, cN=S,cQ=t.dst, t=t, d=Direction.backward)
                if g and self.quick_goal:
                    goalsFound.append(g)

        return goalsFound


    def _extractTopF(self, batchSize):
        # Extract at most batchSize from top-f nodes
        (topF, _) = self.open.peekKey()  # key: (f, -g)

        netFreeNodes = []
        netNodes = []
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
            assert isinstance(ns, ASLDSearch.NodeState), "ns should be a NodeState"

            if ns in self.closed:
                if __debug__:
                    Color.RED.print("Discarding a closed node found on open")
                continue
            self.closed.add(ns)


            expansions += 1
            pendingExpansions += 1

            if IS_TTY:
                clearLine()
                print("  expansions (%4d): " % pendingExpansions, end="")
                print("#"*pendingExpansions, end="")

            # Goal Check
            # ==========
            # REVIEW: allow blocking goal check
            if ns.isGoal():
                gls.append(ns)

            # Add to batch
            if isinstance(ns.n, URIRef):
                if ns in self.g.loaded:
                    netFreeNodes.append(ns)  # Already gathered IRIs are faster to expand locally
                else:
                    netNodes.append(ns)
            else:
                netFreeNodes.append(ns)

        return (netFreeNodes, netNodes, gls, pendingExpansions)


    def paths(self, parallelRequests=40, batchSize=160,
              limit_time=_L_TIME, limit_ans=_L_ANS, limit_triples=_L_TRIPLES):
        """
        Performs search using parallel requests to expand top-f value NodeStates

        Reaching limits causes the search to stop doing requests, but it may
          find a few answers more with whats left.
        """
        # pylint: disable=too-many-arguments,too-many-statements,too-many-locals,too-many-branches

        deadline = None
        if limit_time:
            deadline = time() + limit_time

        # Initialize search
        _t0_search = time()
        self._enqueue(self.startNS)
        pool = AsyncTimeOutPool(parallelRequests, timeout=15)

        answers = 0
        requestsAllowed = True

        # Empty open...
        while self.open:
            # Limits check
            if requestsAllowed:
                if answers > limit_ans:
                    clearLine()
                    Color.YELLOW.print("Reached the %d-goal-limit (%d)" % (limit_ans,
                                                                           answers))
                    requestsAllowed = False
                if len(self.g) > limit_triples:
                    clearLine()
                    Color.YELLOW.print("Reached the %d-triples limit (%d)" % (limit_triples,
                                                                              len(self.g)))
                    requestsAllowed = False
                if deadline and time() > deadline:
                    clearLine()
                    Color.YELLOW.print("Reached the %ds time limit" % (limit_time))
                    requestsAllowed = False

            (netFreeNodes, netNodes, _, pendingExpansions) = self._extractTopF(batchSize)
            self.stats.batch()


            # Local expand (no requests are needed)
            # ============
            # Blocking goal check will ruin this, also, goal states should rank further
            if netFreeNodes:
                expansionsDone = 0
                _t0_localExpansions = time()
                for ns in netFreeNodes:
                    expansionsDone += 1
                    pendingExpansions -= 1
                    if IS_TTY:
                        print("\r  local expansions (%4d): " % pendingExpansions, end="")
                        print("[%s" % ("#"*expansionsDone), end="")
                        print("%s]" % ("."*pendingExpansions), end="")

                    # Expand nodes
                    # Early declare goals (Unless we implement blocking filters :c)
                    _t0_localExpand = time()
                    goalsFound = self._expand(ns)
                    for g in goalsFound:
                        answers += 1
                        self.stats.goal()
                        yield ASLDSearch.getPath(g)

                    #assert ns in self.g.loaded, "%s was already loaded." % ns
                    self.stats.expand(ns.n, 0, time()-_t0_localExpand, local=True)

                _t_end = time()
                _t_localExpansions = _t_end - _t0_localExpansions

                clearLine()
                print(" Sync expanded (%4.2fs) %3d nodes" % (_t_localExpansions, len(netFreeNodes)))


            # Parallel expand
            # ===============
            if requestsAllowed and netNodes:
                newTriples = 0
                _t0_parallelExpand = time()

                requests = [(ns.n, i, ns.SPARQL_query()) for (i, ns) in enumerate(netNodes)]

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
                    ns = netNodes[reqAns.index]
                    assert ns not in self.g.loaded, "%s was already loaded." % ns
                    self.stats.expand(iri, len(reqGraph), t, local=False)


                    # Report progress
                    if IS_TTY:
                        clearLine()
                        print("\r  || expansions (%4d): " % pendingExpansions, end="")
                        print("[%s" % ("#"*requestsFullfilled), end="")
                        print("%s]" % ("."*pendingExpansions), end="")
                        stdout.flush()


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
                        self.stats.goal()
                        yield ASLDSearch.getPath(g)

                _t_end = time()
                _t_parallelExpand = _t_end - _t0_parallelExpand

                clearLine()
                print("[%8s| ans:%5d  expansions: %6d  db:%7d (%3dMB)  t:%6.2fs] Expanded %3d nodes on %4.2fs" %
                      (self.alg,
                       answers,
                       self.stats.expansions(),
                       self.stats.db_triples(),
                       self.stats.memory(),
                       self.stats.wallClock(),
                       requestsCorrectlyFullfilled,
                       _t_parallelExpand)
                     )
                stdout.flush()

        _t_end = time()
        _t_search = time() - _t0_search

        clearLine()
        Color.BLUE.print("Search took %4.2fs" % _t_search)
        print()
        Color.GREEN.print("Open was emptied, there are no more paths")
        pool.close()

    def run(self, parallelRequests=40,
            limit_time=_L_TIME, limit_ans=_L_ANS):
        """Intended only for interactive CLI use"""
        r = []
        if self.closed:
            self._setup_search()

        _t0 = time()
        try:
            answers = 0
            self.stats.tick()  # Adjust stats clock
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
            print()
            Color.BLUE.print("Terminating search.")
        #except Exception as e:
            #Color.RED.print("Terminated Search.run on: %s" % e)
        t = time() - _t0
        Color.GREEN.print("\nSearch took %.2fs. Gathered %d triples and got back %d paths." %
                          (t,
                           len(self.g), len(r)))
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

            self.stats.tick()  # Adjust stats clock
            for path in self.paths(parallelRequests, parallelRequests,
                                   limit_time=limit_time,
                                   limit_ans=limit_ans,
                                   limit_triples=limit_triples):
                _ans.append(path)
                # printPath(path)

        except KeyboardInterrupt:
            Color.BLUE.print("\nTerminating search.")
        #except Exception as e:
            #Color.RED.print("Terminated Search.test on: %s" % e)
        t = time() - _t0

        ans = [ASLDSearch._native_path(path) for path in _ans]

        Color.GREEN.print("\nSearch took %.2fs. Gathered %d triples and got back %d paths." %
                          (t,
                           len(self.g), len(ans)))

        if DUMP_DATA:
            with open("last-db.json", 'w') as f:
                db = [{"s": s, "p": p, "o": o} for (s,p,o) in self.g.g]
                dump(db, f, indent=2)
            with open("last-ans.json", 'w') as f:
                dump(ans, f, indent=2)

        return {
            "Paths": ans,
            "PathCount": len(ans),
            "StatsHistory": [h.json() for h in self.stats.history],
            "Time": t
        }
