from time import time

from rdflib import Graph
from rdflib.term import URIRef

from utils.color_print import Color



class ASLDGraph:
    """
    RDF Graph

    B suffix on blocking calls
    """

    @classmethod
    def print_triple(cls, s, p, o):
        print("%80s (%-40s) %50s" % (Color.RED(s), Color.GREEN(p), Color.YELLOW(o)))


    @classmethod
    def pure_loadB(cls, i__iri):
        (i, iri) = i__iri
        assert isinstance(iri, URIRef)

        for attempt in range(3):
            try:
                g = Graph()
                g.load(iri)
                return (i, iri, g)
            except Exception as e:
                Color.YELLOW.print("Request-%d for '%s' failed: %s" % (attempt, iri, e))

        return (i, iri, None)


    class Stats:
        class Snapshot:
            def __init__(self):
                self.size           = 0
                self.requestTime    = 0
                self.solutionsFound = 0
                self.tripleRecv     = 0

        def __init__(self):
            self.requestsCompleted = 0
            self.requestsFailed    = 0
            self.requestsAttempted = 0
            self.snapshots = [ASLDGraph.Stats.Snapshot()]

        def snap(self):
            self.snapshots.append(ASLDGraph.Stats.Snapshot())


    def __init__(self):
        self.g      = Graph()
        self.loaded = set()
        self.failed = set()

        self.stats = ASLDGraph.Stats()

    def loadB(self, iri: URIRef) -> bool:
        """Loads resource data if needed"""
        assert isinstance(iri, URIRef)

        if iri in self.loaded:
            return True

        try:
            self.g.load(iri)
        except Exception as e:
            self.failed.add(iri)
            Color.RED.print("Loading '%s' failed. (%s)." % (iri, e))

    def retryFailedB(self) -> int:
        """Attempts to get failed requests again"""
        pending = [r for r in self.failed]
        self.failed = set()

        for req in pending:
            self.loadB(req)
        return len(pending)

    def print(self, G=None):
        """Pretty prints a graph or a query"""
        if G is None:
            G = self.g

        for s, p, o in G:
            print_triple(s, p, o)

    def print_query(self, s=None, p=None, o=None):
        self.print(self.query(s, p, o))

    def print_queryB(self, s=None, p=None, o=None):
        self.print(self.queryB(s, p, o))

    def query(self, s=None, p=None, o=None):
        """Queries the current graph"""

        for S,P,O in self.g.triples((s, p, o)):
            yield (S, P, O)

    def queryB(self, s=None, p=None, o=None):
        """Queries the graph after requesting s or o"""
        if o is None:
            self.loadB(s)
        elif s is None:
            self.loadB(o)

        return self.query(s, p, o)
