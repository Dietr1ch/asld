from asld.query.direction import Direction
from asld.query.filter import NodeFilter
from asld.utils.color_print import Color


class State:

    _explain_allowance         = False
    _explain_allowance_trivial = False
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
        self.name = name
        self.h = float("inf")

        self.filterFunction = f
        self.acceptingFunction = a

        # Transitions from this state
        self.prev_transitions_b = set()  # Backward Transitions that reach this state
        self.prev_transitions_f = set()  # Forward Transitions that reach this state
        self.next_transitions_b = set()  # Backward Transitions available from this state
        self.next_transitions_f = set()  # Forward Transitions available from this state



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
        return "State '%s'" % self.name

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
