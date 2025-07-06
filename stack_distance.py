import getopt
import sys
import subprocess
import os


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:f:", ["program=", "file="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    program = "./stack-distance/stack-distance"
    input_file = ""

    for option, argument in opts:
        if option in ("-p", "--program"):
            program = argument
        elif option in ("-f", "--file"):
            input_file = argument
        else:
            print(f"{option} option not recognized\n")

    process = subprocess.Popen(
        [program, "--weight"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    distances = []
    with open(input_file) as file:
        for line in file:
            splitted = line.split(" ")
            if len(splitted) != 2:
                print("No size for this entry. Check the trace\n")
                continue
            id, size = splitted

            process.stdin.write(f"{id} {size}\n")
            process.stdin.flush()

            distance = process.stdout.readline().strip()
            if distance == "9223372036854775807":
                continue
            distances.append(distance)

    process.stdin.close()
    process.terminate()

    filename = os.path.basename(input_file)
    name = os.path.splitext(filename)[0]
    folder = os.path.dirname(input_file)

    output_file_name = f"{folder}/{name}_distances.txt"
    with open(output_file_name, "w") as new_file:
        for distance in distances:
            new_file.write(f"{distance}\n")


if __name__ == "__main__":
    main()
