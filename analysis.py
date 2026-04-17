import argparse
import collections
import dataclasses
import pathlib
import pprint
import sys

import libcachesim as lcs

import stats
from cardinality import calculate_cardinality
from eviction_policies import calculate_miss_ratio
from plot import plot_boxplot, plot_cdf
from power_law import fit_powerlaw_from_reader
from stack_distance import calculate_stack_distance
from stats import five_number_summary
from working_set import calculate_working_set


@dataclasses.dataclass
class PlotResult:
    cdf_path: pathlib.Path = dataclasses.field(default_factory=pathlib.Path)
    boxplot_path: pathlib.Path = dataclasses.field(default_factory=pathlib.Path)


@dataclasses.dataclass
class Result:
    summary: stats.SummaryStats = dataclasses.field(default_factory=stats.SummaryStats)
    plot: PlotResult = dataclasses.field(default_factory=PlotResult)


@dataclasses.dataclass
class StackDistanceResult(Result):
    pass


@dataclasses.dataclass
class WorkingSetResult(Result):
    ws_size: float = 0


@dataclasses.dataclass
class MissRatioResult:
    eviction_policy = None
    eviction_policy_name: str = ""
    cache_size: float = 0
    req_miss_ratio: float = 0
    byte_miss_ratio: float = 0


@dataclasses.dataclass
class AnalysisResult:
    stack_distance: StackDistanceResult = dataclasses.field(
        default_factory=StackDistanceResult
    )
    working_set: list[WorkingSetResult] = dataclasses.field(default_factory=list)
    zipf: float = 0
    cardinality: float = 0
    miss_ratios: list[MissRatioResult] = dataclasses.field(default_factory=list)


def analysis(
    file,
    stack_distance=False,
    working_set=False,
    zipf=False,
    rate=False,
    cardinality=False,
    plot_path: pathlib.Path = pathlib.Path("."),
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
            output_path=plot_path / "stack_distance_cdf.svg",
        )
        analysis_results.stack_distance.plot.cdf_path = cdf_path
        boxplot_path = plot_boxplot(
            sd_results,
            title="Stack Distance Boxplot",
            axis_label="Stack Distance",
            output_path=plot_path / "stack_distance_boxplot.svg",
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
                output_path=plot_path / f"working_set_cdf_{ws_size}.svg",
            )
            results.plot.cdf_path = cdf_path
            boxplot_path = plot_boxplot(
                ws_results,
                title=f"Working Set Boxplot ({ws_size})",
                axis_label="Unique Objects in Working Set",
                output_path=plot_path / f"working_set_boxplot_{ws_size}.svg",
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


def create_report(
    analysis_results: AnalysisResult,
    output_path: pathlib.Path,
):
    with open(output_path / "report.txt", "w") as f:
        f.write("Stack Distance Summary:\n")
        f.write(f"{analysis_results.stack_distance.summary} \n\n")

        for ws_result in analysis_results.working_set:
            f.write(f"Working Set Summary (ws_size={ws_result.ws_size * 100}%):\n")
            f.write(f"{ws_result.summary} \n\n")

        f.write(f"Zipf Alpha: {analysis_results.zipf}\n\n")
        f.write(f"Cardinality: {analysis_results.cardinality}\n\n")

        f.write("Miss Ratios:\n")
        for miss_ratio in analysis_results.miss_ratios:
            f.write(
                f"{miss_ratio.eviction_policy_name} (cache_size={miss_ratio.cache_size * 100}%): "
                f"Req Miss Ratio={miss_ratio.req_miss_ratio:.4f}, Byte Miss Ratio={miss_ratio.byte_miss_ratio:.4f}\n"
            )


def comparison_report(
    normal_results: AnalysisResult,
    shuffled_results: AnalysisResult,
    output_path: pathlib.Path,
    trace_name: str = "Trace",
):
    def _numeric_fields(obj) -> dict[str, float]:
        if dataclasses.is_dataclass(obj):
            raw = dataclasses.asdict(obj)
        elif isinstance(obj, dict):
            raw = obj
        elif hasattr(obj, "__dict__"):
            raw = vars(obj)
        else:
            return {}

        out: dict[str, float] = {}
        for key, value in raw.items():
            if isinstance(value, (int, float)):
                out[key] = float(value)
        return out

    def _comparison_text(
        label: str,
        normal: float,
        shuffled: float,
        highlights: list[tuple[float, str]],
    ) -> str:
        delta = normal - shuffled
        abs_delta = abs(delta)

        if shuffled == 0:
            if normal == 0:
                line = f"{label}: NORMAL equals SHUFFLED (both={normal:.6f})."
                highlights.append((0.0, line))
                return line

            direction = "higher" if delta > 0 else "lower"
            line = (
                f"{label}: NORMAL is {direction} than SHUFFLED by "
                f"{abs_delta:.6f} (normal={normal:.6f}, shuffled=0.000000)."
            )
            highlights.append((abs_delta, line))
            return line

        pct = (delta / shuffled) * 100.0
        direction = "higher" if pct > 0 else "lower"
        line = (
            f"{label}: NORMAL is {abs(pct):.2f}% {direction} than SHUFFLED "
            f"(normal={normal:.6f}, shuffled={shuffled:.6f})."
        )
        highlights.append((abs(pct), line))
        return line

    highlights: list[tuple[float, str]] = []

    with open(output_path / "comparison_report.txt", "w") as f:
        f.write("Comparison Report\n")
        f.write(f"Trace: {trace_name}\n")
        f.write("=================\n\n")

        f.write("1) Stack Distance Summary Comparison\n")
        normal_sd = _numeric_fields(normal_results.stack_distance.summary)
        shuffled_sd = _numeric_fields(shuffled_results.stack_distance.summary)
        for field in sorted(set(normal_sd) & set(shuffled_sd)):
            line = _comparison_text(
                f"  - {field}",
                normal_sd[field],
                shuffled_sd[field],
                highlights,
            )
            f.write(f"{line}\n")
        f.write("\n")

        f.write("2) Working Set Summary Comparison\n")
        normal_ws_map = {ws.ws_size: ws for ws in normal_results.working_set}
        shuffled_ws_map = {ws.ws_size: ws for ws in shuffled_results.working_set}
        common_ws = sorted(set(normal_ws_map) & set(shuffled_ws_map))
        for ws_size in common_ws:
            f.write(f"  ws_size={ws_size:.2f}%\n")
            normal_ws = _numeric_fields(normal_ws_map[ws_size].summary)
            shuffled_ws = _numeric_fields(shuffled_ws_map[ws_size].summary)
            for field in sorted(set(normal_ws) & set(shuffled_ws)):
                line = _comparison_text(
                    f"    - {field}",
                    normal_ws[field],
                    shuffled_ws[field],
                    highlights,
                )
                f.write(f"{line}\n")
        missing_ws = sorted(set(normal_ws_map) ^ set(shuffled_ws_map))
        if missing_ws:
            f.write(f"  Unmatched ws_size entries: {missing_ws}\n")
        f.write("\n")

        f.write("3) Miss Ratio (req_miss_ratio) Comparison\n")
        normal_mr = {
            (mr.cache_size, mr.eviction_policy_name): float(mr.req_miss_ratio)
            for mr in normal_results.miss_ratios
        }
        shuffled_mr = {
            (mr.cache_size, mr.eviction_policy_name): float(mr.req_miss_ratio)
            for mr in shuffled_results.miss_ratios
        }

        common_pairs = sorted(set(normal_mr) & set(shuffled_mr))
        pair_diffs: list[tuple[float, tuple[float, str], str]] = []
        for cache_size, policy in common_pairs:
            label = f"  - cache_size={cache_size * 100:.2f}%, policy={policy}"
            line = _comparison_text(
                label,
                normal_mr[(cache_size, policy)],
                shuffled_mr[(cache_size, policy)],
                highlights,
            )
            f.write(f"{line}\n")
            pair_diffs.append(
                (
                    abs(
                        normal_mr[(cache_size, policy)]
                        - shuffled_mr[(cache_size, policy)]
                    ),
                    (cache_size, policy),
                    line,
                )
            )

        normal_by_cache: dict[float, list[float]] = collections.defaultdict(list)
        shuffled_by_cache: dict[float, list[float]] = collections.defaultdict(list)
        for (cache_size, _), value in normal_mr.items():
            normal_by_cache[cache_size].append(value)
        for (cache_size, _), value in shuffled_mr.items():
            shuffled_by_cache[cache_size].append(value)

        f.write("\n  Average by cache size\n")
        cache_diffs: list[tuple[float, float, str]] = []
        for cache_size in sorted(set(normal_by_cache) & set(shuffled_by_cache)):
            n_avg = sum(normal_by_cache[cache_size]) / len(normal_by_cache[cache_size])
            s_avg = sum(shuffled_by_cache[cache_size]) / len(
                shuffled_by_cache[cache_size]
            )
            line = _comparison_text(
                f"  - cache_size={cache_size * 100:.2f}%",
                n_avg,
                s_avg,
                highlights,
            )
            f.write(f"{line}\n")
            cache_diffs.append((abs(n_avg - s_avg), cache_size, line))

        normal_by_policy: dict[str, list[float]] = collections.defaultdict(list)
        shuffled_by_policy: dict[str, list[float]] = collections.defaultdict(list)
        for (_, policy), value in normal_mr.items():
            normal_by_policy[policy].append(value)
        for (_, policy), value in shuffled_mr.items():
            shuffled_by_policy[policy].append(value)

        f.write("\n  Average by eviction policy\n")
        policy_diffs: list[tuple[float, str, str]] = []
        for policy in sorted(set(normal_by_policy) & set(shuffled_by_policy)):
            n_avg = sum(normal_by_policy[policy]) / len(normal_by_policy[policy])
            s_avg = sum(shuffled_by_policy[policy]) / len(shuffled_by_policy[policy])
            line = _comparison_text(
                f"  - policy={policy}",
                n_avg,
                s_avg,
                highlights,
            )
            f.write(f"{line}\n")
            policy_diffs.append((abs(n_avg - s_avg), policy, line))

        f.write("\n4) Most Significant req_miss_ratio Differences\n")
        if pair_diffs:
            _, (cache_size, policy), line = max(pair_diffs, key=lambda x: x[0])
            f.write(
                "  - By cache size + policy: "
                f"cache_size={cache_size * 100:.2f}%, policy={policy}\n"
                f"    {line}\n"
            )
        if cache_diffs:
            _, cache_size, line = max(cache_diffs, key=lambda x: x[0])
            f.write(
                f"  - By cache size only: cache_size={cache_size * 100:.2f}%\n"
                f"    {line}\n"
            )
        if policy_diffs:
            _, policy, line = max(policy_diffs, key=lambda x: x[0])
            f.write(f"  - By eviction policy only: policy={policy}\n    {line}\n")


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s -f NORMAL_TRACE [-F SHUFFLED_TRACE] [-o output_path] [-t TRACE_NAME] [-s] [-w] [-z] [-r] [-c] [-h]"
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
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="Base path for output files",
    )
    parser.add_argument(
        "-t",
        "--trace-name",
        type=str,
        default="Trace",
        help="Name of the trace for labeling purposes (default: 'Trace')",
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
    trace_name = args.trace_name
    stack_distance = args.stack_distance
    working_set = args.working_set
    zipf = args.zipf
    rate = args.rate
    cardinality = args.cardinality

    normal_path = output / "normal"
    normal_path.mkdir(parents=True, exist_ok=True)
    normal_results = analysis(
        trace, stack_distance, working_set, zipf, rate, cardinality, normal_path
    )
    pprint.pprint(normal_results)
    create_report(normal_results, normal_path)

    if shuffled_trace:
        shuffled_path = output / "shuffled"
        shuffled_path.mkdir(parents=True, exist_ok=True)
        shuffled_results = analysis(
            shuffled_trace, stack_distance, working_set, zipf, rate, cardinality, shuffled_path
        )
        pprint.pprint(shuffled_results)
        create_report(shuffled_results, shuffled_path)

        comparison_report(normal_results, shuffled_results, output, trace_name)


if __name__ == "__main__":
    main()
