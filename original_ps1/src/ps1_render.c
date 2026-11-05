#include "ps1_render.h"
#include "constants.h"

void render_init(RenderCtx *ctx)
{
    /* Double buffer vertically stacked in VRAM: 0..239 and 240..479 */
    SetDefDispEnv(&ctx->db[0].disp, 0, 0, SCREEN_W, SCREEN_H);
    SetDefDrawEnv(&ctx->db[0].draw, 0, SCREEN_H, SCREEN_W, SCREEN_H);
    SetDefDispEnv(&ctx->db[1].disp, 0, SCREEN_H, SCREEN_W, SCREEN_H);
    SetDefDrawEnv(&ctx->db[1].draw, 0, 0, SCREEN_W, SCREEN_H);

    setRGB0(&ctx->db[0].draw, 0, 0, 0);
    setRGB0(&ctx->db[1].draw, 0, 0, 0);
    ctx->db[0].draw.isbg = 1;
    ctx->db[1].draw.isbg = 1;

    ctx->active = 0;
    ctx->nextpri = ctx->db[0].prim;
    ClearOTagR(ctx->db[0].ot, OT_LENGTH);
    ClearOTagR(ctx->db[1].ot, OT_LENGTH);

    PutDrawEnv(&ctx->db[0].draw);
    PutDispEnv(&ctx->db[0].disp);
    SetDispMask(1);
}

void render_begin(RenderCtx *ctx)
{
    ClearOTagR(ctx->db[ctx->active].ot, OT_LENGTH);
    ctx->nextpri = ctx->db[ctx->active].prim;
}

void render_end(RenderCtx *ctx)
{
    /* Never busy-wait DrawSync — VSync is enough for buffer flip */
    VSync(0);

    PutDispEnv(&ctx->db[ctx->active].disp);
    DrawOTagEnv(&ctx->db[ctx->active].ot[OT_LENGTH - 1], &ctx->db[ctx->active].draw);

    ctx->active ^= 1;
}

void *render_prim(RenderCtx *ctx, int z, unsigned size)
{
    uint8_t *p = ctx->nextpri;
    if (z < 0)
        z = 0;
    if (z >= OT_LENGTH)
        z = OT_LENGTH - 1;
    if ((ctx->nextpri + size) > &ctx->db[ctx->active].prim[PRIM_BUFFER_LEN])
        return ctx->db[ctx->active].prim; /* drop prim on overflow */
    addPrim(&ctx->db[ctx->active].ot[z], p);
    ctx->nextpri += size;
    return p;
}
