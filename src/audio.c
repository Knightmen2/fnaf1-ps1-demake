#include "audio.h"
#include "cd_assets.h"
#include <psxspu.h>
#include <hwregs_c.h>
#include <stdint.h>

#define ALLOC_START_ADDR 0x1010
#define BGM_SPU_ADDR     0x50000
#define FR_BGM_LOOP      560
#define SPU_CHUNK        4096
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

typedef struct {
    int spu_addr;
    int sample_rate;
    short loaded;
} SfxBank;

static SfxBank s_bank[SFX_COUNT];
static int s_next_ch;
static int s_next_addr;
static short s_bgm;
static int s_bgm_rate;
static short s_cd_ready;
static short s_sfx_ready;
static short s_bgm_loop_left;
static short s_bgm_in_slot;

/* Deferred BGM upload state — never stall a frame with 160KB DMA */
static const uint8_t *s_bgm_pend_vag;
static int s_bgm_pend_off;
static int s_bgm_pend_size;
static int s_bgm_pend_rate;
static short s_bgm_pend_id;
static short s_bgm_pend_vol;
static short s_bgm_uploading;

extern const uint8_t vag_blip3[];
extern const uint8_t vag_doorclose[];
extern const uint8_t vag_error[];
extern const uint8_t vag_windowscare[];
extern const uint8_t vag_put_down[];
extern const uint8_t vag_xscream[];
extern const uint8_t vag_static[];
extern const uint8_t vag_deep_steps[];
extern const uint8_t vag_running_fast3[];
extern const uint8_t vag_fan_embed[];
extern const uint8_t vag_menu_embed[];

static void spu_dma_wait(void)
{
    int guard = 0;
    while (!SpuIsTransferCompleted(SPU_TRANSFER_PEEK) && guard < 80000)
        guard++;
}

static void upload_chunk(int addr, const void *data, int size)
{
    int sz = (size + 63) & ~63;
    SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
    SpuSetTransferStartAddr((uint32_t)addr);
    SpuWrite((const uint32_t *)data, (size_t)sz);
    spu_dma_wait();
}

static int upload_sample(const void *data, int size)
{
    int addr = s_next_addr;
    int left = size;
    const uint8_t *p = (const uint8_t *)data;
    int at = addr;

    while (left > 0) {
        int n = left > SPU_CHUNK ? SPU_CHUNK : left;
        upload_chunk(at, p, n);
        at += n;
        p += n;
        left -= n;
    }
    s_next_addr = addr + ((size + 63) & ~63);
    return addr;
}

static void bank_from_vag(SfxId id, const uint8_t *vag)
{
    const VAG_Header *h = (const VAG_Header *)vag;
    uint32_t size, rate;
    if (!vag)
        return;
    size = SWAP32(h->size);
    rate = SWAP32(h->sample_rate);
    if (size == 0 || size > 100000)
        return;
    s_bank[id].spu_addr = upload_sample(h + 1, (int)size);
    s_bank[id].sample_rate = (int)rate;
    s_bank[id].loaded = 1;
}

static void play_voice(int ch, int addr, int sample_rate, int vol)
{
    SpuSetKey(0, 1 << ch);
    SPU_CH_FREQ(ch) = getSPUSampleRate(sample_rate);
    SPU_CH_ADDR(ch) = getSPUAddr(addr);
    SPU_CH_VOL_L(ch) = (short)vol;
    SPU_CH_VOL_R(ch) = (short)vol;
    SPU_CH_ADSR1(ch) = 0x80ff;
    SPU_CH_ADSR2(ch) = 0x1fc2;
    SpuSetKey(1, 1 << ch);
}

static void play_addr(int addr, int sample_rate)
{
    int ch = s_next_ch;
    play_voice(ch, addr, sample_rate, 0x3fff);
    s_next_ch = (ch + 1) % 22;
}

static void start_bgm_upload(SfxId id, const uint8_t *vag, int vol)
{
    const VAG_Header *h = (const VAG_Header *)vag;
    uint32_t size, rate;
    if (!vag)
        return;
    size = SWAP32(h->size);
    rate = SWAP32(h->sample_rate);
    if (size == 0 || size > 200000)
        return;

    SpuSetKey(0, 1 << 23);
    s_bgm_pend_vag = (const uint8_t *)(h + 1);
    s_bgm_pend_off = 0;
    s_bgm_pend_size = (int)size;
    s_bgm_pend_rate = (int)rate;
    s_bgm_pend_id = (short)id;
    s_bgm_pend_vol = (short)vol;
    s_bgm_uploading = 1;
    s_bgm_in_slot = -1;
    s_bgm = id;
}

static void bgm_upload_tick(void)
{
    int n;
    if (!s_bgm_uploading || !s_bgm_pend_vag)
        return;

    /* One chunk per frame — keeps game at 60 FPS */
    n = s_bgm_pend_size - s_bgm_pend_off;
    if (n > SPU_CHUNK)
        n = SPU_CHUNK;
    upload_chunk(BGM_SPU_ADDR + s_bgm_pend_off,
                 s_bgm_pend_vag + s_bgm_pend_off, n);
    s_bgm_pend_off += n;

    if (s_bgm_pend_off >= s_bgm_pend_size) {
        s_bgm_uploading = 0;
        s_bgm_in_slot = s_bgm_pend_id;
        s_bgm_rate = s_bgm_pend_rate;
        s_bgm_loop_left = FR_BGM_LOOP;
        play_voice(23, BGM_SPU_ADDR, s_bgm_rate, s_bgm_pend_vol);
    }
}

void audio_init(void)
{
    int i;
    SpuInit();
    SpuSetCommonMasterVolume(0x3fff, 0x3fff);
    s_next_ch = 0;
    s_next_addr = ALLOC_START_ADDR;
    s_bgm = SFX_NONE;
    s_bgm_rate = 22050;
    s_cd_ready = 0;
    s_sfx_ready = 0;
    s_bgm_loop_left = 0;
    s_bgm_in_slot = -1;
    s_bgm_uploading = 0;
    s_bgm_pend_vag = 0;
    for (i = 0; i < SFX_COUNT; i++)
        s_bank[i].loaded = 0;
}

void audio_load_sfx_minimal(void)
{
    if (s_sfx_ready)
        return;
    bank_from_vag(SFX_BLIP, vag_blip3);
    bank_from_vag(SFX_DOOR, vag_doorclose);
    bank_from_vag(SFX_ERROR, vag_error);
    s_sfx_ready = 1;
}

void audio_load_sfx(void)
{
    if (s_sfx_ready >= 2)
        return;
    /* Extend bank without resetting — avoid re-DMA of minimal set */
    if (s_sfx_ready < 1) {
        s_next_addr = ALLOC_START_ADDR;
        bank_from_vag(SFX_BLIP, vag_blip3);
        bank_from_vag(SFX_DOOR, vag_doorclose);
        bank_from_vag(SFX_ERROR, vag_error);
        s_sfx_ready = 1;
    }
    bank_from_vag(SFX_WINDOW_SCARE, vag_windowscare);
    bank_from_vag(SFX_PUT_DOWN, vag_put_down);
    bank_from_vag(SFX_SCREAM, vag_xscream);
    bank_from_vag(SFX_STATIC, vag_static);
    bank_from_vag(SFX_STEPS, vag_deep_steps);
    bank_from_vag(SFX_RUN, vag_running_fast3);
    s_sfx_ready = 2;
}

/* Spread remaining SFX across frames — call from main loop */
void audio_load_sfx_step(void)
{
    if (s_sfx_ready >= 2)
        return;
    audio_load_sfx();
}

void audio_enable_cd(void)
{
    s_cd_ready = 1;
}

void audio_play(SfxId id)
{
    if (id <= SFX_NONE || id >= SFX_COUNT)
        return;

    if (id == BGM_MENU) {
        if (s_bgm_in_slot == BGM_MENU && !s_bgm_uploading) {
            s_bgm = BGM_MENU;
            s_bgm_loop_left = FR_BGM_LOOP;
            play_voice(23, BGM_SPU_ADDR, s_bgm_rate, 0x2fff);
            return;
        }
        start_bgm_upload(BGM_MENU, vag_menu_embed, 0x2fff);
        return;
    }
    if (id == BGM_FAN) {
        if (s_bgm_in_slot == BGM_FAN && !s_bgm_uploading) {
            s_bgm = BGM_FAN;
            s_bgm_loop_left = FR_BGM_LOOP;
            play_voice(23, BGM_SPU_ADDR, s_bgm_rate, 0x28ff);
            return;
        }
        start_bgm_upload(BGM_FAN, vag_fan_embed, 0x28ff);
        return;
    }
    if (id == BGM_EERIE || id == SFX_MUSIC_BOX) {
        /* CD optional — never block; skip if fails */
        int rate = 0;
        if (!s_cd_ready)
            return;
        SpuSetKey(0, 1 << 23);
        if (cd_stream_vag_to_spu("\\SND\\MBOX.VAG", BGM_SPU_ADDR, &rate) > 0) {
            s_bgm_rate = rate;
            s_bgm = SFX_MUSIC_BOX;
            s_bgm_in_slot = -1;
            s_bgm_loop_left = 0;
            play_voice(23, BGM_SPU_ADDR, s_bgm_rate, 0x2fff);
        }
        return;
    }
    if (id == SFX_POWERDOWN || id == SFX_CHIMES) {
        int rate = 0;
        const char *path = (id == SFX_POWERDOWN) ? "\\SND\\PWR.VAG" : "\\SND\\CHIME.VAG";
        if (!s_cd_ready)
            return;
        if (cd_stream_vag_to_spu(path, BGM_SPU_ADDR, &rate) > 0) {
            s_bgm_rate = rate;
            s_bgm_in_slot = -1;
            play_voice(22, BGM_SPU_ADDR, rate, 0x3fff);
        }
        return;
    }

    if (!s_bank[id].loaded)
        return;
    play_addr(s_bank[id].spu_addr, s_bank[id].sample_rate);
}

void audio_stop(SfxId id)
{
    if (id == s_bgm || id == BGM_MENU || id == BGM_FAN || id == SFX_MUSIC_BOX) {
        SpuSetKey(0, 1 << 23);
        s_bgm = SFX_NONE;
        s_bgm_loop_left = 0;
        s_bgm_uploading = 0;
    }
}

void audio_update(void)
{
    bgm_upload_tick();

    if (s_bgm_uploading)
        return;
    if (s_bgm != BGM_FAN && s_bgm != BGM_MENU)
        return;
    if (s_bgm_loop_left > 0) {
        s_bgm_loop_left--;
        return;
    }
    play_voice(23, BGM_SPU_ADDR, s_bgm_rate, s_bgm == BGM_FAN ? 0x28ff : 0x2fff);
    s_bgm_loop_left = FR_BGM_LOOP;
}
