import argparse
import collections
import json
import pathlib
from statistics import mean, median, pstdev

import numpy as np


def compute_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}

    arr = np.asarray(values, dtype=np.float64)
    return {
        "count": float(len(values)),
        "mean": float(mean(values)),
        "median": float(median(values)),
        "p95": float(np.percentile(arr, 95)),
        "stddev": float(pstdev(values)),
    }


def format_stats(stats: dict[str, float]) -> str:
    if not stats:
        return "count=0"
    return (
        f"count={int(stats['count'])}, "
        f"mean={stats['mean']:.6f}s, "
        f"median={stats['median']:.6f}s, "
        f"p95={stats['p95']:.6f}s, "
        f"stddev={stats['stddev']:.6f}s"
    )


def load_records(path: pathlib.Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            records.append(json.loads(raw))
    return records


def role_filtered(records: list[dict], role: str) -> list[dict]:
    if role == "all":
        return records
    return [rec for rec in records if rec.get("role") == role]


def collect_metric_values(records: list[dict]) -> dict[str, list[float]]:
    grouped = collections.defaultdict(list)
    for rec in records:
        timings = rec.get("timings_sec", {})
        for metric, value in timings.items():
            grouped[metric].append(float(value))
        total = rec.get("total_measured_sec")
        if total is not None:
            grouped["total_measured_sec"].append(float(total))
        eviction_avg = rec.get("eviction", {}).get("avg_all_sec")
        if eviction_avg is not None:
            grouped["eviction_avg_all_sec"].append(float(eviction_avg))
    return grouped


def collect_eviction_slices(records: list[dict]) -> tuple[dict, dict, dict]:
    by_pair = collections.defaultdict(list)
    by_policy = collections.defaultdict(list)
    by_size = collections.defaultdict(list)

    for rec in records:
        eviction = rec.get("eviction", {})

        for pair in eviction.get("by_policy_size", []):
            key = (pair.get("policy"), float(pair.get("cache_size")))
            by_pair[key].append(float(pair.get("time_sec", 0.0)))

        for policy_item in eviction.get("avg_by_policy", []):
            key = policy_item.get("policy")
            by_policy[key].append(float(policy_item.get("avg_time_sec", 0.0)))

        for size_item in eviction.get("avg_by_cache_size", []):
            key = float(size_item.get("cache_size"))
            by_size[key].append(float(size_item.get("avg_time_sec", 0.0)))

    return by_pair, by_policy, by_size


def write_scope_report(f, scope_name: str, records: list[dict]):
    f.write(f"=== Scope: {scope_name} ===\n")
    f.write(f"records={len(records)}\n\n")

    metric_values = collect_metric_values(records)
    f.write("Metric Timings\n")
    for metric in sorted(metric_values):
        f.write(f"- {metric}: {format_stats(compute_stats(metric_values[metric]))}\n")
    f.write("\n")

    by_pair, by_policy, by_size = collect_eviction_slices(records)

    f.write("Eviction: Single Policy+Size\n")
    for (policy, cache_size) in sorted(by_pair):
        label = f"policy={policy}, cache_size={cache_size * 100:.2f}%"
        f.write(f"- {label}: {format_stats(compute_stats(by_pair[(policy, cache_size)]))}\n")
    f.write("\n")

    f.write("Eviction: Single Policy (avg across sizes per run)\n")
    for policy in sorted(by_policy):
        f.write(f"- policy={policy}: {format_stats(compute_stats(by_policy[policy]))}\n")
    f.write("\n")

    f.write("Eviction: Single Cache Size (avg across policies per run)\n")
    for cache_size in sorted(by_size):
        label = f"cache_size={cache_size * 100:.2f}%"
        f.write(f"- {label}: {format_stats(compute_stats(by_size[cache_size]))}\n")
    f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate analysis measurement JSONL runs into timing statistics"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=pathlib.Path,
        default=pathlib.Path("traces/measurement_runs.jsonl"),
        help="Input JSON Lines measurement file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("traces/measurement_summary.txt"),
        help="Output summary report file",
    )

    args = parser.parse_args()

    records = load_records(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("Measurement Summary\n")
        f.write("===================\n\n")

        for scope in ["normal", "shuffled", "all"]:
            scoped_records = role_filtered(records, scope)
            write_scope_report(f, scope, scoped_records)


if __name__ == "__main__":
    main()
