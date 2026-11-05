#ifndef FNAF_CONSTANTS_H
#define FNAF_CONSTANTS_H

/* PS1 FNAF demake — integer-only constants (NTSC 60Hz) */

#define SCREEN_W            320
#define SCREEN_H            240
#define FPS_NTSC            60
#define FPS_PAL             50

#define VRAM_W              1024
#define VRAM_H              512
#define TPAGE_MAX           256

#define OFFICE_H            240
#define OFFICE_HALF_W       256
#define OFFICE_SCROLL_MAX   192   /* 512-320 visible pan range approx */

#define CAM_W               256
#define CAM_H               240
#define ATLAS_W             256
#define ATLAS_H             256

#define CAM_COUNT           11
#define POWER_MAX           100
#define USAGE_MIN           1
#define USAGE_MAX           5

#define BONNIE_STEP_MAX     7
#define CHICA_STEP_MAX      9
#define FOXY_STAGE_MAX      3

/* Frame timings (NTSC). Python hour=43s feels endless on PS1 demake —
   shortened so a night is ~3 min; AI wakes proportionally earlier. */
#define FR_HOUR             1800  /* 30s (py 43s) */
#define FR_BONNIE_WAKE      2400  /* 40s (py 86s) */
#define FR_CHICA_WAKE       3000  /* 50s (py 112s) */
#define FR_FOXY_WAKE        1800  /* 30s */
#define FR_STATIC_CLEAR     66    /* 1.1s */
#define FR_DOOR_ANIM        24    /* 0.4s */
#define FR_MONITOR_FLIP     19    /* 0.32s */
#define FR_WAIT_SCREAM      240   /* 4s */
#define FR_LOSE_HOLD        480   /* 8s */
#define FR_POWEROUT_WAIT    600   /* 10s */
#define FR_FREDDY_RUN       180   /* 3s */
#define FR_WIN_HOLD         780   /* 13s */
#define FR_TRANSITION       180   /* 3s */
#define FR_RECORD_BLINK     30    /* 0.5s */
#define FR_NOISE_TICK       4     /* ~0.07s */
#define FR_VENT_TICK        2     /* ~0.03s */

/* Power drain — match fnaf1.py powerspeed (4 / 3 / 1.7 / 1.4 / 1 sec) */
#define FR_POWER_U1         240   /* 4s per 1% */
#define FR_POWER_U2         180   /* 3s */
#define FR_POWER_U3         102   /* ~1.7s */
#define FR_POWER_U4         84    /* ~1.4s */
#define FR_POWER_U5         60    /* 1s */

/* AI wait ranges (frames) night 1 */
#define FR_BON_WAIT_N1_MIN  720
#define FR_BON_WAIT_N1_MAX  1200
#define FR_CHI_WAIT_N1_MIN  840
#define FR_CHI_WAIT_N1_MAX  1320

/* AI wait ranges night 2+ */
#define FR_BON_WAIT_N2_MIN  300
#define FR_BON_WAIT_N2_MAX  600
#define FR_CHI_WAIT_N2_MIN  360
#define FR_CHI_WAIT_N2_MAX  720

typedef enum {
    MODE_MENU = 0,
    MODE_TRANSITION,
    MODE_GAME,
    MODE_CAMERAS,
    MODE_OUTPOWER,
    MODE_WIN,
    MODE_LOSE
} GameMode;

typedef enum {
    ANIM_BONNIE = 0,
    ANIM_CHICA,
    ANIM_FREDDY,
    ANIM_FOXY,
    ANIM_COUNT
} AnimId;

#endif /* FNAF_CONSTANTS_H */
