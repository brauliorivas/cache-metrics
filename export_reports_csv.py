#!/usr/bin/env python3
import argparse
import csv
import pathlib
import re
import sys

SUMMARY_RE = re.compile(
    r"SummaryStats\(min=np\.float64\(([-+0-9.eE]+)\), "
    r"q1=np\.float64\(([-+0-9.eE]+)\), "
    r"q2=np\.float64\(([-+0-9.eE]+)\), "
    r"q3=np\.float64\(([-+0-9.eE]+)\), "
    r"max=np\.float64\(([-+0-9.eE]+)\), "
    r"skewness=np\.float64\(([-+0-9.eE]+)\)\)"
)

WORKING_SET_LABEL_TO_PREFIX = {
    "10.0%": "ws_0_1pct",
    "100%": "ws_1pct",
    "1000%": "ws_10pct",
}

POLICIES = ["Sieve", "WTinyLFU", "LIRS", "ARC", "SLRU", "Random"]
CACHE_SIZES = ["1.0%", "10.0%", "25.0%", "50.0%"]
CACHE_SIZE_TO_LABEL = {
    "1.0%": "1pct",
    "10.0%": "10pct",
    "25.0%": "25pct",
    "50.0%": "50pct",
}
SUMMARY_FIELDS = ["min", "q1", "q2", "q3", "max", "skewness"]

MISS_RATIO_RE = re.compile(
    r"^([A-Za-z0-9]+) \(cache_size=([0-9.]+%)\): "
    r"Req Miss Ratio=([-+0-9.eE]+), Byte Miss Ratio=([-+0-9.eE]+)$"
)


def build_header():
    header = ["trace", "variant"]

    for field in SUMMARY_FIELDS:
        header.append(f"stack_distance_{field}")

    for ws_prefix in ["ws_0_1pct", "ws_1pct", "ws_10pct"]:
        for field in SUMMARY_FIELDS:
            header.append(f"{ws_prefix}_{field}")

    header.extend(["zipf_alpha", "cardinality"])

    for policy in POLICIES:
        policy_label = policy.lower()
        for cache_size in CACHE_SIZES:
            cache_label = CACHE_SIZE_TO_LABEL[cache_size]
            header.append(f"miss_req_{policy_label}_{cache_label}")

    return header


def parse_summary_line(line, ctx):
    match = SUMMARY_RE.search(line)
    if not match:
        raise ValueError(f"Could not parse SummaryStats line for {ctx}: {line}")

    return {
        "min": float(match.group(1)),
        "q1": float(match.group(2)),
        "q2": float(match.group(3)),
        "q3": float(match.group(4)),
        "max": float(match.group(5)),
        "skewness": float(match.group(6)),
    }


def parse_report(path):
    row = {}

    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    working_sets = {}
    miss_req = {}

    while i < len(lines):
        line = lines[i]

        if line == "Stack Distance Summary:":
            i += 1
            if i >= len(lines):
                raise ValueError("Missing Stack Distance SummaryStats line")
            summary = parse_summary_line(lines[i], "stack distance")
            for field in SUMMARY_FIELDS:
                row[f"stack_distance_{field}"] = summary[field]

        elif line.startswith("Working Set Summary (ws_size="):
            label = line.removeprefix("Working Set Summary (ws_size=").removesuffix("):")
            if label not in WORKING_SET_LABEL_TO_PREFIX:
                raise ValueError(f"Unknown working set label: {label}")

            i += 1
            if i >= len(lines):
                raise ValueError(f"Missing Working Set SummaryStats line for {label}")
            working_sets[label] = parse_summary_line(lines[i], f"working set {label}")

        elif line.startswith("Zipf Alpha:"):
            row["zipf_alpha"] = float(line.split(":", 1)[1].strip())

        elif line.startswith("Cardinality:"):
            row["cardinality"] = float(line.split(":", 1)[1].strip())

        elif line == "Miss Ratios:":
            i += 1
            while i < len(lines):
                miss_line = lines[i]
                match = MISS_RATIO_RE.match(miss_line)
                if not match:
                    raise ValueError(f"Could not parse miss ratio line: {miss_line}")
                policy, cache_size, req_ratio, _ = match.groups()
                if policy not in POLICIES:
                    raise ValueError(f"Unknown policy: {policy}")
                if cache_size not in CACHE_SIZE_TO_LABEL:
                    raise ValueError(f"Unknown cache size: {cache_size}")
                key = (policy, cache_size)
                miss_req[key] = float(req_ratio)
                i += 1
            break

        i += 1

    for ws_label, prefix in WORKING_SET_LABEL_TO_PREFIX.items():
        if ws_label not in working_sets:
            raise ValueError(f"Missing working set block for {ws_label}")
        for field in SUMMARY_FIELDS:
            row[f"{prefix}_{field}"] = working_sets[ws_label][field]

    for policy in POLICIES:
        policy_label = policy.lower()
        for cache_size in CACHE_SIZES:
            cache_label = CACHE_SIZE_TO_LABEL[cache_size]
            key = (policy, cache_size)
            if key not in miss_req:
                raise ValueError(f"Missing miss ratio value for {policy} {cache_size}")
            row[f"miss_req_{policy_label}_{cache_label}"] = miss_req[key]

    required_fields = [
        "zipf_alpha",
        "cardinality",
        *[f"stack_distance_{f}" for f in SUMMARY_FIELDS],
    ]
    missing_required = [field for field in required_fields if field not in row]
    if missing_required:
        raise ValueError(f"Missing required fields: {missing_required}")

    return row


def discover_reports(traces_root):
    reports = []
    for path in traces_root.glob("*/*/report.txt"):
        trace = path.parent.parent.name
        variant = path.parent.name
        if variant not in {"normal", "shuffled"}:
            continue
        reports.append((trace, variant, path))

    reports.sort(key=lambda x: (x[0], 0 if x[1] == "normal" else 1, x[1]))
    return reports


def main():
    parser = argparse.ArgumentParser(
        description="Export all traces/*/{normal,shuffled}/report.txt files into one CSV"
    )
    parser.add_argument(
        "--traces-root",
        type=pathlib.Path,
        default=pathlib.Path("traces"),
        help="Path to traces directory",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("merged_reports.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        help="Fail on first malformed report (default)",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Skip malformed reports and continue",
    )
    parser.set_defaults(strict=True)

    args = parser.parse_args()

    if not args.traces_root.exists():
        print(f"error: traces root does not exist: {args.traces_root}", file=sys.stderr)
        return 1

    header = build_header()
    report_entries = discover_reports(args.traces_root)

    if not report_entries:
        print("error: no report files found", file=sys.stderr)
        return 1

    rows = []
    errors = 0

    for trace, variant, path in report_entries:
        try:
            parsed = parse_report(path)
            parsed["trace"] = trace
            parsed["variant"] = variant
            rows.append(parsed)
        except Exception as exc:
            errors += 1
            if args.strict:
                print(f"error: failed parsing {path}: {exc}", file=sys.stderr)
                return 1
            print(f"warning: skipping {path}: {exc}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(
        f"wrote {len(rows)} rows to {args.output} "
        f"(discovered={len(report_entries)}, errors={errors}, strict={args.strict})"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
