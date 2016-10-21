#!/usr/bin/env python
"""
Script for producing comparison plots from search data

Currently it requires runs from A* end Dijkstra on the same setup
"""
import os

import argparse
import jsonpickle

from matplotlib.pyplot import show, figure, plot, legend, title, xlabel, ylabel, savefig

from asld.utils.color_print import Color


parser = argparse.ArgumentParser(description='Plot stuff')

# Query
parser.add_argument('files', metavar='files', type=str, nargs='+',
                    help='json data')
parser.add_argument('--data', metavar='data', type=str, nargs='+',
                    help='json data keys')

parser.add_argument('--first-goals', metavar='first_goals', type=str, nargs='+',
                    help='Print Snapshots reaching k goals first')

parser.add_argument('--x', metavar='x', type=str, nargs=1,
                    help='x axis key')

parser.add_argument('--no-show', dest='no_show', action='store_const',
                    const=True, default=False,
                    help='silent (non-interactive)')

parser.add_argument('--png', dest='extension', action='store_const',
                    const="png", default="pdf",
                    help='silent (non-interactive)')

colors = ["red", "blue", "green"]
labels = ["Dijkstra", "A*"]
STYLE = {
    "AStar":    ("green",  "dotted"),
    "Dijkstra": ("red",    "dotted"),
    "DFS":      ("blue",   "dotted"),

    # Default style
    "":         ("black",  "dotted"),
}


args = parser.parse_args()
jsonFiles = args.files
jsonFiles.sort()
plotDataKeys  = args.data
x = args.x
if x:
    x = x[0]
showPlot = not args.no_show
plotExt = args.extension

MARKS = None
if args.first_goals:
    MARKS = [int(x) for x in args.first_goals]

KEY_ERRORS = False


def load_files(files):
    """
    Loads JSON dumps
    """
    data = dict()
    for jf in files:
        print("Reading '%s'" % jf)
        try:
            with open(jf) as f:
                run_data = jsonpickle.decode(f.read())
                alg_name = run_data["params"]["algorithm"]
                data[alg_name] = run_data
        except KeyError as ke:
            Color.RED.print("Failed to load '%s' (%s)" % (jf, ke))

    return data


def validate_runs(runs):
    """
    Validates runs
    """
    queryName = set()
    quickGoal = set()
    pool_size = set()

    limit_ans     = set()
    limit_triples = set()
    limit_time    = set()
    for run in runs.values():
        queryName.add(    run["query"])
        quickGoal.add(    run["quickGoal"])
        pool_size.add(    run["params"]["parallelRequests"])

        limit_ans.add(    run["params"]["limits"]["ans"])
        limit_triples.add(run["params"]["limits"]["triples"])
        limit_time.add(   run["params"]["limits"]["time"])

    if len(queryName) != 1:
        Color.RED.print("Runs are from different queries")
        return False
    if len(quickGoal) != 1:
        Color.RED.print("Runs use different optimizations")
        return False
    if len(pool_size) != 1:
        Color.RED.print("Runs use different pool sizes")
        return False

    if len(limit_ans) != 1:
        Color.RED.print("Runs use different answers limits")
        return False
    if len(limit_triples) != 1:
        Color.RED.print("Runs use different triples limits")
        return False
    if len(limit_time) != 1:
        Color.RED.print("Runs use different time limits")
        return False

    return True


def sample_runs(runs, marks):
    """
    Samples stats until marks are reached
    """

    if marks is None:
        print("No samples given")
        return

    for (alg, run) in runs.items():
        try:
            hist = run["data"]["StatsHistory"]
            Color.BLUE.print(" -last %s log: %s" % (alg, hist[-1]))

            marks.sort(reverse=True)
            print()
            Color.GREEN.print("Looking for marks on (%s)" % alg)
            for snap in run["data"]["StatsHistory"]:
                goalsFound = snap["goalsFound"]

                while marks and goalsFound>=marks[-1]:
                    mark = marks.pop()

                    print("  %d-goals:  " % mark, end="")
                    print("Expansion: %d;   " % snap["expansions"], end="")
                    print("mem: %5.2f MB;   " % snap["memory"], end="")
                    print("triples: %5d;   " % snap["triples"], end="")
                    print("time: %5.2fs" % snap["wallClock"])

                if len(marks) == 0:
                    break
        except KeyError as ke:
            #pylint: disable=global-statement
            global KEY_ERRORS
            KEY_ERRORS = True
            Color.RED.print("Invalid key (%s)  [--first-goals]" % ke)

        print()


def plot_runs(runs):
    """
    (=
    """
    xLabel = "expansions"
    if x:
        xLabel = x

    # Get some run
    first_run = next(iter(runs.values()))

    queryName = first_run["query"]
    quickGoal = first_run["quickGoal"]
    pool_size = first_run["params"]["parallelRequests"]


    limit_ans     = first_run["params"]["limits"]["ans"]
    limit_triples = first_run["params"]["limits"]["triples"]
    limit_time    = first_run["params"]["limits"]["time"]
    srcPath = os.path.dirname(os.path.realpath(jsonFiles[0]))

    pLab = {
        "algorithm":         "Algorithm used",
        "requestTotalTime":  "Total network time",
        "triples":           "Triples on DB",
        "goalsFound":        "Answers",
        "requestTime":       "Last Request Time",
        "requestTriples":    "Last Request Triples",
        "wallClock":         "Time (s)",
        "memory":            "Memory (MB)",
        "requestIRI":        "Last IRI",
        "expansions":        "Expansions",
        "batchID":           "Batch Number"
    }


    for pdk in plotDataKeys:
        try:
            figure()
            yLabel = pdk
            print("Plotting %s vs %s" % (pdk, xLabel))

            for (alg, run) in runs.items():
                style = STYLE[""]
                if alg in STYLE.keys():
                    style = STYLE[alg]
                (color, _) = style

                Color.GREEN.print("  * %8s: %s" % (alg, color))

                label = alg+""
                hist = run["data"]["StatsHistory"]
                yData = [h[pdk] for h in hist]
                if x:
                    xData = [h[x] for h in hist]
                    plot(xData, yData, color=color, label=label)
                else:
                    plot(yData, color=color, label=label)

            xlabel(pLab[xLabel], fontsize=18)
            ylabel(pLab[yLabel], fontsize=16)
            legend(loc="best")
            titleHeader =  "%s (p%d, q%s)" % (queryName, pool_size, quickGoal)
            title(titleHeader, fontsize=20)

            figPath = "%s/%s-%s_vs_%s" % (srcPath, queryName, yLabel, xLabel)
            figPath += "--%dProcs--%dlAns-%dlTime-%dlTriples" % (pool_size,
                                                                 limit_ans,
                                                                 limit_time,
                                                                 limit_triples)
            figPath += ".%s" % plotExt

            Color.BLUE.print("Saving figure to '%s'" % figPath)
            savefig(figPath)
            if showPlot:
                show()

        except KeyError as ke:
            #pylint: disable=global-statement
            global KEY_ERRORS
            KEY_ERRORS = True
            Color.RED.print("Invalid key (%s)" % ke)


RUNS = load_files(jsonFiles)
if not validate_runs(RUNS):
    exit(1)
sample_runs(RUNS, MARKS)
plot_runs(RUNS)


if KEY_ERRORS:
    Color.RED.print("Invalid keys")
    validKeys = RUNS[0]["data"]["StatsHistory"][0].keys()
    for ik in [k for k in plotDataKeys if k not in validKeys]:
        Color.RED.print("  * %s" % ik)

    Color.YELLOW.print("Available keys:")
    for k in validKeys:
        Color.YELLOW.print("  * %s" % k)
