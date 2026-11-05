#ifndef FNAF_PS1_RENDER_H
#define FNAF_PS1_RENDER_H

#include <stdint.h>
#include <psxgpu.h>

#define OT_LENGTH       16
#define PRIM_BUFFER_LEN 32768

typedef struct {
    DISPENV disp;
    DRAWENV draw;
    uint32_t ot[OT_LENGTH];
    uint8_t  prim[PRIM_BUFFER_LEN];
} DbBuffer;

typedef struct {
    DbBuffer db[2];
    int      active;
    uint8_t *nextpri;
} RenderCtx;

void render_init(RenderCtx *ctx);
void render_begin(RenderCtx *ctx);
void render_end(RenderCtx *ctx);
void *render_prim(RenderCtx *ctx, int z, unsigned size);

#endif
