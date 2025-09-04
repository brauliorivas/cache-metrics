import getopt
import sys
import numpy as np
import matplotlib.pyplot as plt
from vars import units, STACK_DISTANCE, WORKING_SET, STACK_DISTANCE_LABEL, WORKING_SET_LABEL


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:n:m:u:o", [
                                   "min=", "max=", "unit=", "datatype="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    min = -1
    max = -1
    unit = ""
    datatype = ""
    outliers = False

    for option, argument in opts:
        if option in ("-n", "--min"):
            min = int(argument)
        elif option in ("-m", "--max"):
            max = int(argument)
        elif option in ("-u", "--unit"):
            unit = argument
        elif option in ("-t", "--datatype"):
            datatype = argument
        elif option in ("-o"):
            outliers = True
        else:
            print(f"{option} option not recognized\n")

    assert (datatype == WORKING_SET or datatype == STACK_DISTANCE)

    for file_path in args:
        trace_name = file_path.split("_")[0]
        output_image = f"{file_path}.boxplot.png"
        output_stats = f"{file_path}.stats"
        file = open(file_path)

        if datatype == WORKING_SET:
            file.readline()
        values = list(map(lambda value: int(value.strip()), file.readlines()))

        normalizer = units.get(unit, 1)
        if normalizer != 1:
            values = list(map(lambda value: value / normalizer, values))
        values = np.array(values)

        if min != -1:
            values = values[values >= min]
        if max != -1:
            values = values[values <= max]

        min = np.min(values)
        q1 = np.percentile(values, 25)
        median = np.median(values)
        q3 = np.percentile(values, 75)
        max = np.max(values)

        with open(output_stats, "w") as stats_file:
            stats_file.write(f"min: {min}\n")
            stats_file.write(f"q1: {q1}\n")
            stats_file.write(f"median: {median}\n")
            stats_file.write(f"q3: {q3}\n")
            stats_file.write(f"max: {max}\n")

        if datatype == STACK_DISTANCE:
            title = STACK_DISTANCE_LABEL
            xlabel = "Distances"
            if unit:
                xlabel = f"{xlabel} ({unit})"
        elif datatype == WORKING_SET:
            working_set_perc = file_path.split("working_set_")[1]
            title = f"{WORKING_SET_LABEL} ({working_set_perc} %)"
            xlabel = "Number of elements"

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.boxplot(
            values, vert=False, patch_artist=True, showfliers=outliers,
            boxprops=dict(facecolor='skyblue', color='black', linewidth=1.5),
            medianprops=dict(color='red', linewidth=2),
            whiskerprops=dict(color='black', linewidth=1.5),
            capprops=dict(color='black', linewidth=1.5),
            flierprops=dict(marker='o', color='black', alpha=0.5)
        )
        fig.suptitle(title, fontsize=14, fontweight="bold")
        ax.set_title(trace_name, fontsize=14, weight='bold', pad=15, color="gray")
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
