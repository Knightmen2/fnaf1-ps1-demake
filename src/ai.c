#include "ai.h"
#include "audio.h"

static unsigned int ai_rand(unsigned int *rng)
{
    *rng = (*rng) * 1664525u + 1013904223u;
    return *rng;
}

static int ai_range(unsigned int *rng, int lo, int hi)
{
    unsigned int r;
    int span;
    if (hi <= lo)
        return lo;
    span = hi - lo + 1;
    r = ai_rand(rng);
    return lo + (int)(r % (unsigned int)span);
}

void ai_init(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy)
{
    ai_reset_night(bonnie, chica, foxy, freddy);
}

void ai_reset_night(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy)
{
    bonnie->step = 0;
    bonnie->at_door = 0;
    bonnie->seen = 0;
    bonnie->attacking = 0;
    bonnie->scream_frame = 0;
    bonnie->wait_frames = 0;
    bonnie->scream_delay = 0;
    bonnie->active = 0;

    chica->step = 0;
    chica->at_door = 0;
    chica->seen = 0;
    chica->attacking = 0;
    chica->scream_frame = 0;
    chica->wait_frames = 0;
    chica->scream_delay = 0;
    chica->active = 0;

    foxy->stage = 0;
    foxy->run_timer = 0;
    foxy->attacking = 0;
    foxy->scream_frame = 0;
    foxy->running = 0;
    foxy->active = 0;

    freddy->music_timer = 0;
    freddy->attacking = 0;
    freddy->scream_frame = 0;
    freddy->flicker = 0;
}

static int bonnie_wait(unsigned int *rng, int night)
{
    if (night <= 1)
        return ai_range(rng, FR_BON_WAIT_N1_MIN, FR_BON_WAIT_N1_MAX);
    return ai_range(rng, FR_BON_WAIT_N2_MIN, FR_BON_WAIT_N2_MAX);
}

static int chica_wait(unsigned int *rng, int night)
{
    if (night <= 1)
        return ai_range(rng, FR_CHI_WAIT_N1_MIN, FR_CHI_WAIT_N1_MAX);
    return ai_range(rng, FR_CHI_WAIT_N2_MIN, FR_CHI_WAIT_N2_MAX);
}

static void bonnie_tick(Animatronic *b, int door_l, int power, int night, unsigned int *rng)
{
    if (power <= 0 || b->attacking)
        return;

    if (b->scream_delay > 0) {
        b->scream_delay--;
        if (b->scream_delay == 0) {
            if (door_l) {
                b->step = (short)ai_range(rng, 1, 3);
                b->at_door = 0;
                b->seen = 0;
                b->wait_frames = (short)bonnie_wait(rng, night);
                audio_play(SFX_STEPS);
            } else {
                b->attacking = 1;
                b->scream_frame = 0;
            }
        }
        return;
    }

    if (!b->active)
        return;
    if (b->wait_frames > 0) {
        b->wait_frames--;
        return;
    }
    if (b->at_door)
        return;

    if (b->step < BONNIE_STEP_MAX) {
        b->step++;
        if (b->step > 0)
            audio_play(SFX_STEPS);
        if (b->step >= BONNIE_STEP_MAX) {
            b->at_door = 1;
            b->scream_delay = FR_WAIT_SCREAM;
        } else {
            b->wait_frames = (short)bonnie_wait(rng, night);
        }
    }
}

static void chica_tick(Animatronic *c, int door_r, int power, int night, unsigned int *rng)
{
    if (power <= 0 || c->attacking)
        return;

    if (c->scream_delay > 0) {
        c->scream_delay--;
        if (c->scream_delay == 0) {
            if (door_r) {
                c->step = (short)ai_range(rng, 1, 3);
                c->at_door = 0;
                c->seen = 0;
                c->wait_frames = (short)chica_wait(rng, night);
                audio_play(SFX_STEPS);
            } else {
                c->attacking = 1;
                c->scream_frame = 0;
            }
        }
        return;
    }

    if (!c->active)
        return;
    if (c->wait_frames > 0) {
        c->wait_frames--;
        return;
    }
    if (c->at_door)
        return;

    if (c->step < CHICA_STEP_MAX) {
        c->step++;
        if (c->step > 0)
            audio_play(SFX_STEPS);
        if (c->step >= CHICA_STEP_MAX) {
            c->at_door = 1;
            c->scream_delay = (short)ai_range(rng, 300, chica_wait(rng, night) + 120);
        } else {
            c->wait_frames = (short)chica_wait(rng, night);
        }
    }
}

/*
 * Foxy (Pirate Cove cam index 2):
 * stage 0 curtains closed → 1 peek → 2 out → 3 gone (running).
 * Watching cam 1C freezes him. At stage 3 he runs the west hall;
 * left door closed = reset to stage 1, else jumpscare.
 */
static void foxy_tick(FoxyAI *f, int door_l, int power, int cam_open, int cam_id,
                      int night, unsigned int *rng)
{
    int interval;
    if (power <= 0 || f->attacking || !f->active)
        return;

    if (f->running) {
        f->run_timer--;
        if (f->run_timer > 0)
            return;
        if (door_l) {
            f->stage = 1;
            f->running = 0;
            f->run_timer = (short)ai_range(rng, 600, 1000);
            audio_play(SFX_STEPS);
        } else {
            f->attacking = 1;
            f->scream_frame = 0;
            f->running = 0;
            audio_play(SFX_SCREAM);
        }
        return;
    }

    /* Looking at Pirate Cove holds him */
    if (cam_open && cam_id == 2) {
        return;
    }

    if (f->run_timer > 0) {
        f->run_timer--;
        return;
    }

    interval = (night <= 1) ? ai_range(rng, 900, 1500) : ai_range(rng, 450, 900);

    if (f->stage < FOXY_STAGE_MAX) {
        f->stage++;
        f->run_timer = (short)interval;
        if (f->stage >= FOXY_STAGE_MAX) {
            /* Leave cove — start hall run */
            f->running = 1;
            f->run_timer = (short)ai_range(rng, 90, 180); /* ~1.5-3s dash window */
            audio_play(SFX_RUN);
        }
    }
}

static void freddy_outpower_tick(FreddyAI *fr)
{
    if (fr->attacking)
        return;
    fr->flicker ^= 1;
    fr->music_timer++;
}

void ai_update(Animatronic *bonnie, Animatronic *chica, FoxyAI *foxy, FreddyAI *freddy,
               int door_l, int door_r, int power, int night, int mode,
               int cam_open, int cam_id, unsigned int *rng)
{
    if (mode == MODE_OUTPOWER) {
        freddy_outpower_tick(freddy);
        return;
    }

    if (mode != MODE_GAME && mode != MODE_CAMERAS)
        return;

    bonnie_tick(bonnie, door_l, power, night, rng);
    chica_tick(chica, door_r, power, night, rng);
    foxy_tick(foxy, door_l, power, cam_open, cam_id, night, rng);
    (void)freddy;
}
