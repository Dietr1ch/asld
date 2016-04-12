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


args = parser.parse_args()
jsonFiles = args.files
jsonFiles.sort()
plotDataKeys  = args.data


runs = []
for jf in jsonFiles:
    with open(jf) as f:
        runs.append(jsonpickle.decode(f.readline()))

colors = ["red", "green"]


keyErrors = False
for pdk in plotDataKeys:
    try:
        figure()
        print("Showing %s" % pdk)
        for (i, run) in enumerate(runs):
            plot([h[pdk] for h in run["data"]["StatsHistory"]], color=colors[i])
            Color.GREEN.print("  * %s: %s" % (jsonFiles[i], colors[i]))
        show()
    except KeyError as ke:
        Color.RED.print("Invalid key (%s)" % ke)
        keyErrors = True

if keyErrors:
    Color.RED.print("Invalid keys")
    validKeys = runs[0]["data"]["StatsHistory"][0].keys()
    for ik in [k for k in plotDataKeys if k not in validKeys]:
        Color.RED.print("  * %s" % ik)

    Color.YELLOW.print("Available keys:")
    for k in validKeys:
        Color.YELLOW.print("  * %s" % k)
