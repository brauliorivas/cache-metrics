import getopt
import sys
import subprocess

SEPARATOR = ", "


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:f:", ["program="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    program = "./stack-distance/stack-distance"

    for option, argument in opts:
        if option in ("-p", "--program"):
            program = argument
        else:
            print(f"{option} option not recognized\n")

    for file in args:
        process = subprocess.Popen(
            [program, "--weight"],
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
            if len(splitted) != 3:
                print("No size for this entry. Check the trace\n")
                continue
            time_stamp, id, size = splitted

            process.stdin.write(f"{id} {size}\n")
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
