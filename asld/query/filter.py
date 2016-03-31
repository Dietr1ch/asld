from re import compile as regex_compile

from ..utils.color_print import Color


class Filter:
    """
    A Filter is a function that accepts or rejects something.
    """

    def __init__(self):
        if __debug__:
            Color.GREEN.print("Created base Filter")

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

    def __init__(self):
        if __debug__:
            Color.GREEN.print("Created ArcFilter")

    def __call__(self, _) -> bool:
        """Checks if a IRI (or string) is allowed by the ArcFilter"""
        raise Exception("wtf??, Implement the ArcFilter function please")

    def __str__(self) -> str:
        return Color.YELLOW.print("ArcFilter<>")


class ArcFilter_whitelist(ArcFilter):

    def __init__(self, s: set):
        self.s = s
        Color.GREEN.print("Created ArcFilter_whitelist<%s> lambda" % self.s)

    def __call__(self, node) -> bool:
        return node in self.s

    def __str__(self) -> str:
        return Color.GREEN("ArcFilter_whitelist<%s>" % self.s)

    def inverse(self) -> set:
        return self.s


class ArcFilter_blacklist(ArcFilter):

    def __init__(self, s: set):
        self.s = s
        Color.GREEN.print("Created ArcFilter_blacklist<%s> lambda" % self.s)

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

    def __init__(self):
        if __debug__:
            Color.GREEN.print("Created NodeFilter")

    def __call__(self, _) -> bool:
        """Checks if a IRI (or string) is allowed by the NodeFilter"""
        raise Exception("wtf??, Implement the NodeFilter function please")

    def __str__(self) -> str:
        return Color.YELLOW.print("NodeFilter<>")


class NodeFilter_any(NodeFilter):
    """Not really a filter D:"""

    def __init__(self):
        Color.GREEN.print("Created NodeFilter_any<> lambda")

    def __call__(self, _) -> bool:
        return True

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_any<>")


class NodeFilter_only(NodeFilter):

    def __init__(self, n):
        Color.GREEN.print("Created NodeFilter_only<%s> lambda" % n)
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
        Color.GREEN.print("Created NodeFilter_but<%s> lambda" % n)
        self.n = n

    def __call__(self, node) -> bool:
        return node != self.n

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_but<%s>" % self.n)


class NodeFilter_regex(NodeFilter):

    def __init__(self, regex: str):
        self.expr = regex
        self.r = regex_compile(regex)
        Color.GREEN.print("Created NodeFilter_regex<%s> lambda" % self.expr)

    def __call__(self, node) -> bool:
        return self.r.match(node)

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_regex<%s>" % self.expr)


class NodeFilter_whitelist(NodeFilter):

    def __init__(self, s: set):
        self.s = s
        Color.GREEN.print("Created NodeFilter_whitelist<%s> lambda" % self.s)

    def __call__(self, node) -> bool:
        return node in self.s

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_whitelist<%s>" % self.s)

    def inverse(self) -> set:
        return self.s


class NodeFilter_blacklist(NodeFilter):

    def __init__(self, s: set):
        self.s = s
        Color.GREEN.print("Created NodeFilter_blacklist<%s> lambda" % self.s)

    def __call__(self, node) -> bool:
        return node not in self.s

    def __str__(self) -> str:
        return Color.GREEN("NodeFilter_blacklist<%s>" % self.s)


if __name__ is "__main__":
    Color.GREEN.print("=)")
