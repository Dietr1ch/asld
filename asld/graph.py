from time import time
from re import compile as regex_compile

from rdflib import Graph
from rdflib.term import URIRef
from SPARQLWrapper import SPARQLWrapper, JSON

from asld.utils.color_print import Color


# Document servers that are known to provide incomplete inverses, but have a SPARQL endpoint.
scumbag_servers = set()
scumbag_servers.add((regex_compile("^http://yago-knowledge.org/resource/.*"), "https://linkeddata1.calcul.u-psud.fr/sparql"))
scumbag_servers.add((regex_compile("^https://makemake.ing.puc.cl/resource/.*"), "https://localhost:8890/sparql"))
#scumbag_servers.add((regex_compile("^http://yago-knowledge.org/resource/.*"), "http://rdf.framebase.org:82/sparql"))


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
            return """
                SELECT ?P, ?O
                WHERE {
                    <%s> ?P ?O.
                    %s
                }
                """ % (s, flt)
        elif s is None:
            return """
                SELECT ?S, ?P
                WHERE {
                    ?S ?P <%s>.
                    %s
                }""" % (o, flt)
        assert False, "Unexpected query; Either S or O should be given (%s,%s,%s)" % (s, p, o)

    @classmethod
    def print_triple(cls, s, p, o):
        print("%80s (%-40s) %50s" % (Color.RED(s), Color.GREEN(p), Color.YELLOW(o)))

    @classmethod
    def pure_load_evil_SPARQL_reverseB(cls, iri, p):
        """
        Expands reverse arcs from evil servers that have incomplete documents.
        """
        g = Graph()
        for r, endpoint in scumbag_servers:
            if r.match(iri):
                Color.BLUE.print("Looking up on the SPARQL endpoint (server's documents tend to omit backward edges)")

                (p_b, _) = p  # Descriptions for backward and forward predicates

                se = SPARQLWrapper(endpoint)
                queryString = ASLDGraph._sparql_query(None, p_b, iri)
                se.setQuery(queryString)
                se.setReturnFormat(JSON)

                for _ in range(3):
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
                        print("SPARQL reverse query %s yielded %d triples back" % (iri, len(results)))
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

        # Get the document
        for _ in range(3):
            try:
                g.load(iri)
                break
            except Exception:
                pass

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
