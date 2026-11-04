#include "video.h"
#include "assets.h"
#include "atlas_uv.h"
#include "ps1_render.h"
#include <psxgpu.h>
#include <stdio.h>

static RenderCtx *s_ctx;

void video_bind_render(RenderCtx *ctx)
{
    s_ctx = ctx;
}

void video_init(void)
{
}

static void draw_sprt_ex(TexId tex, short x, short y, short u, short v, short w, short h,
                         int z, int semi, uint8_t r, uint8_t g, uint8_t b)
{
    SPRT *s;
    DR_TPAGE *tp;
    TexSlot *t;

    if (!s_ctx || tex < 0 || tex >= TEX_COUNT)
        return;
    t = &g_tex[tex];
    if (!t->loaded)
        return;
    if (x >= SCREEN_W || y >= SCREEN_H || (x + w) <= 0 || (y + h) <= 0)
        return;

    s = (SPRT *)render_prim(s_ctx, z, sizeof(SPRT));
    setSprt(s);
    setXY0(s, x, y);
    setWH(s, w, h);
    setUV0(s, (uint8_t)u, (uint8_t)v);
    setClut(s, t->crect.x, t->crect.y);
    setRGB0(s, r, g, b);
    if (semi)
        setSemiTrans(s, 1);

    tp = (DR_TPAGE *)render_prim(s_ctx, z, sizeof(DR_TPAGE));
    /* Use cached tpage from upload — recalculating with wrong abr inverted colors */
    setDrawTPage(tp, 0, semi ? 1 : 0,
                 semi ? getTPage(t->mode, 1, t->prect.x, t->prect.y) : t->tpage);
}

static void draw_sprt(TexId tex, short x, short y, short u, short v, short w, short h, int z)
{
    draw_sprt_ex(tex, x, y, u, v, w, h, z, 0, 128, 128, 128);
}

static void draw_tile(short x, short y, short w, short h, uint8_t r, uint8_t g, uint8_t b, int z)
{
    TILE *t;
    if (!s_ctx)
        return;
    t = (TILE *)render_prim(s_ctx, z, sizeof(TILE));
    setTile(t);
    setXY0(t, x, y);
    setWH(t, w, h);
    setRGB0(t, r, g, b);
}

/* Cheap fan motion: 3 blades around desk fan spot in office space */
static void draw_fan(const GameState *g)
{
    short cx = (short)(220 - g->office.scroll_x);
    short cy = 120;
    short frame = g->vent_frame % 3;
    short dx, dy;
    /* Blade offsets cycle */
    if (frame == 0) { dx = 6; dy = 0; }
    else if (frame == 1) { dx = 3; dy = 5; }
    else { dx = -3; dy = 5; }
    draw_tile((short)(cx - 2), (short)(cy - 2), 5, 5, 40, 40, 40, 2);
    draw_tile((short)(cx + dx), (short)(cy + dy), 4, 2, 180, 180, 180, 1);
    draw_tile((short)(cx - dx), (short)(cy - dy), 4, 2, 160, 160, 160, 1);
}

static void draw_tablet_bar(void)
{
    /* Always-visible camera tablet cue at bottom */
    draw_tile(110, 220, 100, 14, 20, 20, 20, 1);
    if (g_tex[TEX_UI].loaded) {
        draw_sprt(TEX_UI, 136, 222, UI_MON_OPEN_U, UI_MON_OPEN_V,
                  UI_MON_OPEN_W, UI_MON_OPEN_H, 0);
    }
}

static void draw_office(const GameState *g)
{
    short scroll = g->office.scroll_x;
    short btn_l = UI_BTNL_0_U, btn_lv = UI_BTNL_0_V;
    short btn_r = UI_BTNR_0_U, btn_rv = UI_BTNR_0_V;

    /* Office TIM swap happens in game_update (assets_sync_office) — never LoadImage here */
    draw_sprt(TEX_OFFICE_L, (short)(0 - scroll), 0, 0, 0, 256, 240, 4);
    draw_sprt(TEX_OFFICE_R, (short)(256 - scroll), 0, 0, 0, 256, 240, 4);

    draw_fan(g);

    if (g->office.door_l_y > -240 && g_tex[TEX_DOOR_L].loaded)
        draw_sprt(TEX_DOOR_L, (short)(16 - scroll), g->office.door_l_y, 0, 0, 62, 240, 3);
    if (g->office.door_r_y > -240 && g_tex[TEX_DOOR_R].loaded)
        draw_sprt(TEX_DOOR_R, (short)(430 - scroll), g->office.door_r_y, 0, 0, 62, 240, 3);

    if (g->office.door_l && g->office.light_l) {
        btn_l = UI_BTNL_3_U; btn_lv = UI_BTNL_3_V;
    } else if (g->office.door_l) {
        btn_l = UI_BTNL_1_U; btn_lv = UI_BTNL_1_V;
    } else if (g->office.light_l) {
        btn_l = UI_BTNL_2_U; btn_lv = UI_BTNL_2_V;
    }
    if (g->office.door_r && g->office.light_r) {
        btn_r = UI_BTNR_2_U; btn_rv = UI_BTNR_2_V;
    } else if (g->office.door_r) {
        btn_r = UI_BTNR_1_U; btn_rv = UI_BTNR_1_V;
    } else if (g->office.light_r) {
        btn_r = UI_BTNR_2_U; btn_rv = UI_BTNR_2_V;
    }

    /* Door/light panels as plain tiles — UI atlas buttons were neon/wrong CLUT */
    {
        uint8_t bl = (uint8_t)(g->office.door_l || g->office.light_l ? 90 : 40);
        uint8_t br = (uint8_t)(g->office.door_r || g->office.light_r ? 90 : 40);
        draw_tile((short)(10 - scroll), 90, 14, 40, bl, bl, bl, 2);
        draw_tile((short)(488 - scroll), 90, 14, 40, br, br, br, 2);
        if (g->office.light_l)
            draw_tile((short)(12 - scroll), 94, 10, 8, 200, 200, 160, 1);
        if (g->office.light_r)
            draw_tile((short)(490 - scroll), 94, 10, 8, 200, 200, 160, 1);
    }
    (void)btn_l; (void)btn_lv; (void)btn_r; (void)btn_rv;

    draw_tablet_bar();

    if (g->cams.flip_timer > 0) {
        short h = (short)((FR_MONITOR_FLIP - g->cams.flip_timer) * 12);
        if (h > 240) h = 240;
        draw_tile(0, (short)(240 - h), SCREEN_W, h, 10, 10, 10, 0);
    }
}

static void draw_hud(const GameState *g)
{
    short uidx = (short)(g->usage - 1);
    if (uidx < 0) uidx = 0;
    if (uidx > 4) uidx = 4;

    /* Gray usage bars — no neon green tiles */
    draw_tile(8, 228, 52, 6, 16, 16, 16, 1);
    draw_tile(9, 229, (short)(10 + uidx * 8), 4, 180, 180, 180, 0);
}

static void draw_cam_anim_overlay(const GameState *g)
{
    short frame = -1;
    TexId tex = TEX_BONNIE;
    short cell = 64, cols = 4;
    short u, v;

    if (g->cams.cur == 0 && g->bonnie.step > 0 && !g->bonnie.at_door) {
        tex = TEX_BONNIE; frame = 8 + (g->bonnie.step % 4);
    } else if (g->cams.cur == 2 && g->foxy.active) {
        tex = TEX_FOXY; cell = 128; cols = 2;
        frame = g->foxy.stage;
        if (frame > 3) frame = 3;
        u = (short)((frame % cols) * cell);
        v = (short)((frame / cols) * cell);
        draw_sprt(tex, 96, 40, u, v, cell, cell, 2);
        return;
    } else if (g->cams.cur == 4 && g->bonnie.step >= 6) {
        tex = TEX_BONNIE; frame = 12;
    } else if (g->cams.cur == 7 && g->chica.step >= 8) {
        tex = TEX_CHICA; frame = 12;
    } else if (g->cams.cur == 1 && g->chica.step > 0) {
        tex = TEX_CHICA; frame = 8 + (g->chica.step % 4);
    } else {
        return;
    }

    u = (short)((frame % cols) * cell);
    v = (short)((frame / cols) * cell);
    draw_sprt(tex, 96, 40, u, v, cell, cell, 2);
}

static void draw_cameras(const GameState *g)
{
    short i;
    /* NO assets_load_* here — upload during night start only */
    if (g_tex[TEX_CAM].loaded)
        draw_sprt(TEX_CAM, 32, 0, 0, 0, 256, 240, 4);
    else
        draw_tile(32, 0, 256, 240, 16, 16, 16, 4);

    if (g->cams.someone_walking || g->cams.static_timer > 0)
        draw_tile(32, 0, 256, 240, 40, 40, 40, 3);

    draw_cam_anim_overlay(g);

    if (g_tex[TEX_UI].loaded) {
        draw_sprt(TEX_UI, 200, 160, UI_CAM_NAV_U, UI_CAM_NAV_V, UI_CAM_NAV_W, UI_CAM_NAV_H, 2);
        if (g->cams.record_frame)
            draw_sprt(TEX_UI, 40, 10, UI_RECORD_0_U, UI_RECORD_0_V, UI_RECORD_0_W, UI_RECORD_0_H, 1);
        for (i = 0; i < CAM_COUNT && i < 11; i++) {
            short x = (short)(40 + (i % 6) * 24);
            short y = (short)(170 + (i / 6) * 16);
            short ou = (short)(UI_CAMBTN_0_U + i * 22);
            short onu = (short)(UI_CAMBTN_ON_0_U + i * 22);
            if (i == g->cams.cur)
                draw_sprt(TEX_UI, x, y, onu, UI_CAMBTN_ON_0_V, 21, 14, 1);
            else
                draw_sprt(TEX_UI, x, y, ou, UI_CAMBTN_0_V, 21, 14, 1);
        }
    }

    if (g->cams.flip_timer > 0) {
        short h = (short)(g->cams.flip_timer * 12);
        if (h > 240) h = 240;
        draw_tile(0, 0, SCREEN_W, h, 10, 10, 10, 0);
    }
}

static void draw_screamer(const GameState *g)
{
    TexId tex = TEX_BONNIE;
    short frame = 0;
    short cell = 64;
    short cols = 4;
    short maxf = 7;
    short u, v;
    short ox;

    if (g->bonnie.attacking) {
        tex = TEX_BONNIE; frame = g->bonnie.scream_frame; maxf = 7;
        assets_load_anim_atlas(TEX_BONNIE);
    } else if (g->chica.attacking) {
        tex = TEX_CHICA; frame = g->chica.scream_frame; maxf = 7;
        assets_load_anim_atlas(TEX_CHICA);
    } else if (g->freddy.attacking) {
        tex = TEX_FREDDY; frame = g->freddy.scream_frame; maxf = 9;
        assets_load_anim_atlas(TEX_FREDDY);
    } else if (g->foxy.attacking) {
        tex = TEX_FOXY; frame = g->foxy.scream_frame;
        cell = 128; cols = 2; maxf = 3;
        assets_load_anim_atlas(TEX_FOXY);
    } else {
        return;
    }

    if (frame < 0)
        frame = 0;
    if (frame > maxf)
        frame = maxf;

    if (!g_tex[tex].loaded) {
        draw_tile(32, 0, 256, 240, 80, 0, 0, 2);
        return;
    }

    u = (short)((frame % cols) * cell);
    v = (short)((frame / cols) * cell);
    /* slight shake */
    ox = (short)((frame & 1) ? 2 : -2);
    draw_sprt(tex, (short)(32 + ox), 0, u, v, cell, cell, 2);
    draw_sprt(tex, (short)(32 + cell + ox), 0, u, v, cell, cell, 2);
    draw_sprt(tex, (short)(32 + ox), cell, u, v, cell, cell, 2);
    draw_sprt(tex, (short)(32 + cell + ox), cell, u, v, cell, cell, 2);
}

static void draw_vhs_overlay(const GameState *g)
{
    /* Light scanlines only — heavy snow looked like broken sprites */
    short y;
    unsigned int r = g->rng ^ ((unsigned int)g->cams.noise_frame << 8);

    for (y = (short)(g->cams.noise_frame & 3); y < SCREEN_H; y = (short)(y + 8)) {
        r = r * 1664525u + 1013904223u;
        if ((r & 15u) == 0)
            draw_tile(0, y, SCREEN_W, 1, 28, 28, 28, 1);
    }
}

static void draw_menu(const GameState *g)
{
    TexId tex = (g->menu_pose & 1) ? TEX_OFFICE_R : TEX_OFFICE_L;
    short ox = (short)((g->freddy.flicker & 1) ? 1 : 0);
    short oy = (short)((g->freddy.flicker & 2) ? 1 : 0);

    /* Never LoadImage in draw path */
    draw_tile(0, 0, SCREEN_W, SCREEN_H, 0, 0, 0, 5);
    if (g_tex[tex].loaded)
        draw_sprt(tex, (short)(32 + ox), oy, 0, 0, 256, 240, 4);
    else if (g_tex[TEX_OFFICE_L].loaded)
        draw_sprt(TEX_OFFICE_L, (short)(32 + ox), oy, 0, 0, 256, 240, 4);
    draw_vhs_overlay(g);
}

static void draw_loading(void)
{
    draw_tile(0, 0, SCREEN_W, SCREEN_H, 0, 0, 0, 5);
    if (g_tex[TEX_OFFICE_L].loaded)
        draw_sprt(TEX_OFFICE_L, 32, 0, 0, 0, 256, 240, 4);
}

void video_draw(const GameState *g)
{
    switch (g->mode) {
    case MODE_MENU:
        draw_menu(g);
        break;
    case MODE_TRANSITION:
        draw_loading();
        break;
    case MODE_GAME:
        if (g->bonnie.attacking || g->chica.attacking || g->foxy.attacking)
            draw_screamer(g);
        else
            draw_office(g);
        draw_hud(g);
        break;
    case MODE_CAMERAS:
        draw_cameras(g);
        draw_hud(g);
        break;
    case MODE_OUTPOWER:
        if (g->freddy.attacking)
            draw_screamer(g);
        else if (g->freddy.flicker)
            draw_office(g);
        else
            draw_tile(0, 0, SCREEN_W, SCREEN_H, 0, 0, 0, 4);
        break;
    case MODE_WIN:
        draw_tile(0, 0, SCREEN_W, SCREEN_H, 0, 0, 0, 4);
        break;
    case MODE_LOSE:
        draw_tile(0, 0, SCREEN_W, SCREEN_H, 20, 20, 20, 4);
        break;
    default:
        break;
    }
}
