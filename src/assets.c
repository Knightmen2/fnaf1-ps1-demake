#include "assets.h"
#include "cd_assets.h"
#include <string.h>
#include <stdint.h>

TexSlot g_tex[TEX_COUNT];

static short s_office = -1;
static short s_cam = -1;
static short s_atlases_loaded;

extern uint8_t tim_office_39_L[];
extern uint8_t tim_office_39_R[];
extern uint8_t tim_menu[];
extern uint8_t tim_menu2[];
extern uint8_t tim_menu3[];
extern uint8_t tim_menu4[];
extern uint8_t tim_loading[];
extern uint8_t tim_ui_atlas[];
extern uint8_t tim_font_atlas[];
extern uint8_t tim_door_L[];
extern uint8_t tim_door_R[];
extern uint8_t tim_bonnie_atlas[];
extern uint8_t tim_chica_atlas[];
extern uint8_t tim_freddy_atlas[];
extern uint8_t tim_foxy_atlas[];
extern uint8_t tim_cam_00[];

static short s_menu_pose = -1;

void assets_upload_tim(TexId id, uint32_t *tim, int vram_x, int vram_y, int clut_x, int clut_y)
{
    TIM_IMAGE img;
    RECT pr, cr;

    if (!tim || (((uintptr_t)tim) & 3u))
        return;
    if (GetTimInfo(tim, &img) != 0)
        return;
    if (!img.prect || !img.paddr)
        return;

    pr = *img.prect;
    /* 8-bit TIM: pr.w is in 16-bit VRAM words (= pixels/2). Cap generous. */
    if (pr.w <= 0 || pr.h <= 0 || pr.w > 256 || pr.h > 256)
        return;

    pr.x = (short)vram_x;
    pr.y = (short)vram_y;

    /* Fire-and-forget LoadImage — NO DrawSync wait (was 0 FPS wedge) */
    LoadImage(&pr, img.paddr);

    if ((img.mode & 0x8) && img.crect && img.caddr) {
        cr = *img.crect;
        if (cr.w > 0 && cr.h > 0 && cr.w <= 256 && cr.h <= 256) {
            cr.x = (short)clut_x;
            cr.y = (short)clut_y;
            LoadImage(&cr, img.caddr);
            g_tex[id].crect = cr;
            g_tex[id].clut = getClut(cr.x, cr.y);
        }
    }

    g_tex[id].prect = pr;
    g_tex[id].mode = (short)(img.mode & 3);
    g_tex[id].tpage = getTPage(g_tex[id].mode, 0, pr.x, pr.y);
    g_tex[id].loaded = 1;
}

/* CD TIM load with timed CdRead (see cd_assets.c) — OK outside draw path */
static int try_cd_tim(TexId id, const char *path, int vx, int vy, int cx, int cy)
{
    if (!cd_assets_ready())
        return 0;
    if (!cd_load_file(path))
        return 0;
    assets_upload_tim(id, (uint32_t *)cd_scratch(), vx, vy, cx, cy);
    return g_tex[id].loaded;
}

void assets_init(void)
{
    memset(g_tex, 0, sizeof(g_tex));
    s_office = -1;
    s_cam = -1;
    s_atlases_loaded = 0;
    s_menu_pose = -1;
}

void assets_boot_load_step(int step)
{
    switch (step) {
    case 0:
        assets_upload_tim(TEX_OFFICE_L, (uint32_t *)tim_office_39_L, 640, 0, 640, 248);
        break;
    case 1:
        assets_upload_tim(TEX_OFFICE_R, (uint32_t *)tim_office_39_R, 768, 0, 896, 248);
        break;
    case 2:
        assets_upload_tim(TEX_UI, (uint32_t *)tim_ui_atlas, 896, 256, 0, 490);
        break;
    case 3:
        assets_upload_tim(TEX_FONT, (uint32_t *)tim_font_atlas, 640, 400, 256, 490);
        break;
    case 4:
        /* DOORS INTENTIONALLY SKIPPED — LoadImage door TIM wedges GPU (0 FPS).
           Door panels drawn as tiles in video.c */
        s_office = OFFICE_DARK;
        break;
    default:
        break;
    }
}

void assets_boot_load(void)
{
    int i;
    for (i = 0; i <= 4; i++)
        assets_boot_load_step(i);
}

void assets_load_anim_atlases(void)
{
    /* DISABLED mass atlas upload — 4×256 TIM back-to-back = DuckStation hang.
       Screamers use flat color fallback until streamed one-per-frame later. */
    if (s_atlases_loaded)
        return;
    s_atlases_loaded = 1;
}

void assets_load_office(OfficeVariant v)
{
    /* lit hallway variants live on ISO (see iso.xml OFF58/127/225/227) */
    static const char *path_l[OFFICE_VARIANT_COUNT] = {
        0,
        "\\TIM\\OFF58L.TIM",
        "\\TIM\\OFF127L.TIM",
        "\\TIM\\OFF225L.TIM",
        "\\TIM\\OFF227L.TIM"
    };
    static const char *path_r[OFFICE_VARIANT_COUNT] = {
        0,
        "\\TIM\\OFF58R.TIM",
        "\\TIM\\OFF127R.TIM",
        "\\TIM\\OFF225R.TIM",
        "\\TIM\\OFF227R.TIM"
    };

    if (v < 0 || v >= OFFICE_VARIANT_COUNT)
        v = OFFICE_DARK;
    if ((short)v == s_office)
        return;
    s_menu_pose = -1;

    if (v == OFFICE_DARK) {
        assets_upload_tim(TEX_OFFICE_L, (uint32_t *)tim_office_39_L, 640, 0, 640, 248);
        assets_upload_tim(TEX_OFFICE_R, (uint32_t *)tim_office_39_R, 768, 0, 896, 248);
        s_office = OFFICE_DARK;
        return;
    }

    /* Load BOTH halves from CD (call only from game_update / light toggle — never draw) */
    if (try_cd_tim(TEX_OFFICE_L, path_l[v], 640, 0, 640, 248) &&
        try_cd_tim(TEX_OFFICE_R, path_r[v], 768, 0, 896, 248)) {
        s_office = (short)v;
        return;
    }

    /* CD miss → stay on dark embed so we never wedge */
    assets_upload_tim(TEX_OFFICE_L, (uint32_t *)tim_office_39_L, 640, 0, 640, 248);
    assets_upload_tim(TEX_OFFICE_R, (uint32_t *)tim_office_39_R, 768, 0, 896, 248);
    s_office = OFFICE_DARK;
}

void assets_load_menu(void)
{
    if (s_menu_pose >= 0 && g_tex[TEX_OFFICE_L].loaded && g_tex[TEX_OFFICE_R].loaded)
        return;
    assets_upload_tim(TEX_OFFICE_L, (uint32_t *)tim_menu, 640, 0, 640, 248);
    assets_upload_tim(TEX_OFFICE_R, (uint32_t *)tim_menu2, 768, 0, 896, 248);
    s_menu_pose = 0;
    s_office = -1;
}

void assets_load_menu_frame(int pose)
{
    (void)pose;
    assets_load_menu();
}

void assets_load_loading(void)
{
    if (s_menu_pose == -2 && g_tex[TEX_OFFICE_L].loaded)
        return;
    s_menu_pose = -2;
    assets_upload_tim(TEX_OFFICE_L, (uint32_t *)tim_loading, 640, 0, 640, 248);
    s_office = -1;
}

void assets_load_camera(int cam_id)
{
    static const char *cd_names[CAM_COUNT] = {
        "\\TIM\\CAM00.TIM", "\\TIM\\CAM01.TIM", "\\TIM\\CAM02.TIM",
        "\\TIM\\CAM03.TIM", "\\TIM\\CAM04.TIM", "\\TIM\\CAM05.TIM",
        "\\TIM\\CAM06.TIM", "\\TIM\\CAM07.TIM", "\\TIM\\CAM08.TIM",
        "\\TIM\\CAM09.TIM", "\\TIM\\CAM10.TIM"
    };

    if (cam_id < 0 || cam_id >= CAM_COUNT)
        cam_id = 0;
    if (cam_id == s_cam && g_tex[TEX_CAM].loaded)
        return;

    /* Unique room photo from ISO — only call from game_update / pad, never draw */
    if (try_cd_tim(TEX_CAM, cd_names[cam_id], 768, 256, 0, 502)) {
        s_cam = (short)cam_id;
        return;
    }

    /* Fallback embed (same image) if CD miss — still mark id to avoid spam */
    if (!g_tex[TEX_CAM].loaded)
        assets_upload_tim(TEX_CAM, (uint32_t *)tim_cam_00, 768, 256, 0, 502);
    s_cam = (short)cam_id;
}

/* Night start: cam0 embed ready; switching cams loads CAM01.. from CD */
void assets_preload_cameras(void)
{
    s_cam = -1;
    assets_load_camera(0);
}

void assets_load_anim_atlas(TexId id)
{
    (void)id;
    /* no-op — see assets_load_anim_atlases */
}
