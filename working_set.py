from collections import OrderedDict
import getopt
import sys
import time
from vars import units
from util import calculate_unique_elements

SEPARATOR = ", "


def calculate_working_set(reader, percentage, total_unique=None, trim=True):
    from collections import deque

    if total_unique is None:
        total_unique = calculate_unique_elements(reader)

    window_size = max(1, int(total_unique * percentage / 100))

    results = []
    window = deque()
    window_set = {}  # obj_id -> count of occurrences in window

    for req in reader:
        obj_id = req.obj_id

        # Add new element to the right
        window.append(obj_id)
        window_set[obj_id] = window_set.get(obj_id, 0) + 1

        # Pop oldest element from the left if window exceeds size
        if len(window) > window_size:
            old = window.popleft()
            window_set[old] -= 1
            if window_set[old] == 0:
                del window_set[old]

        results.append(len(window_set))

    if trim:
        results = results[window_size:]

    return results


def byte_trace_size(file):
    items = {}
    k = 0
    with open(file) as f:
        f.readline()
        for line in f:
            time_stamp, id, size = line.strip().split(SEPARATOR)
            size = int(size)
            if id in items:
                old_size = items.get(id)
                if old_size != size:
                    k += 1
            items.setdefault(id, size)
    print(f"{k} objects were found with different size")
    total_size = sum(items.values())
    return total_size


def trace_size(file):
    s = set()
    with open(file) as f:
        f.readline()
        for line in f:
            _, id, _ = line.strip().split(SEPARATOR)
            s.add(id)
    return len(s)


def byte_working_set(input_file, trace_size_bytes, window_size):
    unit = "MiB"
    trace_size_mb = trace_size_bytes / units.get(unit)
    print(f"Trace size: {trace_size_mb} {unit}")
    window_size_bytes = int((trace_size_bytes * window_size) / 100)
    window_size_mb = window_size_bytes / units.get(unit)
    print(f"Window size: {window_size_mb} {unit}")

    time.sleep(3)

    cache = OrderedDict()

    output_file = f"{input_file.split("_clean")[0]}.bytes_working_set_{window_size}"

    input_file = open(input_file)
    output_file = open(output_file, "w")

    input_file.readline()
    output_file.write(f"# trace size: {trace_size_mb} {unit}, window %: {
                      window_size}, window size: {window_size_mb} {unit}\n")

    current_window_size_bytes = 0

    for line in input_file:
        _, id, size = line.strip().split(SEPARATOR)
        if id in cache:
            cache.move_to_end(id)
        else:
            size = int(size)
            cache[id] = size
            current_window_size_bytes += size
        while current_window_size_bytes > window_size_bytes:
            id, size = cache.popitem(last=False)
            current_window_size_bytes -= size
        output_file.write(f"{len(cache)}\n")
    input_file.close()
    output_file.close()


def working_set(input_file, trace_size, window_size):
    print(f"Trace size: {trace_size} (elements)")
    perc_window_size = window_size
    window_size = int((trace_size * perc_window_size) / 100)
    print(f"Window size: {window_size} (elements)")

    time.sleep(3)

    cache = OrderedDict()

    output_file = f"{input_file.split("_clean")[0]}.elements_working_set_{perc_window_size}"

    input_file = open(input_file)
    output_file = open(output_file, "w")

    input_file.readline()
    output_file.write(f"# trace size: {trace_size}, window %: {
                      window_size}, window size: {window_size}\n")

    for line in input_file:
        _, id, _ = line.strip().split(SEPARATOR)
        if id in cache:
            cache.move_to_end(id)
        else:
            cache[id] = None
        while len(cache) > window_size:
            id, _ = cache.popitem(last=False)
        output_file.write(f"{len(cache)}\n")
    input_file.close()
    output_file.close()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:b", ["size=", "bytes"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    window_sizes = [1]
    byte_size = False
    for option, argument in opts:
        if option in ("-s", "--size"):
            window_sizes = map(float, argument.split(","))
        elif option in ("-b", "--bytes"):
            byte_size = True
        else:
            print(f"{option} option not recognized\n")

    if byte_size:
        for file in args:
            print("Calculating size (in bytes)")
            trace_size_bytes = byte_trace_size(file)
            for window_size in window_sizes:
                byte_working_set(file, trace_size_bytes, window_size)
    else:
        for file in args:
            print("Calculating size (cardinality)")
            trace_size_bytes = trace_size(file)
            for window_size in window_sizes:
                working_set(file, trace_size_bytes, window_size)


if __name__ == "__main__":
    main()
