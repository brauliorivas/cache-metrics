#include "xoshiro.h"

static uint64_t xo_state[4];

static uint64_t rotl(uint64_t x, int k) {
  return (x << k) | (x >> (64 - k));
}

uint64_t xo_next(void) {
  uint64_t result = rotl(xo_state[0] + xo_state[3], 23) + xo_state[0];
  uint64_t t = xo_state[1] << 17;
  xo_state[2] ^= xo_state[0];
  xo_state[3] ^= xo_state[1];
  xo_state[1] ^= xo_state[2];
  xo_state[0] ^= xo_state[3];
  xo_state[2] ^= t;
  xo_state[3] = rotl(xo_state[3], 45);
  return result;
}

void seed_rng(uint64_t seed) {
  for (int i = 0; i < 4; i++) {
    seed += 0x9e3779b97f4a7c15ULL;
    uint64_t z = seed;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    xo_state[i] = z ^ (z >> 31);
  }
}
