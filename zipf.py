import sys
import getopt
import numpy as np
from scipy.stats import linregress
from collections import Counter


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:", ["file="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    file = ""

    for option, argument in opts:
        if option in ("-f", "--file"):
            file = argument
        else:
            print(f"{option} option not recognized\n")

    if file == "":
        print("You need to pass the file with ids and size to analyze.\npython <script.py> -f <file_with_ids>\n")
        sys.exit(2)

    ids = []

    with open(file) as clean_file:
        for line in clean_file:
            id, size = line.strip().split(" ")
            ids.append(id)

    ids_freq = Counter(ids)
    frequencies = np.array(sorted(ids_freq.values(), reverse=True))
    ranks = np.arange(1, len(frequencies) + 1)
    log_ranks = np.log(ranks)
    log_freqs = np.log(frequencies)
    slope, _, _, _, _ = linregress(log_ranks, log_freqs)
    alpha = -slope

    print(f"Alpha value: {alpha}")


if __name__ == "__main__":
    main()
