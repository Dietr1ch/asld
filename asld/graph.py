"""
Wrapper over `rdflib` Graph with support for SPARQL
"""
from time import time, sleep
from re import compile as regex_compile
from json import load as json_load
from bisect import bisect_right
from random import randint

from rdflib import Graph
from rdflib.term import URIRef
from SPARQLWrapper import SPARQLWrapper, JSON

from asld.utils.color_print import Color


# Known SPARQL endpoint that provide incomplete inverses (unnecessary if documents are complete).
SPARQL_ENDPOINTS = set()
SPARQL_ENDPOINTS.add((regex_compile("^http://yago-knowledge.org/resource/.*"),
                      "https://linkeddata1.calcul.u-psud.fr/sparql"))
SPARQL_ENDPOINTS.add((regex_compile("^https://makemake.ing.puc.cl/resource/.*"),
                      "http://localhost:8890/sparql/"))


# Set up delays
DELAYS = None
DELAY_MAX = None
DELAY_RESOLUTION = 0.01
DELAY_FILE = "data/request-acc.json"

with open(DELAY_FILE, 'r') as raf:
    DELAYS = json_load(raf)
    DELAY_MAX = DELAYS[-1]

if DELAYS is None or len(DELAYS) <= 10:
    DELAYS = None
    DELAY_MAX = None
else:
    Color.YELLOW.print("Delay data loaded (resolution: %.3fs, samples: %d)" % (DELAY_RESOLUTION,
                                                                               DELAY_MAX))


class ASLDGraph:
    """
    RDF Graph

    B suffix on blocking calls
    """

    class RequestAnswer:
        """
        Answer for a iri request
        Acts as a named tuple
        """
        # pylint: disable=too-few-public-methods

        def __init__(self, g, iri, index, reqTime):
            self.g = g
            self.iri = iri
            self.index = index
            self.reqTime = reqTime

        def __len__(self):
            return len(self.g)

        def __str__(self):
            return "RequestAnswer<%s>" % self.iri


    @classmethod
    def print_triple(cls, s, p, o):
        """Pretty prints an RDF triple"""
        print("%80s (%-40s) %50s" % (Color.RED(s), Color.GREEN(p), Color.YELLOW(o)))

    @classmethod
    def pure_load_SPARQL(cls, iri, queryString: str) -> Graph:
        """
        Expands using SPARQL query against a known endpoint.
        """
        g = Graph()
        for r, endpoint in SPARQL_ENDPOINTS:
            if r.match(iri):
                se = SPARQLWrapper(endpoint)
                se.setQuery(queryString)
                se.setReturnFormat(JSON)

                for _ in range(2):  # Try twice before failing
                    # pylint: disable=broad-except

                    try:
                        results = se.query().convert()
                        results = results["results"]["bindings"]

                        for result in results:
                            # pylint: disable=bare-except
                            try:
                                S = URIRef(result["s"]["value"])
                                P = URIRef(result["p"]["value"])
                                O = URIRef(result["o"]["value"])
                                g.add((S, P, O))
                            except:
                                pass
                        return g

                    except Exception as e:
                        Color.RED.print("Query failed '%s'" % e)

                #pylint: disable=line-too-long
                Color.RED.print("SPARQL Request '%s%s" % (Color.GREEN(queryString), Color.RED("' failed")))
                Color.YELLOW.print("The server's SPARQL endpoint (%s) is unavailable" % endpoint)
        return g


    @classmethod
    def pure_loadB(cls, iri__i__qf):
        """
        Expands an IRI.
        Uses a neighbor description for narrowing SPARQL inverses

        Returns a RequestAnswer (~named tuple)
        """
        # Unwrap parameters
        (iri, i, sparqlFormat) = iri__i__qf
        assert isinstance(iri, URIRef)

        _t0 = time()
        # Get new triples
        g = ASLDGraph.pure_load_SPARQL(iri, sparqlFormat)

        # Get the document
        for _ in range(2):
            # pylint: disable=bare-except
            try:
                g.load(iri)
                break
            except:
                pass

        # Simulate network delays (there is no compensation on longer delays)
        if DELAYS:
            # Pick a sample and wait for it's delay.
            delay_simulated = randint(0, DELAY_MAX)+1
            delay = bisect_right(DELAYS, delay_simulated)*DELAY_RESOLUTION

            spent_time = time() - _t0
            wait_time = delay - spent_time

            if wait_time > 0:
                # print("wating for %5.2fs (%5.2fs)" % (delay, wait_time))
                sleep(wait_time)
            else:
                print("waiting %7.4fs < spent %7.4fs" % (delay, spent_time))


        return ASLDGraph.RequestAnswer(g, iri, i, time()-_t0)



    def __init__(self):
        self.g      = Graph()
        self.loaded = set()
        self.failed = set()

    def __len__(self):
        return len(self.g)

    def add(self, spo):
        """Add an RDF triple to the graph"""
        self.g.add(spo)


    def loadB(self, iri: URIRef) -> bool:
        """
        Loads resource data if needed
        """
        assert isinstance(iri, URIRef)

        if iri in self.loaded:
            return (False, 0)

        # pylint: disable=broad-except
        try:
            old = len(self.g)
            self.g.load(iri)
            incr = len(self.g)-old

            return (True, incr)
        except Exception as e:
            self.failed.add(iri)
            Color.RED.print("Loading '%s' failed. (%s)." % (iri, e))

        return (True, 0)

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
            ASLDGraph.print_triple(s, p, o)

    def print_query(self, s=None, p=None, o=None):
        """Queries the current graph and prints the result"""
        self.print(self.query(s, p, o))

    def print_queryB(self, s=None, p=None, o=None):
        """Queries the graph and prints the result after requesting s or o"""

        self.print(self.queryB(s, p, o))

    def query(self, s=None, p=None, o=None):
        """Queries the current graph"""

        for S,P,O in self.g.triples((s, p, o)):
            yield (S, P, O)

    def queryB(self, s=None, p=None, o=None):
        """ Queries the graph after requesting s or o """
        if o is None:
            self.loadB(s)
        elif s is None:
            self.loadB(o)

        return self.query(s, p, o)
