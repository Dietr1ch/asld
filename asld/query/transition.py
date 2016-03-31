from rdflib.term import URIRef

from asld.query.state import State
from asld.query.direction import Direction
from asld.utils.color_print import Color


class Transition:

    _explain_allowance  = False

    def __init__(self,
                 src: State,
                 arc_filter, direction,
                 dst: State):

        self.src = src
        self.dst = dst

        self.arc_filter = arc_filter
        self.direction = direction

        # Update states transitions
        if self.direction is Direction.forward:
            self.src.next_transitions_f.add(self)
            self.dst.prev_transitions_f.add(self)
        elif self.direction is Direction.backward:
            self.src.next_transitions_b.add(self)
            self.dst.prev_transitions_b.add(self)

    def prev(self):
        """Returns the state that uses this Transition"""
        if self.direction is Direction.forward:
            return self.src
        return self.dst

    def next(self):
        """Returns the state reached by using this Transition"""
        if self.direction is Direction.forward:
            return self.dst
        return self.src


    def inverse(self):
        """
        Returns the set allowed by the Transition
        Or None if the Inverse is not defined/allowed
        """
        return self.arc_filter.inverse()


    def __call__(self, p: URIRef) -> bool:
        r = self.arc_filter(p)

        if Transition._explain_allowance:
            if r:
                Color.GREEN.print("  Arc %s allowed by %s" % (p, self.arc_filter))
            else:
                Color.RED.print(  "  Arc %s rejected by %s" % (p, self.arc_filter))

        return r


    def __str__(self) -> str:
        s = "---"
        if self.arc_dir == Direction.backward:
            s = "~~~"
        return "(%s %s> %s)" % (self.origin, s, self.dest)

    def __repr__(self):
        return str(self)
