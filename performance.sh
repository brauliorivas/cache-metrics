set -euo pipefail

analysis_script=analysis.py
stats_script=measure_stats.py
python_interpreter=python
measurement_file=./measurement_runs.jsonl
summary_file=./measurement_summary.txt

run_measurement() {
  local normal_trace="$1"
  local shuffled_trace="$2"

  echo "  normal=${normal_trace}"
  echo "  shuffled=${shuffled_trace}"

  "$python_interpreter" "$analysis_script" \
    -f "$normal_trace" \
    -F "$shuffled_trace" \
    -s -w -z -r -c \
    -m \
    --measure-output "$measurement_file"
}

# KEY-VALUE TRACES
run_measurement ./202210_kv_traces_all_sort.csv.oracleGeneral_1000000.zst ./202210_kv_traces_all_sort.csv.oracleGeneral_permuted_1000000.zst
run_measurement ./202401_kv_traces_all_sort.csv.oracleGeneral_1000000.zst ./202401_kv_traces_all_sort.csv.oracleGeneral_permuted_1000000.zst
run_measurement ./cluster17.oracleGeneral.sample10_1000000.zst ./cluster17.oracleGeneral.sample10_permuted_1000000.zst
run_measurement ./cluster18.oracleGeneral.sample10_1000000.zst ./cluster18.oracleGeneral.sample10_permuted_1000000.zst
run_measurement ./cluster29.oracleGeneral.sample10_1000000.zst ./cluster29.oracleGeneral.sample10_permuted_1000000.zst
run_measurement ./cluster44.oracleGeneral.sample10_1000000.zst ./cluster44.oracleGeneral.sample10_permuted_1000000.zst
run_measurement ./cluster45.oracleGeneral.sample10_1000000.zst ./cluster45.oracleGeneral.sample10_permuted_1000000.zst
#
# # OBJECT TRACES
run_measurement ./meta_rprn.oracleGeneral_1000000.zst ./meta_rprn.oracleGeneral_permuted_1000000.zst
run_measurement ./wiki_2019t.oracleGeneral_1000000.zst ./wiki_2019t.oracleGeneral_permuted_1000000.zst

# BLOCK TRACES
run_measurement ./cluster2_16TB.sort.csv_1000000.zst ./cluster2_16TB.sort.csv_permuted_1000000.zst
run_measurement ./block_traces_1.oracleGeneral.bin_1000000.zst ./block_traces_1.oracleGeneral.bin_permuted_1000000.zst
run_measurement ./block_traces_2.oracleGeneral.bin_1000000.zst ./block_traces_2.oracleGeneral.bin_permuted_1000000.zst
run_measurement ./block_traces_3.oracleGeneral.bin_1000000.zst ./block_traces_3.oracleGeneral.bin_permuted_1000000.zst
run_measurement ./block_traces_4.oracleGeneral.bin_1000000.zst ./block_traces_4.oracleGeneral.bin_permuted_1000000.zst
run_measurement ./block_traces_5.oracleGeneral.bin_1000000.zst ./block_traces_5.oracleGeneral.bin_permuted_1000000.zst
run_measurement ./tencentBlock_1360.oracleGeneral_1000000.zst ./tencentBlock_1360.oracleGeneral_permuted_1000000.zst
run_measurement ./alibabaBlock_38.oracleGeneral_1000000.zst ./alibabaBlock_38.oracleGeneral_permuted_1000000.zst

"$python_interpreter" "$stats_script" -i "$measurement_file" -o "$summary_file"
echo "[measure] summary written to $summary_file"
