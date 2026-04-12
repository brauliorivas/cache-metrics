#include <stdint.h>

#ifndef __CACHE_RANDOM__
#define __CACHE_RANDOM__

uint64_t xo_next(void);
void seed_rng(uint64_t seed);

#endif // !__CACHE_RANDOM__
