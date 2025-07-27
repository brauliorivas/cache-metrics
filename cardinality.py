import getopt
import sys
from HLL import HyperLogLog

SEPARATOR = ", "


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [""])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    for file in args:
        input_file = open(file)
        output_file_name = f"{file.split("_clean")[0]}.cardinality"
        output_file = open(output_file_name, "w")

        input_file.readline()
        hll = HyperLogLog()
        for line in input_file:
            splitted = line.strip().split(SEPARATOR)
            if len(splitted) != 3:
                print("No size for this entry. Check the trace\n")
                continue
            time_stamp, id, size = splitted
            hll.add(id)

        output_file.write(f"HyperLogLog cardinality: {hll.cardinality()}")


if __name__ == "__main__":
    main()
