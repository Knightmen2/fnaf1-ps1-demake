#ifndef FNAF_PAD_H
#define FNAF_PAD_H

/*
 * Abstract action masks for game_on_pad() — NOT Sony PAD_* bit values.
 * input.c translates psxpad.h active-low bits → these masks.
 */
#define ACT_LEFT    0x0001
#define ACT_RIGHT   0x0002
#define ACT_UP      0x0004
#define ACT_DOWN    0x0008
#define ACT_DOORL   0x0010
#define ACT_DOORM   0x0020
#define ACT_LIGHTL  0x0040
#define ACT_LIGHTR  0x0080
#define ACT_CAM     0x0100
#define ACT_OK      0x0200

#endif
