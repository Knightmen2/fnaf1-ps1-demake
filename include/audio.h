#ifndef FNAF_AUDIO_H
#define FNAF_AUDIO_H

typedef enum {
    SFX_NONE = 0,
    SFX_BLIP,
    SFX_DOOR,
    SFX_ERROR,
    SFX_WINDOW_SCARE,
    SFX_PUT_DOWN,
    SFX_POWERDOWN,
    SFX_SCREAM,
    SFX_STATIC,
    SFX_STEPS,
    SFX_NOSE,
    SFX_CHIMES,
    SFX_MUSIC_BOX,
    SFX_RUN,
    BGM_MENU,
    BGM_FAN,
    BGM_EERIE,
    SFX_COUNT
} SfxId;

void audio_init(void);
void audio_load_sfx_minimal(void); /* blip+door+error only — safe boot */
void audio_load_sfx(void);         /* full embedded bank */
void audio_load_sfx_step(void);    /* same as load_sfx; safe to call anytime */
void audio_enable_cd(void);        /* allow CD BGM/SFX after boot */
void audio_play(SfxId id);
void audio_stop(SfxId id);
void audio_update(void); /* tick streams / loops / deferred BGM DMA */

#endif
