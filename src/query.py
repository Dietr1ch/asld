from enum import Enum
from rdflib.term import URIRef

from utils.color_print import Color


class Direction(Enum):
    """Arc direction"""
    forward  = True,
    backward = False

class FilterType(Enum):
    """Filter type"""
    whitelist = True,
    blacklist = False


def iri(s: str) -> URIRef:
    if s is not URIRef:
        return URIRef(s)
    return s


# Query explanation

## State
_e_state             = False  # Explain state allowance
_e_stateT            = False  # Explain trivial state allowance
_e_state_acceptance  = False  # Explain state acceptance
_e_state_acceptanceT = False  # Explain trivial state allowance

## Transition
_e_transition = False  # Explain transition allowance


class NodeFilter:
    class any:
        def __init__(self):
            Color.GREEN.print("Created any<> lambda")
        def __call__(self, _):
            return True
        def __str__(self):
            return Color.GREEN.print("any<>")
        def __repr__(self):
            return str(self)

    class only:
        def __init__(self, n):
            Color.GREEN.print("Created only<%s> lambda" % n)
            self.n = n
        def __call__(self, node):
            return node == self.n
        def __str__(self):
            return Color.GREEN.print("only<%s>" % self.n)
        def __repr__(self):
            return str(self)

    class but:
        def __init__(self, n):
            Color.GREEN.print("Created but<%s> lambda" % n)
            self.n = n
        def __call__(self, node):
            return node != self.n
        def __str__(self):
            return Color.GREEN.print("but<%s>" % self.n)
        def __repr__(self):
            return str(self)

    class regex:
        def __init__(self, regex: str):
            self.expr = regex
            self.r = re.compile(regex)
            Color.GREEN.print("Created regex<%s> lambda" % self.expr)
        def __call__(self, node):
            return self.r.match(node)
        def __str__(self):
            return Color.GREEN.print("regex<%s>" % self.expr)
        def __repr__(self):
            return str(self)

    class whitelist:
        def __init__(self, s: set):
            self.s = s
            Color.GREEN.print("Created whitelist<%s> lambda" % self.s)
        def __call__(self, node):
            return node in self.s
        def __str__(self):
            return Color.GREEN.print("whitelist<%s>" % self.s)
        def __repr__(self):
            return str(self)

    class blacklist:
        def __init__(self, s: set):
            self.s = s
            Color.GREEN.print("Created blacklist<%s> lambda" % self.s)
        def __call__(self, node):
            return node not in self.s
        def __str__(self):
            return Color.GREEN.print("blacklist<%s>" % self.s)
        def __repr__(self):
            return str(self)


class ASLDQuery:
    """(Automaton, RDFNode) pair that defines a path-query on Linked Data"""


    class State:
        def __init__(self, name, f=None, a=None):
            if __debug__:
                Color.GREEN("Creating state")
            self.name = name

            self.filterFunction = f
            self.acceptingFunction = a

            # Transitions from this state
            self.t_f = set()
            self.t_b = set()

            # States reachable from this State
            self.next_f = set()  # Using a forward transition
            self.next_b = set()  # Using a backward transition

            # States that can reach this State
            self.prev_f = set()  # Using a forward transition
            self.prev_b = set()  # Using a backward transition

            self.h = float("inf")

        def _next(self):
            return self.next_f.union(self.next_b)  # set.union is pure

        def _prev(self):
            return self.prev_f.union(self.prev_b)  # set.union is pure

        def __call__(self, node) -> bool:
            """Approval function"""
            if self.filterFunction is None:
                if _e_stateT:
                    Color.YELLOW.print("  State trivially allows '%s'" % node)
                return True

            r = self.filterFunction(node)
            if _e_state:
                if r:
                    Color.YELLOW.print("  State '%s' (%s)    allows '%s'" % (self.name, self.filterFunction, node))
                else:
                    Color.RED.print(   "  State '%s' (%s) disallows '%s'" % (self.name, self.filterFunction, node))
            return r

        def accepts(self, node) -> bool:
            """Accepting function"""
            if self.acceptingFunction is None:
                if _e_state_acceptanceT:
                    Color.RED.print(   "  State '%s' (%s)   rejects '%s'" % (self.name, self.acceptingFunction, node))
                return False


            r = self.acceptingFunction(node)
            if _e_state_acceptance:
                if r:
                    Color.GREEN.print( "  State '%s' (%s) accepts '%s'" % (self.name, self.acceptingFunction, node))
                else:
                    Color.YELLOW.print("  State '%s' (%s) rejects '%s'" % (self.name, self.acceptingFunction, node))
            return r

        def __str__(self) -> str:
            return "State '%s'" % self.name
        def __repr__(self):
            return str(self)


    class Transition:

        def __init__(self,
                     origin,
                     arc_set:  set,
                     arc_dir:  Direction,
                     arc_type: FilterType,
                     dest):
            """Transition reaching 'dest' state from 'origin'"""

            self.origin = origin
            self.dest   = dest

            self.arc_set  = arc_set
            self.arc_dir  = arc_dir
            self.arc_type = arc_type

            # Update state reachability
            if self.arc_dir == Direction.forward:
                # origin --f--> dest
                origin.t_f.add(self)
                origin.next_f.add(dest)  # Origin can reach dest using a forward transition

                dest.prev_f.add(origin)  # Dest can reached from origin using a backward transition
            else:
                # origin ~~b~~> dest
                origin.t_b.add(self)
                origin.next_b.add(dest)  # Origin can reach dest using a backward transition

                dest.prev_b.add(origin)  # Dest can reached from origin using a backward transition

        def __call__(self, p: URIRef) -> bool:
            r = True
            # (Xor makes this unreadable)
            if self.arc_type == FilterType.whitelist:
                r = p in self.arc_set
            else:
                r = p not in self.arc_set

            if _e_transition:
                if r:
                    Color.GREEN.print("  Arc %s allowed" % p)
                else:
                    Color.RED.print(  "  Arc %s rejected" % p)

            return r

        def __str__(self) -> str:
            s = "---"
            if self.arc_dir == Direction.backward:
                s = "~~~"
            return "(%s %s> %s)" % (self.origin, s, self.dest)
        def __repr__(self):
            return str(self)



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
            self.states[name] = ASLDQuery.State(name, ff, af)

        return self.states[name]

    def addTriple(self,
                  originName,
                  arc_set:  set,
                  arc_dir:  Direction,
                  arc_type: FilterType,
                  destName,
                  dff = None,
                  daf = None):

        assert isinstance(originName, str)
        assert isinstance(  destName, str)

        assert isinstance(arc_dir,  Direction)
        assert isinstance(arc_type, FilterType)

        # Accept singletons as sets
        if arc_set.__class__ is not set:
            _s = set()
            _s.add(arc_set)
            arc_set = _s

        # Get states
        o = self.states[originName]
        d = self.addState(destName, dff, daf)  # This will gracefully create new states =)

        return ASLDQuery.Transition(o, arc_set, arc_dir, arc_type, d)
