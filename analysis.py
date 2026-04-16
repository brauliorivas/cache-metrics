import argparse
import pathlib
import pprint
import sys
from dataclasses import dataclass, field

import libcachesim as lcs

import stats
from cardinality import calculate_cardinality
from eviction_policies import calculate_miss_ratio
from plot import plot_boxplot, plot_cdf
from power_law import fit_powerlaw_from_reader
from stack_distance import calculate_stack_distance
from stats import five_number_summary
from working_set import calculate_working_set


@dataclass
class PlotResult:
    cdf_path: pathlib.Path = field(default_factory=pathlib.Path)
    boxplot_path: pathlib.Path = field(default_factory=pathlib.Path)


@dataclass
class Result:
    summary: stats.SummaryStats = field(default_factory=stats.SummaryStats)
    plot: PlotResult = field(default_factory=PlotResult)


@dataclass
class StackDistanceResult(Result):
    pass


@dataclass
class WorkingSetResult(Result):
    ws_size: float = 0


@dataclass
class MissRatioResult:
    eviction_policy = None
    eviction_policy_name: str = ""
    cache_size: float = 0
    req_miss_ratio: float = 0
    byte_miss_ratio: float = 0


@dataclass
class AnalysisResult:
    stack_distance: StackDistanceResult = field(default_factory=StackDistanceResult)
    working_set: list[WorkingSetResult] = field(default_factory=list)
    zipf: float = 0
    cardinality: float = 0
    miss_ratios: list[MissRatioResult] = field(default_factory=list)


def analysis(
    file,
    stack_distance=False,
    working_set=False,
    zipf=False,
    rate=False,
    cardinality=False,
) -> AnalysisResult:
    analysis_results: AnalysisResult = AnalysisResult()
    analysis_results.working_set = []
    analysis_results.miss_ratios = []
    reader = lcs.TraceReader(
        file,
        lcs.TraceType.ORACLE_GENERAL_TRACE,
        lcs.ReaderInitParam(ignore_obj_size=False),
    )

    if stack_distance:
        sd_results = calculate_stack_distance(reader)
        summary = five_number_summary(sd_results)
        analysis_results.stack_distance.summary = summary
        cdf_path = plot_cdf(
            sd_results,
            title="Stack Distance CDF",
            axis_label="Stack Distance",
            output_path="stack_distance_cdf.svg",
        )
        analysis_results.stack_distance.plot.cdf_path = cdf_path
        boxplot_path = plot_boxplot(
            sd_results,
            title="Stack Distance Boxplot",
            axis_label="Stack Distance",
            output_path="stack_distance_boxplot.svg",
        )
        analysis_results.stack_distance.plot.boxplot_path = boxplot_path

    if working_set:
        working_set_sizes = [0.1, 1, 10]
        for ws_size in working_set_sizes:
            results = WorkingSetResult()
            results.ws_size = ws_size
            ws_results = calculate_working_set(reader, ws_size)
            summary = five_number_summary(ws_results)
            results.summary = summary
            cdf_path = plot_cdf(
                ws_results,
                title=f"Working Set CDF ({ws_size})",
                axis_label="Unique Objects in Working Set",
                output_path=f"working_set_cdf_{ws_size}.svg",
            )
            results.plot.cdf_path = cdf_path
            boxplot_path = plot_boxplot(
                ws_results,
                title=f"Working Set Boxplot ({ws_size})",
                axis_label="Unique Objects in Working Set",
                output_path=f"working_set_boxplot_{ws_size}.svg",
            )
            results.plot.boxplot_path = boxplot_path
            analysis_results.working_set.append(results)

    if zipf:
        powerlaw_result = fit_powerlaw_from_reader(reader, discrete=True, verbose=True)
        analysis_results.zipf = powerlaw_result.power_law.alpha

    if cardinality:
        cardinality = calculate_cardinality(reader)
        analysis_results.cardinality = cardinality

    if rate:
        eviction_policies = [
            (lcs.Sieve, "Sieve"),
            (lcs.WTinyLFU, "WTinyLFU"),
            (lcs.LIRS, "LIRS"),
            (lcs.ARC, "ARC"),
            (lcs.SLRU, "SLRU"),
            (lcs.Random, "Random"),
        ]
        cache_sizes = [0.01, 0.1, 0.25, 0.5]

        for policy_t in eviction_policies:
            for cache_size in cache_sizes:
                policy, policy_name = policy_t
                req_miss_ratio, byte_miss_ratio = calculate_miss_ratio(
                    policy, cache_size, reader
                )
                miss_ratio_result = MissRatioResult()
                miss_ratio_result.eviction_policy_name = policy_name
                miss_ratio_result.eviction_policy = policy
                miss_ratio_result.cache_size = cache_size
                miss_ratio_result.req_miss_ratio = req_miss_ratio
                miss_ratio_result.byte_miss_ratio = byte_miss_ratio
                analysis_results.miss_ratios.append(miss_ratio_result)

    return analysis_results


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s -f NORMAL_TRACE [-F SHUFFLED_TRACE] [-o output_path] [-s] [-w] [-z] [-r] [-c] [-h]"
    )

    parser.add_argument(
        "-f",
        "--trace",
        type=str,
        required=True,
        help="Path to the trace file (required)",
    )
    parser.add_argument(
        "-F",
        "--shuffled-trace",
        type=str,
        help="Path to the shuffled trace file (if provided, analysis performs comparison)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
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

    trace = args.trace
    if not trace:
        sys.exit(1)

    shuffled_trace = args.shuffled_trace
    output = args.output
    stack_distance = args.stack_distance
    working_set = args.working_set
    zipf = args.zipf
    rate = args.rate
    cardinality = args.cardinality

    normal_results = analysis(
        trace, stack_distance, working_set, zipf, rate, cardinality
    )
    pprint.pprint(normal_results)
    if shuffled_trace:
        shuffled_results = analysis(
            shuffled_trace, stack_distance, working_set, zipf, rate, cardinality
        )
        pprint.pprint(shuffled_results)


if __name__ == "__main__":
    main()
