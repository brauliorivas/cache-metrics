/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under both the BSD-style license (found in the
 * LICENSE file in the root directory of this source tree) and the GPLv2 (found
 * in the COPYING file in the root directory of this source tree).
 * You may select, at your option, one of the above-listed licenses.
 */

/*
 * This header file has common utility functions used in examples.
 */
#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>    // fprintf, perror, fopen, etc.
#include <stdlib.h>   // malloc, free, exit
#include <sys/stat.h> // stat

/* UNUSED_ATTR tells the compiler it is okay if the function is unused. */
#if defined(__GNUC__)
#define UNUSED_ATTR __attribute__((unused))
#else
#define UNUSED_ATTR
#endif

#define HEADER_FUNCTION static UNUSED_ATTR

/*
 * Define the returned error code from utility functions.
 */
typedef enum {
  ERROR_fsize = 1,
  ERROR_fopen = 2,
  ERROR_fclose = 3,
  ERROR_fwrite = 5,
  ERROR_malloc = 8,
  ERROR_largeFile = 9,
} COMMON_ErrorCode;

/*! CHECK
 * Check that the condition holds. If it doesn't print a message and die.
 */
#define CHECK(cond, ...)                                                       \
  do {                                                                         \
    if (!(cond)) {                                                             \
      fprintf(stderr, "%s:%d CHECK(%s) failed: ", __FILE__, __LINE__, #cond);  \
      fprintf(stderr, "" __VA_ARGS__);                                         \
      fprintf(stderr, "\n");                                                   \
      exit(1);                                                                 \
    }                                                                          \
  } while (0)

/*! CHECK_ZSTD
 * Check the zstd error code and die if an error occurred after printing a
 * message.
 */
#define CHECK_ZSTD(fn)                                                         \
  do {                                                                         \
    size_t const err = (fn);                                                   \
    CHECK(!ZSTD_isError(err), "%s", ZSTD_getErrorName(err));                   \
  } while (0)

/*! fsize_orDie() :
 * Get the size of a given file path.
 *
 * @return The size of a given file path.
 */
HEADER_FUNCTION size_t fsize_orDie(const char *filename) {
  struct stat st;
  if (stat(filename, &st) != 0) {
    /* error */
    perror(filename);
    exit(ERROR_fsize);
  }

  off_t const fileSize = st.st_size;
  size_t const size = (size_t)fileSize;
  /* 1. fileSize should be non-negative,
   * 2. if off_t -> size_t type conversion results in discrepancy,
   *    the file size is too large for type size_t.
   */
  if ((fileSize < 0) || (fileSize != (off_t)size)) {
    fprintf(stderr, "%s : filesize too large \n", filename);
    exit(ERROR_largeFile);
  }
  return size;
}

/*! fopen_orDie() :
 * Open a file using given file path and open option.
 *
 * @return If successful this function will return a FILE pointer to an
 * opened file otherwise it sends an error to stderr and exits.
 */
HEADER_FUNCTION FILE *fopen_orDie(const char *filename,
                                  const char *instruction) {
  FILE *const inFile = fopen(filename, instruction);
  if (inFile)
    return inFile;
  /* error */
  perror(filename);
  exit(ERROR_fopen);
}

/*! fclose_orDie() :
 * Close an opened file using given FILE pointer.
 */
HEADER_FUNCTION void fclose_orDie(FILE *file) {
  if (!fclose(file)) {
    return;
  };
  /* error */
  perror("fclose");
  exit(ERROR_fclose);
}

/*! fwrite_orDie() :
 *
 * Write sizeToWrite bytes to a file pointed to by file, obtaining
 * them from a location given by buffer.
 *
 * Note: This function will send an error to stderr and exit if it
 * cannot write data to the given file pointer.
 *
 * @return The number of bytes written.
 */
HEADER_FUNCTION size_t fwrite_orDie(const void *buffer, size_t sizeToWrite,
                                    FILE *file) {
  size_t const writtenSize = fwrite(buffer, 1, sizeToWrite, file);
  if (writtenSize == sizeToWrite)
    return sizeToWrite; /* good */
  /* error */
  perror("fwrite");
  exit(ERROR_fwrite);
}

/*! malloc_orDie() :
 * Allocate memory.
 *
 * @return If successful this function returns a pointer to allo-
 * cated memory.  If there is an error, this function will send that
 * error to stderr and exit.
 */
HEADER_FUNCTION void *malloc_orDie(size_t size) {
  void *const buff = malloc(size);
  if (buff)
    return buff;
  /* error */
  perror("malloc");
  exit(ERROR_malloc);
}

#endif
