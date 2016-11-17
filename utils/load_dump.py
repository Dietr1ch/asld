#!/usr/bin/env python
"""
Plot utils
"""
#pylint: disable=invalid-name
import argparse
import json
from jsonpickle import decode as json_decode

#pylint: disable=unused-import
from matplotlib.pyplot import show, figure, plot, legend, title, xlabel, ylabel, savefig, close


from fs import get_files, get_subdirs, get_json_files

EXTENSION = "pdf"
ALGORITHMS = ["AStar", "Dijkstra", "DFS"]
LIMIT_KEYS = ["ans", "triples", "time"]
PARALLELISM_SHOWN = [1, 20]
ALG_COLORS = {
    "AStar":     "green",
    "Dijkstra":  "red",
    "DFS":       "blue",

    None: "black"
}
ALG_LINES = {
    "AStar":    "-",
    "Dijkstra": "--",
    "DFS":      ":",

    # Default style
    "":         "dotted",
}
TITLE = {
    # Easy
    "Node_name":        "Node name",
    "Dereference":      "Gather node",


    # Authorship
    "Publications":     "Publications",
    "Journals":         "Journals",
    "Conferences":      "Conferences",
    "Direct_Coauthors": "Coauthors",
    "CoauthorStar_IRI": "Coauthor* (IRIs)",
    "CoauthorStar":     "Coauthor* Names",


    # Acting
    "CoactorStar__DBPEDIA":  "Coactor* [dbPedia]",
    "CoactorStar__LMDB":     "Coactor* [LMDB]",
    "CoactorStar_IRI__YAGO": "Coactor* IRIs [YAGO]",

    "CoactorStar__ANY":        "Coactor* [dbPedia/LMDB/YAGO]",
    "Coactor_movies__ANY":     "Movies directed by coactor* [dbPedia/LMDB/YAGO]",
    "CoactorStar_movies__ANY": "Movies directed by coactor* [dbPedia/LMDB/YAGO]",

    "CoactorStar_movies__dbPedia": "Movies directed by coactor* [dbPedia]",


    # Gubichev's queries
    "NATO_Business":           "NATO Business [Gubichev]",
    "EuropeCapitals":          "Europe Capitals  [Gubichev]",
    "AirportsInNetherlands":   "Airports in the Netherlads [Gubichev]",


    "":    "(empty)",
    None:  "(None)"
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
    40:  "green",
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


def get_max_min_labels(data):
    """
    Gets the max, and min values and keys for parallel arrays in a dict
    """
    assert isinstance(data, dict)

    key_list = data.keys()
    l = min([len(v) for v in data.values()])

    v_max = [float("-inf")]*l
    k_max = []

    v_min = [float("inf")]*l
    k_min = []

    for i in range(l):
        k_max.append(set())
        k_min.append(set())
        for k in key_list:
            if v_max[i] <= data[k][i]:
                v_max[i] = data[k][i]
                k_max[i].add(k)
            if v_min[i] >= data[k][i]:
                v_min[i] = data[k][i]
                k_min[i].add(k)

    return (v_max, k_max, v_min, k_min)


def appearances(k, set_list):
    """
    Count appearances in a [set()]
    """
    count = 0
    for s in set_list:
        if k in s:
            count += 1
    return count


def time_sample_dump(dump, interval=0.25):
    snaps = dump["data"]["StatsHistory"]
    t_max = snaps[-1]["wallClock"]

    t = 0
    resampled_snaps = [None]

    for s in snaps:
        s_t = s["wallClock"]
        while s_t > t:
            t += interval
            resampled_snaps.append(resampled_snaps[-1])
        if s_t <= t:
            resampled_snaps[-1] = s

    return resampled_snaps

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
    if it is not list:
        print(it)
    for i in it:
        print("  - %s" % i)
        allowed -= 1
        if allowed <= 0:
            break

    if allowed == 0:
        print("  ...")

    print("--")


def save_fig(figure_path: str):
    """Saves figure"""
    print("    Saving figure to '%s'" % figure_path)
    legend(loc="best")
    savefig(figure_path)


def load_jsons(filenames):
    """
    Loads JSON files as (dict, filename) pairs
    """

    filenames = iterable_strict_eval(filenames)
    list.sort(filenames)

    for file_name in filenames:
        try:
            with open(file_name) as dump_file:
                data = json_decode(dump_file.read())
                yield (data, file_name)
        except Exception as ex:
            print("Failed to load '%s' (%s)" % (file_name, ex))


def dumpset_comparable_limits(json_dumps, checks=LIMIT_KEYS):
    """
    Checks if some dumps have matching parameters
    """

    limits = dict()
    for c in checks:
        limits[c] = set()

    for (jd, _) in json_dumps:
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
    assert isinstance(dump, dict)
    alg_name = dump["params"]["algorithm"]
    weight = dump["params"]["weight"]
    pool_size = dump["params"]["parallelRequests"]

    alg_label = alg_name
    if pool_size > 1:
        alg_label += "-%dp" % pool_size
    if weight != 1:
        alg_label += "-%dw" % weight

    return (alg_label, alg_name, weight, pool_size)  # = dump_alg_name(dump)


def dumps_plot(json_dumps, x_key, y_key, ttl=None, x_label=None, y_label=None, colorize_function=None):
    """
    Plots y_key v/s x_key for some json_dumps
    """
    if x_label is None:
        x_label = get_plot_label(x_key)
    if y_label is None:
        y_label = get_plot_label(y_key)

    json_dumps = iterable_strict_eval(json_dumps)
    assert dumpset_comparable_limits(json_dumps)

    empty_plot = True
    for (dump, name) in json_dumps:
        assert isinstance(dump, dict)
        assert isinstance(name, str)

        (alg_label, alg, _, _) = dump_alg_name(dump)

        hist = dump["data"]["StatsHistory"]
        (x_data, y_data) = use_last_x(hist, x_key, y_key)


        line_style = ALG_LINES[""]
        if alg in ALG_LINES.keys():
            line_style = ALG_LINES[alg]

        if colorize_function is None:
            plot(x_data, y_data, line_style, label=alg_label)
        else:
            plot(x_data, y_data, line_style, label=alg_label, color=colorize_function(dump))
        empty_plot = False

    if empty_plot:
        raise Exception("No dumps given")

    xlabel(x_label, fontsize=18)
    ylabel(y_label, fontsize=16)

    if ttl is None:
        ttl = json_dumps[0][0]["query"]
        if ttl in TITLE.keys():
            ttl = TITLE[ttl]

    title(ttl, fontsize=20)


def plot_query_parallelism(query_path, x_key, y_key, alg="AStar"):
    """
    Plots a query on multiple parallelism and algorithms
    """
    if query_path[-1] != '/':
        query_path += '/'
    bench_dumps_regex = "%s**/*%s*.json" % (query_path, alg)

    data = []
    for (dump, name) in load_jsons(get_files(bench_dumps_regex)):
        params = dump["params"]
        K = params["parallelRequests"]
        if K in PARALLELISM_SHOWN:
            data.append((K, dump, name))

    list.sort(data)

    # Project dumps only
    json_dumps = [(dump, name) for (_, dump, name) in data]
    dumps_plot(json_dumps, x_key=x_key, y_key=y_key, colorize_function=color_by_parallelism)


def plot_bench__query_by_parallelism(bench_dir, x_key, y_key):
    """
    Plot multiple-parallelism for A*, Dijkstra and DFS
    """
    for query_dir in get_subdirs(bench_dir):
        print("  Plotting parallelism comparison for '%s'" % query_dir)

        fig = figure()
        for algorithm in ALGORITHMS:
            try:
                plot_query_parallelism(query_dir, x_key, y_key, alg=algorithm)
            except Exception as ex:
                print("Exception: '%s'" % ex)

        parallelism = ",".join([str(p) for p in PARALLELISM_SHOWN])
        figPath = query_dir + "parallelism_%s-%s-p%s.%s" % (y_key, x_key, parallelism, EXTENSION)
        save_fig(figPath)
        close(fig)


def plot_algs(query_path, x_key, y_key):
    """
    Plots different algorithms on comparable parameters
    """
    bench_dumps = load_jsons(get_json_files(query_path))


    dumps_plot(bench_dumps,
               x_key=x_key,
               y_key=y_key,
               colorize_function=color_by_alg)


def plot_bench__by_queries(bench_dir, x_key, y_key):
    """
    Plots multiple algorithms on similar conditions
    """
    print("  Plotting algorithm comparison on '%s'" % bench_dir)

    for query in get_subdirs(bench_dir):          # q10
        for parallelism in get_subdirs(query):    # p1
            for exp in get_subdirs(parallelism):  # quick goal
                fig = figure()
                plot_algs(exp, x_key=x_key, y_key=y_key)
                figPath = exp + "%s-%s.%s" % (y_key, x_key, EXTENSION)
                save_fig(figPath)
                close(fig)


ZEROABLE_STATS = ["goals_found", "triples", "batchID", "expansions", "local_expansions", "remote_expansions"]

def dominate_benchs__by_queries(bench_dir, x_key, y_key, dominance_level=0.6):
    """
    Builds the `dominates` table

    Nasty code. Using SQL is way better than filtering and projecting JSON files
    """

    print("  Building dominates tables on '%s'" % bench_dir)
    set_algs = set()
    set_K = set()
    for query in get_subdirs(bench_dir):          # q10
        for parallelism in get_subdirs(query):    # p1
            for exp in get_subdirs(parallelism):  # quick goal
                for (dump, name) in load_jsons(get_json_files(exp)):
                    assert isinstance(dump, dict)
                    assert isinstance(name, str)
                    (_, alg, _, _) = dump_alg_name(dump)
                    set_algs.add(alg)
                    set_K.add(dump["params"]["parallelRequests"])

    algs = list(set_algs)
    K = list(set_K)
    algs.sort()
    K.sort()
    print(algs)
    print(K)

    table = ""
    table += "\\begin{table}\n"
    table += "\\begin{tabular}{l|lll}\n"
    table += "parallelism & " + " & ".join(algs) + "\n"
    table += "%s"
    table += "\\end{tabular}\n"
    table += "\\end{table}\n"


    domination = dict()
    for k in K:
        domination[k] = dict()
        for alg in algs:
            domination[k][alg] = 0

    for query in get_subdirs(bench_dir):          # q10
        for parallelism in get_subdirs(query):    # p1
            for exp in get_subdirs(parallelism):  # quick goal

                data = []
                _K = 0
                for (dump, name) in load_jsons(get_json_files(exp)):
                    assert isinstance(dump, dict)
                    assert isinstance(name, str)
                    _K = dump["params"]["parallelRequests"]
                    print("  * %s" % (name))
                    (_, alg, _, _) = dump_alg_name(dump)
                    data.append((alg, dump))

                measures = float("inf")
                v_max = None
                v_min = None
                k_max = None
                k_min = None
                if x_key == "wallClock":
                    y_samples = dict()
                    for (alg, dump) in data:
                        y_samples[alg] = time_sample_dump(dump)

                    for alg in algs:
                        filtered_samples = []
                        for s in y_samples[alg]:
                            if s is None:
                                val = None
                                if y_key in ZEROABLE_STATS:
                                    val = 0
                                filtered_samples.append(val)
                            else:
                                filtered_samples.append(s[y_key])
                        y_samples[alg] = filtered_samples
                    for alg in algs:
                        if len(y_samples[alg]) < measures:
                            measures = len(y_samples[alg])

                    (v_max, k_max, v_min, k_min) = get_max_min_labels(y_samples)
                elif x_key == "remote_expansions":
                    y_data = dict()
                    for (alg, dump) in data:
                        y_data[alg] = [d[y_key] for d in dump["data"]["StatsHistory"]]

                    (v_max, k_max, v_min, k_min) = get_max_min_labels(y_data)
                    measures = len(y_data[algs[0]])
                else:
                    print("IMPLEMENT %s", x_key)

                sup = dict()
                for alg in algs:
                    sup[alg] = appearances(alg, k_max)
                    if sup[alg]/measures >= dominance_level:
                        domination[_K][alg] += 1
                print(sup)

                inf = dict()
                for alg in algs:
                    inf[alg] = appearances(alg, k_min)
                print(inf)

                file_name = exp + "comparison_%s-%s.txt" % (y_key, x_key)
                result = {
                    "x_key": x_key,
                    "y_key": y_key,
                    "max": {
                        "values": v_max,
                        "values_count": len(v_max),
                        "top": [list(keys) for keys in k_max],
                        "dominance": sup
                    },
                    "min": {
                        "values": v_min,
                        "values_count": len(v_min),
                        "top": [list(keys) for keys in k_min],
                        "dominance": inf
                    }
                }
                print("Writing log to %s" % file_name)
                with open(file_name, 'w') as f:
                    json.dump(result, f, indent=2)
                print()
    table_data = ""
    print(domination)
    for k in K:
        table_data += "%s & " % k
        table_data += " & ".join([str(domination[k][alg]) for alg in algs]) + "\n"

    table = table % table_data
    print(table)

    table_filename = bench_dir + "dom_%.2f.tex" % dominance_level
    with open(table_filename, 'w') as f:
        f.write(table)



def plot_benchs(bench_directories, x_key, y_key):
    """
    Plots
    """

    print("Analyzing:")
    print_iter(bench_directories)
    for bench_dir in bench_directories:
        print("Analyzing '%s'" % bench_dir)
        plot_bench__by_queries(bench_dir, x_key, y_key)
        plot_bench__query_by_parallelism(bench_dir, x_key, y_key)
        dominate_benchs__by_queries(bench_dir, x_key, y_key)
        print()
    print("Done")


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

    parser.add_argument('--x', metavar='x', type=str, nargs='+',
                        help='x axis key')

    parser.add_argument('--y', metavar='y', type=str, nargs='+',
                        help='y axis key')

    args = parser.parse_args()
    bench_directories = args.directories
    x_keys = args.x or ["remote_expansions"]
    y_keys = args.y or ["goals_found"]

    for y_key in y_keys:
        for x_key in x_keys:
            print("plotting %s vs %s" % (y_key, x_key))
            plot_benchs(bench_directories, x_key, y_key)


if __name__ == '__main__':
    main()



sample_dump = {
    "params": {
        "parallelRequests": 1,
        "weight": 1,
        "limits": {
            "triples": 100000.0,
            "ans": 1000.0,
            "time": 620
        },
        "algorithm": "AStar",
        "quickGoal": True
    },
    "query": "Publications",
    "data": {
        "Paths": [
            [
                {
                    "transition": None,
                    "state": "Author",
                    "node": "http://dblp.l3s.de/d2r/resource/authors/Michael_Stonebraker"
                },
                {
                    "transition": {
                        "d": "<",
                        "P": "http://purl.org/dc/elements/1.1/creator"
                    },
                    "state": "Paper",
                    "node": "http://dblp.l3s.de/d2r/resource/publications/books/aw/Stonebraker86"
                },
                {
                    "transition": {
                        "d": ">",
                        "P": "http://www.w3.org/2000/01/rdf-schema#label"
                    },
                    "state": "Title",
                    "node": "The INGRES Papers: Anatomy of a Relational Database System"
                }
            ]
        ],
        "PathCount": 285,
        "StatsHistory": [
            {
                "requestTime": 0,
                "wallClock": 0.004499673843383789,
                "local_expansions": 0,
                "remote_expansions": 0,
                "requestTriples": 0,
                "triples": 0,
                "batchID": 0,
                "memory": 24.8984375,
                "requestIRI": "",
                "expansions": 0,
                "requestTotalTime": 0,
                "goals_found": 0
            }
        ],
        "Time": 344.36218309402466
    }
}
