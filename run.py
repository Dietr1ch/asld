#!/usr/bin/env python
import argparse
from pprint import pprint
import jsonpickle

from asld.search import ASLDSearch
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
parser.add_argument('--pool-size', metavar='p', type=int, default=40,
                    help='Process pool size to use')

# Search limits
parser.add_argument('--time', metavar='t', type=int, default=30*60,
                    help='Time limit')
parser.add_argument('--ans', metavar='a', type=int, default=1e3,
                    help='Answer limit')
parser.add_argument('--triples', metavar='s', type=int, default=1e5,
                    help='Triples limit')

args = parser.parse_args()

w            = args.w
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
    "params": {
        "limits": {
            "time": limit_time,
            "triples": limit_triples,
            "ans": limit_ans,
        },
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
    print("  Pool Size:    %d" % parallel_requests)
    print("  Limits:")
    print("    Time:    %ds" % limit_time)
    print("    Answers: %d" % limit_ans)
    print("    Triples: %d" % limit_triples)

    # Run search
    search = ASLDSearch(query(w=w))

    data = search.test(parallelRequests=40,
                       limit_time=limit_time,
                       limit_ans=limit_ans,
                       limit_triples=limit_triples)
    result["data"] = data


except KeyboardInterrupt:
    Color.BLUE.print("\nTerminating search.")

finally:
    print("====")
    print(result)
    print("====")

    fileName = "last"
    fileName += "-p%d" % (parallel_requests)
    fileName += "-time%d-ans%d-triples%d" % (limit_time,
                                             limit_ans,
                                             limit_triples)
    fileName += "---q%d-w%d" % (query_number, w)
    fileName += ".json"

    print("Writing log to %s" % fileName)
    with open(fileName, 'w') as f:
        f.write(jsonpickle.dumps(result))

    if data:
        stats = data["StatsHistory"]
        if stats:
            lastStats = stats[-1]
            Color.BLUE.print("Last stats:")
            pprint(lastStats)
