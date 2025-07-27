import sys
import getopt
from typing import Callable, TextIO
import mmh3

FT = "csv"
MAX = 0xffffffffffffffff


def clean_file(files: list[str], records: int, process_file: Callable[[str, TextIO, int], None], verbose: bool, permuted: bool, sorted_trace: bool) -> None:
    for original_file_name in files:
        new_file_name = f"{original_file_name[:-4]}_{'full' if records == -1 else records}_clean"
        if permuted:
            new_file_name = f"{new_file_name}_permuted"
        new_file_name = f"{new_file_name}.{FT}"
        with open(new_file_name, "w") as new_file:
            process_file(original_file_name, new_file, records, permuted, sorted_trace)


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


def memcached_twitter(original_file: str, new_file: TextIO, records: int, permuted: bool, sorted_trace: bool) -> None:
    i = 0
    file = open(original_file, "r")
    new_file.write("# time, object, size")
    old_time_stamp = 0
    for line in file:
        splited_line = line.strip().split(",")
        time_stamp, anon_key, key_size, value_size, client_id, operation, ttl = splited_line
        if operation != "get":
            continue
        time_stamp = int(time_stamp)
        if time_stamp < old_time_stamp and not sorted_trace:
            continue
        old_time_stamp = time_stamp
        id_hash = mmh3.hash64(anon_key)[0] & MAX
        value_size = int(value_size)
        new_file.write(f"\n{time_stamp}, {id_hash}, {value_size}")
        i += 1
        if i == records:
            break
    file.close()


def wiki(original_file: str, new_file: TextIO, records: int, permuted: bool) -> None:
    pass


trace_algorithms = {
    "ibm_object_store": ibm_object_store,
    "memcached_twitter": memcached_twitter,
}


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvr:t:ps", [
                                   "help", "verbose", "records=", "trace=", "permuted", "sorted"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    records = -1
    verbose = False
    trace = ""
    permuted = False
    sorted_trace = False

    for option, argument in opts:
        if option == "-v":
            verbose = True
        elif option == "-p":
            permuted = True
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

    fn = trace_algorithms.get(trace) or None
    if fn is None:
        print("Can't handle this trace")
        sys.exit(2)
    clean_file(args, records, fn, verbose, permuted, sorted_trace)


if __name__ == '__main__':
    main()
