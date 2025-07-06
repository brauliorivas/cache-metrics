import sys
import getopt
from typing import Callable, TextIO


def process(files: list[str], records: int, process_file: Callable[[str, TextIO, int], None], verbose: bool, permuted: bool) -> None:
    for original_file_name in files:
        new_file_name = f"{original_file_name.lower()}_clean"
        if permuted:
            new_file_name = f"{new_file_name}_permuted.txt"
        else:
            new_file_name = f"{new_file_name}.txt"
        with open(new_file_name, "w") as new_file:
            process_file(original_file_name, new_file, records, permuted)


def ibm_object_store(original_file: str, new_file: TextIO, records: int, permuted: bool) -> None:
    i = 0
    with open(original_file, "r") as file:
        for line in file:
            splited_line = line.split(" ")
            time_stamp, request_type, id = splited_line[:3]
            if request_type != "REST.GET.OBJECT":
                continue
            id = f"id-{id}"
            if len(splited_line) >= 4:
                new_file.write(f"{id} {splited_line[3]}\n")
            else:
                new_file.write(f"{id}\n")
            i += 1
            if i == records:
                break


def memcached_twitter(original_file: str, new_file: TextIO, records: int, permuted: bool) -> None:
    i = 0
    with open(original_file, "r") as file:
        for line in file:
            splited_line = line.split(",")
            time_stamp, anon_key, key_size, value_size, client_id, operation, ttl = splited_line
            if operation != "get":
                continue
            id = f"id-{anon_key}"
            value_size = int(value_size)
            new_file.write(f"{id} {value_size}\n")
            i += 1
            if i == records:
                break


def wiki(original_file: str, new_file: TextIO, records: int, permuted: bool) -> None:
    pass


trace_algorithms = {
    "ibm_object_store": ibm_object_store,
    "memcached_twitter": memcached_twitter,
}


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvr:t:p", [
                                   "help", "verbose", "records=", "trace=", "permuted"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    records = -1
    verbose = False
    trace = ""
    permuted = False

    for option, argument in opts:
        if option == "-v":
            verbose = True
        elif option == "-p":
            permuted = True
        elif option in ("-r", "--records"):
            try:
                records = int(argument)
            except Exception as e:
                print(e)
                print("Record must be an integer")
                sys.exit(2)
        elif option in ("-t", "--trace"):
            trace = argument
        else:
            print(f"{option} option not recognized")

    fn = trace_algorithms.get(trace) or None
    if fn is None:
        print("Can't handle this trace")
        sys.exit(2)
    process(args, records, fn, verbose, permuted)


if __name__ == '__main__':
    main()
