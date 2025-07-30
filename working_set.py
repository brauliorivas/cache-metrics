from collections import deque
import getopt
import sys
from vars import units

SEPARATOR = ", "


def trace_size(file):
    items = {}
    with open(file) as f:
        f.readline()
        for line in f:
            time_stamp, id, size = line.strip().split(SEPARATOR)
            size = int(size)
            items.setdefault(id, size)
    total_size = sum(items.values())
    return total_size


def working_set(input_file, window_size):
    print("Calculating size")
    trace_size_bytes = trace_size(input_file)
    unit = "MiB"
    print(f"Trace size: {trace_size_bytes / units.get(unit)} {unit}")
    window_size_bytes = int((trace_size_bytes * window_size) / 100)
    print(f"Window size: {window_size_bytes / units.get(unit)} {unit}")
    window = deque()
    sizes = {}
    ids = set()

    output_file = f"{input_file.split("_clean")[0]}.working_set_{window_size}"

    input_file = open(input_file)
    output_file = open(output_file, "w")

    input_file.readline()
    output_file.write(f"# trace size: {trace_size_bytes}, window %: {window_size}, window size: {window_size_bytes}\n")
    current_window_size = 0

    for line in input_file:
        time_stamp, id, size = line.strip().split(SEPARATOR)
        if id not in ids:
            window.append(id)
            ids.add(id)
            size = int(size)
            sizes[id] = size
            current_window_size += size
        while current_window_size > window_size_bytes:
            old_id = window.popleft()
            current_window_size -= sizes.get(old_id)
            ids.remove(old_id)
            del sizes[old_id]
        working_set = len(ids)
        output_file.write(f"{working_set}\n")

    input_file.close()
    output_file.close()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:", ["size="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    window_size = 1
    for option, argument in opts:
        if option in ("-s", "--size"):
            window_size = float(argument)
        else:
            print(f"{option} option not recognized\n")

    for file in args:
        working_set(file, window_size)


if __name__ == "__main__":
    main()
