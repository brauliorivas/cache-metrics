import getopt
import sys
from collections import defaultdict


def get_miss_ratios(file):
    miss_ratios = []
    with open(file) as fd:
        lines = fd.readlines()
        assert len(lines) == 4
        for line in lines:
            split_line = line.split(", ")
            miss_ratio = split_line[2]
            miss_ratio = miss_ratio.split("miss ratio ")[1]
            miss_ratio = float(miss_ratio)
            assert miss_ratio <= 1
            miss_ratios.append(miss_ratio)
    return miss_ratios


def miss_ratio_delta(i, sorted, shuffled, index):
    return shuffled[i][index] - sorted[i][index]


def miss_ratio_average(files):
    sorted_traces = []
    shuffled_traces = []

    for file in files:
        if "shuffled" in file:
            shuffled_traces.append(file)
        else:
            sorted_traces.append(file)

    assert len(sorted_traces) == len(shuffled_traces)

    sorted_traces_miss_ratios = [get_miss_ratios(file) for file in sorted_traces]
    shuffled_traces_miss_ratios = [get_miss_ratios(file) for file in shuffled_traces]

    cache_size_index = {
        "0.01": 0,
        "0.10": 1,
        "0.25": 2,
        "0.50": 3,
    }

    deltas = defaultdict(list)
    for i in range(len(sorted_traces)):
        for cache_size, index in cache_size_index.items():
            deltas[cache_size].append(miss_ratio_delta(
                i, sorted_traces_miss_ratios, shuffled_traces_miss_ratios, index))

    with open("miss_ratios.txt", "w") as output_file:
        for cache_size in deltas:
            average = sum(deltas[cache_size]) / len(deltas[cache_size])
            output_file.write(f"{cache_size}: {average * 100}%\n")


def run():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [""])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    miss_ratio_average(args)


if __name__ == '__main__':
    run()
