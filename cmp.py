#!/usr/bin/env python
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

colors = ["red", "green"]
labels = ["Dijkstra", "A*"]


args = parser.parse_args()
jsonFiles = args.files
jsonFiles.sort()
plotDataKeys  = args.data
x = args.x
if x:
    x = x[0]
showPlot = not args.no_show
plotExt = args.extension


runs = []
for jf in jsonFiles:
    with open(jf) as f:
        runs.append(jsonpickle.decode(f.readline()))

for (i, run) in enumerate(runs):
    hist = run["data"]["StatsHistory"]
    Color.BLUE.print(" -last log %s (%s)" % (hist[-1], colors[i]))

if args.first_goals:
    try:
        for (i, run) in enumerate(runs):
            pending_marks = [int(x) for x in args.first_goals]
            pending_marks.sort(reverse=True)
            print()
            Color.GREEN.print("Looking for marks on %d (%s)" % (i, colors[i]))
            for snap in run["data"]["StatsHistory"]:
                goalsFound = snap["goalsFound"]

                while pending_marks  and  goalsFound>=pending_marks[-1]:
                    mark = pending_marks.pop()
                    Color.GREEN.print("  * Expansion %d reached %d-goals:" % (snap["expansions"], mark))
                    print(snap)

                if len(pending_marks) == 0:
                    break
    except KeyError as ke:
        keyErrors = True
        Color.RED.print("Invalid key (%s)  [--first-goals]" % ke)
    print()


keyErrors = False
xLabel = "expansions"
if x:
    xLabel = x
queryName = runs[0]["query"]
srcPath = os.path.dirname(os.path.realpath(jsonFiles[0]))

for pdk in plotDataKeys:
    try:
        figure()
        yLabel = pdk
        print("Showing %s vs %s" % (pdk, xLabel))

        for (i, run) in enumerate(runs):
            hist = run["data"]["StatsHistory"]
            yData = [h[pdk] for h in hist]
            if x:
                xData = [h[x] for h in hist]
                plot(xData, yData, color=colors[i], label=labels[i])
            else:
                plot(yData, color=colors[i], label=labels[i])

            Color.GREEN.print("  * %s: %s" % (jsonFiles[i], colors[i]))

        xlabel(xLabel, fontsize=18)
        ylabel(yLabel, fontsize=16)
        legend(loc="best")
        title(queryName, fontsize=20)

        figPath = "%s/%s-%s-%s.%s" % (srcPath, queryName, pdk, xLabel, plotExt)
        Color.BLUE.print("Saving figure to '%s'" % figPath)
        savefig(figPath)
        if showPlot:
            show()

    except KeyError as ke:
        keyErrors = True
        Color.RED.print("Invalid key (%s)" % ke)

if keyErrors:
    Color.RED.print("Invalid keys")
    validKeys = runs[0]["data"]["StatsHistory"][0].keys()
    for ik in [k for k in plotDataKeys if k not in validKeys]:
        Color.RED.print("  * %s" % ik)

    Color.YELLOW.print("Available keys:")
    for k in validKeys:
        Color.YELLOW.print("  * %s" % k)
