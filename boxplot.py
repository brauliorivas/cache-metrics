import getopt
import sys
import numpy as np
import matplotlib.pyplot as plt
from vars import units, labels


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:n:m:u:", ["min=", "max=", "unit=", "datatype="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    min = -1
    max = -1
    unit = ""
    datatype = ""

    for option, argument in opts:
        if option in ("-n", "--min"):
            min = int(argument)
        elif option in ("-m", "--max"):
            max = int(argument)
        elif option in ("-u", "--unit"):
            unit = argument
        elif option in ("-t", "--datatype"):
            datatype = argument
        else:
            print(f"{option} option not recognized\n")

    for file in args:
        file_name = file
        output_image = f"{file_name}.boxplot.png"
        file = open(file)
        normalizer = units.get(unit, 1)
        if datatype == "working_set":
            file.readline()
        distances = list(map(lambda distance: int(distance.strip()) / normalizer, file.readlines()))
        distances = np.array(distances)

        if min != -1:
            distances = distances[distances > min]
        if max != -1:
            distances = distances[distances < max]

        if datatype == "working_set":
            img_labels = labels.get("working_set")
        elif datatype == "distance":
            img_labels = labels.get("distance")

        title = img_labels.get("title")
        xlabel = f"{img_labels.get("xlabel")} {unit}"

        q1 = np.percentile(distances, 25)
        median = np.median(distances)
        q3 = np.percentile(distances, 75)

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.boxplot(
            distances, vert=False, patch_artist=True,
            boxprops=dict(facecolor='skyblue', color='black', linewidth=1.5),
            medianprops=dict(color='red', linewidth=2),
            whiskerprops=dict(color='black', linewidth=1.5),
            capprops=dict(color='black', linewidth=1.5),
            flierprops=dict(marker='o', color='black', alpha=0.5)
        )

        ax.set_title(title, fontsize=14, weight='bold', pad=15)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.grid(axis='x', linestyle='--', alpha=0.7)

        y = 1
        ax.annotate(f'Q1 = {q1:.2f}', xy=(q1, y + 0.05), xytext=(q1, y + 0.2),
                    arrowprops=dict(facecolor='black', arrowstyle='-|>', lw=1), fontsize=10)
        ax.annotate(f'Median = {median:.2f}', xy=(median, y + 0.05), xytext=(median, y + 0.3),
                    arrowprops=dict(facecolor='red', arrowstyle='-|>', lw=1), fontsize=10, color='red')
        ax.annotate(f'Q3 = {q3:.2f}', xy=(q3, y + 0.05), xytext=(q3, y + 0.2),
                    arrowprops=dict(facecolor='black', arrowstyle='-|>', lw=1), fontsize=10)

        plt.tight_layout()
        plt.savefig(output_image, dpi=300)
        plt.close()

        file.close()


if __name__ == "__main__":
    main()
