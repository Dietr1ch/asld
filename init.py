from rdflib.term import URIRef
from rdflib.namespace import Namespace, DC, FOAF, OWL, RDF, RDFS, XMLNS

from asld.utils.color_print import Color
from asld.query.query import Query
from asld.query.direction import Direction
from asld.query.filter import *
from asld.query.query_builder import QueryBuilder

from asld.search import ASLDSearch

# Init
# ====
from asld.sample_queries import *


# Extra tools
# ===========
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import show, figure, plot


automatons = [
    name,
    journals,
    conferences,
    coAuth,
    coAuthStar,
    directors,
    CoActor_LMDB,
    CoActorStar_LMDB,
    CoActorStar_DBpedia,
    CoActorStar_director_DBpedia,
    CoActorStar_YAGO,
    NATO_business,
    NATO_business_r,
    NATO,
    Europe,
    Airports
]


def runAll(queries, parallelRequests=40, limit_time=30*60, limit_ans=float("inf")):
    searches = []
    try:
        for (q, name) in queries:
            Color.BLUE.print("Running search on %s..." % name)
            s = ASLDSearch(q)

            # Run search
            (ans, aC, t) = s.test(parallelRequests, limit_time, limit_ans)
            searches.append(
            {
                "query": name,
                "answerCount": aC,
                "answers": ans,
                "time": t,
                "stats": s.stats.history
            }
            )
    except KeyboardInterrupt:
        Color.BLUE.print("\nTerminating search.")
    except Exception as e:
        Color.RED.print("Terminated on: %s" % e)

    return searches


def test(parallelRequests=40, limit_time=30*60, limit_ans=float("inf")):
    astar = [( q(w=1), q.__name__ ) for q in automatons]
    bfs   = [( q(w=0), q.__name__ ) for q in automatons]  # w=0 turns A* into BFS (Dijkstra)

    searches = []
    try:
        Color.BLUE.print("Running A*...")
        print(runAll(astar, parallelRequests, limit_time, limit_ans))

        Color.BLUE.print("Running Dijkstra...")
        print(runAll(  bfs, parallelRequests, limit_time, limit_ans))

    except KeyboardInterrupt:
        Color.BLUE.print("\nTerminating search.")
    except Exception as e:
        Color.RED.print("Terminated on: %s" % e)

