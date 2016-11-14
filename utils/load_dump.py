#!/usr/bin/env python
"""
Plot utils
"""
#pylint: disable=invalid-name
import argparse
from jsonpickle import decode as json_decode

#pylint: disable=unused-import
from matplotlib.pyplot import show, figure, plot, legend, title, xlabel, ylabel, savefig


from fs import get_files, get_subdirs, get_json_files

ALG_COLORS = {
    "AStar":     "green",
    "Dijkstra":  "red",
    "DFS":       "blue",

    None: "black"
}


def color_by_alg(dump):
    """
    Picks a color for a dump based on the algorithm
    """
    (_, alg_name, _, _) = dump_alg_name(dump)
    return ALG_COLORS[alg_name]


PARALLELISM_COLORS = {
    1:   "blue",
    3:   "blue",
    5:   "blue",
    10:  "red",
    20:  "red",
    40:  "red",
    80:  "green",
    160: "green",
    200: "green",

    None: "black"
}



def color_by_parallelism(dump):
    """
    Picks a color for a dump based on the parallelism used
    """
    (_, _, _, pool_size) = dump_alg_name(dump)
    return PARALLELISM_COLORS[pool_size]


LABELS = {
    "algorithm":         "Algorithm used",
    "requestTotalTime":  "Total network time",
    "triples":           "Triples on DB",
    "goals_found":       "Answers",
    "requestTime":       "Last Request Time",
    "requestTriples":    "Last Request Triples",
    "wallClock":         "Time (s)",
    "memory":            "Memory (MB)",
    "requestIRI":        "Last IRI",
    "expansions":        "Expansions",
    "local_expansions":  "Local expansions",
    "remote_expansions": "Requests",
    "batchID":           "Batch Number",


    "":                  "[Empty String]",
    42:                  "(The answer)",
    None:                "[None]"
}


def get_plot_label(key):
    """
    Picks a label for a key
    """
    if key in LABELS:
        return LABELS[key]
    else:
        return "[%s]" % key.replace('_', ' ')


def iterable_strict_eval(it):
    """
    Converts generators to lists (if needed)
    """
    import types
    if isinstance(it, types.GeneratorType):
        return [_ for _ in it]
    return it


def use_last_x(hist, x_key, y_key):
    """
    Trims points where x-value is unchanged'
    """
    xs = [h[x_key] for h in hist]
    ys = [h[y_key] for h in hist]

    last_x = xs[0]
    last_y = ys[0]
    fx = [last_x]
    fy = [last_y]

    for (_x, _y) in zip(xs, ys):
        if _x == last_x:
            fx[-1] = _x
            fy[-1] = _y
        else:
            fx.append(_x)
            fy.append(_y)

        last_x = _x
        last_y = _y

    if len(xs) != len(fx):
        print("Trimmed %d %s snapshots" % ((len(xs) - len(fx)), x_key))

    return (fx, fy)


def print_iter(it, allowed=20):
    """
    Prints an iterator and it's contents
    """
    print(it)
    for i in it:
        print("  - %s" % i)
        allowed -= 1
        if allowed <= 0:
            break

    if allowed == 0:
        print("  ...")

    print("--")


def load_jsons(filenames):
    """
    Loads JSON files as (dict, filename) pairs
    """

    filenames = iterable_strict_eval(filenames)
    list.sort(filenames)

    for file_name in filenames:
        #pylint: disable=broad-except
        try:
            with open(file_name) as dump_file:
                data = json_decode(dump_file.read())
                yield (data, file_name)
        except Exception as ex:
            print("Failed to load '%s' (%s)" % (file_name, ex))


def dumpset_comparable_limits(json_dumps, checks=["ans", "triples", "time"]):
    """
    Checks if some dumps have matching parameters
    """
    #pylint: disable=dangerous-default-value
    limits = dict()
    for c in checks:
        limits[c] = set()

    for jd in json_dumps:
        for c in checks:
            limits[c].add(jd["params"]["limits"][c])

    for c in checks:
        if len(limits[c]) != 1:
            print("Dumps do not seem to be comparable on '%s'" % c)
            for l in limits[c]:
                print("  * limit['%s'] = '%s'" % (c, l))
            return False

    return True


def dump_alg_name(dump):
    """
    Builds a name for an algorithm on a dump
    """
    alg_name = dump["params"]["algorithm"]
    weight = dump["weight"]
    pool_size = dump["params"]["parallelRequests"]

    alg_label = alg_name
    if pool_size > 1:
        alg_label += "-%dp" % pool_size
    if weight != 1:
        alg_label += "-%dw" % weight

    return (alg_label, alg_name, weight, pool_size)


def dumps_plot(json_dumps, x_key, y_key, x_label=None, y_label=None, colorize_function=None):
    """
    Plots x_key v/s y_key for some json_dumps
    """
    #pylint: disable=too-many-arguments
    if x_label is None:
        x_label = get_plot_label(x_key)
    if y_label is None:
        y_label = get_plot_label(y_key)

    json_dumps = iterable_strict_eval(json_dumps)
    assert dumpset_comparable_limits(json_dumps)

    empty_plot = True
    for dump in json_dumps:
        (alg_label, _, _, _) = dump_alg_name(dump)

        hist = dump["data"]["StatsHistory"]
        (x_data, y_data) = use_last_x(hist, x_key, y_key)

        if colorize_function is None:
            plot(x_data, y_data, label=alg_label)
        else:
            plot(x_data, y_data, label=alg_label, color=colorize_function(dump))
        empty_plot = False

    if empty_plot:
        raise Exception("No dumps given")

    legend(loc="best")
    xlabel(x_label, fontsize=18)
    ylabel(y_label, fontsize=16)

    title("title", fontsize=20)


def plot_parallelism(query_path, x_key, y_key, alg="AStar"):
    """
    Avoid global variable names
    """
    if query_path[-1] != '/':
        query_path += '/'

    bench_dumps = "%s**/*%s*.json" % (query_path, alg)

    data = []
    for (dump, name) in load_jsons(get_files(bench_dumps)):
        print(name)
        params = dump["params"]
        data.append((params["parallelRequests"], dump, name))

    list.sort(data)
    for (k, _, name) in data:
        print("Loaded k=%3d from '%s'" % (k, name))

    # Project dumps only (now sorted)
    dumps = [d for (_, d, _) in data]
    dumps_plot(dumps, x_key=x_key, y_key=y_key, colorize_function=color_by_parallelism)


def plot_algs(query_path, x_key, y_key):
    """
    Plots different algorithms on comparable parameters
    """


    dumps_plot(load_jsons(get_json_files(query_path)),
               x_key=x_key,
               y_key=y_key,
               colorize_function=color_by_alg)


def plot_bench(dirs, x_key, y_key):
    """
    Plots
    """

    # Plot multiple-parallelism for A*, Dijkstra and DFS
    for bench in dirs:
        print("Plotting parallelism comparison on '%s'" % bench)
        for query in get_subdirs(bench):
            for alg in ["AStar", "Dijkstra", "DFS"]:
                #pylint: disable=broad-except
                try:
                    plot_parallelism(query, x_key, y_key, alg=alg)
                    show()
                    #savefig(figPath)
                except Exception as ex:
                    print(ex)

    # Plots multiple algorithms on similar conditions
    for bench in dirs:
        print("Plotting algorithm comparison on '%s'" % bench)

        for query in get_subdirs(bench):              # q10
            for parallelism in get_subdirs(query):    # p1
                for exp in get_subdirs(parallelism):  # quick goal
                    plot_algs(exp, x_key=x_key, y_key=y_key)
                    show()
                    #savefig(figPath)


def main():
    """
    Plots benchmark dumps
    """
    parser = argparse.ArgumentParser(description='Plot stuff')

    ## Query
    parser.add_argument('directories', metavar='directories', type=str, nargs='+',
                        help='bench directories (bench/benchID/)')
    parser.add_argument('--data', metavar='data', type=str, nargs='+',
                        help='json data keys')

    parser.add_argument('--first-goals', metavar='first_goals', type=str, nargs='+',
                        help='Print Snapshots reaching k goals first')

    parser.add_argument('--x', metavar='x', type=str, nargs=1,
                        help='x axis key')

    parser.add_argument('--y', metavar='y', type=str, nargs=1,
                        help='y axis key')

    parser.add_argument('--no-show', dest='no_show', action='store_const',
                        const=True, default=False,
                        help='silent (non-interactive)')

    parser.add_argument('--png', dest='extension', action='store_const',
                        const="png", default="pdf",
                        help='silent (non-interactive)')

    args = parser.parse_args()
    directories = args.directories
    x_key = args.x or "remote_expansions"
    y_key = args.y or "goals_found"


    plot_bench(directories, x_key, y_key)


if __name__ == '__main__':
    main()
