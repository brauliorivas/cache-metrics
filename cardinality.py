import getopt
import sys
from HLL import HyperLogLog
from vars import units

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

        cardinality = hll.cardinality()
        output_file.write(f"HyperLogLog cardinality: {cardinality}")
        unit = "K"
        k = units.get(unit)
        output_file.write(f"\n{cardinality / k}{unit}")
        unit = "M"
        m = units.get(unit)
        output_file.write(f"\n{cardinality / m}{unit}")


if __name__ == "__main__":
    main()
