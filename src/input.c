#include "input.h"
#include "pad.h"
#include "game.h"
#include <psxpad.h>
#include <psxapi.h>
#include <psxetc.h>
#include <string.h>

static uint8_t s_pad_buff[2][34];
static unsigned short s_prev;

void input_init_ps1(void)
{
    InitPAD(&s_pad_buff[0][0], 34, &s_pad_buff[1][0], 34);
    StartPAD();
    ChangeClearPAD(0);
    s_prev = 0;
    memset(s_pad_buff, 0xFF, sizeof(s_pad_buff));
}

unsigned short input_read_raw(void)
{
    PADTYPE *pad = (PADTYPE *)&s_pad_buff[0][0];
    if (pad->stat != 0)
        return 0xFFFF;
    return pad->btn;
}

/*
 * Every action has 2–3 pad buttons so DuckStation can bind many PC keys.
 * See KEYBOARD.txt for recommended keyboard → pad map.
 */
unsigned short input_map(unsigned short raw_btn_active_low)
{
    unsigned short m = 0;

    /* Look / menu / cams navigate */
    if (!(raw_btn_active_low & PAD_LEFT))     m |= ACT_LEFT;
    if (!(raw_btn_active_low & PAD_RIGHT))    m |= ACT_RIGHT;
    if (!(raw_btn_active_low & PAD_UP))       m |= ACT_UP;
    if (!(raw_btn_active_low & PAD_DOWN))     m |= ACT_DOWN;

    /* Doors — Square primary, L2 also door L, R2 also door R */
    if (!(raw_btn_active_low & PAD_SQUARE))   m |= ACT_DOORL;
    if (!(raw_btn_active_low & PAD_L2))       m |= ACT_DOORL;
    if (!(raw_btn_active_low & PAD_CIRCLE))   m |= ACT_DOORM;
    if (!(raw_btn_active_low & PAD_R2))       m |= ACT_DOORM;

    /* Lights — Cross/Triangle primary; also holdable aliases */
    if (!(raw_btn_active_low & PAD_CROSS))    m |= ACT_LIGHTL;
    if (!(raw_btn_active_low & PAD_TRIANGLE)) m |= ACT_LIGHTR;

    /* Camera tablet — L1, R1, Select, L3, R3 (many PC keys can bind) */
    if (!(raw_btn_active_low & PAD_L1))       m |= ACT_CAM;
    if (!(raw_btn_active_low & PAD_R1))       m |= ACT_CAM;
    if (!(raw_btn_active_low & PAD_SELECT))   m |= ACT_CAM;
    if (!(raw_btn_active_low & PAD_L3))       m |= ACT_CAM;
    if (!(raw_btn_active_low & PAD_R3))       m |= ACT_CAM;

    /* Confirm / New Game */
    if (!(raw_btn_active_low & PAD_START))    m |= ACT_OK;

    return m;
}

/* DuckStation: WASD → left stick, arrows → D-pad. Merge both. */
static unsigned short input_map_stick(void)
{
    PADTYPE *pad = (PADTYPE *)&s_pad_buff[0][0];
    unsigned short m = 0;
    const int dead = 40;

    if (pad->stat != 0)
        return 0;

    if (pad->type == PAD_ID_ANALOG || pad->type == PAD_ID_ANALOG_STICK || pad->len >= 3) {
        int lx = (int)pad->ls_x - 128;
        int ly = (int)pad->ls_y - 128;
        if (lx < -dead) m |= ACT_LEFT;
        if (lx >  dead) m |= ACT_RIGHT;
        if (ly < -dead) m |= ACT_UP;
        if (ly >  dead) m |= ACT_DOWN;
    }
    return m;
}

void input_poll(void)
{
    unsigned short raw = input_read_raw();
    unsigned short cur = (unsigned short)(input_map(raw) | input_map_stick());
    unsigned short pressed = (unsigned short)(cur & (unsigned short)~s_prev);
    s_prev = cur;
    game_on_pad(pressed, cur);
}
