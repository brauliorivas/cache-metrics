import getopt
import sys
from collections import defaultdict


def get_values(file_paths):
    pair_values = defaultdict(list)

    i = 0
    for file_path in file_paths:
        with open(file_path) as file:
            lines = file.readlines()
            for line in lines:
                if "median" in line:
                    median = float(line.strip().split("median: ")[1])
                    pair_values[file_paths[int(i / 2) * 2]].append(median)
        i += 1
    assert len(file_paths) == (len(pair_values) * 2)
    return pair_values


def rate_difference(a, b):
    return (b * 100) / a - 100


def print_rate_difference(pair_values):
    for k, s in pair_values.items():
        a = s[0]
        b = s[1]
        print(f"{k}: {rate_difference(a, b)}% a: {a}, b: {b}")


def run():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    values = get_values(args)
    print_rate_difference(values)


if __name__ == '__main__':
    run()
