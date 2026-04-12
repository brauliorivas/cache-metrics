#include "trace.h"
#include "common.h"
#include "file_names.h"
#include "types.h"
#include "xoshiro.h"
#include <libCacheSim.h>
#include <zstd.h>

#define BUFFER_SIZE (10 * 1024 * 1024)

/* ── Fisher-Yates shuffle ── */
static void shuffle(OracleGeneral *buf, size_t n) {
  for (size_t i = n - 1; i > 0; i--) {
    size_t j = xo_next() % (i + 1);
    OracleGeneral tmp = buf[i];
    buf[i] = buf[j];
    buf[j] = tmp;
  }
}

static void compressBuffer_orDie(const OracleGeneral *buf, size_t n, FILE *fout,
                                 ZSTD_CCtx *cctx, int last) {
  size_t const buffOutSize = ZSTD_CStreamOutSize();
  void *const buffOut = malloc_orDie(buffOutSize);

  ZSTD_inBuffer input = {buf, n * sizeof(OracleGeneral), 0};

  ZSTD_EndDirective const mode = last ? ZSTD_e_end : ZSTD_e_continue;

  int finished;
  do {
    ZSTD_outBuffer output = {buffOut, buffOutSize, 0};
    size_t const remaining = ZSTD_compressStream2(cctx, &output, &input, mode);
    CHECK_ZSTD(remaining);
    fwrite_orDie(buffOut, output.pos, fout);
    finished = (remaining == 0);
  } while (!finished);

  CHECK(
      input.pos == input.size,
      "Impossible: zstd only returns 0 when the input is completely consumed!");

  free(buffOut);
}

/* ── main logic ── */
void convert_trace(char *in_path, uint64_t records, int permute) {
  char *out_path = build_filename(in_path, permute, records);
  FILE *fout = fopen_orDie(out_path, "wb");

  reader_t *reader = open_trace(in_path, ORACLE_GENERAL_TRACE, NULL);
  request_t *req = new_request();

  size_t buffInSize = BUFFER_SIZE - (BUFFER_SIZE % sizeof(OracleGeneral));
  OracleGeneral *buf = (OracleGeneral *)malloc_orDie(buffInSize);
  uint64_t chunk_records = buffInSize / sizeof(OracleGeneral);

  ZSTD_CCtx *cctx = ZSTD_createCCtx();
  CHECK(cctx != NULL, "ZSTD_createCCtx() failed!");
  CHECK_ZSTD(
      ZSTD_CCtx_setParameter(cctx, ZSTD_c_compressionLevel, COMPRESS_LEVEL));
  CHECK_ZSTD(ZSTD_CCtx_setParameter(cctx, ZSTD_c_checksumFlag, 1));

  size_t n = 0;
  uint64_t total = 0;
  while (read_one_req(reader, req) == 0) {
    buf[n].timestamp = 0;
    buf[n].obj_id = req->obj_id;
    buf[n].obj_size = (uint32_t)req->obj_size;
    buf[n].next_access_vtime = -2;
    ++n;
    ++total;

    if (n == chunk_records) {
      if (permute)
        shuffle(buf, n);
      compressBuffer_orDie(buf, n, fout, cctx, 0);
      printf("written %zu records (total %" PRIu64 ")\r", n, total);
      n = 0;
    }

    if (total == records)
      break;
  }

  if (n > 0) {
    shuffle(buf, n);
    compressBuffer_orDie(buf, n, fout, cctx, 1);
    printf("written %zu records (total %" PRIu64 ")\r", n, total);
  }

  printf("\ndone. %" PRIu64 " records total.\n", total);
  printf("Generated new file %s\n", out_path);

  ZSTD_freeCCtx(cctx);
  free(buf);
  free(out_path);
  fclose_orDie(fout);
  free_request(req);
  close_trace(reader);
}
