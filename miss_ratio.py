import getopt
import sys
from collections import defaultdict

policies = ["LRU", "Sieve", "LIRS", "ARC", "S4LRU", "Random"]


def get_miss_ratios(file_path):
    miss_ratios = defaultdict(list)
    with open(file_path) as file:
        lines = file.readlines()
        for line in lines:
            for policy in policies:
                if f" {policy}" in line:
                    split_line = line.split(", ")
                    miss_ratio = split_line[2]
                    miss_ratio = miss_ratio.split("miss ratio ")[1]
                    miss_ratio = float(miss_ratio)
                    assert miss_ratio <= 1
                    miss_ratios[policy].append(miss_ratio)
    return miss_ratios


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

    def default_value():
        return {
            "0.01": list(),
            "0.10": list(),
            "0.25": list(),
            "0.50": list(),
        }

    sorted_policies_miss_ratios = defaultdict(default_value)
    shuffled_policies_miss_ratios = defaultdict(default_value)

    for trace in sorted_traces_miss_ratios:
        for policy, miss_ratios in trace.items():
            for size, index in cache_size_index.items():
                sorted_policies_miss_ratios[policy][size].append(miss_ratios[index])

    for trace in shuffled_traces_miss_ratios:
        for policy, miss_ratios in trace.items():
            for size, index in cache_size_index.items():
                shuffled_policies_miss_ratios[policy][size].append(miss_ratios[index])

    policies_deltas = defaultdict(default_value)

    for policy in sorted_policies_miss_ratios:
        for cache_size in cache_size_index:
            sorted_values = sorted_policies_miss_ratios[policy][cache_size]
            shuffled_values = shuffled_policies_miss_ratios[policy][cache_size]
            assert len(sorted_values) == len(shuffled_values)
            delta = (sum(shuffled_values) - sum(sorted_values)) / len(sorted_values)
            policies_deltas[policy][cache_size] = delta

    with open("miss_ratios.txt", "w") as output_file:
        for policy in policies:
            output_file.write(f"Policy: {policy}\n")
            for cache_size in cache_size_index:
                output_file.write(f"{cache_size}: {
                                  (policies_deltas[policy][cache_size]) * 100}%\n")
            output_file.write("\n")


def run():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [""])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    miss_ratio_average(args)


if __name__ == '__main__':
    run()
