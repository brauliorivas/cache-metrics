import getopt
import sys
import numpy as np
import matplotlib.pyplot as plt
from vars import units, STACK_DISTANCE, WORKING_SET, STACK_DISTANCE_LABEL, WORKING_SET_LABEL


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:n:m:u:", ["min=", "max=", "unit=", "datatype="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    min_val = -1
    max_val = -1
    unit = ""
    datatype = ""

    for option, argument in opts:
        if option in ("-n", "--min"):
            min_val = int(argument)
        elif option in ("-m", "--max"):
            max_val = int(argument)
        elif option in ("-u", "--unit"):
            unit = argument
        elif option in ("--datatype"):
            datatype = argument
        else:
            print(f"{option} option not recognized\n")

    assert (datatype == WORKING_SET or datatype == STACK_DISTANCE)

    for file_path in args:
        trace_name = file_path.split("_")[0]
        output_image = f"{file_path}.cdf.png"
        file = open(file_path)
        if datatype == WORKING_SET:
            file.readline()
        normalizer = units.get(unit, 1)
        distances = list(map(lambda distance: int(distance.strip()) / normalizer, file.readlines()))
        distances = np.array(distances)

        q1 = np.percentile(distances, 25)
        q3 = np.percentile(distances, 75)
        iqr = q3 - q1
        lower = max(q1 - 1.5 * iqr, 0)
        upper = q3 + 1.5 * iqr
        distances = distances[(distances >= lower) & (distances <= upper)]

        if min_val != -1:
            distances = distances[distances >= min_val]
        if max != -1:
            distances = distances[distances <= max_val]

        values, counts = np.unique(distances, return_counts=True)
        cdf = np.cumsum(counts) / counts.sum()

        if datatype == STACK_DISTANCE:
            title = STACK_DISTANCE_LABEL 
            xlabel = "Distances"
            if unit:
                xlabel = f"{xlabel} ({unit})"
        elif datatype == WORKING_SET:
            working_set_perc = file_path.split("working_set_")[1]
            title = f"{WORKING_SET_LABEL} ({working_set_perc} %)"
            xlabel = "Number of elements"

        plt.figure(figsize=(8, 5))
        plt.title(title, fontsize=14, weight='bold')
        plt.suptitle(trace_name)
        plt.xlabel(xlabel, fontsize=12)
        plt.step(values, cdf, where='post', color='steelblue', linewidth=2)
        plt.ylabel("CDF", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(output_image, dpi=300)

        file.close()


if __name__ == "__main__":
    main()
