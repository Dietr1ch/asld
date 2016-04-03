from rdflib.term import URIRef

from asld.query.state import State
from asld.query.direction import Direction
from asld.utils.color_print import Color


class Transition:
    """
    A transition allows moving from State src to State dst using a triple
      allowed by a filter in an specific direction.

    The transition may require the triple forward or not,
    src -- P --> dst   (src, p', dst)
    src ~~ P ~~> dst   (dst, p', src)
    """

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


    def inverse(self):
        """
        Returns the set allowed by the Transition
        Or None if the Inverse is not defined (or unreasonable to compute)
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
        if self.direction == Direction.backward:
            s = "~~~"
        return "(%s %s> %s)" % (self.src, s, self.dst)

    def __repr__(self):
        return str(self)
