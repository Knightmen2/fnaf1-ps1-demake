#include "cd_assets.h"
#include <psxcd.h>
#include <psxspu.h>
#include <string.h>

#define SWAP32(x) ( \
    (((uint32_t)(x) & 0x000000ffu) << 24) | \
    (((uint32_t)(x) & 0x0000ff00u) <<  8) | \
    (((uint32_t)(x) & 0x00ff0000u) >>  8) | \
    (((uint32_t)(x) & 0xff000000u) >> 24))

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t interleave;
    uint32_t size;
    uint32_t sample_rate;
    uint16_t _reserved[5];
    uint16_t channels;
    char name[16];
} VAG_Header;

static uint8_t s_scratch[CD_SCRATCH_BYTES] __attribute__((aligned(4)));
static int s_ready;

/* CdReadSync(0) waits forever on DuckStation misses — always poll with cap */
static int cd_wait_read(void)
{
    int guard = 0;
    int left;
    while (guard < 300000) {
        left = CdReadSync(1, 0);
        if (left <= 0)
            return (left < 0) ? 0 : 1;
        guard++;
    }
    return 0; /* timeout — treat as fail, never hang */
}

static void spu_wait_dma(void)
{
    int guard = 0;
    while (!SpuIsTransferCompleted(SPU_TRANSFER_PEEK) && guard < 100000)
        guard++;
}

void cd_assets_init(void)
{
    if (!CdInit()) {
        s_ready = 0;
        return;
    }
    s_ready = 1;
}

int cd_assets_ready(void)
{
    return s_ready;
}

uint8_t *cd_scratch(void)
{
    return s_scratch;
}

size_t cd_load_file(const char *path)
{
    CdlFILE file;
    size_t len;
    size_t sectors;

    if (!s_ready || !path)
        return 0;
    if (!CdSearchFile(&file, path))
        return 0;

    len = (size_t)file.size;
    sectors = (len + 2047) / 2048;
    if (sectors * 2048 > CD_SCRATCH_BYTES)
        return 0;

    memset(s_scratch, 0, sectors * 2048);
    CdControl(CdlSetloc, &(file.pos), 0);
    CdRead((int)sectors, (uint32_t *)s_scratch, CdlModeSpeed);
    if (!cd_wait_read())
        return 0;
    return len;
}

int cd_stream_vag_to_spu(const char *path, int spu_addr, int *out_rate)
{
    CdlFILE file;
    size_t len;
    size_t sectors;
    size_t i;
    const VAG_Header *h;
    uint32_t data_size;
    uint32_t rate;
    int addr;
    size_t remaining;
    size_t off;

    if (!s_ready || !path || !out_rate)
        return 0;
    if (!CdSearchFile(&file, path))
        return 0;

    len = (size_t)file.size;
    if (len < sizeof(VAG_Header) + 16)
        return 0;

    sectors = (len + 2047) / 2048;
    CdControl(CdlSetloc, &(file.pos), 0);

    CdRead(1, (uint32_t *)s_scratch, CdlModeSpeed);
    if (!cd_wait_read())
        return 0;

    h = (const VAG_Header *)s_scratch;
    data_size = SWAP32(h->size);
    rate = SWAP32(h->sample_rate);
    if (data_size == 0 || data_size > 200000)
        return 0;
    *out_rate = (int)rate;

    addr = spu_addr;
    SpuSetTransferMode(SPU_TRANSFER_BY_DMA);

    remaining = data_size;
    off = sizeof(VAG_Header);

    {
        size_t chunk = 2048 - off;
        if (chunk > remaining)
            chunk = remaining;
        SpuSetTransferStartAddr((uint32_t)addr);
        SpuWrite((const uint32_t *)(s_scratch + off), (size_t)((chunk + 63) & ~63));
        spu_wait_dma();
        addr += (int)chunk;
        remaining -= chunk;
    }

    for (i = 1; i < sectors && remaining > 0; i++) {
        size_t chunk;
        CdRead(1, (uint32_t *)s_scratch, CdlModeSpeed);
        if (!cd_wait_read())
            return 0;
        chunk = remaining > 2048 ? 2048 : remaining;
        SpuSetTransferStartAddr((uint32_t)addr);
        SpuWrite((const uint32_t *)s_scratch, (size_t)((chunk + 63) & ~63));
        spu_wait_dma();
        addr += (int)chunk;
        remaining -= chunk;
    }

    return (int)data_size;
}
