import libcachesim as lcs
import sys
import argparse
from stack_distance import calculate_stack_distance
from working_set import calculate_working_set
from eviction_policies import calculate_miss_ratio
from cardinality import calculate_cardinality
from power_law import fit_powerlaw_from_reader


def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s -f FILE [-s] [-w] [-z] [-r] [-c] [-h]"
    )

    parser.add_argument("-f", "--file", type=str)
    parser.add_argument("-s", "--stack-distance", action="store_true")
    parser.add_argument("-w", "--working-set", action="store_true")
    parser.add_argument("-z", "--zipf", action="store_true")
    parser.add_argument("-r", "--rate", action="store_true")
    parser.add_argument("-c", "--cardinality", action="store_true")

    args = parser.parse_args()

    file = args.file

    if not file:
        parser.print_help()
        sys.exit(1)

    stack_distance = args.stack_distance
    working_set = args.working_set
    zipf = args.zipf
    rate = args.rate
    cardinality = args.cardinality

    reader = lcs.TraceReader(file, lcs.TraceType.ORACLE_GENERAL_TRACE,
                             lcs.ReaderInitParam(ignore_obj_size=False))

    if stack_distance:
        sd_results = calculate_stack_distance(reader)

    if working_set:
        ws_results = calculate_working_set(reader, 0.1)
        ws_results = calculate_working_set(reader, 1)
        ws_results = calculate_working_set(reader, 10)

    if zipf:
        # zipf_result = estimate_zipf_from_reader(reader)
        powerlaw_result = fit_powerlaw_from_reader(reader, discrete=True, verbose=True)
        print(f"Estimated power law exponent: {powerlaw_result.power_law.alpha:.4f}")

    if cardinality:
        cardinality = calculate_cardinality(reader)

    if rate:
        eviction_policies = [lcs.Sieve, lcs.WTinyLFU,
                             lcs.LIRS, lcs.ARC, lcs.SLRU, lcs.Random]
        cache_sizes = [0.01, 0.1, 0.25, 0.5]

        for policy in eviction_policies:
            for cache_size in cache_sizes:
                req_miss_ratio, byte_miss_ratio = calculate_miss_ratio(
                    policy, cache_size, reader)


if __name__ == '__main__':
    main()
