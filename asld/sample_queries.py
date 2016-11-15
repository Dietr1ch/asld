from rdflib.term import URIRef
from rdflib.namespace import Namespace, DC, FOAF, OWL, RDF, RDFS, XMLNS

from asld.utils.color_print import Color
from asld.query.query_builder import QueryBuilder

from asld.query.filter import NodeFilter_but
from asld.query.filter import NodeFilter_only
from asld.query.filter import NodeFilter_regex



# Constants
# =========
# DBPedia
DB  = Namespace(URIRef("http://dbpedia.org/"         ))
DBO = Namespace(URIRef("http://dbpedia.org/ontology/"))
DBP = Namespace(URIRef("http://dbpedia.org/property/"))
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
# YAGO = Namespace(URIRef("https://makemake.ing.puc.cl/resource/"))  # Mirror
YAGO = Namespace(URIRef("http://yago-knowledge.org/resource/"))

# Framebase
FRAMEBASE = Namespace(URIRef("http://framebase.org/ns/"))


# Predicates
TYPE = RDF["type"]
SAME_AS = OWL["sameAs"]


# DBLP Authors
mStonebraker  = DBLP_Authors["Michael_Stonebraker" ]
# LMDB Actors
kBacon = LMDB_Actors["29539"]

# Use  foaf:name and rdfs:label as names
NAME=set()
NAME.add(FOAF.name)
NAME.add(RDFS.label)

# Actor (dbPedia & LMDB)
ACTOR=set()
ACTOR.add(DBO["starring"])
ACTOR.add(LMDB_Movie["actor"])

# Acted_in (YAGO)
ACTED_IN=set()
ACTED_IN.add(YAGO["actedIn"])
ACTED_IN.add(FRAMEBASE["dereif-Performers_and_roles-playsInPerformance"])

# Director (dbPedia & LMDB)
DIRECTOR=set()
DIRECTOR.add(DBO["director"])
DIRECTOR.add(LMDB_Movie["director"])

# TODO: Director (YAGO)
DIRECTED_BY=set()


# Queries
# =======

# Simple
def Name(n=mStonebraker, w=1):
    """Node name"""
    b = QueryBuilder(n, "Root")
    b.frm("Root").through(FOAF["name"]).final("Name")

    return b.build(w)


def Dereference(n=mStonebraker, w=1):
    """Dereference"""
    b = QueryBuilder(n, "Root")
    b.frm("Root").through_not("").final("Data")

    return b.build(w)


# Authorship
def publications(n=mStonebraker, w=1):
    """Publications by an author"""
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC.creator).backwards_to("Paper")

    b.frm("Paper").through(NAME).final("Title")
    return b.build(w)


def journals(n=mStonebraker, w=1):
    """Published in journal"""
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC.creator).backwards_to("jPaper", NodeFilter_regex(".*journal.*"))
    b.frm("jPaper").through(SWRC.journal).to("Journal")
    b.frm("Journal").through(NAME).final("Name")

    return b.build(w)


def conferences(n=mStonebraker, w=1):
    """ dc:creator-/swrc:series/rdfs:label """
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC.creator).backwards_to("Paper")
    b.frm("Paper").through(SWRC.series).to("Conference")
    b.frm("Conference").through(NAME).final("Name")

    return b.build(w)


def coauthors(n=mStonebraker, w=1):
    """Direct Coauthors"""
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC["creator"]).backwards_to("Paper")
    b.frm("Paper").through(DC["creator"]).to("CoAuth", NodeFilter_but(n))

    b.frm("CoAuth").through(NAME).final("Name")

    return b.build(w)


def coauthors_star_IRI(n=mStonebraker, w=1):
    """Coauthors* [IRI only]"""
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC["creator"]).backwards_to("Paper")
    b.frm("Paper").through(DC["creator"]).final("CoAuth", NodeFilter_but(n))

    b.frm("CoAuth").through(DC["creator"]).backwards_to("Paper'")
    b.frm("Paper'").through(DC["creator"]).to("CoAuth")

    return b.build(w)


def coauthors_star(n=mStonebraker, w=1):
    """Coauthors*"""
    b = QueryBuilder(n, "Author")
    b.frm("Author").through(DC["creator"]).backwards_to("Paper")
    b.frm("Paper").through(DC["creator"]).to("CoAuth", NodeFilter_but(n))

    b.frm("CoAuth").through(DC["creator"]).backwards_to("Paper'")
    b.frm("Paper'").through(DC["creator"]).to("CoAuth")

    b.frm("CoAuth").through(NAME).final("Name")

    return b.build(w)


# Acting
def coactor_star__DBPEDIA(n=DBR["Kevin_Bacon"], w=1):
    """Coactor* (dbPedia)"""
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(DBO["starring"]).backwards_to("Movie")
    b.frm("Movie").through(DBO["starring"]).to("CoActor", NodeFilter_but(n))

    b.frm("CoActor").through(DBO["starring"]).backwards_to("Movie")

    b.frm("CoActor").through(NAME).final("Name")

    return b.build(w)


def coactor_star__LMDB(n=kBacon, w=1):
    """Coactor* (LMDB)"""
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(LMDB_Movie["actor"]).backwards_to("Movie")
    b.frm("Movie").through(LMDB_Movie["actor"]).to("CoActor", NodeFilter_but(n))

    b.frm("CoActor").through(LMDB_Movie["actor"]).backwards_to("Movie")

    b.frm("CoActor").through(NAME).final("Name")

    return b.build(w)


def coactor_star_IRI__YAGO(n=YAGO["Kevin_Bacon"], w=1):
    """Coactor* (YAGO)"""
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(ACTED_IN).to("Movie")
    b.frm("Movie").through(ACTED_IN).backwards_final("CoActor", NodeFilter_but(n))
    b.frm("CoActor").through(ACTED_IN).to("Movie")

    #b.frm("CoActor").loop(SAME_AS)  # YAGO has no foaf:name or rdfs:label
    #b.frm("CoActor").through(NAME).final("Name")

    return b.build(w)


def coactor_star_sameAs_ANY(n=kBacon, w=1):
    """Coactor* (sameAs)"""
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(ACTED_IN).to(       "Movie")
    b.frm("Actor").through(ACTOR).backwards_to("Movie")

    b.frm("Movie").loop(SAME_AS)

    b.frm("Movie").through(ACTOR).to(             "CoActor", NodeFilter_but(n))
    b.frm("Movie").through(ACTED_IN).backwards_to("CoActor")

    b.frm("CoActor").through(ACTED_IN).to(       "Movie")
    b.frm("CoActor").through(ACTOR).backwards_to("Movie")

    b.frm("CoActor").through(NAME).final("Name")


    return b.build(w)


def movies_by_coactor_ANY(n=kBacon, w=1):
    """Movies by coactor"""
    b = QueryBuilder(n, "Actor")
    b.frm("Actor").through(ACTED_IN).to(       "Movie")
    b.frm("Actor").through(ACTOR).backwards_to("Movie")

    b.frm("Movie").through(ACTED_IN).backwards_to("CoActor", NodeFilter_but(n))
    b.frm("Movie").through(ACTOR).to(             "CoActor")

    b.frm("CoActor").through(DIRECTOR).backwards_to("Directed_Movie")

    b.frm("Directed_Movie").through(NAME).final("Name")

    return b.build(w)


def movies_by_coactor_star_ANY(n=kBacon, w=1):
    """Movies by coactor"""
    b = QueryBuilder(n, "Actor")
    # Actor   => Movie
    b.frm("Actor").through(ACTED_IN).to(       "Movie")
    b.frm("Actor").through(ACTOR).backwards_to("Movie")

    # Movie   => CoActor
    b.frm("Movie").through(ACTED_IN).backwards_to("CoActor", NodeFilter_but(n))
    b.frm("Movie").through(ACTOR).to(             "CoActor")

    # CoActor => Movie
    b.frm("CoActor").through(ACTED_IN).to(       "Movie")
    b.frm("CoActor").through(ACTOR).backwards_to("Movie")

    # CoActor => Directed_Movie
    b.frm("CoActor").through(DIRECTOR).backwards_to("Directed_Movie")

    # Directed_Movie -> name
    b.frm("Directed_Movie").through(NAME).final("Name")

    return b.build(w)



# Gubichev's queries
def gubichev_NATO_business_r(n=YAGO["Berlin"], w=1):
    """
    prefix yago: <http://yago-knowledge.org/resource/>

    select ?x, ?country, ?area
    where {
      ?x        yago:isLocatedIn* ?country.
      ?country  yago:dealsWith    ?area.
      ?area      rdf:type         yago:wikicat_Member_states_of_NATO
    }
    """
    b = QueryBuilder(YAGO["wikicat_Member_states_of_NATO"])

    b.frm("s0").through(RDF["type"]).to("Area")
    b.frm("s0").through(RDF["type"]).backwards_to("Area")

    b.frm("Area").through(YAGO["dealsWith"]).backwards_to("Place", None, NodeFilter_but(n))

    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    return b.build(w)


def gubichev_europe(n=YAGO["wikicat_Capitals_in_Europe"], w=1):
    """Europe"""
    # Using wikicat_* instead of wikicategory_*

    b = QueryBuilder(n, "EuropeCapitals")
    b.frm("EuropeCapitals").through(RDF["type"]).backwards_to("Capital")
    b.frm("Capital").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")
    b.frm("Place").through(YAGO["dealsWith"]).final("Area")

    return b.build(w)


def gubichev_airports(n=YAGO["wikicat_Airports_in_the_Netherlands"], w=1):
    """Netherlands airports"""
    b = QueryBuilder(n, "Airports")

    b.frm("Airports").through(RDF["type"]).backwards_to("airport")
    b.frm("airport").through(YAGO["isLocatedIn"]).final("Place")
    b.frm("Place").through(YAGO["isLocatedIn"]).to("Place")

    return b.build(w)





automatons = [
    # Test
    (Name,                         "Node_name"),               # 0
    (Dereference,                  "Dereference"),             # 1
    (None, ""),                                                # 2
    (None, ""),                                                # 3
    (None, ""),                                                # 4
    (None, ""),                                                # 5
    (None, ""),                                                # 6
    (None, ""),                                                # 7
    (None, ""),                                                # 8
    (None, ""),                                                # 9

    # Authorship
    (publications,                 "Publications"),            #10
    (journals,                     "Journals"),                #11
    (conferences,                  "Conferences"),             #12
    (coauthors,                    "Direct_Coauthors"),        #13
    (coauthors_star_IRI,           "CoauthorStar_IRI"),        #14
    (coauthors_star,               "CoauthorStar"),            #15
    (None, ""),                                                #16
    (None, ""),                                                #17
    (None, ""),                                                #18
    (None, ""),                                                #19

    # Acting
    (coactor_star__DBPEDIA,        "CoactorStar__DBPEDIA"),    #20
    (coactor_star__LMDB,           "CoactorStar__LMDB"),       #21
    (coactor_star_IRI__YAGO,       "CoactorStar_IRI__YAGO"),   #22
    (coactor_star_sameAs_ANY,      "CoactorStar__ANY"),        #23
    (movies_by_coactor_ANY,        "Coactor_movies__ANY"),     #24
    (movies_by_coactor_star_ANY,   "CoactorStar__ANY"),        #25
    (None, ""),                                                #26
    (None, ""),                                                #27
    (None, ""),                                                #28
    (None, ""),                                                #29


    # Gubichev's queries
    (gubichev_NATO_business_r,      "NATO_Business"),          #30
    (gubichev_europe,               "EuropeCapitals"),         #31
    (gubichev_airports,             "AirportsInNetherlands"),  #32

    # End
    (None, "")
]
