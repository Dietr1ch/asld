from time import time, sleep
from re import compile as regex_compile
from json import load as json_load
from bisect import bisect
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
DELAY_RESOLUTION = 0.05
with open("request-acc.json", 'r') as raf:
    DELAYS = json_load(raf)
    DELAY_MAX = DELAYS[-1]
if DELAYS is None or len(DELAYS) <= 10:
    DELAYS = None
    DELAY_MAX = None
else:
    Color.YELLOW.print("Delay data loaded")


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
    def _sparql_query(cls, s, P, o):
        """
        Builds a SPARQL query to expand a node (s or o) over a set of predicates P

        There is NO support for complemented Arcs. (they are marginally easier than getting all arcs)
        Is there even a real query that needs complement? It seems a non-invertable ArcFilter is plain useless
        """

        # Disjunction of sameTERMs of P elements   ("sT(?P, p_0) || sT(?P, p_1) || ..." \forall p_i \in P)
        flt = ""
        if P:  # P exists and is non-empty
            flt = " || ".join(  map(lambda p: "sameTERM(?P, <%s>)"%p, P)  )
            flt = "FILTER (%s)" % flt

        if o is None:
            return ("""
                SELECT ?P, ?O
                WHERE {
                    <%s> ?P ?O.
                    %s
                }
                """ % (s, flt)).strip()
        elif s is None:
            return ("""
                SELECT ?S, ?P
                WHERE {
                    ?S ?P <%s>.
                    %s
                }""" % (o, flt)).strip()
        assert False, "Unexpected query; Either S or O should be given (%s,%s,%s)" % (s, p, o)

    @classmethod
    def print_triple(cls, s, p, o):
        print("%80s (%-40s) %50s" % (Color.RED(s), Color.GREEN(p), Color.YELLOW(o)))

    @classmethod
    def pure_load_evil_SPARQL(cls, iri, p):
        """
        Expands forward arcs using SPARQL.
        """
        g = Graph()
        for r, endpoint in SPARQL_ENDPOINTS:
            if r.match(iri):

                (_, p) = p
                # Color.BLUE.print("Looking up '%s' on the SPARQL endpoint" % iri)

                se = SPARQLWrapper(endpoint)
                queryString = ASLDGraph._sparql_query(iri, p, None)
                se.setQuery(queryString)
                se.setReturnFormat(JSON)

                for _ in range(2):  # Try twice before failing
                    try:
                        results = se.query().convert()
                        results = results["results"]["bindings"]

                        for result in results:
                            P = URIRef(result["P"]["value"])
                            O = URIRef(result["O"]["value"])
                            try:
                                g.add((iri, P, O))
                            except:
                                pass
                        #print("SPARQL forward query %s yielded %d triples back" % (iri, len(results)))
                        #if len(results)==0:
                            #Color.YELLOW.print("Empty query to %s:\n%s" % (endpoint, queryString))
                        return g

                    except Exception as e:
                        Color.RED.print(e)
                        pass
                Color.RED.print("SPARQL Request '%s%s" % (Color.GREEN(queryString), Color.RED("' failed")))
                Color.YELLOW.print("The server's SPARQL endpoint (%s) is unavailable" % endpoint)
        return g

    @classmethod
    def pure_load_evil_SPARQL_reverseB(cls, iri, p):
        """
        Expands backward arcs using SPARQL.
        """
        g = Graph()
        for r, endpoint in SPARQL_ENDPOINTS:
            if r.match(iri):
                # Color.BLUE.print("Looking up '%s' on the SPARQL endpoint (server's documents tend to omit backward edges)" % iri)

                (p_b, _) = p  # Descriptions for backward and forward predicates

                se = SPARQLWrapper(endpoint)
                queryString = ASLDGraph._sparql_query(None, p_b, iri)
                se.setQuery(queryString)
                se.setReturnFormat(JSON)

                for _ in range(2):  # Try twice before failing
                    try:
                        results = se.query().convert()
                        results = results["results"]["bindings"]

                        for result in results:
                            S = URIRef(result["S"]["value"])
                            P = URIRef(result["P"]["value"])
                            try:
                                g.add((S, P, iri))
                            except:
                                pass
                        #print("SPARQL reverse query %s yielded %d triples back" % (iri, len(results)))
                        if len(results)==0:
                            Color.YELLOW.print("Query to %s:" % endpoint)
                            Color.YELLOW.print(queryString)
                        return g

                    except Exception:
                        pass
                Color.RED.print("SPARQL Request '%s%s" % (Color.GREEN(queryString), Color.RED("' failed")))
                Color.YELLOW.print("The server's SPARQL endpoint (%s) is unavailable" % endpoint)
        return g

    @classmethod
    def pure_loadB(cls, iri__i__p__hBT):
        """
        Expands an IRI.
        Uses a neighbor description for narrowing SPARQL inverses

        Returns a RequestAnswer (~named tuple)
        """
        # Unwrap parameters
        (iri, i, p, hBT) = iri__i__p__hBT
        assert isinstance(iri, URIRef)

        _t0 = time()
        # Get new triples
        g = Graph()
        if hBT:
            # Workaround for evil servers on backward transitions
            # This adds extra time on those servers :c
            g = ASLDGraph.pure_load_evil_SPARQL_reverseB(iri, p)
        else:
            g = ASLDGraph.pure_load_evil_SPARQL(iri, p)
        #else:
            #g = ASLDGraph.pure_load_evil_SPARQL(iri, p)

        # Get the document
        for _ in range(2):
            try:
                g.load(iri)
                break
            except:
                pass

        # Simulate network delays (there is no compensation on longer delays)
        if DELAYS:
            # Pick a sample and wait for it's delay.
            delay_simulated = randint(0, DELAY_MAX)
            delay = bisect(DELAYS, delay_simulated)*DELAY_RESOLUTION

            spent_time = time() - _t0
            wait_time = delay - spent_time

            if wait_time > 0:
                print("wating for %f.4s" % wait_time)
                sleep(wait_time)
            else:
                print("wating %.4s < spent %.4s" % (delay, spent_time))
                print("wating failed (%f.4s)" % wait_time)


        return ASLDGraph.RequestAnswer(g, iri, i, time()-_t0)



    def __init__(self):
        self.g      = Graph()
        self.loaded = set()
        self.failed = set()

    def __len__(self):
        return len(self.g)

    def add(self, spo):
        self.g.add(spo)


    def loadB(self, iri: URIRef) -> bool:
        """
        Loads resource data if needed
        """
        assert isinstance(iri, URIRef)

        if iri in self.loaded:
            return (False, 0)

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
        self.print(self.query(s, p, o))

    def print_queryB(self, s=None, p=None, o=None):
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
