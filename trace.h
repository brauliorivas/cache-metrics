#include "types.h"
#include <stdint.h>

#ifndef __CACHE_COMPRESS__
#define __CACHE_COMPRESS__

#define COMPRESS_LEVEL 3
#define SHUFFLE_SEED 42ULL

void convert_trace(char *in_path, uint64_t records, int permute);

#endif // !__CACHE_COMPRESS__
