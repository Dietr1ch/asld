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
plotDataKeys  = args.data


data = []
for jf in jsonFiles:
    with open(jf) as f:
        data.append(jsonpickle.decode(f.readline()))

colors = ["red", "green"]


for pdk in plotDataKeys:
    Color.GREEN.print("Showing %s" % pdk)
    figure()
    for (i, d) in enumerate(data):
        Color.GREEN.print("  * %s: %s" % (jsonFiles[i], colors[i]))
        plot([h[pdk] for h in d["data"]["StatsHistory"]], color=colors[i])
    show()
