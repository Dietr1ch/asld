from rdflib.term import URIRef
from asld.query.direction import Direction
from asld.query.query import Query
from asld.query.filter import Filter, ArcFilter, ArcFilter_whitelist, ArcFilter_blacklist

from asld.utils.heap import Heap
from asld.utils.color_print import Color


class QueryBuilder:

    class _S:
        def __init__(self, a, originName: str):
            self.a = a
            self.originName = originName

        def through(self, arc_set):
            if not isinstance(arc_set, set):
                arc_set = set(arc_set)
            return ASLDQueryBuilder._SP(self, FilterType.whitelist(arc_set))
        def through_not(self, arc_set):
            if not isinstance(arc_set, set):
                arc_set = set(arc_set)
            return ASLDQueryBuilder._SP(self, FilterType.blacklist(arc_set))

        def to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              set(), Direction.forward, FilterType.blacklist,
                              destName, ff, af)
        def backwards_to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              set(), Direction.backward, FilterType.blacklist,
                              destName, ff, af)

        def final(self, destName):
            self.to(destName, None, NodeFilter.any())
        def backwards_final(self, destName):
            self.backwards_to(destName, None, NodeFilter.any())

    class _SP:
        def __init__(self, arc_filter: ArcFilter):
            self.a = _s.a
            self.originName = _s.originName

            self.arc_filter = arc_filter

        def to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              set(), Direction.forward, FilterType.blacklist,
                              destName, ff, af)
        def backwards_to(self, destName, ff=None, af=None):
            if destName in self.a.states.keys():
                assert ff is None
                assert af is None
            self.a._addTriple(self.originName,
                              set(), Direction.backward, FilterType.blacklist,
                              destName, ff, af)

        def final(self, destName):
            self.to(destName, None, NodeFilter.any())
        def backwards_final(self, destName):
            self.backwards_to(destName, None, NodeFilter.any())


    def __init__(self, n:URIRef, name="s0", ff=None, af=None):
        self.startNode = n
        self.startName = name
        self.a = ASLDQuery(n, name, ff, af)

    def frm(self, nodeName=None):
        if nodeName is None:
            nodeName = self.startName
        return ASLDQueryBuilder._S(self.a, nodeName)

    def build(self):
        stateNames = self.a.states.keys()
        reachedStates = set()
        remainingStates = set()

        _open = Heap()

        for sn in stateNames:
            if self.a.states[sn].acceptingFunction is not None:
                self.a.states[sn].h = 0
                _open.push(0, sn)
                reachedStates.add(sn)
            else:
                remainingStates.add(sn)

        while _open:
            (h, sn) = _open.pop()

            for cS in self.a.states[sn]._next():
                if cS.h > h+1:
                    reachedStates.add(cS)

                    cS.h = h+1
                    if cS in remainingStates:
                        remainingStates.remove(cS)

        if remainingStates:
            Color.RED.print("Some states were not reached: %s" % remainingStates)
            Color.YELLOW.print("States reached: %s" % reachedStates)

        return self.a
