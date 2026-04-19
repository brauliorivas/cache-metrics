# Cache Trace Analysis Toolkit

A comprehensive toolkit for processing, shuffling, and analyzing cache traces in OracleGeneral format. This project enables comparative analysis between normal and shuffled traces to study temporal locality effects on cache performance.

## Overview

This toolkit consists of two main components:

1. **`main`** (C++): Processes `.zst` compressed trace files for reading, printing, selecting a subset of records, and shuffling traces using the Fisher-Yates algorithm.

2. **`analysis.py`** (Python): Performs comprehensive trace analysis including stack distance calculation, working set analysis, Zipfian distribution fitting, cardinality estimation, and miss ratio comparisons across multiple eviction policies.

3. **`analysis.sh`** (Bash): Orchestrates the execution of both tools to perform complete analysis pipelines on trace datasets.

## Building

### Prerequisites

- C++ compiler (g++)
- libCacheSim library
- glib-2.0
- zstd library
- Python 3 with dependencies (see `pyproject.toml`)

### Compilation

```bash
make
```

This will compile the C++ source files and create the `main` executable.

## Usage

### 1. Trace Processor (`main`)

The C++ program provides trace file processing capabilities for OracleGeneral format traces.

**Command Line Options:**

```
Usage: ./main -f FILE [-r RECORDS] [-p] [-s] [-v] [-h]

Options:
  -f, --file FILE       Path to the input .zst trace file (required)
  -r, --records NUM     Number of records to select/sample (0 = all)
  -p, --print           Print trace contents (for debugging)
  -s, --shuffle         Shuffle the trace using Fisher-Yates algorithm
  -v, --verbose         Enable verbose output
  -h, --help            Display help message
```

**Examples:**

```bash
# Select 1 million records from a trace
./main -f trace.oracleGeneral.zst -r 1000000

# Shuffle a trace (generates permuted output)
./main -f trace.oracleGeneral.zst -r 1000000 -s

# Print trace contents with verbose output
./main -f trace.oracleGeneral.zst -p -v
```

**Output:**
- When selecting records: Creates a new file with suffix `_{N}` (e.g., `trace_1000000.zst`)
- When shuffling: Creates a file with suffix `_permuted_{N}` (e.g., `trace_permuted_1000000.zst`)
- The output filename is printed to stdout for piping to other tools

### 2. Trace Analysis (`analysis.py`)

The Python script performs comprehensive statistical analysis on cache traces.

**Command Line Options:**

```
usage: analysis.py -f NORMAL_TRACE [-F SHUFFLED_TRACE] [-o output_path] [-t TRACE_NAME] [-s] [-w] [-z] [-r] [-c] [-h]

Options:
  -f, --trace FILE              Path to the trace file (required)
  -F, --shuffled-trace FILE     Path to the shuffled trace file (optional; enables comparison mode)
  -o, --output PATH             Base path for output files (default: current directory)
  -t, --trace-name NAME         Name of the trace for labeling (default: 'Trace')
  -s, --stack-distance          Calculate stack distance distribution
  -w, --working-set             Calculate working set size distribution
  -z, --zipf                    Fit a power law distribution to estimate Zipf coefficient
  -r, --rate                    Calculate miss ratios for eviction policies
  -c, --cardinality             Calculate cardinality using HyperLogLog
  -h, --help                    Show help message
```

**Examples:**

```bash
# Analyze a single trace with all metrics
python analysis.py -f trace.zst -s -w -z -r -c -o output/ -t my_trace

# Compare normal vs shuffled traces
python analysis.py -f normal.zst -F shuffled.zst -s -w -z -r -c -o comparison/ -t my_trace

# Calculate only stack distance and working set
python analysis.py -f trace.zst -s -w -o results/
```

**Output Structure:**

```
output/
├── normal/
│   ├── report.txt              # Summary statistics
│   ├── stack_distance_cdf.png  # CDF plot
│   ├── stack_distance_boxplot.png
│   ├── working_set_cdf_{size}.png
│   ├── working_set_boxplot_{size}.png
│   └── ...
└── shuffled/                   # (if comparison mode)
    ├── report.txt
    └── ...
└── comparison_report.txt       # (if comparison mode)
```

### 3. Batch Analysis (`analysis.sh`)

The bash script automates the complete analysis pipeline for multiple traces.

**Configuration:**

Edit the script to configure:
- `main`: Path to the compiled C++ executable
- `records`: Number of records to sample (default: 1,000,000)
- `analysis_script`: Path to the Python analysis script
- `python_interpreter`: Python executable to use

**Usage:**

```bash
./analysis.sh
```

The script processes each trace by:
1. Selecting and shuffling the specified number of records using `main`
2. Running `analysis.py` with all metrics enabled (`-s -w -z -r -c`)
3. Generating comparison reports between normal and shuffled traces

## Implementation Details

### Trace Format (OracleGeneral)

The toolkit processes traces in OracleGeneral format with the following structure:

```c
struct OracleGeneral {
    uint32_t timestamp;        // Access timestamp
    uint64_t obj_id;         // Object identifier
    uint32_t obj_size;       // Object size in bytes
    int64_t  next_access_vtime; // Virtual time of next access (-2 if unknown)
};
```

All trace files are compressed using Zstandard (zstd) for efficient storage.

### Shuffling Algorithm

The shuffling implementation uses the **Fisher-Yates (Knuth) shuffle algorithm**:

```
For i from n-1 down to 1:
    j = random integer with 0 <= j <= i
    exchange array[j] and array[i]
```

**Key characteristics:**
- Each permutation is equally likely (unbiased)
- In-place shuffling for memory efficiency
- Applied in chunks of 10MB to handle large traces
- Uses Xoshiro256** PRNG for high-quality random numbers

**Random Number Generator:**
- Algorithm: Xoshiro256** (xor/shift/rotate)
- Seed: Fixed at 42 for reproducibility (`SHUFFLE_SEED`)
- Period: 2^256 - 1
- State initialization uses SplitMix64 to seed from a single 64-bit value

### Stack Distance Calculation

Stack distance measures temporal locality by counting unique objects accessed between consecutive accesses to the same object.

**Algorithm:**
1. Maintain a sorted list of last access timestamps
2. For each request:
   - If first access (cold miss): optionally record -1 or skip
   - Otherwise: stack distance = rank of previous access in sorted list
   - Update timestamp and resort

**Implementation uses `sortedcontainers.SortedList`** for O(log n) rank queries and updates.

**Cold Miss Handling:**
- `include_cold_miss_flag=True`: Records -1 for first accesses
- `include_cold_miss_flag=False`: Skips first accesses (default)

### Working Set Analysis

Working set measures the number of unique objects accessed within a window of recent requests.

**Algorithm:**
- Window size = `total_unique_objects × percentage / 100`
- Uses sliding window (deque) with hash map for O(1) uniqueness checks
- Default percentages: 0.1%, 1%, and 10% of total unique objects
- Results are trimmed by window size to exclude initialization bias

### Zipfian Distribution

Fits a power law distribution to the frequency of object accesses using the `powerlaw` library.

**Interpretation:**
- Alpha (α) ≈ 1.0: Classic Zipf distribution
- Higher α: More skewed (few hot objects dominate)
- Lower α: More uniform distribution

The fitting uses maximum likelihood estimation with discrete distribution support.

### Cardinality Estimation

Uses **HyperLogLog (HLL)** algorithm for approximate distinct counting:
- Memory efficient: ~1.5KB for billions of unique elements
- Standard error: ~2%
- Implementation from `HLL` Python package

### Miss Ratio Simulation

Uses `libcachesim` to simulate cache behavior with various eviction policies:

**Supported Policies:**
- Sieve
- WTinyLFU
- LIRS
- ARC
- SLRU
- Random

**Cache Sizes:**
Simulated at 1%, 10%, 25%, and 50% of total trace size.

**Metrics:**
- Request miss ratio: Fraction of requests that miss
- Byte miss ratio: Fraction of bytes that miss

### Comparison Analysis

When both normal and shuffled traces are provided, the tool generates a comparison report highlighting:

1. **Stack Distance Summary Comparison:** Compares min, max, median, Q1, Q3, mean between traces
2. **Working Set Comparison:** Per-window-size analysis
3. **Miss Ratio Comparison:**
   - Per cache size + eviction policy combination
   - Average by cache size
   - Average by eviction policy
4. **Most Significant Differences:** Identifies the largest divergences

Difference metrics include absolute delta and percentage change.

## Dependencies

### C++
- libCacheSim: Cache simulation library
- glib-2.0: General purpose utility library
- zstd: Zstandard compression library

### Python
- libcachesim: Python bindings for cache simulation
- powerlaw: Power law distribution fitting
- sortedcontainers: Sorted list implementations
- HLL: HyperLogLog cardinality estimation
- matplotlib: Plotting library
- numpy: Numerical computing

Install Python dependencies:
```bash
pip install -e .
```

Or using uv:
```bash
uv sync
```

## License

See LICENSE file for details. Code is licensed under MIT License.
