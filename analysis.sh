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

# 2020 Twitter trace
run_analysis ./cluster17.oracleGeneral.sample10.zst ./traces/cluster17 cluster17 # DONE
run_analysis ./cluster18.oracleGeneral.sample10.zst ./traces/cluster18 cluster18 # DONE
run_analysis ./cluster29.oracleGeneral.sample10.zst ./traces/cluster29 cluster29 # DONE
run_analysis ./cluster44.oracleGeneral.sample10.zst ./traces/cluster44 cluster44 # DONE
run_analysis ./cluster45.oracleGeneral.sample10.zst ./traces/cluster45 cluster45 # DONE

# 2019 Wikimedia upload (image)
run_analysis ./wiki_2019t.oracleGeneral.zst ./traces/wiki_2019t wiki_2019t # TAKES TOO LONG

# 2022 Meta CDN (rprn 1/4.58, DRAM 8357 MB, NVM 375956 MB)
run_analysis ./meta_rprn.oracleGeneral.zst ./traces/meta_rprn meta_rprn # DONE
