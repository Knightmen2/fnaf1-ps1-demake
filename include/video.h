#ifndef FNAF_VIDEO_H
#define FNAF_VIDEO_H

#include "game.h"
#include "ps1_render.h"

void video_bind_render(RenderCtx *ctx);
void video_init(void);
void video_draw(const GameState *g);

#endif
