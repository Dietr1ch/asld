"""
Helper classes to build Property-Automata
"""
from rdflib.term import URIRef
from asld.query.transition import Direction
from asld.query.query import Query
from asld.query.filter import Filter
from asld.query.filter import NodeFilter, NodeFilter_any
from asld.query.filter import ArcFilter, ArcFilter_any, ArcFilter_whitelist, ArcFilter_blacklist

from asld.utils.heap import Heap
from asld.utils.color_print import Color


class QueryBuilder:


    class _S:

        def __init__(self, a, originName: str):
            self.a = a
            self.originName = originName


        def through(self, arc_set):
            if not isinstance(arc_set, set):
                _set = set()
                _set.add(arc_set)
                arc_set = _set
            return QueryBuilder._SP(self, ArcFilter_whitelist(arc_set))

        def through_not(self, arc_set):
            if not isinstance(arc_set, set):
                _set = set()
                _set.add(arc_set)
                arc_set = _set
            return QueryBuilder._SP(self, ArcFilter_blacklist(arc_set))


        def to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None, "State was already defined"
                assert af is None, "State was already defined"
            self.a._addTriple(self.originName,
                              ArcFilter_any(), Direction.forward,
                              destName, ff, af)

        def backwards_to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None, "State was already defined"
                assert af is None, "State was already defined"
            self.a._addTriple(self.originName,
                              ArcFilter_any(), Direction.backward,
                              destName, ff, af)


        def final(self, destName, flt=None):
            self.to(destName, flt, NodeFilter_any())

        def backwards_final(self, destName, flt=None):
            self.backwards_to(destName, flt, NodeFilter_any())


    class _SP:

        def __init__(self, _s, arc_filter: ArcFilter):
            self.a = _s.a
            self.originName = _s.originName

            self.arc_filter = arc_filter


        def to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              self.arc_filter, Direction.forward,
                              destName, ff, af)

        def backwards_to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              self.arc_filter, Direction.backward,
                              destName, ff, af)


        def final(self, destName, flt=None):
            self.to(destName, flt, NodeFilter_any())

        def backwards_final(self, destName, flt=None):
            self.backwards_to(destName, flt, NodeFilter_any())


    def __init__(self, n:URIRef, name="s0", ff=None, af=None):
        self.startNode = n
        self.startName = name
        self.a = Query(n, name, ff, af)

    def frm(self, nodeName=None):
        if nodeName is None:
            nodeName = self.startName
        return QueryBuilder._S(self.a, nodeName)

    def build(self, w=1):
        """
        Computes the heuristic for a given Query
        """
        states = self.a.states.values()
        reachedStates = set()
        remainingStates = set()

        _open = Heap()

        for s in states:
            if s.acceptingFunction is not None:
                s.h = 0
                _open.push(0, s)
                reachedStates.add(s)
            else:
                remainingStates.add(s)

        if not reachedStates:
            Color.RED.print("No states reached!")
            Color.RED.print("States were not reached: %s" % remainingStates)
            raise Exception("Query has no goal, please review it!")

        while _open:
            (h, s) = _open.pop()

            for cS in s._prev():
                if h+w < cS.h:
                    reachedStates.add(cS)
                    _open.push(h+w, cS)

                    cS.h = h+w
                    if cS in remainingStates:
                        remainingStates.remove(cS)

        if remainingStates:
            Color.RED.print("Some states were not reached: %s" % remainingStates)
            Color.YELLOW.print("States reached: %s" % reachedStates)
            raise Exception("Query is probably unfinished, please review it")

        reached = [(s.h, s) for s in reachedStates]
        reached.sort()

        if __debug__:
            Color.GREEN.print("Heuristic:")
            for (h, s) in reached:
                Color.GREEN.print("  * %d: %s" % (h, s))

        for s in states:
            s._h = s.h

        return self.a
