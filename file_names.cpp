#include "file_names.h"
#include "common.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

char *build_filename(char *filename, int permuted, uint64_t number) {
  char *dot = strrchr(filename, '.');

  size_t base_len = dot ? (size_t)(dot - filename) : strlen(filename);
  const char *ext = dot ? dot : "";

  char suffix[64] = {0};
  if (permuted)
    strncat(suffix, "_permuted", sizeof(suffix) - 1);
  if (number != 0) {
    char num_buf[32];
    snprintf(num_buf, sizeof(num_buf), "_%" PRIu64, number);
    strncat(suffix, num_buf, sizeof(suffix) - strlen(suffix) - 1);
  }

  size_t total = base_len + strlen(suffix) + strlen(ext) + 1;
  char *result = (char *)malloc_orDie(total);
  if (!result)
    return NULL;

  memcpy(result, filename, base_len);                // base
  memcpy(result + base_len, suffix, strlen(suffix)); // suffix
  memcpy(result + base_len + strlen(suffix), ext,
         strlen(ext) + 1); // ext + '\0'

  return result;
}
