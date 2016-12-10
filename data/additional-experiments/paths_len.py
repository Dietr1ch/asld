#!/usr/bin/env python
import json

# q16 behaves better, as they all start with all Stonebraker's papers on first expansion
# Also, the automaton transition tie breaking (order within a hashset) prefers goal node, so the run mimics A*

# q17 is awful for DFS, take a look..
astar = (json.load(open("./q17-CoAuthStarPapers/p1/quick/q17--AStar-w1-p1-quickGoal-time600-ans1000-triples100000.json")),    "A*" )
dfs   = (json.load(open("./q17-CoAuthStarPapers/p1/quick/q17--DFS-w1-p1-quickGoal-time600-ans1000-triples100000.json")),      "DFS")
bfs   = (json.load(open("./q17-CoAuthStarPapers/p1/quick/q17--Dijkstra-w1-p1-quickGoal-time600-ans1000-triples100000.json")), "BFS")

k = 20
for (alg, name) in [astar, bfs, dfs]:
    print("%s:" % name)
    print("  Showing first %s paths" % k)
    paths = alg["data"]["Paths"]

    some_paths = paths[0:k]
    l = [len(p)-1 for p in some_paths]
    print("  %s" % l)

    print("  The last of those is:")
    last_path = some_paths[-1]
    for s in last_path:
        n = s["node"]
        t = s["transition"]
        if t is None:
            print("  %s" % n)
        else:
            p = t["P"]
            d = t["d"]
            print("  %s %s %s" % (p, d, n))
    print()
