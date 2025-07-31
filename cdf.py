import getopt
import sys
import numpy as np
import matplotlib.pyplot as plt
from vars import units, labels


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:n:m:u:", ["min=", "max=", "unit="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    min = -1
    max = -1
    unit = ""

    for option, argument in opts:
        if option in ("-n", "--min"):
            min = int(argument)
        elif option in ("-m", "--max"):
            max = int(argument)
        elif option in ("-u", "--unit"):
            unit = argument
        else:
            print(f"{option} option not recognized\n")

    for file in args:
        file_name = file
        output_image = f"{file_name}.cdf.png"
        file = open(file)
        file.readline()
        normalizer = units.get(unit, 1)
        distances = list(map(lambda distance: int(distance.strip()) / normalizer, file.readlines()))
        distances = np.array(distances)

        # remove outliers
        q1 = np.percentile(distances, 25)
        q3 = np.percentile(distances, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        distances = distances[(distances >= lower) & (distances <= upper)]

        if min != -1:
            distances = distances[distances > min]
        if max != -1:
            distances = distances[distances < max]

        values, counts = np.unique(distances, return_counts=True)
        cdf = np.cumsum(counts) / counts.sum()

        if "working_set" in file_name:
            img_labels = labels.get("working_set")
        elif "distance" in file_name:
            img_labels = labels.get("distance")

        title = img_labels.get("title")
        xlabel = f"{img_labels.get("xlabel")}"
        if unit != "":
            xlabel = f"{xlabel} ({unit})"

        plt.figure(figsize=(8, 5))
        plt.step(values, cdf, where='post', color='steelblue', linewidth=2)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel("CDF", fontsize=12)
        plt.title(title, fontsize=14, weight='bold')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(output_image, dpi=300)

        file.close()


if __name__ == "__main__":
    main()
