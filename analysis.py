import argparse
import sys

import libcachesim as lcs

from cardinality import calculate_cardinality
from eviction_policies import calculate_miss_ratio
from plot import plot_boxplot, plot_cdf
from power_law import fit_powerlaw_from_reader
from stack_distance import calculate_stack_distance
from stats import five_number_summary
from working_set import calculate_working_set


def analysis(
    file,
    stack_distance=False,
    working_set=False,
    zipf=False,
    rate=False,
    cardinality=False,
):
    reader = lcs.TraceReader(
        file,
        lcs.TraceType.ORACLE_GENERAL_TRACE,
        lcs.ReaderInitParam(ignore_obj_size=False),
    )

    if stack_distance:
        sd_results = calculate_stack_distance(reader)
        summary = five_number_summary(sd_results)
        cdf_path = plot_cdf(
            sd_results,
            title="Stack Distance CDF",
            axis_label="Stack Distance",
            output_path="stack_distance_cdf.svg",
        )
        boxplot_path = plot_boxplot(
            sd_results,
            title="Stack Distance Boxplot",
            axis_label="Stack Distance",
            output_path="stack_distance_boxplot.svg",
        )

    if working_set:
        working_set_sizes = [0.1, 1, 10]
        for ws_size in working_set_sizes:
            ws_results = calculate_working_set(reader, ws_size)
            summary = five_number_summary(ws_results)
            # print(f"Working Set Summary ({ws_size}s): {summary}")
            cdf_path = plot_cdf(
                ws_results,
                title=f"Working Set CDF ({ws_size})",
                axis_label="Unique Objects in Working Set",
                output_path=f"working_set_cdf_{ws_size}.svg",
            )
            boxplot_path = plot_boxplot(
                ws_results,
                title=f"Working Set Boxplot ({ws_size})",
                axis_label="Unique Objects in Working Set",
                output_path=f"working_set_boxplot_{ws_size}.svg",
            )

    if zipf:
        powerlaw_result = fit_powerlaw_from_reader(reader, discrete=True, verbose=True)
        # print(f"Estimated power law exponent: {powerlaw_result.power_law.alpha:.4f}")

    if cardinality:
        cardinality = calculate_cardinality(reader)

    if rate:
        eviction_policies = [
            lcs.Sieve,
            lcs.WTinyLFU,
            lcs.LIRS,
            lcs.ARC,
            lcs.SLRU,
            lcs.Random,
        ]
        cache_sizes = [0.01, 0.1, 0.25, 0.5]

        for policy in eviction_policies:
            for cache_size in cache_sizes:
                req_miss_ratio, byte_miss_ratio = calculate_miss_ratio(
                    policy, cache_size, reader
                )


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s -f NORMAL_FILE SHUFFLED_FILE -o output_path [-s] [-w] [-z] [-r] [-c] [-h]"
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        nargs=2,
        required=True,
        help="Paths to the normal and shuffled trace files (required)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output",
        required=True,
        help="Base path for output files",
    )
    parser.add_argument(
        "-s",
        "--stack-distance",
        action="store_true",
        help="Calculate stack distance distribution",
    )
    parser.add_argument(
        "-w",
        "--working-set",
        action="store_true",
        help="Calculate working set size distribution",
    )
    parser.add_argument(
        "-z",
        "--zipf",
        action="store_true",
        help="Fit a power law distribution to the data",
    )
    parser.add_argument(
        "-r",
        "--rate",
        action="store_true",
        help="Calculate miss ratios for different eviction policies and cache sizes",
    )
    parser.add_argument(
        "-c",
        "--cardinality",
        action="store_true",
        help="Calculate the cardinality of unique objects in the trace using HyperLogLog",
    )

    args = parser.parse_args()

    files = args.file
    if not files or len(files) != 2:
        parser.print_help()
        sys.exit(1)

    normal_trace, shuffled_trace = files

    output_path = args.output
    stack_distance = args.stack_distance
    working_set = args.working_set
    zipf = args.zipf
    rate = args.rate
    cardinality = args.cardinality

    normal_results = analysis(
        normal_trace, stack_distance, working_set, zipf, rate, cardinality
    )
    shuffled_results = analysis(
        shuffled_trace, stack_distance, working_set, zipf, rate, cardinality
    )


if __name__ == "__main__":
    main()
