main=./main
records=1000000
analysis_script=analysis.py
python_interpreter=python

run_analysis() {
  {
    IFS= read -r trace 
    IFS= read -r shuffled_trace 
  } < <($main -f "$1" -r "$records" -s)

  echo "$trace"
  echo "$shuffled_trace"

  $python_interpreter $analysis_script -f $trace -F $shuffled_trace -o $2 -t $3 -s -w -z -r -c
}


# KEY-VALUE TRACES
# 2022 Meta KV
run_analysis ./202210_kv_traces_all_sort.csv.oracleGeneral.zst ./traces/202210_meta_kv 202210_meta_kv # DONE
run_analysis ./202401_kv_traces_all_sort.csv.oracleGeneral.zst ./traces/202401_meta_kv 202401_meta_kv # DONE
# 2020 Twitter trace
run_analysis ./cluster17.oracleGeneral.sample10.zst ./traces/cluster17 cluster17 # DONE
run_analysis ./cluster18.oracleGeneral.sample10.zst ./traces/cluster18 cluster18 # DONE
run_analysis ./cluster29.oracleGeneral.sample10.zst ./traces/cluster29 cluster29 # DONE
run_analysis ./cluster44.oracleGeneral.sample10.zst ./traces/cluster44 cluster44 # DONE
run_analysis ./cluster45.oracleGeneral.sample10.zst ./traces/cluster45 cluster45 # DONE

# OBJECT TRACES
# 2022 Meta CDN (rprn 1/4.58, DRAM 8357 MB, NVM 375956 MB)
run_analysis ./meta_rprn.oracleGeneral.zst ./traces/meta_cdn_rprn meta_cdn_rprn # DONE
# 2019 Wikimedia CDN (upload image)
run_analysis ./wiki_2019t.oracleGeneral.zst ./traces/wiki_2019t wiki_2019t # DONE

# BLOCK TRACES
# 2022 Meta Storage
run_analysis ./block_traces_1.oracleGeneral.bin.zst ./traces/meta_storage_1 meta_storage_1 # DONE
run_analysis ./block_traces_2.oracleGeneral.bin.zst ./traces/meta_storage_2 meta_storage_2 # DONE
run_analysis ./block_traces_3.oracleGeneral.bin.zst ./traces/meta_storage_3 meta_storage_3 # DONE
run_analysis ./block_traces_4.oracleGeneral.bin.zst ./traces/meta_storage_4 meta_storage_4 # DONE
run_analysis ./block_traces_5.oracleGeneral.bin.zst ./traces/meta_storage_5 meta_storage_5 # DONE
# 2020 Alibaba Block
run_analysis ./alibabaBlock_38.oracleGeneral.zst ./traces/alibaba_block_38 alibaba_block_38 # DONE
