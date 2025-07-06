# Caching metrics

## Usage

### Cleaning

Run `clean.py` to transform a trace. It extracts the id and size of each row and writes into a new file.
It accepts some options:
- `-r|--records` number of elements to transform from the original trace.
- `-t|--trace` name of trace to clean. 
- `-v|--verbose` verbose mode. 

**Output**

```txt
abc 10
def 15
ghi 30
```
Each argument is considered a path to a file to clean from the original trace. Arguments are passed after options like `file1 file2 file3`

Example usage:

`python clean.py -r 1000000 -t ibm_object_store -v tracefile1 tracefile2 ...`

### Calculate Mattson's Stack Algorithm

Run `stack_distance.py` to get the stack distance of each element from a clean trace file.
Options:
- `-p|--program` path to executable that calculates stack distance.
- `-f|--file` path to clean file that contains the id and size of each element. 

Example usage:

`python stack_distance.py -p ./stack-distance/stack-distance -f path/to/clean/file`
