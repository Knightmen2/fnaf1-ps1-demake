#include "game.h"
#include "pad.h"
#include "audio.h"
#include "assets.h"

GameState g_game;

static short power_interval_for_usage(short usage)
{
    switch (usage) {
    case 1: return FR_POWER_U1;
    case 2: return FR_POWER_U2;
    case 3: return FR_POWER_U3;
    case 4: return FR_POWER_U4;
    default: return FR_POWER_U5;
    }
}

static void recalc_usage(void)
{
    short u = 1;
    if (g_game.office.door_l) u++;
    if (g_game.office.door_r) u++;
    if (g_game.office.light_l) u++;
    if (g_game.office.light_r) u++;
    if (g_game.cams.open) u++;
    if (u < USAGE_MIN) u = USAGE_MIN;
    if (u > USAGE_MAX) u = USAGE_MAX;
    g_game.usage = u;
}

void game_init(void)
{
    g_game.rng = 0xF1A5F001u ^ 0x1A2B3C4Du;
    g_game.night = 1;
    g_game.continue_night = 1;
    g_game.star_win = 0;
    g_game.menu_pose = 0;
    ai_init(&g_game.bonnie, &g_game.chica, &g_game.foxy, &g_game.freddy);
    game_reset_to_menu();
}

void game_reset_to_menu(void)
{
    /* BGM optional — never block reset if CD/SPU not ready */
    audio_stop(BGM_FAN);
    g_game.mode = MODE_MENU;
    g_game.hour = 0;
    g_game.power = POWER_MAX;
    g_game.usage = 1;
    g_game.power_timer = FR_POWER_U1;
    g_game.hour_timer = 0;
    g_game.bonnie_wake_timer = 0;
    g_game.chica_wake_timer = 0;
    g_game.foxy_wake_timer = 0;
    g_game.vent_frame = 0;
    g_game.menu_frame = 12;
    g_game.menu_sel = 0;
    g_game.menu_pose = 0;
    g_game.transition_timer = 0;
    g_game.lose_timer = 0;
    g_game.win_timer = 0;
    assets_load_menu(); /* once: menu + menu2 into VRAM L/R */
    audio_play(BGM_MENU);

    g_game.office.door_l = 0;
    g_game.office.door_r = 0;
    g_game.office.light_l = 0;
    g_game.office.light_r = 0;
    g_game.office.light_allowed = 1;
    g_game.office.scroll_x = OFFICE_SCROLL_MAX / 2;
    g_game.office.door_l_y = -240; /* fully up / open */
    g_game.office.door_r_y = -240;
    g_game.office.door_l_timer = 0;
    g_game.office.door_r_timer = 0;

    g_game.cams.cur = 0;
    g_game.cams.open = 0;
    g_game.cams.flip_timer = 0;
    g_game.cams.noise_frame = 0;
    g_game.cams.record_frame = 0;
    g_game.cams.someone_walking = 0;
    g_game.cams.static_timer = 0;

    ai_reset_night(&g_game.bonnie, &g_game.chica, &g_game.foxy, &g_game.freddy);
}

void game_start_night(void)
{
    audio_stop(BGM_MENU);
    g_game.mode = MODE_TRANSITION;
    g_game.transition_timer = FR_TRANSITION;
    g_game.lose_timer = 0;
    g_game.win_timer = 0;
}

static void enter_gameplay(void)
{
    g_game.mode = MODE_GAME;
    g_game.hour = 0;
    g_game.power = POWER_MAX;
    g_game.hour_timer = FR_HOUR;
    g_game.power_timer = power_interval_for_usage(g_game.usage);
    g_game.bonnie_wake_timer = FR_BONNIE_WAKE;
    g_game.chica_wake_timer = FR_CHICA_WAKE;
    g_game.foxy_wake_timer = FR_FOXY_WAKE;
    ai_reset_night(&g_game.bonnie, &g_game.chica, &g_game.foxy, &g_game.freddy);
    g_game.foxy.run_timer = 900;
    /* Restore office + preload cam BEFORE player can open tablet */
    assets_load_office(OFFICE_DARK);
    assets_preload_cameras();
    audio_stop(BGM_MENU);
    audio_enable_cd();
    audio_play(BGM_FAN);
}

static void toggle_door_l(void)
{
    if (!g_game.office.light_allowed) {
        audio_play(SFX_ERROR);
        return;
    }
    g_game.office.door_l ^= 1;
    g_game.office.door_l_timer = FR_DOOR_ANIM;
    audio_play(SFX_DOOR);
    recalc_usage();
}

static void toggle_door_r(void)
{
    if (!g_game.office.light_allowed) {
        audio_play(SFX_ERROR);
        return;
    }
    g_game.office.door_r ^= 1;
    g_game.office.door_r_timer = FR_DOOR_ANIM;
    audio_play(SFX_DOOR);
    recalc_usage();
}

static void tick_door_anim(void)
{
    /* door_y: -240 open (up), 0 closed (down). Animate over FR_DOOR_ANIM frames. */
    const short open_y = -240;
    const short shut_y = 0;
    short step = 240 / FR_DOOR_ANIM;
    if (step < 1) step = 1;

    if (g_game.office.door_l_timer > 0) {
        g_game.office.door_l_timer--;
        if (g_game.office.door_l) {
            if (g_game.office.door_l_y < shut_y) {
                g_game.office.door_l_y = (short)(g_game.office.door_l_y + step);
                if (g_game.office.door_l_y > shut_y)
                    g_game.office.door_l_y = shut_y;
            }
        } else {
            if (g_game.office.door_l_y > open_y) {
                g_game.office.door_l_y = (short)(g_game.office.door_l_y - step);
                if (g_game.office.door_l_y < open_y)
                    g_game.office.door_l_y = open_y;
            }
        }
    } else {
        g_game.office.door_l_y = g_game.office.door_l ? shut_y : open_y;
    }

    if (g_game.office.door_r_timer > 0) {
        g_game.office.door_r_timer--;
        if (g_game.office.door_r) {
            if (g_game.office.door_r_y < shut_y) {
                g_game.office.door_r_y = (short)(g_game.office.door_r_y + step);
                if (g_game.office.door_r_y > shut_y)
                    g_game.office.door_r_y = shut_y;
            }
        } else {
            if (g_game.office.door_r_y > open_y) {
                g_game.office.door_r_y = (short)(g_game.office.door_r_y - step);
                if (g_game.office.door_r_y < open_y)
                    g_game.office.door_r_y = open_y;
            }
        }
    } else {
        g_game.office.door_r_y = g_game.office.door_r ? shut_y : open_y;
    }
}

static void set_light_l(int on)
{
    if (!g_game.office.light_allowed)
        return;
    if (on && !g_game.office.light_l) {
        g_game.office.light_l = 1;
        if (g_game.bonnie.at_door && !g_game.bonnie.seen) {
            g_game.bonnie.seen = 1;
            audio_play(SFX_WINDOW_SCARE);
        }
    } else if (!on && g_game.office.light_l) {
        g_game.office.light_l = 0;
    }
    recalc_usage();
}

static void set_light_r(int on)
{
    if (!g_game.office.light_allowed)
        return;
    if (on && !g_game.office.light_r) {
        g_game.office.light_r = 1;
        if (g_game.chica.at_door && !g_game.chica.seen) {
            g_game.chica.seen = 1;
            audio_play(SFX_WINDOW_SCARE);
        }
    } else if (!on && g_game.office.light_r) {
        g_game.office.light_r = 0;
    }
    recalc_usage();
}

static void flip_monitor(void)
{
    if (g_game.hour >= 6 || g_game.power < 0)
        return;
    if (g_game.cams.flip_timer > 0)
        return;

    if (g_game.mode == MODE_GAME) {
        assets_load_camera(g_game.cams.cur); /* correct room TIM before show */
        set_light_l(0);
        set_light_r(0);
        g_game.cams.open = 1;
        g_game.mode = MODE_CAMERAS;
        g_game.cams.flip_timer = FR_MONITOR_FLIP;
        g_game.cams.static_timer = FR_STATIC_CLEAR;
        audio_play(SFX_PUT_DOWN);
        recalc_usage();
    } else if (g_game.mode == MODE_CAMERAS) {
        g_game.cams.open = 0;
        g_game.mode = MODE_GAME;
        g_game.cams.flip_timer = FR_MONITOR_FLIP;
        audio_play(SFX_PUT_DOWN);
        recalc_usage();
    }
}

void game_on_pad(unsigned short pressed, unsigned short held)
{
    if (g_game.mode == MODE_MENU) {
        if (pressed & ACT_UP) {
            if (g_game.menu_sel > 0) {
                g_game.menu_sel--;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_DOWN) {
            if (g_game.menu_sel < 1) {
                g_game.menu_sel++;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_OK) {
            audio_play(SFX_BLIP);
            if (g_game.menu_sel == 0) {
                /* New Game */
                g_game.night = 1;
            } else {
                /* Continue — unlocked night (RAM save; no memcard yet) */
                g_game.night = g_game.continue_night;
                if (g_game.night < 1)
                    g_game.night = 1;
                if (g_game.night > 5)
                    g_game.night = 5;
            }
            game_start_night();
        }
        return;
    }

    if (g_game.mode == MODE_GAME) {
        if (held & ACT_LEFT) {
            if (g_game.office.scroll_x > 0)
                g_game.office.scroll_x -= 4;
        }
        if (held & ACT_RIGHT) {
            if (g_game.office.scroll_x < OFFICE_SCROLL_MAX)
                g_game.office.scroll_x += 4;
        }
        if (pressed & ACT_DOORL)
            toggle_door_l();
        if (pressed & ACT_DOORM)
            toggle_door_r();
        set_light_l((held & ACT_LIGHTL) ? 1 : 0);
        set_light_r((held & ACT_LIGHTR) ? 1 : 0);
        if (pressed & ACT_CAM)
            flip_monitor();
        return;
    }

    if (g_game.mode == MODE_CAMERAS) {
        if (pressed & ACT_LEFT) {
            if (g_game.cams.cur > 0) {
                g_game.cams.cur--;
                assets_load_camera(g_game.cams.cur);
                g_game.cams.static_timer = FR_STATIC_CLEAR;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_RIGHT) {
            if (g_game.cams.cur < CAM_COUNT - 1) {
                g_game.cams.cur++;
                assets_load_camera(g_game.cams.cur);
                g_game.cams.static_timer = FR_STATIC_CLEAR;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_UP) {
            if (g_game.cams.cur >= 3) {
                g_game.cams.cur = (short)(g_game.cams.cur - 3);
                assets_load_camera(g_game.cams.cur);
                g_game.cams.static_timer = FR_STATIC_CLEAR;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_DOWN) {
            if (g_game.cams.cur + 3 < CAM_COUNT) {
                g_game.cams.cur = (short)(g_game.cams.cur + 3);
                assets_load_camera(g_game.cams.cur);
                g_game.cams.static_timer = FR_STATIC_CLEAR;
                audio_play(SFX_BLIP);
            }
        }
        if (pressed & ACT_CAM)
            flip_monitor();
        return;
    }

    if (g_game.mode == MODE_OUTPOWER) {
        if (held & ACT_LEFT) {
            if (g_game.office.scroll_x > 0)
                g_game.office.scroll_x -= 3;
        }
        if (held & ACT_RIGHT) {
            if (g_game.office.scroll_x < OFFICE_SCROLL_MAX)
                g_game.office.scroll_x += 3;
        }
    }
}

static void tick_screamers(void)
{
    /* Advance screamer atlas frames (~every 2 frames for speed) */
    static short sub;
    sub ^= 1;
    if (!sub)
        return;

    if (g_game.bonnie.attacking) {
        g_game.mode = MODE_GAME;
        g_game.office.light_allowed = 0;
        if (g_game.bonnie.scream_frame == 0)
            audio_play(SFX_SCREAM);
        g_game.bonnie.scream_frame++;
        if (g_game.bonnie.scream_frame >= 8) {
            g_game.mode = MODE_LOSE;
            g_game.lose_timer = FR_LOSE_HOLD;
            g_game.bonnie.attacking = 0;
            audio_play(SFX_STATIC);
        }
    }
    if (g_game.chica.attacking) {
        g_game.mode = MODE_GAME;
        g_game.office.light_allowed = 0;
        if (g_game.chica.scream_frame == 0)
            audio_play(SFX_SCREAM);
        g_game.chica.scream_frame++;
        if (g_game.chica.scream_frame >= 8) {
            g_game.mode = MODE_LOSE;
            g_game.lose_timer = FR_LOSE_HOLD;
            g_game.chica.attacking = 0;
            audio_play(SFX_STATIC);
        }
    }
    if (g_game.foxy.attacking) {
        /* Foxy atlas = 4 cells @128 (not a long screamer strip) */
        if (g_game.foxy.scream_frame == 0)
            audio_play(SFX_SCREAM);
        g_game.foxy.scream_frame++;
        if (g_game.foxy.scream_frame >= 4) {
            g_game.mode = MODE_LOSE;
            g_game.lose_timer = FR_LOSE_HOLD;
            g_game.foxy.attacking = 0;
            audio_play(SFX_STATIC);
        }
    }
    if (g_game.freddy.attacking) {
        /* Freddy scream cells first in atlas — 10 readable frames */
        if (g_game.freddy.scream_frame == 0)
            audio_play(SFX_SCREAM);
        g_game.freddy.scream_frame++;
        if (g_game.freddy.scream_frame >= 10) {
            g_game.mode = MODE_LOSE;
            g_game.lose_timer = FR_LOSE_HOLD;
            g_game.freddy.attacking = 0;
            audio_play(SFX_STATIC);
        }
    }
}

void game_update(void)
{
    /* Menu twitch: flip pose 0/1 only (VRAM already has both). NO LoadImage here. */
    if (g_game.mode == MODE_MENU) {
        g_game.cams.noise_frame = (short)((g_game.cams.noise_frame + 1) & 7);
        if (g_game.menu_frame > 0) {
            g_game.menu_frame--;
        } else {
            g_game.rng = g_game.rng * 1664525u + 1013904223u;
            g_game.menu_frame = (short)(8 + (g_game.rng % 12u));
            g_game.menu_pose ^= 1;
            g_game.freddy.flicker = (short)(g_game.rng & 3u);
        }
        return;
    }

    if (g_game.mode == MODE_TRANSITION) {
        /* Load loading card once on entry to transition, not every draw */
        if (g_game.transition_timer == FR_TRANSITION)
            assets_load_loading();
        if (g_game.transition_timer > 0)
            g_game.transition_timer--;
        else
            enter_gameplay();
        return;
    }

    if (g_game.mode == MODE_LOSE) {
        g_game.cams.noise_frame = (short)((g_game.cams.noise_frame + 1) & 7);
        if (g_game.lose_timer > 0)
            g_game.lose_timer--;
        else
            game_reset_to_menu();
        return;
    }

    if (g_game.mode == MODE_WIN) {
        if (g_game.win_timer > 0)
            g_game.win_timer--;
        else {
            g_game.star_win = 1;
            if (g_game.night < 5)
                g_game.continue_night = (short)(g_game.night + 1);
            else
                g_game.continue_night = 5;
            game_reset_to_menu();
        }
        return;
    }

    if (g_game.cams.flip_timer > 0)
        g_game.cams.flip_timer--;

    tick_door_anim();

    /* Vent fan animation */
    {
        static short vent_div;
        vent_div++;
        if (vent_div >= FR_VENT_TICK) {
            vent_div = 0;
            g_game.vent_frame = (short)((g_game.vent_frame + 1) % 3);
        }
    }

    if (g_game.mode == MODE_CAMERAS) {
        static short rec_div, noise_div;
        rec_div++;
        if (rec_div >= FR_RECORD_BLINK) {
            rec_div = 0;
            g_game.cams.record_frame ^= 1;
        }
        noise_div++;
        if (noise_div >= FR_NOISE_TICK) {
            noise_div = 0;
            g_game.cams.noise_frame = (short)((g_game.cams.noise_frame + 1) & 7);
        }
    }

    if (g_game.cams.static_timer > 0) {
        g_game.cams.static_timer--;
        if (g_game.cams.static_timer == 0)
            g_game.cams.someone_walking = 0;
    }

    /* Wake timers */
    if (g_game.mode == MODE_GAME || g_game.mode == MODE_CAMERAS) {
        if (g_game.bonnie_wake_timer > 0) {
            g_game.bonnie_wake_timer--;
            if (g_game.bonnie_wake_timer == 0) {
                g_game.bonnie.active = 1;
                g_game.bonnie.wait_frames = 1;
            }
        }
        if (g_game.chica_wake_timer > 0) {
            g_game.chica_wake_timer--;
            if (g_game.chica_wake_timer == 0) {
                g_game.chica.active = 1;
                g_game.chica.wait_frames = 1;
            }
        }
        if (g_game.foxy_wake_timer > 0) {
            g_game.foxy_wake_timer--;
            if (g_game.foxy_wake_timer == 0) {
                g_game.foxy.active = 1;
                g_game.foxy.run_timer = 600;
            }
        }

        /* Hour clock */
        if (g_game.hour_timer > 0)
            g_game.hour_timer--;
        else {
            g_game.hour++;
            g_game.hour_timer = FR_HOUR;
            if (g_game.hour >= 6) {
                g_game.mode = MODE_WIN;
                g_game.win_timer = FR_WIN_HOLD;
                audio_stop(BGM_FAN);
                audio_play(SFX_CHIMES);
                return;
            }
        }

        /* Power drain */
        if (g_game.power >= 0) {
            if (g_game.power_timer > 0)
                g_game.power_timer--;
            else {
                g_game.power--;
                g_game.power_timer = power_interval_for_usage(g_game.usage);
                if (g_game.power < 0) {
                    g_game.office.door_l = 0;
                    g_game.office.door_r = 0;
                    g_game.office.light_l = 0;
                    g_game.office.light_r = 0;
                    g_game.cams.open = 0;
                    g_game.mode = MODE_OUTPOWER;
                    g_game.freddy.music_timer = 0;
                    g_game.freddy.attacking = 0;
                    g_game.lose_timer = FR_POWEROUT_WAIT; /* reuse as music phase */
                    audio_stop(BGM_FAN);
                    audio_play(SFX_MUSIC_BOX);
                }
            }
        }

        ai_update(&g_game.bonnie, &g_game.chica, &g_game.foxy, &g_game.freddy,
                  g_game.office.door_l, g_game.office.door_r,
                  g_game.power, g_game.night, (int)g_game.mode,
                  g_game.cams.open, g_game.cams.cur, &g_game.rng);

        /* Mark static flash on AI step edges could be hooked here */
        tick_screamers();
    }

    if (g_game.mode == MODE_OUTPOWER) {
        ai_update(&g_game.bonnie, &g_game.chica, &g_game.foxy, &g_game.freddy,
                  0, 0, 0, g_game.night, MODE_OUTPOWER,
                  0, 0, &g_game.rng);
        if (!g_game.freddy.attacking) {
            if (g_game.lose_timer > 0)
                g_game.lose_timer--;
            else {
                /* After music box, short run then screamer */
                static short run_phase;
                if (!run_phase) {
                    run_phase = 1;
                    g_game.lose_timer = FR_FREDDY_RUN;
                } else {
                    run_phase = 0;
                    g_game.freddy.attacking = 1;
                    g_game.freddy.scream_frame = 0;
                }
            }
        }
        tick_screamers();
    }
}
