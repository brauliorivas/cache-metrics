#!/usr/bin/env bash

if [ $# -lt 1 ]; then
  echo "Usage: $0 trace.csv"
  exit 1
fi

TRACE_FILE="$1"

ALGORITHMS=("lru" "sieve" "lirs" "arc" "slru" "random")

for algo in "${ALGORITHMS[@]}"; do
  echo "Running $algo..."
  cachesim "$TRACE_FILE" csv "$algo" "0.01,0.10,0.25,0.50" \
    -t "time-col=1, obj-id-col=2, obj-size-col=3, delimiter=,, obj-id-is-num=1"
done
