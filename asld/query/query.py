from rdflib.term import URIRef

from asld.query.state import State
from asld.query.transition import Transition
from asld.query.direction import Direction
from asld.query.filter import ArcFilter, ArcFilter_whitelist
from asld.utils.color_print import Color


class Query:
    """
    (Automaton, RDFNode) pair that defines a path-query on Linked Data

    Future work:
    RDFNode is unneeded if we implement invertable-nodes search
    (Regular search has an invertable start node)
    """

    def __init__(self, iri: URIRef, name="s0", ff=None, af=None):
        self.states = {}
        self.startState = self._addState(name, ff, af)
        self.startNode  = iri


    def __str__(self) -> str:
        return "Automaton-Query with states {%s}" % self.states.keys()
    def __repr__(self):
        return str(self)


    def addState(self, name, ff=None, af=None):
        """Interactive state add"""
        if name in self.states:
            Color.RED.print("State '%s' already exists, it won't be updated!!" % name)
        return self._addState(name, ff, af)

    def _addState(self, name, ff=None, af=None):
        """Adds a new state or returns the old one (unchanged)"""
        if name not in self.states:
            self.states[name] = State(name, ff, af)

        return self.states[name]


    def _addTriple(self,
                   originName,
                   arc_filter:  ArcFilter,
                   arc_direction:  Direction,
                   destName,
                   dff = None,
                   daf = None):
        """Creates a Transition to a possibly new State"""

        assert isinstance(originName, str)
        assert isinstance(  destName, str)

        assert isinstance(arc_direction,  Direction)

        # Accept singletons as sets
        if not isinstance(arc_filter, ArcFilter):
            if isinstance(arc_filter, set):
                # Use sets for whitelists
                arc_filter = ArcFilter_whitelist(arc_filter)
            else:
                # Use element as singleton whitelist
                _s = set()
                _s.add(arc_filter)
                arc_filter = ArcFilter_whitelist(_s)

        # Get states
        o = self.states[originName]
        d = self._addState(destName, dff, daf)  # (gracefully create new states =))

        return Transition(o, arc_filter, arc_direction, d)
