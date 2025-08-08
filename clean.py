import sys
import getopt
import mmh3
import random

FT = "csv"
MAX = 0xffffffffffffffff


class Cleaner:
    def __init__(self, records: int, sorted_trace: bool, shuffle: bool, verbose: bool):
        self.records = records
        self.sorted_trace = sorted_trace
        self.shuffle = shuffle
        self.old_time_stamp = 0
        self.verbose = verbose

    def hash_id(self, id: str):
        return mmh3.hash64(id)[0] & MAX

    def process_line(self, line: str):
        pass

    def clean_file(self, original_file_path: str):
        new_file_path = original_file_path
        if "." in original_file_path:
            new_file_path = original_file_path[:-4]
        full = False
        if self.shuffle:
            new_file_path = f"{new_file_path}_shuffled"
        if self.records == -1:
            new_file_path = f"{new_file_path}_full"
            full = True
        else:
            new_file_path = f"{new_file_path}_{self.records}"
        new_file_path = f"{new_file_path}_clean"
        new_file_path = f"{new_file_path}.{FT}"

        new_file = open(new_file_path, "w")
        new_file.write("# time, object, size")

        old_file = open(original_file_path, "r")
        if self.shuffle and full:
            return
        elif self.shuffle and self.records > 0:
            i = 0
            lines = []
            for line in old_file:
                if not self.valid_line(line):
                    continue
                lines.append(line)
                i += 1
                if i == self.records:
                    break
            random.shuffle(lines)
        else:
            lines = old_file
        i = 0
        for line in lines:
            new_line = self.process_line(line.strip())
            if new_line is None:
                continue
            time_stamp, id, object_size = new_line
            new_file.write(f"\n{time_stamp}, {id}, {object_size}")
            i += 1
            if i == self.records:
                break
        new_file.close()
        old_file.close()


class IBMObjectStore(Cleaner):
    sep = " "

    def valid_line(self, line: str):
        splited_line = line.split(IBMObjectStore.sep)
        time_stamp, request_type, id = splited_line[:3]
        if request_type != "REST.GET.OBJECT":
            return False
        if len(splited_line) < 4:
            return False
        return True

    def process_line(self, line: str):
        splited_line = line.split(IBMObjectStore.sep)
        time_stamp, request_type, id = splited_line[:3]
        if request_type != "REST.GET.OBJECT":
            return
        if len(splited_line) < 4:
            return
        object_size = splited_line[3]
        time_stamp = int(time_stamp)
        if time_stamp < self.old_time_stamp and not self.sorted_trace:
            return
        self.old_time_stamp = time_stamp
        return time_stamp, self.hash_id(id), int(object_size)


class MemcachedTwitter(Cleaner):
    sep = ","

    def valid_line(self, line: str):
        splited_line = line.split(MemcachedTwitter.sep)
        time_stamp, id, _, object_size, _, operation, _ = splited_line
        return operation == "get"

    def process_line(self, line: str):
        splited_line = line.split(MemcachedTwitter.sep)
        time_stamp, id, _, object_size, _, operation, _ = splited_line
        if operation != "get":
            return
        time_stamp = int(time_stamp)
        if time_stamp < self.old_time_stamp and not self.sorted_trace:
            return
        self.old_time_stamp = time_stamp
        return time_stamp, self.hash_id(id), int(object_size)


class WikiUpload(Cleaner):
    def process_line(self, line: str):
        splited_line = line.split()
        time_stamp, id, _, object_size, _ = splited_line
        time_stamp = int(time_stamp)
        if time_stamp < self.old_time_stamp and not self.sorted_trace:
            return
        self.old_time_stamp = time_stamp
        return time_stamp, self.hash_id(id), int(object_size)


class WikiText(Cleaner):
    def process_line(self, line: str):
        splited_line = line.split()
        time_stamp, id, object_size, _ = splited_line
        time_stamp = int(time_stamp)
        if time_stamp < self.old_time_stamp and not self.sorted_trace:
            return
        self.old_time_stamp = time_stamp
        return time_stamp, self.hash_id(id), int(object_size)


trace_algorithms = {
    "ibm_object_store": IBMObjectStore,
    "memcached_twitter": MemcachedTwitter,
    "wiki_upload": WikiUpload,
    "wiki_text": WikiText,
}


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvr:t:us", [
                                   "help", "verbose", "records=", "trace=", "shuffle", "sorted"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    records = -1
    verbose = False
    trace = ""
    shuffled = False
    sorted_trace = False

    for option, argument in opts:
        if option == "-v":
            verbose = True
        elif option in ("-u", "--shuffle"):
            shuffled = True
        elif option in "-s":
            sorted_trace = True
        elif option in ("-t", "--trace"):
            trace = argument
        elif option in ("-r", "--records"):
            try:
                records = int(argument)
            except Exception as e:
                print(e)
                print("Record must be an integer")
                sys.exit(2)
        else:
            print(f"{option} option not recognized")

    cleaner = trace_algorithms.get(trace) or None
    if cleaner is None:
        print("Can't handle this trace")
        sys.exit(2)

    random.seed(42)
    cleaner_instance: Cleaner = cleaner(records, sorted_trace, shuffled, verbose)
    for file_path in args:
        cleaner_instance.clean_file(file_path)


if __name__ == '__main__':
    main()
