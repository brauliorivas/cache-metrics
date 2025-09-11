import sys
import getopt
import mmh3
import random
import os
from collections import defaultdict, Counter

FT = "csv"
MAX = 0xffffffffffffffff


class Cleaner:
    def __init__(self, records: int, sorted_trace: bool, shuffle: bool, verbose: bool):
        self.records = records
        self.full = records == -1
        self.sorted_trace = sorted_trace
        self.shuffle = shuffle
        self.old_time_stamp = 0
        self.verbose = verbose
        self.hashes = defaultdict(set)

    def hash_id(self, id: str):
        return mmh3.hash64(id)[0] & MAX

    def filter_file_lines(self, line):
        new_line = self.process_line(line.strip())
        if new_line is None:
            return False
        time_stamp, id, object_size = new_line
        if time_stamp < self.old_time_stamp:
            self.j += 1
            return False
        else:
            self.old_time_stamp = time_stamp
        return True

    def clean_file(self, original_file_path: str, remove_ext: bool):
        if remove_ext:
            filename, extension = os.path.splitext(original_file_path)
            new_file_path = filename
        else:
            new_file_path = original_file_path

        if self.shuffle:
            new_file_path = f"{new_file_path}_shuffled"

        prefix = new_file_path
        n_elements = f"{'full' if self.full else self.records}"
        suffix = f"clean.{FT}"
        new_file_path = "_".join([prefix, n_elements, suffix])

        new_file = open(new_file_path, "w")
        new_file.write("# time, object, size")
        old_file = open(original_file_path, "r")

        if isinstance(self, WikiText) or isinstance(self, WikiUpload) or isinstance(self, MetaCDN):
            old_file.readline()

        i = 0
        j = 0
        k = 0
        trace = []
        sizes = {}
        ignored_objects = set()
        count = Counter()

        while i != self.records:
            line = old_file.readline()
            k += 1
            new_line = self.process_line(line.strip())
            if new_line is None:
                continue
            time_stamp, id, object_size = new_line
            if id in ignored_objects:
                continue
            if time_stamp < self.old_time_stamp:
                j += 1
                continue
            else:
                self.old_time_stamp = time_stamp
            if id in sizes:
                sizes[id] = min(object_size, sizes[id])
            else:
                sizes[id] = object_size
            if sizes[id] <= 0:
                ignored_objects.add(id)
                i -= count[id]
            else:
                trace.append(id)
                count[id] += 1
                i += 1

        print(f"There are {j} requests not sorted")
        print(f"First {k} lines were read")

        assert sum(count.values()) == i

        trace = [obj for obj in trace if obj not in ignored_objects]

        assert len(trace) == i

        if self.shuffle:
            random.shuffle(trace)

        for obj in trace:
            new_file.write(f"\n0, {obj}, {sizes[obj]}")

        print(f"There are {len(self.hashes)} unique elements")
        max_collisions = 0
        most_crashed = ""
        for k, v in self.hashes.items():
            if len(v) > max_collisions:
                max_collisions = len(v)
                most_crashed = k
        print(f"Id {most_crashed} crashed with {max_collisions} ids")
        new_file.close()
        old_file.close()
        os.rename(new_file_path, "_".join([prefix, str(i), suffix]))

    def add_hashed_id(self, original_id):
        hashed_id = self.hash_id(original_id)
        self.hashes[hashed_id].add(original_id)
        return hashed_id


class IBMObjectStore(Cleaner):
    sep = " "

    def process_line(self, line: str):
        splited_line = line.split(IBMObjectStore.sep)
        time_stamp, request_type, id = splited_line[:3]
        if request_type != "REST.GET.OBJECT":
            return
        if len(splited_line) < 4:
            return
        object_size = splited_line[3]
        time_stamp = int(time_stamp)
        return time_stamp, self.add_hashed_id(id), int(object_size)


class MemcachedTwitter(Cleaner):
    sep = ","

    def process_line(self, line: str):
        splited_line = line.split(MemcachedTwitter.sep)
        time_stamp, id, _, object_size, _, operation, _ = splited_line
        if operation != "get":
            return
        time_stamp = int(time_stamp)
        return time_stamp, self.add_hashed_id(id), int(object_size)


class WikiUpload(Cleaner):
    def process_line(self, line: str):
        splited_line = line.split()
        time_stamp, id, _, object_size, _ = splited_line
        time_stamp = int(time_stamp)
        return time_stamp, self.add_hashed_id(id), int(object_size)


class WikiText(Cleaner):
    def process_line(self, line: str):
        splited_line = line.split()
        time_stamp, id, object_size, _ = splited_line
        time_stamp = int(time_stamp)
        return time_stamp, self.add_hashed_id(id), int(object_size)


class MetaCDN(Cleaner):
    sep = ","

    def process_line(self, line: str):
        splited_line = line.split(MetaCDN.sep)
        time_stamp, id, object_size, _ = splited_line
        time_stamp = int(time_stamp)
        id_hash = self.add_hashed_id(id)
        self.hashes[id_hash].add(id)
        return time_stamp, self.add_hashed_id(id), int(object_size)


traces = {
    "ibm_object_store": IBMObjectStore,
    "memcached_twitter": MemcachedTwitter,
    "wiki_upload": WikiUpload,
    "wiki_text": WikiText,
    "metaCDN": MetaCDN,
}


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvr:t:", [
                                   "help", "verbose", "records=", "trace=", "shuffle", "sorted", "remove-ext"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    records = -1
    verbose = False
    trace = ""
    shuffled = False
    sorted_trace = False
    remove_ext = False

    for option, argument in opts:
        if option == "-v":
            verbose = True
        elif option in ("-u", "--shuffle"):
            shuffled = True
        elif option in ("-s", "--sorted"):
            sorted_trace = True
        elif option in ("-t", "--trace"):
            trace = argument
        elif option in ("--remove-ext"):
            remove_ext = True
        elif option in ("-r", "--records"):
            try:
                records = int(argument)
            except Exception as e:
                print(e)
                print("Record must be an integer")
                sys.exit(2)
        else:
            print(f"{option} option not recognized")

    cleaner = traces.get(trace) or None
    if cleaner is None:
        print("Can't handle this trace")
        sys.exit(2)

    random.seed(42)
    cleaner_instance: Cleaner = cleaner(records, sorted_trace, shuffled, verbose)
    for file_path in args:
        cleaner_instance.clean_file(file_path, remove_ext)


if __name__ == '__main__':
    main()
