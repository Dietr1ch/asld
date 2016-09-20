"""
Property-Automata States
"""
from asld.query.filter import NodeFilter
from asld.utils.color_print import Color


class State:
    """
    A State of the Property Automaton
    """
    # pylint: disable=too-many-instance-attributes

    _fine_grained_sparql_queries = True

    _explain_allowance          = False
    _explain_allowance_trivial  = False
    _explain_acceptance         = False
    _explain_acceptance_trivial = False


    def __init__(self, name, f: NodeFilter=None, a: NodeFilter=None):
        """
        A State allows or reject Nodes, possibly accepting some as goals.
        States also allow a (partial) path to reach new States by any of the
          available outgoing transitions.
        """
        if __debug__:
            Color.GREEN("Creating State(name: '%s', ff:%s, af:%s)" % (name, f, a))

        self._ready = False

        # State
        # -----
        self.name = name
        self.filterFunction    = f  # Filter to check if an IRI is allowed
        self.acceptingFunction = a  # Filter to check if an IRI is accepted

        # Transitions
        # -----------
        self.prev_transitions_b = set()  # Backward Transitions that reach this state
        self.prev_transitions_f = set()  # Forward  Transitions that reach this state
        self.next_transitions_b = set()  # Backward Transitions available from this state
        self.next_transitions_f = set()  # Forward  Transitions available from this state

        # Search
        # ------
        self.h  = float("inf")  # Heuristic value (might differ from _h for some algorithms)
        self._h = float("inf")  # Standard heuristic value

        # SPARQL Query
        # ------------
        self._sparql_format = ""  # Format to build SPARQL queries
        # Outgoing predicates
        self.predicates_f = set()  # Predicates on Forward Transitions
        self.predicates_b = set()  # Predicates on Backward Transitions


    def _prev(self):
        """ States that can reach this one """
        prev_set = set()

        for t in self.prev_transitions_b:
            prev_set.add(t.src)
        for t in self.prev_transitions_f:
            prev_set.add(t.src)
        return prev_set

    def _next(self):
        """ States reachable from this one """
        next_set = set()

        for t in self.next_transitions_b:
            next_set.add(t.dst)
        for t in self.next_transitions_f:
            next_set.add(t.dst)

        return next_set


    def _next_P(self):
        """
        Returns a pair of sets of outgoing predicates
        (backward_P, forward_P)
        """
        backward_P = set()
        forward_P  = set()

        for t in self.next_transitions_b:
            if backward_P is not None:
                inv = t.inverse()
                if inv is None:
                    backward_P = None
                    break
                else:
                    backward_P |= inv

        for t in self.next_transitions_f:
            if forward_P is not None:
                inv = t.inverse()
                if inv is None:
                    forward_P = None
                    break
                else:
                    forward_P |= inv

        return (backward_P, forward_P)


    def __call__(self, node) -> bool:
        """ Approval function """

        if self.filterFunction is None:
            if State._explain_acceptance_trivial:
                Color.YELLOW.print("  State trivially allows '%s'" % node)
            return True

        r = self.filterFunction(node)
        if State._explain_acceptance:
            if r:
                Color.YELLOW.print("  State '%s' (%s)    allows '%s'" % (self.name, self.filterFunction, node))
            else:
                Color.RED.print(   "  State '%s' (%s) disallows '%s'" % (self.name, self.filterFunction, node))
        return r

    def accepts(self, node) -> bool:
        """ Accepting function """
        if self.acceptingFunction is None:
            if State._explain_acceptance_trivial:
                Color.RED.print(   "  State '%s' (%s)   rejects '%s'" % (self.name, self.acceptingFunction, node))
            return False


        r = self.acceptingFunction(node)
        if State._explain_acceptance:
            if r:
                Color.GREEN.print( "  State '%s' (%s) accepts '%s'" % (self.name, self.acceptingFunction, node))
            else:
                Color.YELLOW.print("  State '%s' (%s) rejects '%s'" % (self.name, self.acceptingFunction, node))
        return r


    def __str__(self) -> str:
        if self.h == float("inf"):
            return "State (oo) '%12s'" % (self.name)
        return "State (%2d) '%12s'" % (self.h, self.name)

    def __repr__(self) -> str:
        return str(self)


    def __lt__(self, other) -> bool:
        return self.name < other.name


    def isFinal(self):
        """ Checks if this State may match a goal """
        return self.acceptingFunction is not None

    def hasBackwardTransition(self):
        """ (States with backward transitions cannot be fully expanded, ever) """
        return len(self.next_transitions_b) > 0


    def prepare(self):
        """
        Finishes up precomputing and mark as ready
        """
        assert not self._ready, "%s was marked ready, no preparation was already done" % (self)

        self._ready = True

        # Save original heuristic value
        self._h = self.h

        # SPARQL query
        # ------------
        # Forward and Backward predicates might be needed
        # Predicates might have a known inverse

        self._sparql_format = ""
        # Prepare filters
        # $\bigvee_{i \in P}  sameTERM(?P, p_i)$

        # Build forward  filter string
        forward_flt = None
        if self.predicates_f is not None:
            # Forward  predicates are needed
            if State._fine_grained_sparql_queries and len(self.predicates_f):
                # There is a known inverse
                forward_flt  = " || ".join( ["sameTERM(?P, <%s>)"%p for p in self.predicates_f] )
                forward_flt = " && (%s)" % forward_flt    # prepend the &&
            else:
                # Every predicate might be useful
                forward_flt = " "

        # Build backward filter string
        backward_flt = None
        if self.predicates_b is not None:
            # Backward predicates are needed
            if State._fine_grained_sparql_queries and len(self.predicates_b):
                # There is a known inverse
                backward_flt = " || ".join( ["sameTERM(?P, <%s>)"%p for p in self.predicates_b] )
                backward_flt = "&& (%s)" % backward_flt  # Prepend the &&
            else:
                # Every predicate might be useful
                backward_flt = " "

        if forward_flt and backward_flt:
            # Both directions are needed
            self._sparql_format = """
            select ?s ?p ?o where {{
                {{ ?s ?p ?o.  filter (sameTERM(?s, {0})  %s) }}
              union
                {{ ?s ?p ?o.  filter (sameTERM(?o, {0})  %s) }}
            }}
            """ % (forward_flt, backward_flt)
        elif forward_flt:
            self._sparql_format = """
            select ?s ?p ?o where {{
              ?s ?p ?o.
              filter (sameTERM(?s, {0}) %s)
            }}
            """ % forward_flt
        elif backward_flt:
            self._sparql_format = """
            select ?s ?p ?o where {{
              ?s ?p ?o.
              filter (sameTERM(?o, {0}) %s)
            }}
            """ % backward_flt

    def register_outgoing_transition(self, t):
        """
        Registers an outgoing transition.

        Used to build SPARQL queries
        """
        assert not self._ready, "%s was marked ready, no new transitions allowed" % (self)

        if t.src != self:
            Color.RED.print("Tried to register a non-matching outgoing transition")
            return

    def SPARQL_query(self, iri):
        """
        Builds a SPARQL query to expand a Node-State
        """
        assert self._ready, "%s was not yet ready" % (self)

        return self._sparql_format.format("<%s>" % iri)
