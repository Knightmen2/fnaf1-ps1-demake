#ifndef FNAF_AI_H
#define FNAF_AI_H

#include "constants.h"

typedef struct {
    short step;
    short at_door;
    short seen;
    short attacking;
    short scream_frame;
    short wait_frames;
    short scream_delay;
    short active;
} Animatronic;

typedef struct {
    short stage;       /* 0..3 Pirate Cove */
    short run_timer;
    short attacking;
    short scream_frame;
    short running;     /* 1 = dashing down west hall */
    short active;
} FoxyAI;

typedef struct {
    short music_timer;
    short attacking;
    short scream_frame;
    short flicker;
} FreddyAI;

void ai_init(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy);
void ai_reset_night(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy);
void ai_update(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy,
               int door_l, int door_r, int power, int night, int mode,
               int cam_open, int cam_id, unsigned int *rng);

#endif
