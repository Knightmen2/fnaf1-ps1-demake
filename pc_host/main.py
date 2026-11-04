#!/usr/bin/env python3
"""FNAF1 PS1 demake — PC host.

SPACE = flip tablet (reliable). Mouse look / doors / hold lights.
Hallway lights swap office_58/127/225/227 crushed textures (same as PS1 ISO).
"""
from __future__ import annotations

import os
import sys
import random
from pathlib import Path

import pygame

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CANDIDATES = [
    ROOT / "ps1_assets",
    ROOT.parent / "fnaf_ps1_ready" / "ps1_assets",
    Path(__file__).resolve().parent.parent / "fnaf_ps1_ready" / "ps1_assets",
]
ASSETS = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])
GFX, AUD, TIM = ASSETS / "graphics", ASSETS / "audio", ASSETS / "tim"

LW, LH = 320, 240
SCALE = 4
WW, WH = LW * SCALE, LH * SCALE
FPS = 60
SCROLL_MAX = 192

FR_HOUR = 1800
FR_BONNIE_WAKE = 2400
FR_CHICA_WAKE = 3000
FR_MONITOR_FLIP = 19
FR_LOSE_HOLD = 480
FR_WIN_HOLD = 780
FR_TRANSITION = 180
FR_POWER = {1: 240, 2: 180, 3: 102, 4: 84, 5: 60}

MON_X, MON_Y, MON_W, MON_H = 40, 200, 240, 36  # big hit zone

UI_BTNL = [(0, 36), (36, 36), (72, 36), (108, 36)]
UI_BTNR = [(144, 36), (180, 36), (216, 36), (216, 36)]

# office variants — match Python office_sp / PS1 OFF*
OFFICE_FILES = {
    "dark": ("office_39_L.png", "office_39_R.png"),
    "light_l": ("office_58_L.png", "office_58_R.png"),
    "light_r": ("office_127_L.png", "office_127_R.png"),
    "bonnie": ("office_225_L.png", "office_225_R.png"),
    "chica": ("office_227_L.png", "office_227_R.png"),
}


def load_img(path: Path):
    if not path.exists():
        s = pygame.Surface((256, 240), pygame.SRCALPHA)
        s.fill((30, 0, 30, 255))
        return s.convert_alpha()
    return pygame.image.load(str(path)).convert_alpha()


def load_wav(stem: str):
    for name in (f"{stem}_ps1.wav", f"{stem}.wav"):
        p = AUD / name
        if p.exists():
            try:
                return pygame.mixer.Sound(str(p))
            except pygame.error:
                pass
    return None


def blit_scaled(dst, src, x, y):
    r = pygame.transform.scale(src, (max(1, src.get_width() * SCALE), max(1, src.get_height() * SCALE)))
    dst.blit(r, (int(x * SCALE), int(y * SCALE)))


def sub(atlas, u, v, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.blit(atlas, (0, 0), (u, v, w, h))
    return s


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        self.screen = pygame.display.set_mode((WW, WH))
        pygame.display.set_caption("FNAF1 PS1 — SPACE=tablet | mouse look/doors/lights")
        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("courier new", 11 * SCALE, bold=True)

        self.ui = load_img(GFX / "ui_atlas.png")
        self.door_l_spr = load_img(GFX / "door_L.png")
        self.door_r_spr = load_img(GFX / "door_R.png")
        self.offices = {}
        for key, (fl, fr) in OFFICE_FILES.items():
            self.offices[key] = (load_img(GFX / fl), load_img(GFX / fr))
        self.office_l, self.office_r = self.offices["dark"]
        self.office_key = "dark"

        self.menu_img = load_img(TIM / "menu.png") if (TIM / "menu.png").exists() else self.office_l
        self.loading_img = load_img(TIM / "loading.png") if (TIM / "loading.png").exists() else self.office_r
        self.mon_open = load_img(GFX / "mon_open.png")
        if self.mon_open.get_width() < 10:
            self.mon_open = pygame.Surface((MON_W, 16), pygame.SRCALPHA)
            self.mon_open.fill((200, 200, 200, 230))
        self.cam_nav = load_img(GFX / "cam_nav.png") if (GFX / "cam_nav.png").exists() else None
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
            "menu": load_wav("darkness_music"),
            "scare": load_wav("windowscare"),
        }
        self.fan_ch = self.menu_ch = None

        self.mode = "menu"
        self.menu_sel = 0
        self.night = 1
        self.continue_night = 1
        self.show_ps1_info = False
        self.hour = 0
        self.power = 100
        self.usage = 1
        self.power_int = FR_POWER[1]
        self.scroll = 96
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.flip_t = self.static_t = 0
        self.hour_t = FR_HOUR
        self.power_t = self.power_int
        self.bonnie_wake = FR_BONNIE_WAKE
        self.chica_wake = FR_CHICA_WAKE
        self.bonnie_step = self.chica_step = 0
        self.bonnie_wait = self.chica_wait = 0
        self.bonnie_door = self.chica_door = False
        self.bonnie_seen = self.chica_seen = False
        self.lose_t = self.win_t = self.trans_t = 0
        self.noise_frame = 0
        self.rng = random.randint(1, 0x7FFFFFFF)
        self.vhs_surf = pygame.Surface((LW, LH), pygame.SRCALPHA)

    def play(self, k):
        s = self.sfx.get(k)
        if s:
            s.play()

    def recalc(self):
        u = 1 + int(self.door_l) + int(self.door_r) + int(self.light_l) + int(self.light_r) + int(self.cams_open)
        self.usage = min(5, u)
        self.power_int = FR_POWER.get(self.usage, 240)

    def sync_office(self):
        if self.light_l and self.bonnie_door:
            key = "bonnie"
        elif self.light_r and self.chica_door:
            key = "chica"
        elif self.light_l:
            key = "light_l"
        elif self.light_r:
            key = "light_r"
        else:
            key = "dark"
        if key != self.office_key:
            self.office_key = key
            self.office_l, self.office_r = self.offices[key]

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
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.scroll = 96
        self.bonnie_step = self.chica_step = 0
        self.bonnie_door = self.chica_door = False
        self.bonnie_seen = self.chica_seen = False
        self.bonnie_wake = FR_BONNIE_WAKE
        self.chica_wake = FR_CHICA_WAKE
        self.bonnie_wait = self.chica_wait = 0
        self.flip_t = self.static_t = 0
        self.recalc()
        self.power_t = self.power_int
        self.hour_t = FR_HOUR
        self.sync_office()

    def enter_game(self):
        self.mode = "game"
        if self.sfx["fan"]:
            self.fan_ch = self.sfx["fan"].play(loops=-1)

    def stop_fan(self):
        if self.fan_ch:
            self.fan_ch.stop()
            self.fan_ch = None

    def toggle_cams(self):
        """SPACE / tablet strip — always works."""
        if self.mode not in ("game", "cameras"):
            return
        self.cams_open = not self.cams_open
        self.mode = "cameras" if self.cams_open else "game"
        self.flip_t = FR_MONITOR_FLIP
        self.play("put")
        if self.cams_open:
            self.light_l = self.light_r = False
            self.static_t = 20
            self.sync_office()
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

        if self.mode == "game" and not self.cams_open:
            mx, _ = pygame.mouse.get_pos()
            if mx < WW * 0.2:
                self.scroll = max(0, self.scroll - 5)
            elif mx > WW * 0.8:
                self.scroll = min(SCROLL_MAX, self.scroll + 5)

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
                if self.door_l:
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
                if self.door_r:
                    self.chica_step = random.randint(1, 3)
                    self.chica_door = False
                    self.chica_wait = random.randint(840, 1320)
                else:
                    self.mode = "lose"
                    self.lose_t = FR_LOSE_HOLD
                    self.stop_fan()
                    self.play("scream")

        self.sync_office()

    def draw_vhs(self, target):
        self.vhs_surf.fill((0, 0, 0, 0))
        r = self.rng
        for y in range(self.noise_frame & 1, LH, 2):
            pygame.draw.line(self.vhs_surf, (0, 0, 0, 50), (0, y), (LW, y))
        for _ in range(70):
            r = (r * 1664525 + 1013904223) & 0xFFFFFFFF
            self.vhs_surf.set_at((r % LW, (r >> 8) % LH), (90, 90, 90, 50))
        target.blit(pygame.transform.scale(self.vhs_surf, (WW, WH)), (0, 0))

    def draw_text(self, text, x, y, color=(255, 255, 255)):
        self.screen.blit(self.font_sm.render(text, True, color), (x * SCALE, y * SCALE))

    def draw_tablet_strip(self):
        # opaque bright bar — impossible to miss
        bar = pygame.Surface((MON_W * SCALE, MON_H * SCALE))
        bar.fill((55, 55, 55))
        pygame.draw.rect(bar, (220, 220, 220), bar.get_rect(), 3 * SCALE)
        self.screen.blit(bar, (MON_X * SCALE, MON_Y * SCALE))
        mo = pygame.transform.scale(self.mon_open, (MON_W * SCALE, 16 * SCALE))
        self.screen.blit(mo, (MON_X * SCALE, (MON_Y + 4) * SCALE))
        label = "SPACE / CLICK = CLOSE CAMS" if self.cams_open else "SPACE / CLICK = OPEN TABLET"
        self.draw_text(label, MON_X + 18, MON_Y + 12, (255, 255, 100))

    def draw(self):
        s = self.screen
        s.fill((0, 0, 0))
        if self.mode == "menu":
            blit_scaled(s, self.menu_img, 32, 0)
            for i, o in enumerate(["New Game", "Continue", "Ps1Version"]):
                col = (255, 255, 0) if i == self.menu_sel else (220, 220, 220)
                self.draw_text(("> " if i == self.menu_sel else "  ") + o, 24, 140 + i * 16, col)
            if self.show_ps1_info:
                self.draw_text("Authentic PS1 demake assets", 24, 210, (180, 255, 180))
            self.draw_vhs(s)
        elif self.mode == "transition":
            blit_scaled(s, self.loading_img, 32, 0)
            self.draw_text(f"12 AM  Night {self.night}", 100, 110)
            self.draw_vhs(s)
        elif self.mode in ("game", "cameras"):
            if self.cams_open:
                blit_scaled(s, self.cams[self.cam % len(self.cams)], 32, 0)
                if self.static_t > 0:
                    ov = pygame.Surface((WW, WH), pygame.SRCALPHA)
                    ov.fill((40, 40, 40, 110))
                    s.blit(ov, (0, 0))
                if self.cam_nav:
                    blit_scaled(s, pygame.transform.scale(self.cam_nav, (96, 96)), 200, 110)
                for i in range(11):
                    lx = 40 + (i % 6) * 24
                    ly = 160 + (i // 6) * 16
                    v0 = 106 if i == self.cam else 90
                    blit_scaled(s, sub(self.ui, i * 22, v0, 21, 14), lx, ly)
                self.draw_text(f"CAM {self.cam + 1:02d}", 40, 10, (255, 40, 40))
            else:
                sc = self.scroll
                blit_scaled(s, self.office_l, 0 - sc, 0)
                blit_scaled(s, self.office_r, 256 - sc, 0)
                if self.door_l:
                    blit_scaled(s, self.door_l_spr, 16 - sc, 0)
                if self.door_r:
                    blit_scaled(s, self.door_r_spr, 430 - sc, 0)
                li = 3 if (self.door_l and self.light_l) else (1 if self.door_l else (2 if self.light_l else 0))
                ri = 2 if (self.door_r and self.light_r) else (1 if self.door_r else (2 if self.light_r else 0))
                bu, bv = UI_BTNL[li]
                blit_scaled(s, sub(self.ui, bu, bv, 18, 48), 10 - sc, 90)
                bu, bv = UI_BTNR[ri]
                blit_scaled(s, sub(self.ui, bu, bv, 18, 48), 488 - sc, 90)

            self.draw_tablet_strip()
            am = 12 if self.hour == 0 else self.hour
            self.draw_text(f"PWR {max(0, self.power)}%  {am} AM  N{self.night}  U{self.usage}", 8, 8)
            self.draw_text("[SPACE]=tablet  hold light buttons", 8, 20, (180, 180, 180))
            if self.flip_t > 0:
                h = min(LH, self.flip_t * 12)
                pygame.draw.rect(s, (8, 8, 8), (0, 0, WW, h * SCALE))
            self.draw_vhs(s)
        elif self.mode == "lose":
            s.fill((0, 0, 0))
            self.draw_text("GAME OVER", 110, 110, (200, 0, 0))
            self.draw_vhs(s)
        elif self.mode == "win":
            s.fill((0, 0, 0))
            self.draw_text("6 AM", 140, 110)
            self.draw_vhs(s)

    def on_click(self, pos):
        lx, ly = pos[0] // SCALE, pos[1] // SCALE
        if self.mode == "menu":
            for i in range(3):
                if 20 <= lx <= 180 and 140 + i * 16 <= ly <= 154 + i * 16:
                    self.menu_sel = i
                    self.play("blip")
                    if i == 0:
                        self.start_night(1)
                    elif i == 1:
                        self.start_night(self.continue_night)
                    else:
                        self.show_ps1_info = True
            return
        if self.mode not in ("game", "cameras"):
            return
        # tablet strip click
        if MON_X <= lx <= MON_X + MON_W and MON_Y <= ly <= MON_Y + MON_H:
            self.toggle_cams()
            return
        if self.cams_open:
            for i in range(11):
                bx = 40 + (i % 6) * 24
                by = 160 + (i // 6) * 16
                if bx <= lx <= bx + 21 and by <= ly <= by + 14:
                    self.cam = i
                    self.static_t = 12
                    self.play("blip")
            return
        ox = lx + self.scroll
        # door = upper panel, light TOGGLE on lower (also hold works)
        if 8 <= ox <= 30 and 88 <= ly <= 114:
            self.door_l = not self.door_l
            self.play("door")
            self.recalc()
            return
        if 8 <= ox <= 30 and 114 <= ly <= 140:
            self.light_l = not self.light_l
            if self.light_l:
                self.light_r = False
                if self.bonnie_door and not self.bonnie_seen:
                    self.bonnie_seen = True
                    self.play("scare")
            self.recalc()
            self.sync_office()
            return
        if 486 <= ox <= 508 and 88 <= ly <= 114:
            self.door_r = not self.door_r
            self.play("door")
            self.recalc()
            return
        if 486 <= ox <= 508 and 114 <= ly <= 140:
            self.light_r = not self.light_r
            if self.light_r:
                self.light_l = False
                if self.chica_door and not self.chica_seen:
                    self.chica_seen = True
                    self.play("scare")
            self.recalc()
            self.sync_office()
            return

    def update_light_hold(self):
        """Original hold: while mouse held on light half, keep light on."""
        if self.mode != "game" or self.cams_open:
            return
        if not pygame.mouse.get_pressed()[0]:
            return
        lx, ly = pygame.mouse.get_pos()[0] // SCALE, pygame.mouse.get_pos()[1] // SCALE
        ox = lx + self.scroll
        if 8 <= ox <= 30 and 114 <= ly <= 140:
            if not self.light_l:
                self.light_l = True
                self.light_r = False
                self.recalc()
                self.sync_office()
        elif 486 <= ox <= 508 and 114 <= ly <= 140:
            if not self.light_r:
                self.light_r = True
                self.light_l = False
                self.recalc()
                self.sync_office()

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
                    if e.key == pygame.K_SPACE:
                        self.toggle_cams()
                    if self.mode == "menu":
                        if e.key in (pygame.K_UP, pygame.K_w):
                            self.menu_sel = (self.menu_sel - 1) % 3
                            self.play("blip")
                        if e.key in (pygame.K_DOWN, pygame.K_s):
                            self.menu_sel = (self.menu_sel + 1) % 3
                            self.play("blip")
                        if e.key in (pygame.K_RETURN,):
                            self.play("blip")
                            if self.menu_sel == 0:
                                self.start_night(1)
                            elif self.menu_sel == 1:
                                self.start_night(self.continue_night)
                            else:
                                self.show_ps1_info = True
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.on_click(e.pos)

            self.update_light_hold()
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
