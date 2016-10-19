#!/usr/bin/env python
"""
Command line interface for running sample queries
"""

import os
import argparse
from pprint import pprint
from json import dump

from asld.search import ASLDSearch, Algorithm
from asld.sample_queries import automatons

from asld.utils.color_print import Color


# Parse arguments
# ===============
parser = argparse.ArgumentParser(description='Process some queries')

# Query
parser.add_argument('-w', metavar='w', type=int, default=1,
                    help='weight to use on the heuristic')
parser.add_argument('-q', metavar='q', type=int, default=0,
                    help='query ID')

# Search tuning
parser.add_argument("--slow-goal", help="Use regular goal declaration", action="store_true")
parser.add_argument('--pool-size', metavar='p', type=int, default=40,
                    help='Process pool size to use')

# Search limits
parser.add_argument('--time', metavar='t', type=int, default=30*60,
                    help='Time limit')
parser.add_argument('--ans', metavar='a', type=int, default=1e3,
                    help='Answer limit')
parser.add_argument('--triples', metavar='s', type=int, default=1e5,
                    help='Triples limit')

parser.add_argument('--alg', metavar='t', type=str, default="a*",
                    help='A* | Dijkstra | BFS | DFS')

args = parser.parse_args()

ALGORITHM    = Algorithm.parse(args.alg)
ALGORITHM_N  = Algorithm.to_string(ALGORITHM)
w            = args.w
quick_goal   = not args.slow_goal
query_number = args.q

parallel_requests = args.pool_size

limit_time    = args.time
limit_ans     = args.ans
limit_triples = args.triples

(query, name) = automatons[query_number]


# Run query
# =========
data = None
result = {
    "query": name,
    "weight": w,
    "quickGoal": quick_goal,
    "params": {
        "limits": {
            "time":    limit_time,
            "triples": limit_triples,
            "ans":     limit_ans,
        },
        "algorithm": ALGORITHM_N,
        "parallelRequests": parallel_requests
    },
    "data": data
}

try:
    if w==0:
        print("Running BFS (Dijkstra) on '%s'..." % name)
    elif w==1:
        print("Running A* on '%s'..." % name)
    else:
        # Just for completeness
        print("Running A* with weight=%d on '%s..." % (w, name))

    print("Parameters:")
    print("  Algorithm:    %s" % ALGORITHM_N)
    print("  Pool Size:    %d" % parallel_requests)
    print("  Limits:")
    print("    Time:    %ds" % limit_time)
    print("    Answers: %d"  % limit_ans)
    print("    Triples: %d"  % limit_triples)

    # Run search
    search = ASLDSearch(query(w=w), quick_goal=quick_goal, alg=ALGORITHM)

    data = search.test(parallel_requests,
                       limit_time    = limit_time,
                       limit_ans     = limit_ans,
                       limit_triples = limit_triples)
    result["data"] = data


except KeyboardInterrupt:
    Color.BLUE.print("\nTerminating search.")

finally:
    # Make sub-directory
    results_directory = "bench/last/"
    results_directory += "q%d/" % query_number

    results_directory += "p%d/" % parallel_requests
    if quick_goal:
        results_directory += "quick/"
    else:
        results_directory += "slow/"
    os.makedirs(results_directory, mode=0o777, exist_ok=True)

    # Save files
    fileName = results_directory
    fileName += "q%d--" % query_number
    fileName += "%s" % ALGORITHM_N
    fileName += "-w%d" % w
    fileName += "-p%d" % parallel_requests
    if quick_goal:
        fileName += "-quickGoal"
    else:
        fileName += "-slowGoal"
    fileName += "-time%d-ans%d-triples%d" % (limit_time,
                                             limit_ans,
                                             limit_triples)
    fileName += ".json"

    print("Writing log to %s" % fileName)
    with open(fileName, 'w') as f:
        dump(result, f, indent=2)

    if data:
        stats = data["StatsHistory"]
        if stats:
            Color.BLUE.print("Last stats:")
            pprint(stats[-1])
