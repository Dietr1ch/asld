#!/usr/bin/env python
import argparse
import jsonpickle

from matplotlib.pyplot import show, figure, plot

from asld.utils.color_print import Color


parser = argparse.ArgumentParser(description='Plot stuff')

# Query
parser.add_argument('files', metavar='files', type=str, nargs='+',
                    help='json data')
parser.add_argument('--data', metavar='data', type=str, nargs='+',
                    help='json data keys')

parser.add_argument('--x', metavar='x', type=str, nargs='+',
                    help='x axis key')

colors = ["red", "green"]


args = parser.parse_args()
jsonFiles = args.files
jsonFiles.sort()
plotDataKeys  = args.data
x = args.x
if x:
    x = x[0]


runs = []
for jf in jsonFiles:
    with open(jf) as f:
        runs.append(jsonpickle.decode(f.readline()))

for (i, run) in enumerate(runs):
    hist = run["data"]["StatsHistory"]
    Color.BLUE.print(" -last log %s (%s)" % (hist[-1], colors[i]))

keyErrors = False
for pdk in plotDataKeys:
    try:
        figure()
        print("Showing %s" % pdk)
        for (i, run) in enumerate(runs):
            hist = run["data"]["StatsHistory"]
            yData = [h[pdk] for h in hist]
            if x:
                xData = [h[x] for h in hist]
                plot(xData, yData, color=colors[i])
            else:
                plot(yData, color=colors[i])

            Color.GREEN.print("  * %s: %s" % (jsonFiles[i], colors[i]))
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
