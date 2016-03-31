from time import time
from multiprocessing import Pool
from signal import SIGINT, SIG_IGN, signal

from rdflib.term import URIRef, Literal

from asld.utils.heap import Heap
from asld.utils.color_print import Color

from asld.graph import ASLDGraph
from asld.query.direction import Direction
from asld.query.query import Query
from asld.query.state import State
from asld.query.transition import Transition


def _worker_ignore_SIGINT():
    signal(SIGINT, SIG_IGN)


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
            assert node.__class__ is URIRef  or  node.__class__ is Literal

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



    def __init__(self, queryAutomaton: Query):
        self.g = ASLDGraph()
        self.query = queryAutomaton

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


    def _getPath(self, ns):
        path = []
        while ns is not None:
            path.append(ns)
            ns = ns.parent
        path.reverse()
        return path


    def _reach(self, ns, P, cN,cQ, t, d):
        """Reaches (cN, cQ) from ns using t on direction d"""

        if not t(P):
            return  # Predicate not allowed by t

        if not cQ(cN):
            return  # Destination Node not allowed by q

        cns = self._get(cN,cQ, parent=ns, P=P, t=t, d=d)
        if cns in self.closed:
            return  # target node already expanded

        # Reach
        newCost = ns.g + 1
        if newCost >= cns.g:
            return  # Nothing to see here...

        # Update child
        cns.parent = ns

        cns.g = newCost

        cns.P = P
        cns.t = t
        cns.d = d

        # Enqueue child
        self._enqueue(cns)

    def _expand(self, ns):

        for t in ns.q.next_transitions_f:
            for _,P,O in self.g.query(ns.n):
                self._reach(ns, P, cN=O,cQ=t.dst, t=t, d=Direction.forward)

        for t in ns.q.next_transitions_b:
            for S,P,_ in self.g.query(None, None, ns.n):
                self._reach(ns, P, cN=S,cQ=t.dst, t=t, d=Direction.backward)


    def _paths(self):
        """Performs search using a single process"""
        # Initialize search
        _t0_search = time()
        self._enqueue(self.startNS)

        # Empty open...
        while self.open:
            _t0_localExpand = time()

            # Extract a single top-F node
            ns = self._pop()

            if ns in self.closed:
                if __debug__:
                    Color.RED.print("Discarding a closed node found on open")
                continue

            # Goal Check
            # ==========
            # REVIEW: allow blocking goal check
            if ns.q.accepts(ns.n):
                yield ns
                continue

            # Blocking load
            self.g.loadB(ns.n)

            # Local expand
            self._expand(ns)
            _t_localExpand = time() - _t0_localExpand
            print("\r Sync expanded (%5.2fs) %s" % (_t_localExpand, ns))

        _t_search = time() - _t0_search
        Color.BLUE.print("\nSearch took %4.2fs" % _t_search)
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
            print("\r  expansions (%4d): %s" % (pendingExpansions, "."*pendingExpansions), end="")

            # Goal Check
            # ==========
            # REVIEW: allow blocking goal check
            if ns.q.accepts(ns.n):
                gls.append(ns)
                continue

            # Add to batch
            if ns not in self.g.loaded:
                if isinstance(ns.n, URIRef):
                    pnd.append(ns)
                else:
                    rdy.append(ns)
            else:
                rdy.append(ns)

        return (rdy, pnd, gls, pendingExpansions)

    def paths(self, parallelRequests=40, batchSize=160):
        """
        Performs search using parallel requests to expand top-f value NodeStates
        """
        if parallelRequests<2:
            return self._paths()

        # Initialize search
        _t0_search = time()
        self._enqueue(self.startNS)
        pool = Pool(parallelRequests, _worker_ignore_SIGINT)  # Workaround python mp-bug

        # Empty open...
        while self.open:
            (rdy, pnd, gls, pendingExpansions) = self._extractTopF(batchSize)

            # Declare goals (building this list adds overhead :c)
            for g in gls:
                yield self._getPath(g)

            # Local expand (no requests are needed (blocking goal check will ruin this))
            # ============
            if rdy:
                _t0_localExpand = time()
                for ns in rdy:
                    pendingExpansions -= 1
                    print("\r  expansions (%4d): %s" % (pendingExpansions, "."*pendingExpansions), end="")

                    # Expand nodes
                    self._expand(ns)
                _t_end = time()
                _t_localExpand = _t_end - _t0_localExpand
                print("\r Sync expanded (%4.2fs) %3d nodes" % (_t_localExpand, len(rdy)))

            # Parallel expand
            # ===============
            if pnd:
                newTriples = 0
                _t0_parallelExpand = time()
                requests = [(i, ns.n, ns.q._next_P(), ns.q.hasBackwardTransition()) for (i, ns) in enumerate(pnd)]

                Color.BLUE.print("\nMapping %d requests:" % len(requests))
                for (i, iri, reqGraph) in pool.imap_unordered(ASLDGraph.pure_loadB, requests):
                    pendingExpansions -= 1
                    print("\r  expansions (%4d): %s" % (pendingExpansions, "."*pendingExpansions), end="")

                    if reqGraph is None:  # Request failed
                        Color.RED.print("\nRequest[%d] for '%s' failed" % (i, iri))
                        continue

                    ns = pnd[i]

                    # merge graphs
                    newTriples += len(reqGraph)
                    for spo in reqGraph:
                        self.g.g.add(spo)

                    # Expand nodes
                    self._expand(ns)

                _t_end = time()
                _t_parallelExpand = _t_end - _t0_parallelExpand
                print("\rAsync expanded (%4.2fs) %3d nodes" % (_t_parallelExpand, len(pnd)))

        _t_end = time()
        _t_search = time() - _t0_search
        Color.BLUE.print("\nSearch took %4.2fs" % _t_search)
        Color.GREEN.print("\nOpen was emptied, there are no more paths")
        pool.close()

    def run(self):
        """Intended only for interactive CLI use"""
        r = []
        try:
            for p in self.paths():
                r.append(p)
        except KeyboardInterrupt:
            Color.BLUE.print("\nTerminating search.")
        except Exception as e:
            Color.RED.print("Terminated on: %s" % e)
        return r
