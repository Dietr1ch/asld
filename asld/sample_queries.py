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
DBR = Namespace(URIRef("http://dbpedia.org/resource/"))

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
def name(n=jBaier, w=1):
    b = QueryBuilder(n, "Person")
    b.frm("Person").through(FOAF["name"]).final("Name")

    a = b.build(w)
    assert a.states["Person"].h  == 1*w
    assert a.states["Name"].h    == 0*w
    return a


def journals(n=jBaier, w=1):
    """ dc:creator-/swrc:journal/rdfs:label """

    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC.creator).backwards_to("jPaper", NodeFilter_regex(".*journal.*"))
    b.frm("jPaper").through(SWRC.journal).to("Journal")
    b.frm("Journal").through(RDFS.label).final("Name")

    a = b.build(w)
    assert a.states["Author"].h  == 3*w
    assert a.states["jPaper"].h  == 2*w
    assert a.states["Journal"].h == 1*w
    assert a.states["Name"].h    == 0*w
    return a


def conferences(n=jBaier, w=1):
    """ dc:creator-/swrc:series/rdfs:label """
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC.creator).backwards_to("Paper")
    b.frm("Paper").through(SWRC.series).to("Conference")
    b.frm("Conference").through(RDFS.label).final("Name")

    a = b.build(w)
    assert a.states["Author"].h      == 3*w
    assert a.states["Paper"].h       == 2*w
    assert a.states["Conference"].h  == 1*w
    assert a.states["Name"].h        == 0*w
    return a


# Coauthors
def coAuth(n=jBaier, w=1):
    # Works
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC["creator"]).backwards_to("Paper")
    b.frm("Paper").through(DC["creator"]).to("CoAuth", NodeFilter_but(n))

    b.frm("CoAuth").through(NAME).final("Name")

    a = b.build(w)
    assert a.states["Author"].h == 3*w
    assert a.states["Paper"].h  == 2*w
    assert a.states["CoAuth"].h == 1*w
    assert a.states["Name"].h   == 0*w
    return a


def coAuthStar(n=jBaier, w=1):
    # Works
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC["creator"]).backwards_to("Paper")
    b.frm("Paper").through(DC["creator"]).to("CoAuth", NodeFilter_but(n))

    b.frm("CoAuth").through(DC["creator"]).backwards_to("Paper'")
    b.frm("Paper'").through(DC["creator"]).to("CoAuth")

    b.frm("CoAuth").through(NAME).final("Name")

    a = b.build(w)
    assert a.states["Author"].h == 3*w
    assert a.states["Paper"].h  == 2*w
    assert a.states["Paper'"].h == 2*w
    assert a.states["CoAuth"].h == 1*w
    assert a.states["Name"].h   == 0*w
    return a



# LMDB
# ----
# Directors
def directors(n=kBacon, w=1):
    """ Expected: {A dbo:starring^    -/      dbo:director/foaf:name ?x}
        Used:     {A lmdbMovie:actor^ -/lmdbMovie:director/foaf:name ?x} """

    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(LMDB_Movie["actor"]).backwards_to("Movie")
    b.frm("Movie").through(LMDB_Movie["director"]).to("Director")
    b.frm("Director").through(NAME).final("Name")

    a = b.build(w)
    assert a.states["Actor"].h    == 3*w
    assert a.states["Movie"].h    == 2*w
    assert a.states["Director"].h == 1*w
    assert a.states["Name"].h     == 0*w
    return a


def CoActor_LMDB(n=kBacon, w=1):
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(LMDB_Movie["actor"]).backwards_to("Movie")
    b.frm("Movie").through(LMDB_Movie["actor"]).to("CoActor", NodeFilter_but(n))
    b.frm("CoActor").through(NAME).final("Name")

    a = b.build(w)
    assert a.states["Actor"].h   == 3*w
    assert a.states["Movie"].h   == 2*w
    assert a.states["CoActor"].h == 1*w
    assert a.states["Name"].h    == 0*w
    return a


def CoActorStar_LMDB(n=kBacon, w=1):
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(LMDB_Movie["actor"]).backwards_to("Movie")
    b.frm("Movie").through(LMDB_Movie["actor"]).to("CoActor", NodeFilter_but(n))

    b.frm("CoActor").through(LMDB_Movie["actor"]).backwards_to("Movie'")
    b.frm("Movie'").through(LMDB_Movie["actor"]).to("CoActor")  # CoActor already defined

    b.frm("CoActor").through(NAME).final("Name")

    a = b.build(w)
    assert a.states["Actor"].h   == 3*w
    assert a.states["Movie"].h   == 2*w
    assert a.states["CoActor"].h == 1*w
    assert a.states["Name"].h    == 0*w
    assert a.states["Movie'"].h  == 2*w
    return a



# DBPedia
# -------
def CoActorStar_DBpedia(n=DBR["Kevin_Bacon"], w=1):
    # PREFIX dbo: <http://dbpedia.org/ontology/>
    # PREFIX dbr: <http://dbpedia.org/resource/>

    # select * where {?x (^dbo:starring/dbo:starring)* dbr:Kevin_Bacon}

    b = QueryBuilder(n, "RootActor")
    b.frm().through(DBO["starring"]).backwards_to("Movie")
    b.frm("Movie").through(DBO["starring"]).to("CoActor", None, NodeFilter_but(n))

    b.frm("CoActor").through(DBO["starring"]).backwards_to("Movie")

    return b.build(w)


def CoActorStar_director_DBpedia(n=DBR["Kevin_Bacon"], w=1):
    # Might not be what you expect, Movies will be matched only once, leaving out multiple directors

    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(DBO["starring"]).backwards_to("Movie")
    b.frm("Movie").through(DBO["starring"]).to("Actor")


    # We can be lazy about finding out the correct direction for dbo:director (=
    b.frm("Actor").through(DBO["director"]).final("DirectedMovie")
    b.frm("Actor").through(DBO["director"]).backwards_to("DirectedMovie")  # DirectedMovie already defined

    return b.build(w)


# YAGO
# ----
def CoActorStar_YAGO(n=YAGO["Kevin_Bacon"], w=1):
    # PREFIX yago: <http://yago-knowledge.org/resource/>
    # select * where {?x (yago:actedIn/^yago:actedIn)* yago:Kevin_Bacon}

    other = NodeFilter_but(n)
    b = QueryBuilder(n, "RootActor")
    b.frm().through(YAGO["actedIn"]).to("Movie")
    b.frm("Movie").through(YAGO["actedIn"]).backwards_final("CoActor", other)

    b.frm("CoActor").through(YAGO["actedIn"]).to("Movie")

    return b.build(w)


def NATO_business(n=YAGO["Berlin"], w=1):
    # ?x yago:isLocatedIn* ?country
    #    yago:dealsWith    ?area
    #     rdf:type         yago:wikicat_Member_states_of_NATO
    b = QueryBuilder(n, "City")
    b.frm("City").through(YAGO["isLocatedIn"]).to("Place")

    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    b.frm("Place").through(YAGO["dealsWith"]).to("Area")

    b.frm("Area").through(RDF["type"]).to("NATO", None, NodeFilter_only(YAGO["wikicategory_Member_states_of_NATO"]))


    a = b.build(w)
    assert a.states["City"].h  == 3*w
    assert a.states["Place"].h == 2*w
    assert a.states["Area"].h  == 1*w
    assert a.states["NATO"].h  == 0*w
    return a


def NATO_business_r(n=YAGO["Berlin"], w=1):
    # This query is NOT answered by the yago SPARQL endpoint
    # See the endpoint struggle trying to use over 1GB of RAM (=

    # (Virtuoso 42000 Error TN...: Exceeded 1000000000 bytes in transitive temp memory.  use t_distinct, t_max or more T_MAX_memory options to limit the search or increase the pool)
    # (1000000000 bytes in transitive temp memory)

    # Endpoint: https://linkeddata1.calcul.u-psud.fr/sparql


    # PREFIX yago: <http://yago-knowledge.org/resource/>
    #
    # select ?x, ?country, ?area
    # where {
    #   ?x        yago:isLocatedIn* ?country.
    #   ?country  yago:dealsWith    ?area.
    #   ?area      rdf:type         yago:wikicat_Member_states_of_NATO
    # }

    b = QueryBuilder(YAGO["wikicat_Member_states_of_NATO"])

    b.frm("s0").through(RDF["type"]).to("Area")
    b.frm("s0").through(RDF["type"]).backwards_to("Area")

    b.frm("Area").through(YAGO["dealsWith"]).backwards_to("Place", None, NodeFilter_but(n))

    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    a = b.build(w)
    assert a.states["s0"].h    == 2*w
    assert a.states["Area"].h  == 1*w
    assert a.states["Place"].h == 0*w
    return a



def NATO(n=YAGO["wikicat_Member_states_of_NATO"], w=1):
    b = QueryBuilder(n, "NationType")
    b.frm("NationType").through(RDF["type"]).backwards_to("Area")
    b.frm("Area").through(YAGO["dealsWith"]).backwards_to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).backwards_final("Place_f")

    a = b.build(w)
    assert a.states["NationType"].h == 3*w
    assert a.states["Area"].h       == 2*w
    assert a.states["Place"].h      == 1*w
    assert a.states["Place_f"].h    == 0*w
    return a


def Europe(n=YAGO["wikicat_Capitals_in_Europe"], w=1):
    # Using wikicat_* instead of wikicategory_*

    b = QueryBuilder(n, "EuropeCapitals")
    b.frm("EuropeCapitals").through(RDF["type"]).backwards_to("Capital")
    b.frm("Capital").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["dealsWith"]).final("Area")

    a = b.build(w)
    assert a.states["EuropeCapitals"].h == 3*w
    assert a.states["Capital"].h        == 2*w
    assert a.states["Place"].h          == 1*w
    assert a.states["Area"].h           == 0*w
    return a


def Airports(n=YAGO["wikicat_Airports_in_the_Netherlands"], w=1):
    b = QueryBuilder(n, "Airports")

    b.frm("Airports").through(RDF["type"]).backwards_to("airport")
    b.frm("airport").through(YAGO["isLocatedIn"]).final("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    a = b.build(w)
    assert a.states["Airports"].h == 2*w
    assert a.states["airport"].h  == 1*w
    assert a.states["Place"].h    == 0*w
    return a




print("DBLP: examples")
print("  * coAuthStar(jBaier)")
print("  * coAuth(jReutter)")
print("  * name(dVroc)")
print("")

print("LMDB examples:")
print("  * directors(kBacon)")
print("  * coActorStar(kBacon)")
print("")

print("YAGO examples:")
print("  * NATO_business()")
print("  * NATO()")
print("  * Europe()")
print("  * Airports()")
print("")
