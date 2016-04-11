#!/usr/bin/env python
import argparse
import jsonpickle
from pprint import pprint

from asld.utils.color_print import Color
from asld.search import ASLDSearch

from init import automatons





parser = argparse.ArgumentParser(description='Process some queries')

# Query
parser.add_argument('-w', metavar='w', type=int, default=1,
                    help='weight to use on the heuristic')
parser.add_argument('-q', metavar='q', type=int, default=0,
                    help='query ID')

# Search tuning
parser.add_argument('--pool_size', metavar='p', type=int, default=40,
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
        Color.BLUE.print("Running BFS (Dijkstra) on '%s'..." % name)
    elif w==1:
        Color.BLUE.print("Running A* on '%s'..." % name)
    else:
        # Just for completeness
        Color.BLUE.print("Running A* with weight=%d on '%s..." % (w, name))

    Color.BLUE.print("  Limits:")
    Color.BLUE.print("    Time:    %ds" % limit_time)
    Color.BLUE.print("    Answers: %d" % limit_ans)
    Color.BLUE.print("    Triples: %d" % limit_triples)

    # Run search
    search = ASLDSearch(query(w=w))

    data = search.test(parallelRequests=40,
                       limit_time=limit_time,
                       limit_ans=limit_ans,
                       limit_triples=limit_triples)
    result["data"] = data


except KeyboardInterrupt:
    Color.BLUE.print("\nTerminating search.")
#except Exception as e:
    #Color.RED.print("Terminated run on: %s" % e)

finally:
    print("====")
    print(result)
    print("====")

    fileName = "last-q%d-w%d" % (query_number, w)
    fileName += "--p%d" % (parallel_requests)
    fileName += "--time%d--ans%d--triples%d" % (limit_time,
                                                limit_ans,
                                                limit_triples)
    fileName += ".json"

    with open(fileName, 'w') as f:
        f.write(jsonpickle.dumps(result))

    if data:
        stats = data["StatsHistory"]
        if stats:
            lastStats = stats[-1]
            Color.BLUE.print("Last stats:")
            pprint(lastStats)
