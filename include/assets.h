#ifndef FNAF_ASSETS_H
#define FNAF_ASSETS_H

#include <stdint.h>
#include <psxgpu.h>
#include "constants.h"

/*
 * VRAM (1024x512):
 *   FB0 (0,0) 320x240 | FB1 (0,240) 320x240
 *   Free strip X>=320:
 *     BONNIE atlas (320,0)   256x256
 *     CHICA  atlas (576,0)   256x256
 *     CAM          (320,256) 256x240 + CLUT
 *     FOXY/FREDDY share CAM when screaming
 *     OFFICE_L (640,0) OFFICE_R (768,0)
 *     UI (896,256) FONT (640,400) DOORS (960/992,0)
 */

typedef enum {
    TEX_OFFICE_L = 0,
    TEX_OFFICE_R,
    TEX_CAM,
    TEX_UI,
    TEX_FONT,
    TEX_BONNIE,
    TEX_CHICA,
    TEX_FREDDY,
    TEX_FOXY,
    TEX_DOOR_L,
    TEX_DOOR_R,
    TEX_COUNT
} TexId;

typedef enum {
    OFFICE_DARK = 0,
    OFFICE_LIGHT_L,
    OFFICE_LIGHT_R,
    OFFICE_BONNIE,
    OFFICE_CHICA,
    OFFICE_VARIANT_COUNT
} OfficeVariant;

typedef struct {
    RECT prect;
    RECT crect;
    uint16_t tpage;
    uint16_t clut;
    short mode;
    short loaded;
} TexSlot;

extern TexSlot g_tex[TEX_COUNT];

void assets_init(void);
void assets_boot_load(void);          /* all minimal boot TIMs */
void assets_boot_load_step(int step); /* 0..4 one TIM each for diagnostics */
void assets_load_anim_atlases(void);  /* bonnie/chica/freddy/foxy/cam0 */
void assets_load_office(OfficeVariant v);
void assets_load_menu(void);          /* lobby 431+440 → OFFICE_L/R once */
void assets_load_menu_frame(int pose); /* alias → assets_load_menu() */
void assets_load_loading(void);       /* original 453_ loading card */
void assets_load_camera(int cam_id);
void assets_preload_cameras(void);    /* once at night start — safe cam open */
void assets_load_anim_atlas(TexId id);
void assets_upload_tim(TexId id, uint32_t *tim, int vram_x, int vram_y, int clut_x, int clut_y);

#endif
