#include "types.h"
#include <libCacheSim/enum.h>
#include <stdint.h>

#ifndef __CACHE_COMPRESS__
#define __CACHE_COMPRESS__

#define COMPRESS_LEVEL 3
#define SHUFFLE_SEED 42ULL

void convert_trace(char *in_path, trace_type_e trace_format, uint64_t records,
                   int permute, int verbose);

#endif // !__CACHE_COMPRESS__
