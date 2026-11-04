#include <stdio.h>
#include <psxgpu.h>
#include <psxapi.h>
#include <psxpad.h>
#include <psxetc.h>

#include "game.h"
#include "video.h"
#include "audio.h"
#include "input.h"
#include "ps1_render.h"
#include "assets.h"
#include "cd_assets.h"

static RenderCtx s_ctx;
static short s_fnt_mode = -1;
static short s_boot_audio_frames;

static void boot_msg(const char *line)
{
    int i;
    render_begin(&s_ctx);
    FntPrint(-1, "%s\n", line);
    FntFlush(-1);
    render_end(&s_ctx);
    for (i = 0; i < 2; i++)
        VSync(0);
}

static void fnt_for_mode(short mode)
{
    if (mode == s_fnt_mode)
        return;
    s_fnt_mode = mode;
    if (mode == MODE_MENU)
        FntOpen(16, 20, 148, 180, 0, 256);
    else
        FntOpen(4, 200, 312, 36, 0, 160);
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    ResetGraph(0);
    SetVideoMode(MODE_NTSC);
    FntLoad(960, 0);
    FntOpen(4, 200, 312, 36, 0, 160);

    render_init(&s_ctx);
    video_bind_render(&s_ctx);
    boot_msg("1 GPU OK");

    cd_assets_init();
    boot_msg(cd_assets_ready() ? "2 CD OK" : "2 CD FAIL");

    input_init_ps1();
    boot_msg("3 PAD OK");

    boot_msg("4 SPU SKIP");

    assets_init();
    boot_msg("5a OFF L");
    assets_boot_load_step(0);
    boot_msg("5b OFF R");
    assets_boot_load_step(1);
    boot_msg("5c UI");
    assets_boot_load_step(2);
    boot_msg("5d FONT");
    assets_boot_load_step(3);
    boot_msg("5e NO DOOR");
    assets_boot_load_step(4); /* doors skipped inside — known GPU wedge */
    boot_msg("5 TIM OK");

    audio_init();
    boot_msg("7 SPU");
    audio_load_sfx_minimal();
    boot_msg("7b SFX MIN");

    /* NO full SFX / NO menu TIM / NO BGM during boot — those caused 0 FPS */
    game_init();
    /* game_reset plays BGM via deferred chunked DMA — OK */
    boot_msg("8 READY");
    s_boot_audio_frames = 0;

    for (;;) {
        input_poll();
        game_update();
        audio_update(); /* also pumps deferred BGM DMA 4KB/frame */

        /* Finish SFX bank a few frames after READY — never in boot_msg chain */
        if (s_boot_audio_frames < 90) {
            s_boot_audio_frames++;
            if (s_boot_audio_frames == 30)
                audio_load_sfx();
        }

        render_begin(&s_ctx);
        video_draw(&g_game);

        fnt_for_mode((short)g_game.mode);
        if (g_game.mode == MODE_MENU) {
            FntPrint(-1, "Five\nNights\nat\nFreddy's\n\n");
            if (g_game.menu_sel == 0)
                FntPrint(-1, ">> New Game\n   Continue\n");
            else
                FntPrint(-1, "   New Game\n>> Continue\n");
            if (g_game.continue_night > 1)
                FntPrint(-1, "   Night %d\n", g_game.continue_night);
        } else if (g_game.mode == MODE_CAMERAS) {
            FntPrint(-1, "CAM%02d PWR%d%%  Q=close\n",
                     g_game.cams.cur + 1,
                     g_game.power < 0 ? 0 : g_game.power);
        } else if (g_game.mode == MODE_GAME) {
            FntPrint(-1, "PWR%d%% %dAM N%d U%d\n",
                     g_game.power < 0 ? 0 : g_game.power,
                     g_game.hour == 0 ? 12 : g_game.hour,
                     g_game.night,
                     g_game.usage);
        }

        FntFlush(-1);
        render_end(&s_ctx);
    }

    return 0;
}
