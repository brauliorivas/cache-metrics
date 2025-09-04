import getopt
import sys
from HLL import HyperLogLog
from vars import units
from clean import traces

SEPARATOR = ", "


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["trace="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    trace = ""
    for option, argument in opts:
        if option in ("--trace"):
            trace = argument

    for file_path in args:
        cleaner_class = traces.get(trace)
        cleaner = cleaner_class(-1, True, False, False)
        input_file = open(file_path)
        output_file_name = f"{file_path.split("_clean")[0]}.cardinality"
        output_file = open(output_file_name, "w")

        input_file.readline()
        hll = HyperLogLog()
        for line in input_file:
            new_line = cleaner.process_line(line.strip())
            if new_line is None:
                continue
            _, id, _ = line.strip().split(SEPARATOR)
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
