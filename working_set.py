from collections import OrderedDict
import getopt
import sys
import time
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


class LRUCache:
    def __init__(self):
        self.cache = OrderedDict()

    def append(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = None
        return key

    def pop(self, key):
        if key not in self.cache:
            return None
        self.cache.popitem(last=False)
        return key


def working_set(input_file, window_size):
    print("Calculating size")
    trace_size_bytes = trace_size(input_file)
    unit = "MiB"
    trace_size_mb = trace_size_bytes / units.get(unit)
    print(f"Trace size: {trace_size_mb} {unit}")
    window_size_bytes = int((trace_size_bytes * window_size) / 100)
    window_size_mb = window_size_bytes / units.get(unit)
    print(f"Window size: {window_size_mb} {unit}")

    time.sleep(3)

    window = LRUCache()
    sizes = {}

    output_file = f"{input_file.split("_clean")[0]}.working_set_{window_size}"

    input_file = open(input_file)
    output_file = open(output_file, "w")

    input_file.readline()
    output_file.write(f"# trace size: {trace_size_mb} {unit}, window %: {
                      window_size}, window size: {window_size_mb} {unit}\n")

    current_window_size_bytes = 0

    for line in input_file:
        _, id, size = line.strip().split(SEPARATOR)
        window.append(id)
        if id not in sizes:
            size = int(size)
            sizes[id] = size
            current_window_size_bytes += size
        while current_window_size_bytes > window_size_bytes:
            output_file.write(f"{len(sizes)}\n")
            old_id = window.pop(id)
            current_window_size_bytes -= sizes.get(old_id)
            del sizes[old_id]
    output_file.write(f"{len(sizes)}\n")
    input_file.close()
    output_file.close()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:", ["size="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    window_sizes = [1]
    for option, argument in opts:
        if option in ("-s", "--size"):
            window_sizes = map(float, argument.split(","))
        else:
            print(f"{option} option not recognized\n")

    for file in args:
        for window_size in window_sizes:
            working_set(file, window_size)


if __name__ == "__main__":
    main()
