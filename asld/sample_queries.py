from rdflib.term import URIRef
from rdflib.namespace import Namespace, DC, FOAF, OWL, RDF, RDFS, XMLNS

from asld.utils.color_print import Color
from asld.query.direction import Direction
from asld.query.query import Query
from asld.query.query_builder import QueryBuilder

from asld.query.filter import NodeFilter_any
from asld.query.filter import NodeFilter_but
from asld.query.filter import NodeFilter_only
from asld.query.filter import NodeFilter_blacklist
from asld.query.filter import NodeFilter_whitelist
from asld.query.filter import NodeFilter_regex

from asld.query.filter import ArcFilter
from asld.query.filter import ArcFilter_blacklist
from asld.query.filter import ArcFilter_whitelist

from asld.search import ASLDSearch


# Constants
# =========
# DBPedia
DB  = Namespace(URIRef("http://dbpedia.org/"         ))
DBO = Namespace(URIRef("http://dbpedia.org/ontology/"))
# DBLP
DBLP          = Namespace(URIRef("http://dblp.l3s.de/d2r/"                 ))
DBLP_Authors  = Namespace(URIRef("http://dblp.l3s.de/d2r/resource/authors/"))
# Linked Movie DB
LMDB         = Namespace(URIRef("http://data.linkedmdb.org/"                ))
LMDB_Actors  = Namespace(URIRef("http://data.linkedmdb.org/resource/actor/" ))
LMDB_Films   = Namespace(URIRef("http://data.linkedmdb.org/resource/film/"  ))
LMDB_Movie   = Namespace(URIRef("http://data.linkedmdb.org/resource/movie/" ))
# SWRC
SWRC = Namespace(URIRef("http://swrc.ontoware.org/ontology#"))
# YAGO
YAGO = Namespace(URIRef("http://yago-knowledge.org/resource/"))



# DBLP Authors
mArenas  = DBLP_Authors["Marcelo_Arenas"  ]
jBaier   = DBLP_Authors["Jorge_A._Baier"  ]
jReutter = DBLP_Authors["Juan_L._Reutter" ]
cRiveros = DBLP_Authors["Cristian_Riveros"]
aSoto    = DBLP_Authors["Adri%C3%A1n_Soto"]
dVroc    = DBLP_Authors["Domagoj_Vrgoc"   ]

# LMDB Movies
mysticRiver = LMDB_Films["942"]
# LMDB Actors
kBacon = LMDB_Actors["29539"]
Color.GREEN.print("A few URIRefs were defined (mArenas, jBaier, jReutter, cRiveros, aSoto, dVroc;  mysticRiver;  kBacon)")


NAME=set()
NAME.add(FOAF.name)
NAME.add(RDFS.label)



# Queries
# =======
def name(n, w=1):
    a = Query(n)
    a._addTriple("s0",
                 FOAF.name, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h   = 1*w
    a.states["Name"].h = 0*w
    return a

def journals(n, w=1):
    """ dc:creator-/swrc:journal/rdfs:label """

    a = Query(n, "author")
    a._addTriple("author",
                 DC.creator, Direction.backward,
                 "jPaper", NodeFilter_regex(".*journal.*"))
    a._addTriple("jPaper",
                 SWRC.journal, Direction.forward,
                 "Journal")
    a._addTriple("Journal",
                 RDFS.label, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["author"].h      = 3*w
    a.states["jPaper"].h  = 2*w
    a.states["Journal"].h = 1*w
    a.states["Name"].h    = 0*w
    return a

def conferences(n, w=1):
    """ dc:creator-/swrc:series/rdfs:label """
    a = Query(n)
    a._addTriple("s0",
                 DC.creator, Direction.backward,
                 "Paper")
    a._addTriple("Paper",
                 SWRC.series, Direction.forward,
                 "Conf")
    a._addTriple("Conf",
                 RDFS.label, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h    = 3*w
    a.states["Paper"].h = 2*w
    a.states["Conf"].h  = 1*w
    a.states["Name"].h  = 0*w
    return a


# Coauthors
def coAuth(n, w=1):
    # Works
    a = Query(n)
    a._addTriple("s0",
                 DC.creator, Direction.backward,
                 "Paper1")
    a._addTriple("Paper1",
                 DC.creator, Direction.forward,
                 "CoAuth", NodeFilter_but(n))
    a._addTriple("CoAuth",
                 FOAF.name, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h     = 3*w
    a.states["Paper1"].h = 2*w
    a.states["CoAuth"].h = 1*w
    a.states["Name"].h   = 0*w
    return a

def coAuthStar(n, w=1):
    # Works
    a = Query(n)
    a._addTriple("s0",
                 DC.creator, Direction.backward,
                 "Paper1")
    a._addTriple("Paper1",
                 DC.creator, Direction.forward,
                 "CoAuth", NodeFilter_but(n))

    a._addTriple("CoAuth",
                 DC.creator, Direction.backward,
                 "Paper2")
    a._addTriple("Paper2",
                 DC.creator, Direction.forward,
                 "CoAuth")

    a._addTriple("CoAuth",
                 FOAF.name, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h     = 3*w
    a.states["Paper1"].h = 2*w
    a.states["CoAuth"].h = 1*w
    a.states["Name"].h   = 0*w
    a.states["Paper2"].h = 2*w
    return a

def _coAuthStar(n, w=1):
    # TODO: check heuristic build
    b = ASLDQueryBuilder(n)
    b.frm().through(DC.creator).backwards_to("Paper1")
    b.frm("Paper1").through(DC.creator).to("CoAuth", ff=NodeFilter_but(n))

    b.frm("CoAuth").through(DC.creator).backwards_to("Paper2")
    b.frm("Paper2").through(DC.creator).to("CoAuth")

    b.frm("CoAuth").through(FOAF.name).final("Name")

    a = b.build()
    #a.states["s0"].h     = 3*w
    #a.states["Paper1"].h = 2*w
    #a.states["CoAuth"].h = 1*w
    #a.states["Paper2"].h = 2*w
    assert a.states["s0"].h     == 3
    assert a.states["Paper1"].h == 2
    assert a.states["CoAuth"].h == 1
    assert a.states["Paper2"].h == 2
    return a


# LMDB
# ----
# Directors
def directors(n, w=1):
    """ Expected: {A dbo:starring^    -/      dbo:director/foaf:name ?x}
        Used:     {A lmdbMovie:actor^ -/lmdbMovie:director/foaf:name ?x} """

    a = Query(n)
    a._addTriple("s0",
                 LMDB_Movie.actor, Direction.backward,
                 "Movie")
    a._addTriple("Movie",
                 LMDB_Movie.director, Direction.forward,
                 "Director")
    a._addTriple("Director",
                 NAME, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h       = 3*w
    a.states["Movie"].h    = 2*w
    a.states["Director"].h = 1*w
    a.states["Name"].h     = 0*w
    return a

def coActor(n, w=1):
    a = Query(n)
    a._addTriple("s0",
                 LMDB_Movie.actor, Direction.backward,
                 "Movie")
    a._addTriple("Movie",
                 LMDB_Movie.actor, Direction.forward,
                 "CoActor", NodeFilter_but(n))

    a._addTriple("CoActor",
                 NAME, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h      = 3*w
    a.states["Movie"].h   = 2*w
    a.states["CoActor"].h = 1*w
    a.states["Name"].h    = 0*w
    return a

def coActorStar(n, w=1):
    a = Query(n)
    a._addTriple("s0",
                 LMDB_Movie.actor, Direction.backward,
                 "Movie")
    a._addTriple("Movie",
                 LMDB_Movie.actor, Direction.forward,
                 "CoActor", NodeFilter_but(n))

    a._addTriple("CoActor",
                 LMDB_Movie.actor, Direction.backward,
                 "Movie2")
    a._addTriple("Movie2",
                 LMDB_Movie.actor, Direction.forward,
                 "CoActor")

    a._addTriple("CoActor",
                 NAME, Direction.forward,
                 "Name", None, NodeFilter_any())
    a.states["s0"].h      = 3*w
    a.states["Movie"].h   = 2*w
    a.states["CoActor"].h = 1*w
    a.states["Name"].h    = 0*w
    a.states["Movie2"].h  = 2*w
    return a


# YAGO
# ----
def NATO_business(n=YAGO["Berlin"], w=1):
    # ?x yago:isLocatedIn* ?country
    #    yago:dealsWith    ?area
    #     rdf:type         yago:wikicat_Member_states_of_NATO
    a = Query(n)
    a._addTriple("s0",
                 YAGO.isLocatedIn, Direction.forward,
                 "Place")

    a._addTriple("Place",
                 YAGO["isLocatedIn"], Direction.forward,
                 "Place")

    a._addTriple("Place",
                 YAGO["dealsWith"], Direction.forward,
                 "Area")

    a._addTriple("Area",
                 RDF["type"], Direction.forward,
                 "NATO", None, NodeFilter_only(YAGO["wikicategory_Member_states_of_NATO"]))

    a.states["s0"].h    = 3*w
    a.states["Place"].h = 2*w
    a.states["Area"].h  = 1*w
    a.states["NATO"].h  = 0*w
    return a

def NATO_business_r(n=YAGO["Berlin"], w=1):
    # ?x yago:isLocatedIn* ?country
    #    yago:dealsWith    ?area
    #     rdf:type         yago:wikicat_Member_states_of_NATO
    a = Query(YAGO["wikicategory_Member_states_of_NATO"])
    a._addTriple("s0",
                 RDF["type"], Direction.backward,
                 "Area")
    a._addTriple("s0",
                 RDF["type"], Direction.forward,
                 "Area")

    a._addTriple("Area",
                 YAGO["dealsWith"], Direction.backward,
                 "Place", None, NodeFilter_only(n))

    a._addTriple("Place",
                 YAGO["isLocatedIn"], Direction.forward,
                 "Place")

    a.states["s0"].h    = 2*w
    a.states["Area"].h  = 1*w
    a.states["Place"].h = 0*w
    return a


# Init
# ====


#def NATO(n=YAGO["wikicategory_Member_states_of_NATO"], w=1):
def NATO(n=YAGO["wikicat_Member_states_of_NATO"], w=1):
    # TODO: check heuristic build
    b = ASLDQueryBuilder(n, "NationType")
    b.frm("NationType").through(RDF["type"]).backwards_to("Area")
    b.frm("Area").through(YAGO["dealsWith"]).backwards_to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).backwards_final("Place_f")

    a = b.build()
    a.states["NationType"].h = 3*w
    a.states["Area"].h       = 2*w
    a.states["Place"].h      = 1*w
    a.states["Place_f"].h    = 0*w

    assert a.states["NationType"].h == 3*w
    assert a.states["Area"].h       == 2*w
    assert a.states["Place"].h      == 1*w
    assert a.states["Place_f"].h    == 0*w
    return a


def Europe(n=YAGO["wikicategory_Capitals_in_Europe"], w=1):
    # TODO: check heuristic build
    b = ASLDQueryBuilder(n, "EuropeCapitals")
    b.frm("EuropeCapitals").through(RDF["type"]).backwards_to("Capital")
    b.frm("Capital").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["dealsWith"]).to("Area")

    a = b.build()
    a.states["EuropeCapitals"].h = 3*w
    a.states["Capital"].h        = 2*w
    a.states["Place"].h          = 1*w
    a.states["Area"].h           = 0*w

    assert a.states["EuropeCapitals"].h == 3*w
    assert a.states["Capital"].h        == 2*w
    assert a.states["Place"].h          == 1*w
    assert a.states["Area"].h           == 0*w
    return a


def Airports(n=YAGO["wikicategory_Airports_in_the_Netherlands"], w=1):
    # TODO: check heuristic build
    b = ASLDQueryBuilder(n, "Airports")
    b.frm("Airports").through(RDF["type"]).backwards_to("airport")
    b.frm("airport").through(YAGO["isLocatedIn"]).final("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    a = b.build()
    a.states["Airports"].h = 2*w
    a.states["airport"].h  = 1*w
    a.states["Place"].h    = 0*w

    assert a.states["Airports"].h == 2*w
    assert a.states["airport"].h  == 1*w
    assert a.states["Place"].h    == 0*w
    return a


print("DBLP: examples")
print("  * f(coAuthStar(jBaier))")
print("  * f(coAuth(jReutter))")
print("  * f(name(dVroc))")
print("")

print("LMDB examples:")
print("  * f(directors(kBacon))")
print("  * f(coActorStar(kBacon))")
print("")

print("YAGO examples:")
#print("  * f(NATO_business())")
print("  * f(NATO())")
print("  * f(Europe())")
print("  * f(Airports())")
print("")
