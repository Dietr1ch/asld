import argparse
import gc
from copy import copy
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
    (Name,                         "Node name"),
    (Journals,                     "Journal papers"),
    (Conferences,                  "Conferences"),
    (CoAuth,                       "Coauthors"),
    (CoAuthStar,                   "Coauthor*"),
    (Directors,                    "Directors"),
    (CoActor_LMDB,                 "Coauthor [LMDB]"),
    (CoActorStar_LMDB,             "Coauthor* [LMDB]"),
    (CoActorStar_DBpedia,          "Coauthor* [DBpedia]"),
    (CoActorStar_director_DBpedia, "Coauthor*/Director [DBpedia]"),
    (CoActorStar_YAGO,             "Coauthor* [YAGO]"),
    (NATO_business,                "NATO business (Berlin)"),
    (NATO_business_r,              "NATO business (reverse)"),
    (NATO,                         "NATO"),
    (Europe,                       "Europe Capitals"),
    (Airports,                     "Airports in the Netherlands")
]


def runAll(queries,
           parallelRequests=40,
           limit_time=30*60, limit_ans=float("inf"), limit_triples=1e5):
    searches = []
    for (q, name) in queries:
        try:
            Color.BLUE.print("Running search on %s..." % name)
            s = ASLDSearch(q)

            # Run search
            data = s.test(parallelRequests,
                          limit_time, limit_ans, limit_triples)
            searches.append(
                {
                    "query": name,
                    "data": data
                }
            )
            s = None
            gc.collect()

        except KeyboardInterrupt:
            Color.BLUE.print("\nTerminating search.")
        except Exception as e:
            Color.RED.print("Terminated runAll on: %s" % e)

    return searches


def bench(parallelRequests=40,
          limit_time=30*60, limit_ans=float("inf"), limit_triples=1e5):
    astar = [q(w=1) for q in automatons]
    bfs   = [q(w=0) for q in automatons]  # w=0 turns A* into BFS (Dijkstra)

    searches = []
    try:
        Color.BLUE.print("Running A*...")
        searches.extend(runAll(astar,
                               parallelRequests,
                               limit_time, limit_ans, limit_triples))

        Color.BLUE.print("Running Dijkstra...")
        searches.extend(runAll(bfs,
                               parallelRequests,
                               limit_time, limit_ans, limit_triples))

    except KeyboardInterrupt:
        Color.BLUE.print("\nTerminating search.")
    except Exception as e:
        Color.RED.print("Terminated bench on: %s" % e)

    return searches

