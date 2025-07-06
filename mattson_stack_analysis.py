import getopt
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew
import seaborn as sns


sns.set(style="whitegrid")

units = {
    "GiB": 1024**3,
    "MiB": 1024**2,
    "KiB": 1024,
}


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:n:m:u:", ["file=", "min=", "max=", "unit="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    file = ""
    min = -1
    max = -1
    unit = ""

    for option, argument in opts:
        if option in ("-f", "--file"):
            file = argument
        elif option in ("-n", "--min"):
            min = int(argument)
        elif option in ("-m", "--max"):
            max = int(argument)
        elif option in ("-u", "--unit"):
            unit = argument
        else:
            print(f"{option} option not recognized\n")

    if file == "":
        print("You need to pass the file with distances to analyze.\npython <script.py> -f <file_with_distances>\n")
        sys.exit(2)

    distances = []

    with open(file) as file_with_distances:
        for line in file_with_distances:
            distance = int(line.strip())
            distances.append(distance)

    normalizer = units.get(unit, 1)

    distances = np.array(distances) / normalizer

    if min != -1:
        distances = distances[distances > min]
    if max != -1:
        distances = distances[distances < max]

    values, counts = np.unique(distances, return_counts=True)
    cdf = np.cumsum(counts) / counts.sum()

    plt.figure(figsize=(8, 5))
    plt.step(values, cdf, where='post', color='steelblue', linewidth=2)
    plt.xlabel("Distance", fontsize=12)
    plt.ylabel("CDF", fontsize=12)
    plt.title("CDF of Distances (Unique Values)", fontsize=14, weight='bold')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

    min = np.min(distances)
    q1 = np.percentile(distances, 25)
    median = np.median(distances)
    q3 = np.percentile(distances, 75)
    max = np.max(distances)
    skewness = skew(distances)

    print(f"Skewness: {skewness}")
    print(f"Min value: {min}")
    print(f"q1: {q1}")
    print(f"median: {median}")
    print(f"q3: {q3}")
    print(f"Max value: {max}")

    plt.figure(figsize=(6, 4))
    sns.boxplot(x=distances, color='skyblue')
    plt.title("Boxplot of Distances", fontsize=14, weight='bold')
    plt.xlabel("Distance", fontsize=12)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
