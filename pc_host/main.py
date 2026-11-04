#!/usr/bin/env python3
"""FNAF1 PS1 demake — PC host.

Uses crushed PS1 assets (graphics/audio/fonts from ps1_assets).
Only difference vs PS1: window scale + original FNAF mouse controls + VHS overlay.
"""
from __future__ import annotations

import os
import sys
import random
from pathlib import Path

import pygame

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
# Prefer packaged ps1_assets next to EXE / script; fallback to workspace demake tree
CANDIDATES = [
    ROOT / "ps1_assets",
    ROOT.parent / "fnaf_ps1_ready" / "ps1_assets",
    Path(__file__).resolve().parent.parent / "fnaf_ps1_ready" / "ps1_assets",
]
ASSETS = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])
GFX, AUD, FNT, TIM = ASSETS / "graphics", ASSETS / "audio", ASSETS / "fonts", ASSETS / "tim"

# Logical PS1 framebuffer — only scale changes on PC
LW, LH = 320, 240
SCALE = 4
WW, WH = LW * SCALE, LH * SCALE
FPS = 60
OFFICE_W = 512
SCROLL_MAX = 192

# Timings from constants.h (NTSC)
FR_HOUR = 1800
FR_BONNIE_WAKE = 2400
FR_CHICA_WAKE = 3000
FR_DOOR_ANIM = 24
FR_MONITOR_FLIP = 19
FR_LOSE_HOLD = 480
FR_WIN_HOLD = 780
FR_TRANSITION = 180
FR_POWER = {1: 240, 2: 180, 3: 102, 4: 84, 5: 60}

# UI atlas UVs (atlas_uv.h)
UI = {
    "btnL": [(0, 36), (36, 36), (72, 36), (108, 36)],
    "btnR": [(144, 36), (180, 36), (216, 36), (216, 36)],
    "mon": (110, 16, 48, 5),
    "cambtn": (0, 90),
    "cambtn_on": (0, 106),
}


def load_img(path: Path):
    if not path.exists():
        s = pygame.Surface((64, 64))
        s.fill((40, 0, 40))
        return s.convert()
    return pygame.image.load(str(path)).convert_alpha()


def load_wav(stem: str):
    for name in (f"{stem}_ps1.wav", f"{stem}.wav", stem):
        p = AUD / name
        if p.exists():
            try:
                return pygame.mixer.Sound(str(p))
            except pygame.error:
                pass
    # fuzzy
    if AUD.exists():
        for f in AUD.iterdir():
            if f.suffix.lower() == ".wav" and stem.lower() in f.stem.lower():
                try:
                    return pygame.mixer.Sound(str(f))
                except pygame.error:
                    pass
    return None


def blit_scaled(dst, src, x, y):
    """Blit logical sprite onto scaled window."""
    if src.get_width() == 0:
        return
    r = pygame.transform.scale(src, (src.get_width() * SCALE, src.get_height() * SCALE))
    dst.blit(r, (x * SCALE, y * SCALE))


def sub(atlas, u, v, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.blit(atlas, (0, 0), (u, v, w, h))
    return s


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        self.screen = pygame.display.set_mode((WW, WH))
        pygame.display.set_caption("FNAF1 PS1 Demake — PC")
        self.clock = pygame.time.Clock()
        # pixel font from atlas if possible, else SysFont
        self.font_atlas = load_img(FNT / "font_atlas.png") if (FNT / "font_atlas.png").exists() else None
        self.font = pygame.font.SysFont("courier new", 14 * SCALE, bold=True)
        self.font_sm = pygame.font.SysFont("courier new", 10 * SCALE)

        self.ui = load_img(GFX / "ui_atlas.png")
        self.door_l = load_img(GFX / "door_L.png")
        self.door_r = load_img(GFX / "door_R.png")
        self.office_l = load_img(GFX / "office_39_L.png")
        self.office_r = load_img(GFX / "office_39_R.png")
        self.menu_img = load_img(TIM / "menu.png") if (TIM / "menu.png").exists() else self.office_l
        self.loading_img = load_img(TIM / "loading.png") if (TIM / "loading.png").exists() else self.office_r
        cams = [
            "cam_00_19.png", "cam_01_48.png", "cam_02_66.png", "cam_03_337.png",
            "cam_04_0.png", "cam_05_62.png", "cam_06_67.png", "cam_07_49.png",
            "cam_08_83.png", "cam_09_42.png", "cam_10_41.png",
        ]
        self.cams = [load_img(GFX / c) for c in cams]
        self.bonnie = load_img(GFX / "bonnie_atlas.png")
        self.chica = load_img(GFX / "chica_atlas.png")

        self.sfx = {
            "blip": load_wav("blip3"),
            "door": load_wav("doorclose"),
            "put": load_wav("put_down"),
            "fan": load_wav("buzz_fan_florescent2"),
            "scream": load_wav("xscream"),
            "static": load_wav("static"),
            "menu": load_wav("darkness_music"),
            "error": load_wav("error"),
        }
        self.fan_ch = None
        self.menu_ch = None

        self.mode = "menu"
        self.menu_sel = 0  # 0 New, 1 Continue, 2 Ps1Version
        self.night = 1
        self.continue_night = 1
        self.show_ps1_info = False
        self.hour = 0
        self.power = 100
        self.usage = 1
        self.power_int = FR_POWER[1]
        self.scroll = 96
        self.door_l_on = self.door_r_on = False
        self.light_l = self.light_r = False
        self.door_l_y = -240
        self.door_r_y = -240
        self.door_l_t = self.door_r_t = 0
        self.cams_open = False
        self.cam = 0
        self.flip_t = 0
        self.static_t = 0
        self.hour_t = FR_HOUR
        self.power_t = self.power_int
        self.bonnie_wake = FR_BONNIE_WAKE
        self.chica_wake = FR_CHICA_WAKE
        self.bonnie_step = self.chica_step = 0
        self.bonnie_wait = self.chica_wait = 0
        self.bonnie_door = self.chica_door = False
        self.lose_t = self.win_t = self.trans_t = 0
        self.noise_frame = 0
        self.rng = random.randint(1, 0x7FFFFFFF)
        self.vhs_surf = pygame.Surface((LW, LH), pygame.SRCALPHA)

    def play(self, k):
        s = self.sfx.get(k)
        if s:
            s.play()

    def recalc(self):
        u = 1 + int(self.door_l_on) + int(self.door_r_on) + int(self.light_l) + int(self.light_r) + int(self.cams_open)
        self.usage = min(5, u)
        self.power_int = FR_POWER.get(self.usage, 240)

    def start_night(self, n=None):
        if n is not None:
            self.night = n
        self.show_ps1_info = False
        if self.menu_ch:
            self.menu_ch.stop()
            self.menu_ch = None
        self.mode = "transition"
        self.trans_t = FR_TRANSITION
        self.hour = 0
        self.power = 100
        self.door_l_on = self.door_r_on = False
        self.light_l = self.light_r = False
        self.door_l_y = self.door_r_y = -240
        self.cams_open = False
        self.cam = 0
        self.scroll = 96
        self.bonnie_step = self.chica_step = 0
        self.bonnie_door = self.chica_door = False
        self.bonnie_wake = FR_BONNIE_WAKE
        self.chica_wake = FR_CHICA_WAKE
        self.bonnie_wait = self.chica_wait = 0
        self.flip_t = self.static_t = 0
        self.recalc()
        self.power_t = self.power_int
        self.hour_t = FR_HOUR

    def enter_game(self):
        self.mode = "game"
        if self.sfx["fan"]:
            self.fan_ch = self.sfx["fan"].play(loops=-1)

    def stop_fan(self):
        if self.fan_ch:
            self.fan_ch.stop()
            self.fan_ch = None

    def toggle_door(self, side):
        if side == "l":
            self.door_l_on = not self.door_l_on
            self.door_l_t = FR_DOOR_ANIM
            self.door_l_y = 0 if self.door_l_on else -240
        else:
            self.door_r_on = not self.door_r_on
            self.door_r_t = FR_DOOR_ANIM
            self.door_r_y = 0 if self.door_r_on else -240
        self.play("door")
        self.recalc()

    def toggle_cams(self):
        self.cams_open = not self.cams_open
        self.mode = "cameras" if self.cams_open else "game"
        self.flip_t = FR_MONITOR_FLIP
        if self.cams_open:
            self.light_l = self.light_r = False
            self.static_t = 20
            self.play("put")
        else:
            self.play("put")
        self.recalc()

    def update(self):
        self.noise_frame = (self.noise_frame + 1) & 255
        self.rng = (self.rng * 1664525 + 1013904223) & 0xFFFFFFFF

        if self.mode == "menu":
            if self.sfx["menu"] and not self.menu_ch:
                self.menu_ch = self.sfx["menu"].play(loops=-1)
            return
        if self.mode == "transition":
            self.trans_t -= 1
            if self.trans_t <= 0:
                self.enter_game()
            return
        if self.mode == "lose":
            self.lose_t -= 1
            if self.lose_t <= 0:
                self.stop_fan()
                self.mode = "menu"
            return
        if self.mode == "win":
            self.win_t -= 1
            if self.win_t <= 0:
                self.stop_fan()
                self.continue_night = min(5, self.night + 1)
                self.mode = "menu"
            return
        if self.mode not in ("game", "cameras"):
            return

        if self.flip_t > 0:
            self.flip_t -= 1
        if self.static_t > 0:
            self.static_t -= 1

        # mouse look (original FNAF)
        if self.mode == "game" and not self.cams_open:
            mx, _ = pygame.mouse.get_pos()
            if mx < WW * 0.25:
                self.scroll = max(0, self.scroll - 4)
            elif mx > WW * 0.75:
                self.scroll = min(SCROLL_MAX, self.scroll + 4)

        if self.bonnie_wake > 0:
            self.bonnie_wake -= 1
        if self.chica_wake > 0:
            self.chica_wake -= 1

        self.hour_t -= 1
        if self.hour_t <= 0:
            self.hour += 1
            self.hour_t = FR_HOUR
            if self.hour >= 6:
                self.stop_fan()
                self.mode = "win"
                self.win_t = FR_WIN_HOLD
                return

        self.power_t -= 1
        if self.power_t <= 0:
            self.power -= 1
            self.power_t = self.power_int
            if self.power < 0:
                self.stop_fan()
                self.mode = "lose"
                self.lose_t = FR_LOSE_HOLD
                self.play("scream")
                return

        # AI (same frame waits as demake N1)
        if self.bonnie_wake <= 0:
            if self.bonnie_wait > 0:
                self.bonnie_wait -= 1
            elif not self.bonnie_door:
                self.bonnie_step += 1
                self.bonnie_wait = random.randint(720, 1200)
                if self.bonnie_step >= 7:
                    self.bonnie_door = True
                    self.bonnie_wait = 240
            elif self.bonnie_wait <= 0:
                if self.door_l_on:
                    self.bonnie_step = random.randint(1, 3)
                    self.bonnie_door = False
                    self.bonnie_wait = random.randint(720, 1200)
                else:
                    self.mode = "lose"
                    self.lose_t = FR_LOSE_HOLD
                    self.stop_fan()
                    self.play("scream")

        if self.chica_wake <= 0:
            if self.chica_wait > 0:
                self.chica_wait -= 1
            elif not self.chica_door:
                self.chica_step += 1
                self.chica_wait = random.randint(840, 1320)
                if self.chica_step >= 9:
                    self.chica_door = True
                    self.chica_wait = 240
            elif self.chica_wait <= 0:
                if self.door_r_on:
                    self.chica_step = random.randint(1, 3)
                    self.chica_door = False
                    self.chica_wait = random.randint(840, 1320)
                else:
                    self.mode = "lose"
                    self.lose_t = FR_LOSE_HOLD
                    self.stop_fan()
                    self.play("scream")

    def draw_vhs(self, target):
        """Original-style VHS: scanlines + tracking noise + flicker (EXE/APK only)."""
        self.vhs_surf.fill((0, 0, 0, 0))
        r = self.rng
        # scanlines
        for y in range(self.noise_frame & 1, LH, 2):
            pygame.draw.line(self.vhs_surf, (0, 0, 0, 70), (0, y), (LW, y))
        # heavier bands every ~8px
        for y in range(self.noise_frame & 3, LH, 8):
            r = (r * 1664525 + 1013904223) & 0xFFFFFFFF
            if (r & 15) == 0:
                pygame.draw.line(self.vhs_surf, (255, 255, 255, 28), (0, y), (LW, y))
        # snow noise
        for _ in range(120):
            r = (r * 1664525 + 1013904223) & 0xFFFFFFFF
            x = r % LW
            y = (r >> 8) % LH
            v = 40 + (r & 63)
            a = 50 + (r & 63)
            self.vhs_surf.set_at((x, y), (v, v, v, a))
        # tracking tear
        tear_y = (self.noise_frame * 3) % LH
        pygame.draw.rect(self.vhs_surf, (255, 255, 255, 18), (0, tear_y, LW, 3))
        scaled = pygame.transform.scale(self.vhs_surf, (WW, WH))
        target.blit(scaled, (0, 0))

    def draw_text(self, text, x, y, color=(255, 255, 255)):
        self.screen.blit(self.font_sm.render(text, True, color), (x * SCALE, y * SCALE))

    def draw(self):
        s = self.screen
        s.fill((0, 0, 0))
        if self.mode == "menu":
            blit_scaled(s, self.menu_img, 32, 0)
            opts = ["New Game", "Continue", "Ps1Version"]
            for i, o in enumerate(opts):
                col = (255, 255, 0) if i == self.menu_sel else (220, 220, 220)
                pref = "> " if i == self.menu_sel else "  "
                self.draw_text(pref + o, 24, 140 + i * 16, col)
            if self.continue_night > 1:
                self.draw_text(f"Night {self.continue_night}", 40, 190, (160, 160, 160))
            if self.show_ps1_info:
                self.draw_text("Authentic PS1 demake assets", 24, 210, (180, 255, 180))
                self.draw_text("crushed TIM/VAG/font atlas", 24, 222, (180, 255, 180))
            self.draw_vhs(s)
        elif self.mode == "transition":
            blit_scaled(s, self.loading_img, 32, 0)
            self.draw_text(f"12 AM  Night {self.night}", 100, 110)
            self.draw_vhs(s)
        elif self.mode in ("game", "cameras"):
            if self.cams_open:
                cam = self.cams[self.cam % len(self.cams)]
                blit_scaled(s, cam, 32, 0)
                if self.static_t > 0:
                    overlay = pygame.Surface((WW, WH), pygame.SRCALPHA)
                    overlay.fill((40, 40, 40, 120))
                    s.blit(overlay, (0, 0))
                # cam buttons from UI atlas
                for i in range(11):
                    lx = 40 + (i % 6) * 24
                    ly = 170 + (i // 6) * 16
                    u0 = 0 + i * 22
                    v0 = 106 if i == self.cam else 90
                    btn = sub(self.ui, u0, v0, 21, 14)
                    blit_scaled(s, btn, lx, ly)
                self.draw_text(f"CAM {self.cam + 1:02d}", 40, 10, (255, 0, 0))
            else:
                sc = self.scroll
                blit_scaled(s, self.office_l, 0 - sc, 0)
                blit_scaled(s, self.office_r, 256 - sc, 0)
                # doors
                if self.door_l_on or self.door_l_y > -240:
                    blit_scaled(s, self.door_l, 16 - sc, 0 if self.door_l_on else self.door_l_y)
                if self.door_r_on or self.door_r_y > -240:
                    blit_scaled(s, self.door_r, 430 - sc, 0 if self.door_r_on else self.door_r_y)
                # door/light UI buttons from atlas (not grey tiles)
                li = 0
                if self.door_l_on and self.light_l:
                    li = 3
                elif self.door_l_on:
                    li = 1
                elif self.light_l:
                    li = 2
                ri = 0
                if self.door_r_on and self.light_r:
                    ri = 2
                elif self.door_r_on:
                    ri = 1
                elif self.light_r:
                    ri = 2
                bu, bv = UI["btnL"][li]
                blit_scaled(s, sub(self.ui, bu, bv, 18, 48), 10 - sc, 90)
                bu, bv = UI["btnR"][ri]
                blit_scaled(s, sub(self.ui, bu, bv, 18, 48), 488 - sc, 90)
                # hallway silhouettes when light + at door
                if self.light_l and self.bonnie_door:
                    fr = sub(self.bonnie, 0, 192, 64, 64)
                    blit_scaled(s, fr, 40 - sc, 80)
                if self.light_r and self.chica_door:
                    fr = sub(self.chica, 0, 192, 64, 64)
                    blit_scaled(s, fr, 420 - sc, 80)
            # tablet bar + mon icon
            bar = pygame.Surface((100 * SCALE, 14 * SCALE))
            bar.fill((20, 20, 20))
            s.blit(bar, (110 * SCALE, 220 * SCALE))
            blit_scaled(s, sub(self.ui, *UI["mon"]), 136, 222)
            am = 12 if self.hour == 0 else self.hour
            self.draw_text(f"PWR {max(0, self.power)}%  {am} AM  N{self.night}  U{self.usage}", 8, 8)
            # usage bar
            pygame.draw.rect(s, (16, 16, 16), (8 * SCALE, 228 * SCALE, 52 * SCALE, 6 * SCALE))
            pygame.draw.rect(
                s, (180, 180, 180),
                (9 * SCALE, 229 * SCALE, (10 + (self.usage - 1) * 8) * SCALE, 4 * SCALE),
            )
            if self.flip_t > 0:
                h = min(LH, (FR_MONITOR_FLIP - self.flip_t) * 12) if self.cams_open else min(LH, self.flip_t * 12)
                pygame.draw.rect(s, (10, 10, 10), (0, (LH - h) * SCALE if self.cams_open else 0, WW, h * SCALE))
            self.draw_vhs(s)
        elif self.mode == "lose":
            s.fill((0, 0, 0))
            self.draw_text("GAME OVER", 110, 110, (200, 0, 0))
            self.draw_vhs(s)
        elif self.mode == "win":
            s.fill((0, 0, 0))
            self.draw_text("6 AM", 140, 110)
            self.draw_vhs(s)

    def logical_pos(self, pos):
        return pos[0] // SCALE, pos[1] // SCALE

    def on_click(self, pos):
        lx, ly = self.logical_pos(pos)
        if self.mode == "menu":
            # clickable rows
            for i in range(3):
                if 20 <= lx <= 160 and 140 + i * 16 <= ly <= 154 + i * 16:
                    self.menu_sel = i
                    self.play("blip")
                    if i == 0:
                        self.start_night(1)
                    elif i == 1:
                        self.start_night(self.continue_night)
                    else:
                        self.show_ps1_info = True
                    return
            return
        if self.mode not in ("game", "cameras"):
            return
        # tablet
        if 110 <= lx <= 210 and 220 <= ly <= 234:
            self.toggle_cams()
            return
        if self.cams_open:
            for i in range(11):
                bx = 40 + (i % 6) * 24
                by = 170 + (i // 6) * 16
                if bx <= lx <= bx + 21 and by <= ly <= by + 14:
                    self.cam = i
                    self.static_t = 12
                    self.play("blip")
            return
        ox = lx + self.scroll
        # left door button
        if 10 <= ox <= 28 and 90 <= ly <= 138:
            self.toggle_door("l")
            return
        # left light — lower half of button panel
        if 10 <= ox <= 28 and 114 <= ly <= 138:
            self.light_l = not self.light_l
            if self.light_l:
                self.light_r = False
            self.recalc()
            return
        if 488 <= ox <= 506 and 90 <= ly <= 138:
            self.toggle_door("r")
            return
        if 488 <= ox <= 506 and 114 <= ly <= 138:
            self.light_r = not self.light_r
            if self.light_r:
                self.light_l = False
            self.recalc()
            return

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.mode in ("game", "cameras"):
                            self.stop_fan()
                            self.mode = "menu"
                        else:
                            pygame.quit()
                            return
                    if self.mode == "menu":
                        if e.key in (pygame.K_UP, pygame.K_w):
                            self.menu_sel = (self.menu_sel - 1) % 3
                            self.play("blip")
                        if e.key in (pygame.K_DOWN, pygame.K_s):
                            self.menu_sel = (self.menu_sel + 1) % 3
                            self.play("blip")
                        if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.play("blip")
                            if self.menu_sel == 0:
                                self.start_night(1)
                            elif self.menu_sel == 1:
                                self.start_night(self.continue_night)
                            else:
                                self.show_ps1_info = True
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.on_click(e.pos)

            # hold lights on button (original hold behaviour via mouse on panel)
            if self.mode == "game" and pygame.mouse.get_pressed()[0] and not self.cams_open:
                lx, ly = self.logical_pos(pygame.mouse.get_pos())
                ox = lx + self.scroll
                # light zone = lower part of door panels
                hl = 10 <= ox <= 28 and 114 <= ly <= 138
                hr = 488 <= ox <= 506 and 114 <= ly <= 138
                # only update lights when holding light zone (door clicks handled on down)
                if hl or hr:
                    self.light_l = hl
                    self.light_r = hr
                    self.recalc()
            elif self.mode == "game" and not self.cams_open:
                if self.light_l or self.light_r:
                    # release clears lights (original-style)
                    pass  # keep toggle model for panel; hold model above

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


def main():
    if getattr(sys, "frozen", False):
        os.chdir(Path(sys.executable).parent)
    Game().run()


if __name__ == "__main__":
    main()
