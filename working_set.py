import core
import getopt
import sys

from collections import deque, Counter


def calculate_trace_size(file):
    items = {}
    with open(file) as f:
        for line in f:
            id, size = line.strip().split(" ")
            size = int(size)
            items.setdefault(id, size)
    total_size = sum(items.values())
    return total_size


def compute_size(sizes, counter):
    total = 0
    for id, size in sizes.items():
        total += size * counter[id]
    return total


def perform_working_set(file, window_size):
    working_sets = []
    trace_size = calculate_trace_size(file)
    window_size = int((trace_size * window_size) / 100)
    window = deque()
    sizes = {}
    counter = Counter()
    with open(file) as f:
        for line in f:
            id, size = line.strip().split(" ")
            size = int(size)
            window.append((id, size))
            sizes.setdefault(id, size)
            counter[id] += 1
            while compute_size(sizes, counter) > window_size:  # evict
                old_id, old_size = window.popleft()
                counter[old_id] -= 1
                assert counter[old_id] >= 0
                if counter[old_id] == 0:
                    sizes.pop(old_id)
            working_set = compute_size(sizes, counter)
            working_sets.append(working_set)
    summary = core.five_number_summary(working_sets)
    with open("working_set_{}".format(file), "w") as working_set_file:
        for k, v in summary.items():
            working_set_file.write("{}: {}\n".format(k, int(v)))
    print("Trace working set: {}\n\n".format(summary))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:s:", ["file=", "size="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    file = ""
    window_size = 0
    for option, argument in opts:
        if option in ("-f", "--file"):
            file = argument
        elif option in ("-s", "--size"):
            window_size = float(argument)
        else:
            print(f"{option} option not recognized\n")

    perform_working_set(file, window_size)


if __name__ == "__main__":
    main()
