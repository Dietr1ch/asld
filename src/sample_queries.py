from rdflib.term import URIRef
from rdflib.namespace import Namespace, DC, FOAF, OWL, RDF, RDFS, XMLNS

from utils.color_print import Color
from query import ASLDQuery, Direction, FilterType, NodeFilter

from search import ASLDSearch


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
    a = ASLDQuery(n)
    a.addTriple("s0",
                FOAF.name, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h   = 1*w
    a.states["Name"].h = 0*w
    return a

def journals(n, w=1):
    """ dc:creator-/swrc:journal/rdfs:label """

    a = ASLDQuery(n, "author")
    a.addTriple("author",
                DC.creator, Direction.backward, FilterType.whitelist,
                "jPaper", NodeFilter.regex(".*journal.*"))
    a.addTriple("jPaper",
                SWRC.journal, Direction.forward, FilterType.whitelist,
                "Journal")
    a.addTriple("Journal",
                RDFS.label, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["author"].h      = 3*w
    a.states["jPaper"].h  = 2*w
    a.states["Journal"].h = 1*w
    a.states["Name"].h    = 0*w
    return a

def conferences(n, w=1):
    """ dc:creator-/swrc:series/rdfs:label """

    a = ASLDQuery(n)
    a.addTriple("s0",
                DC.creator, Direction.backward, FilterType.whitelist,
                "Paper")
    a.addTriple("Paper",
                SWRC.series, Direction.forward, FilterType.whitelist,
                "Conf")
    a.addTriple("Conf",
                RDFS.label, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h    = 3*w
    a.states["Paper"].h = 2*w
    a.states["Conf"].h  = 1*w
    a.states["Name"].h  = 0*w
    return a


# Coauthors
def coAuth(n, w=1):
    a = ASLDQuery(n)
    a.addTriple("s0",
                DC.creator, Direction.backward, FilterType.whitelist,
                "Paper1")
    a.addTriple("Paper1",
                DC.creator, Direction.forward, FilterType.whitelist,
                "CoAuth", NodeFilter.but(n))
    a.addTriple("CoAuth",
                FOAF.name, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h     = 3*w
    a.states["Paper1"].h = 2*w
    a.states["CoAuth"].h = 1*w
    a.states["Name"].h   = 0*w
    return a

def coAuthStar(n, w=1):
    a = ASLDQuery(n)
    a.addTriple("s0",
                DC.creator, Direction.backward, FilterType.whitelist,
                "Paper1")
    a.addTriple("Paper1",
                DC.creator, Direction.forward, FilterType.whitelist,
                "CoAuth", NodeFilter.but(n))

    a.addTriple("CoAuth",
                DC.creator, Direction.backward, FilterType.whitelist,
                "Paper2")
    a.addTriple("Paper2",
                DC.creator, Direction.forward, FilterType.whitelist,
                "CoAuth")

    a.addTriple("CoAuth",
                FOAF.name, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h     = 3*w
    a.states["Paper1"].h = 2*w
    a.states["CoAuth"].h = 1*w
    a.states["Name"].h   = 0*w
    a.states["Paper2"].h = 2*w
    return a

def _coAuthStar(n, w=1):
    b = LDAutomatonBuilder(n)
    b.frm().through(DC.creator).backwards_to("Paper1")
    b.frm("Paper1").through(DC.creator).to("CoAuth", ff=NodeFilter.but(n))

    b.frm("CoAuth").through(DC.creator).backwards_to("Paper2")
    b.frm("Paper2").through(DC.creator).to("CoAuth")

    b.frm("CoAuth").through(FOAF.name).final("Name")

    a = b.build()
    a.states["s0"].h     = 3*w
    a.states["Paper1"].h = 2*w
    a.states["CoAuth"].h = 1*w
    a.states["Paper2"].h = 2*w
    return a


# LMDB
# ----
# Directors
def directors(n, w=1):
    """ Expected: {A dbo:starring^    -/      dbo:director/foaf:name ?x}
        Used:     {A lmdbMovie:actor^ -/lmdbMovie:director/foaf:name ?x} """

    a = ASLDQuery(n)
    a.addTriple("s0",
                LMDB_Movie.actor, Direction.backward, FilterType.whitelist,
                "Movie")
    a.addTriple("Movie",
                LMDB_Movie.director, Direction.forward, FilterType.whitelist,
                "Director")
    a.addTriple("Director",
                NAME, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h       = 3*w
    a.states["Movie"].h    = 2*w
    a.states["Director"].h = 1*w
    a.states["Name"].h     = 0*w
    return a

def coActor(n, w=1):
    a = ASLDQuery(n)
    a.addTriple("s0",
                LMDB_Movie.actor, Direction.backward, FilterType.whitelist,
                "Movie")
    a.addTriple("Movie",
                LMDB_Movie.actor, Direction.forward, FilterType.whitelist,
                "CoActor", NodeFilter.but(n))

    a.addTriple("CoActor",
                NAME, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
    a.states["s0"].h      = 3*w
    a.states["Movie"].h   = 2*w
    a.states["CoActor"].h = 1*w
    a.states["Name"].h    = 0*w
    return a

def coActorStar(n, w=1):
    a = ASLDQuery(n)
    a.addTriple("s0",
                LMDB_Movie.actor, Direction.backward, FilterType.whitelist,
                "Movie")
    a.addTriple("Movie",
                LMDB_Movie.actor, Direction.forward, FilterType.whitelist,
                "CoActor", NodeFilter.but(n))

    a.addTriple("CoActor",
                LMDB_Movie.actor, Direction.backward, FilterType.whitelist,
                "Movie2")
    a.addTriple("Movie2",
                LMDB_Movie.actor, Direction.forward, FilterType.whitelist,
                "CoActor")

    a.addTriple("CoActor",
                NAME, Direction.forward, FilterType.whitelist,
                "Name", None, NodeFilter.any())
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
    a = ASLDQuery(n)
    a.addTriple("s0",
                YAGO.isLocatedIn, Direction.forward, FilterType.whitelist,
                "Place")

    a.addTriple("Place",
                YAGO["isLocatedIn"], Direction.forward, FilterType.whitelist,
                "Place")

    a.addTriple("Place",
                YAGO["dealsWith"], Direction.forward, FilterType.whitelist,
                "Area")

    a.addTriple("Area",
                RDF["type"], Direction.forward, FilterType.whitelist,
                "NATO", None, NodeFilter.only(YAGO["wikicategory_Member_states_of_NATO"]))
                #"NATO", None, NodeFilter.any())

def NATO_business_r(n=YAGO["Berlin"], w=1):
    # ?x yago:isLocatedIn* ?country
    #    yago:dealsWith    ?area
    #     rdf:type         yago:wikicat_Member_states_of_NATO
    a = ASLDQuery(YAGO["wikicategory_Member_states_of_NATO"])
    a.addTriple("s0",
                RDF["type"], Direction.backward, FilterType.whitelist,
                "Area")
    a.addTriple("s0",
                RDF["type"], Direction.forward, FilterType.whitelist,
                "Area")

    a.addTriple("Area",
                YAGO["dealsWith"], Direction.backward, FilterType.whitelist,
                "Place", None, NodeFilter.only(n))

    a.addTriple("Place",
                YAGO["isLocatedIn"], Direction.forward, FilterType.whitelist,
                "Place")

    a.states["s0"].h  = 2*w
    a.states["Area"].h  = 1*w
    a.states["Place"].h = 0*w
    return a


# Init
# ====

print("DBLP: examples")
print("  * f(coAuthStar(jBaier))")
print("  * f(coAuth(jReutter))")
print("  * f(name(dVroc))")

print("LMDB examples:")
print("  * f(directors(kBacon))")
print("  * f(coActorStar(kBacon))")

print("YAGO examples:")
print("  * f(NATO_business())")
