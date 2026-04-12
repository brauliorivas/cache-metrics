import getopt
import sys
import subprocess


def calculate_stack_distance(reader, include_cold_miss_flag=False):
    """
    Calculate stack distance for each request in the trace.

    Stack distance = number of unique objects accessed since the last access to this object.
    Cold miss (first access):
        - include_cold_miss_flag=True  → appends -1
        - include_cold_miss_flag=False → skips the entry

    Returns a list of (obj_id, obj_size, stack_distance) tuples.
    """
    results = []

    from sortedcontainers import SortedList

    lru = SortedList()    # holds negative timestamps of last access (for fast rank query)
    last_time = {}        # obj_id -> last access time

    time = 0
    for req in reader:
        obj_id = req.obj_id

        if obj_id not in last_time:
            if include_cold_miss_flag:
                results.append(-1)
        else:
            t = last_time[obj_id]
            # rank = number of elements with timestamp > t = stack distance
            sd = lru.bisect_right(-t)
            results.append(sd)
            lru.remove(-t)

        last_time[obj_id] = time
        lru.add(-time)
        time += 1

    return results


SEPARATOR = ", "


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:w", [
                                   "program=", "weights"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    program = "./stack-distance/stack-distance"
    weights = False

    for option, argument in opts:
        if option in ("-p", "--program"):
            program = argument
        elif option in ("-w", "--weights"):
            weights = True
        else:
            print(f"{option} option not recognized\n")

    process_args = [program]
    if weights:
        process_args.append("--weight")

    for file in args:
        process = subprocess.Popen(
            process_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        input_file = open(file)
        output_file_name = f"{file.split("_clean")[0]}.distance"
        output_file = open(output_file_name, "w")

        input_file.readline()
        for line in input_file:
            splitted = line.strip().split(SEPARATOR)
            time_stamp, id, size = splitted

            if weights:
                process.stdin.write(f"{id} {size}\n")
            else:
                process.stdin.write(f"{id}\n")
            process.stdin.flush()

            distance = process.stdout.readline().strip()
            if distance == "9223372036854775807":
                continue
            output_file.write(f"{distance}\n")

        process.stdin.close()
        process.terminate()

        input_file.close()
        output_file.close()


if __name__ == "__main__":
    main()
