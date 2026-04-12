#include <stdint.h>

#ifndef __CACHE_ORACLE_GENERAL__
#define __CACHE_ORACLE_GENERAL__

typedef struct __attribute__((packed)) oracle_general {
    uint32_t timestamp;
    uint64_t obj_id;
    uint32_t obj_size;
    int64_t  next_access_vtime;
} OracleGeneral;

#endif // !CACHEMETRICS_TYPES
