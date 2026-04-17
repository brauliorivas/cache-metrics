#include "trace.h"
#include "xoshiro.h"
#include <getopt.h>
#include <libCacheSim.h>
#include <libCacheSim/cache.h>
#include <libCacheSim/evictionAlgo.h>
#include <libCacheSim/reader.h>
#include <libCacheSim/simulator.h>
#include <stdio.h>

struct option long_options[] = {
    {"help", no_argument, NULL, 'h'},
    {"file", required_argument, NULL, 'f'},
    {"print", no_argument, NULL, 'p'},
    {"records", required_argument, NULL, 'r'},
    {"shuffle", no_argument, NULL, 's'},
    {NULL, 0, NULL, 0} // terminator
};

int main(int argc, char *argv[]) {
  seed_rng(SHUFFLE_SEED);
  int opt;

  char *file = NULL;
  int print = 0;
  int shuffle = 0;
  uint64_t records = 0;

  while ((opt = getopt_long(argc, argv, "hf:pr:s", long_options, NULL)) != -1) {
    switch (opt) {
    case 'h':
      fprintf(stdout, "Usage: %s -f FILE [-r RECORDS] [-p] [-s] [-h]\n",
              argv[0]);
      return 0;
    case 'f':
      file = optarg;
      break;
    case 'p':
      print = 1;
      break;
    case 'r':
      char *end;
      errno = 0;
      records = (uint64_t)strtoull(optarg, &end, 10);

      if (errno == ERANGE) {
        fprintf(stderr, "Error: number out of range\n");
        return 1;
      }
      if (end == optarg || *end != '\0') {
        fprintf(stderr, "Error: invalid number '%s'\n", optarg);
        return 1;
      }

      break;
    case 's':
      shuffle = 1;
      break;
    case '?':
      fprintf(stderr, "Try '%s --help' for usage.\n", argv[0]);
      return 1;
    }
  }

  if (print) {
    reader_t *reader = open_trace(file, ORACLE_GENERAL_TRACE, NULL);
    request_t *req = new_request();
    uint64_t c = 0;
    while (read_one_req(reader, req) == 0) {
      c++;
      if (c % 1000000 == 0) {
        printf("obj_id=%lu obj_size=%lu clock=%ld next=%ld : c=%lu\n",
               req->obj_id, req->obj_size, req->clock_time,
               req->next_access_vtime, c);
      }
    }
    printf("There are %lu records in this trace\n", c);
    close_trace(reader);
    free_request(req);
    return 0;
  }

  if (records != 0) {
    printf("Selecting %lu records from the trace: %s\n", records, file);
    convert_trace(file, records, 0);
  }

  if (shuffle) {
    printf("Shuffling the trace: %s\n", file);
    convert_trace(file, records, 1);
  }

  return 0;
}
