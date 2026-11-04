#ifndef FNAF_CD_ASSETS_H
#define FNAF_CD_ASSETS_H

#include <stddef.h>
#include <stdint.h>

/* Sector-aligned static CD scratch (no malloc). Enough for one 8-bit 256x256 TIM. */
#define CD_SCRATCH_BYTES 131072

void cd_assets_init(void);
int  cd_assets_ready(void);

/* Load file from ISO into static scratch. Returns byte size or 0 on failure. */
size_t cd_load_file(const char *path_iso9660);

/* Stream a VAG file from CD straight into SPU RAM (DMA). Returns data size or 0. */
int cd_stream_vag_to_spu(const char *path_iso9660, int spu_addr, int *out_rate);

uint8_t *cd_scratch(void);

#endif
