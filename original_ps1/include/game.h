#ifndef FNAF_GAME_H
#define FNAF_GAME_H

#include "constants.h"
#include "ai.h"

typedef struct {
    short door_l;
    short door_r;
    short light_l;
    short light_r;
    short light_allowed;
    short scroll_x;       /* 0 .. OFFICE_SCROLL_MAX */
    short door_l_y;       /* animated door position (pixels) */
    short door_r_y;
    short door_l_timer;
    short door_r_timer;
} OfficeState;

typedef struct {
    short cur;            /* 0..CAM_COUNT-1 */
    short open;           /* monitor raised */
    short flip_timer;
    short noise_frame;
    short record_frame;
    short someone_walking;
    short static_timer;
} CameraState;

typedef struct {
    GameMode mode;
    short night;
    short hour;           /* 0=12AM .. 6=6AM */
    short power;          /* 0..100, -1 = out */
    short usage;          /* 1..5 */
    short power_timer;
    short hour_timer;
    short bonnie_wake_timer;
    short chica_wake_timer;
    short foxy_wake_timer;
    short menu_sel;           /* 0 = New Game, 1 = Continue */
    short continue_night;     /* unlocked night for Continue (1..5) */
    short menu_pose;          /* Freddy lobby frame 0..3 */
    short vent_frame;
    short menu_frame;
    short star_win;
    short transition_timer;
    short lose_timer;
    short win_timer;
    unsigned int rng;
    OfficeState office;
    CameraState cams;
    Animatronic bonnie;
    Animatronic chica;
    FoxyAI foxy;
    FreddyAI freddy;
} GameState;

extern GameState g_game;

void game_init(void);
void game_reset_to_menu(void);
void game_start_night(void);
void game_update(void);
void game_on_pad(unsigned short pressed, unsigned short held);

#endif /* FNAF_GAME_H */
