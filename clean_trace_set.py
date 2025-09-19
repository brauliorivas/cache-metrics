import getopt
import sys

sep = ", "


def clean_trace_cardinality(file_paths):
    with open("clean_trace_cardinality.txt", "w") as file:
        for file_path in file_paths:
            s = set()
            with open(file_path) as trace:
                trace.readline()
                for line in trace:
                    _, id, _ = line.strip().split(" ")
                    s.add(id)

            c = len(s)
            file.write(f"Trace: {file_path} Cardinality: {c} {c / 1000}K {c / 1000**2}M\n ")


def run():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [""])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    clean_trace_cardinality(args)


if __name__ == '__main__':
    run()
