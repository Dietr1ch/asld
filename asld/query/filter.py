from re import compile as regex_compile

from ..utils.color_print import Color


class Filter:
    """
    A Filter is a function that accepts or rejects something.
    """

    def __call__(self, _) -> bool:
        """
        Checks if a IRI (or string) is allowed by the filter
        """
        raise Exception("wtf??, Implement the filter function please")

    def __str__(self) -> str:
        return Color.YELLOW.print("BaseFilter<>")

    def __repr__(self) -> str:
        return str(self)

    def inverse(self):
        """
        Computes the IRI set that is matched by the filter
        Returns None if no Inverse is computable
        """
        return None


# Arcs
# ====
class ArcFilter(Filter):
    """
    An ArcFilter is a function that accepts or rejects IRI arcs.
    """

    def __call__(self, _) -> bool:
        """Checks if a IRI (or string) is allowed by the ArcFilter"""
        raise Exception("wtf??, Implement the ArcFilter function please")

    def __str__(self) -> str:
        return Color.YELLOW.print("ArcFilter<>")


class ArcFilter_any(ArcFilter):
    """ Dummy filter """

    def __call__(self, node) -> bool:
        return True

    def __str__(self) -> str:
        return Color.GREEN("ArcFilter_any<>")


class ArcFilter_whitelist(ArcFilter):

    def __init__(self, s: set):
        assert isinstance(s, set)
        self.s = s

    def __call__(self, node) -> bool:
        return node in self.s

    def __str__(self) -> str:
        return Color.GREEN("ArcFilter_whitelist<%s>" % self.s)

    def inverse(self) -> set:
        return self.s


class ArcFilter_blacklist(ArcFilter):

    def __init__(self, s: set):
        assert isinstance(s, set)
        self.s = s

    def __call__(self, node) -> bool:
        return node not in self.s

    def __str__(self) -> str:
        return Color.GREEN("ArcFilter_blacklist<%s>" % self.s)


# Nodes
# =====
class NodeFilter(Filter):
    """
    An NodeFilter is a function that accepts or rejects IRI or String Nodes.
    """

    def __call__(self, _) -> bool:
        """Checks if a IRI (or string) is allowed by the NodeFilter"""
        raise Exception("wtf??, Implement the NodeFilter function please")

    def __str__(self) -> str:
        return Color.YELLOW.print("NodeFilter<>")


class NodeFilter_any(NodeFilter):
    """Not really a filter D:"""

    def __call__(self, _) -> bool:
        return True

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_any<>")


class NodeFilter_only(NodeFilter):

    def __init__(self, n):
        self.n = n
        self.nodeSet = set()
        self.nodeSet.add(n)

    def __call__(self, node) -> bool:
        return node == self.n

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_only<%s>" % self.n)

    def inverse(self) -> set:
        return self.nodeSet


class NodeFilter_but(NodeFilter):

    def __init__(self, n):
        self.n = n

    def __call__(self, node) -> bool:
        return node != self.n

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_but<%s>" % self.n)


class NodeFilter_regex(NodeFilter):

    def __init__(self, regex: str):
        self.expr = regex
        self.r = regex_compile(regex)

    def __call__(self, node) -> bool:
        return self.r.match(node)

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_regex<%s>" % self.expr)


class NodeFilter_whitelist(NodeFilter):

    def __init__(self, s: set):
        self.s = s

    def __call__(self, node) -> bool:
        return node in self.s

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_whitelist<%s>" % self.s)

    def inverse(self) -> set:
        return self.s


class NodeFilter_blacklist(NodeFilter):

    def __init__(self, s: set):
        self.s = s

    def __call__(self, node) -> bool:
        return node not in self.s

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_blacklist<%s>" % self.s)


# Combiners
# =========
class AtLeast(Filter):
    """
    Combines filters requiring at least K acceptances to accept
    """

    def __init__(self, filters: [], required_acceptances: int):
        assert len(filters > 0), "Some filters are required"
        assert required_acceptances <= len(filters), "You can't require more acceptances than filters"

        self.filters = filters
        self.required_acceptances = required_acceptances

    def __call__(self, node) -> bool:
        acceptances = 0
        for flt in self.filters:
            if flt(node):
                acceptances += 1
                if acceptances >= self.required_acceptances:
                    return True
        return False

    def __str__(self) -> str:
        return Color.GREEN("AtLeast-%d-Filter<%s>" % (self.required_acceptances, self.filters))


class AtMost(Filter):
    """
    Combines filters requiring at most K acceptances to accept.
    """

    def __init__(self, filters: [], maximum_acceptances: int):
        assert len(filters > 0), "Some filters are required"
        assert maximum_acceptances < len(filters), "You shouldn't require less than 1 failure, use an And filter instead"

        self.filters = filters
        self.maximum_acceptances = maximum_acceptances
        self.needed_rejects = len(self.filters) - self.maximum_acceptances + 1  # The +1 finishes the 'proof'

    def __call__(self, node) -> bool:
        rejects = 0
        for flt in self.filters:
            if not flt(node):
                rejects += 1
                if rejects >= self.needed_rejects:
                    return True
        return False

    def __str__(self) -> str:
        return Color.GREEN("AtMost-%d-Filter<%s>" % (self.maximum_acceptances, self.filters))


class And(Filter):
    """
    Combines filters requiring at least K acceptances to accept
    """

    def __init__(self, filters: []):
        assert len(filters > 0), "Some filters are required"

        self.filters = filters

    def __call__(self, node) -> bool:
        for flt in self.filters:
            if not flt(node):
                return False
        return True

    def __str__(self) -> str:
        return Color.GREEN("And-Filter<%s>" % self.filters)


class Or(Filter):
    """
    Combines filters requiring at least K acceptances to accept
    """

    def __init__(self, filters: []):
        assert len(filters > 0), "Some filters are required"

        self.filters = filters

    def __call__(self, node) -> bool:
        for flt in self.filters:
            if flt(node):
                return True
        return False

    def __str__(self) -> str:
        return Color.GREEN("Or-Filter<%s>" % self.filters)
