#!/usr/bin/env python3
"""FNAF1 demake PC host — original mouse controls, no PS1 hardware limits."""
from __future__ import annotations

import os
import sys
import random
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent

# Prefer assets next to EXE / script, then workspace media pack
CANDIDATE_IMG = [
    ROOT / "images",
    ROOT / "fnaf_files_for_py" / "images",
    ROOT.parent / "fnaf_files_for_py" / "images",
]
CANDIDATE_MUSIC = [
    ROOT / "music",
    ROOT / "fnaf_files_for_py" / "music",
    ROOT.parent / "fnaf_files_for_py" / "music",
]


def first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return paths[0]


IMG = first_existing(CANDIDATE_IMG)
MUSIC = first_existing(CANDIDATE_MUSIC)

W, H = 1280, 720
FPS = 60
OFFICE_W = 1600


def load_img(name: str, size=None):
    p = IMG / name
    if not p.exists():
        surf = pygame.Surface(size or (256, 240))
        surf.fill((20, 20, 20))
        return surf.convert()
    im = pygame.image.load(str(p)).convert_alpha()
    if size:
        im = pygame.transform.smoothscale(im, size)
    return im


def load_sound(name: str):
    stems = [
        name,
        name.lower(),
        name.replace(" ", "_"),
        name.replace("_", " "),
    ]
    for base in (MUSIC, ROOT / "music"):
        if not base.exists():
            continue
        for stem in stems:
            for ext in (".wav", ".ogg", ".mp3", ""):
                c = base / f"{stem}{ext}" if ext else base / stem
                if c.exists() and c.is_file():
                    try:
                        return pygame.mixer.Sound(str(c))
                    except pygame.error:
                        pass
        # fuzzy search
        try:
            for f in base.iterdir():
                if f.is_file() and stem.lower() in f.stem.lower():
                    try:
                        return pygame.mixer.Sound(str(f))
                    except pygame.error:
                        pass
        except OSError:
            pass
    return None


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("FNAF1 PS1 Demake — PC (mouse)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 28)
        self.big = pygame.font.SysFont("consolas", 48, bold=True)

        self.mode = "menu"
        self.night = 1
        self.continue_night = 1
        self.menu_sel = 0
        self.hour = 0
        self.power = 100
        self.usage = 1
        self.power_interval = 4 * FPS
        self.scroll = 0
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.hour_t = 30 * FPS
        self.power_t = 4 * FPS
        self.bonnie_wake = 40 * FPS
        self.chica_wake = 50 * FPS
        self.bonnie_step = 0
        self.chica_step = 0
        self.bonnie_wait = 0
        self.chica_wait = 0
        self.bonnie_door = False
        self.chica_door = False
        self.lose_t = 0
        self.win_t = 0
        self.trans_t = 0

        # Full-res assets (no 256 TPage / VRAM limit)
        self.menu_bg = load_img("431.png", (W, H))
        self.loading = load_img("453_.png", (W, H))
        self.office = load_img("39.png", (OFFICE_W, H))
        if self.office.get_width() < 100:
            self.office = pygame.Surface((OFFICE_W, H))
            self.office.fill((30, 25, 20))
        cam_files = [
            "19.png", "48.png", "66.png", "337.png", "0.png", "62.png",
            "67.png", "49.png", "83.png", "42.png", "41.png",
        ]
        self.cam_imgs = [load_img(f, (W, H)) for f in cam_files]

        self.sfx = {
            "blip": load_sound("blip3"),
            "door": load_sound("DoorClose") or load_sound("doorclose"),
            "error": load_sound("error"),
            "put": load_sound("put_down"),
            "fan": load_sound("buzz_fan_florescent2"),
            "scream": load_sound("XSCREAM") or load_sound("xscream"),
        }
        self.fan_ch = None

    def play(self, key):
        s = self.sfx.get(key)
        if s:
            s.play()

    def recalc_usage(self):
        u = 1
        if self.door_l:
            u += 1
        if self.door_r:
            u += 1
        if self.light_l:
            u += 1
        if self.light_r:
            u += 1
        if self.cams_open:
            u += 1
        self.usage = min(5, u)
        speeds = {1: 4.0, 2: 3.0, 3: 1.7, 4: 1.4, 5: 1.0}
        self.power_interval = max(1, int(speeds.get(self.usage, 4.0) * FPS))

    def start_night(self):
        self.mode = "transition"
        self.trans_t = 3 * FPS
        self.hour = 0
        self.power = 100
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.scroll = OFFICE_W // 2 - W // 2
        self.bonnie_step = self.chica_step = 0
        self.bonnie_door = self.chica_door = False
        self.bonnie_wake = 40 * FPS
        self.chica_wake = 50 * FPS
        self.bonnie_wait = self.chica_wait = 0
        self.recalc_usage()
        self.power_t = self.power_interval
        self.hour_t = 30 * FPS

    def enter_game(self):
        self.mode = "game"
        if self.sfx["fan"]:
            self.fan_ch = self.sfx["fan"].play(loops=-1)

    def stop_fan(self):
        if self.fan_ch:
            self.fan_ch.stop()
            self.fan_ch = None

    def update(self):
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

        if self.mode == "game" and not self.cams_open:
            mx, _ = pygame.mouse.get_pos()
            if mx < W * 0.25:
                self.scroll = max(0, self.scroll - 8)
            elif mx > W * 0.75:
                self.scroll = min(OFFICE_W - W, self.scroll + 8)

        if self.bonnie_wake > 0:
            self.bonnie_wake -= 1
        if self.chica_wake > 0:
            self.chica_wake -= 1

        self.hour_t -= 1
        if self.hour_t <= 0:
            self.hour += 1
            self.hour_t = 30 * FPS
            if self.hour >= 6:
                self.stop_fan()
                self.mode = "win"
                self.win_t = 8 * FPS
                return

        self.power_t -= 1
        if self.power_t <= 0:
            self.power -= 1
            self.power_t = self.power_interval
            if self.power < 0:
                self.stop_fan()
                self.mode = "lose"
                self.lose_t = 5 * FPS
                self.play("scream")
                return

        if self.bonnie_wake <= 0:
            if self.bonnie_wait > 0:
                self.bonnie_wait -= 1
            elif not self.bonnie_door:
                self.bonnie_step += 1
                self.bonnie_wait = random.randint(12 * FPS, 20 * FPS)
                if self.bonnie_step >= 7:
                    self.bonnie_door = True
                    self.bonnie_wait = 4 * FPS
            else:
                if self.bonnie_wait <= 0:
                    if self.door_l:
                        self.bonnie_step = random.randint(1, 3)
                        self.bonnie_door = False
                        self.bonnie_wait = random.randint(12 * FPS, 20 * FPS)
                    else:
                        self.mode = "lose"
                        self.lose_t = 5 * FPS
                        self.stop_fan()
                        self.play("scream")

        if self.chica_wake <= 0:
            if self.chica_wait > 0:
                self.chica_wait -= 1
            elif not self.chica_door:
                self.chica_step += 1
                self.chica_wait = random.randint(14 * FPS, 22 * FPS)
                if self.chica_step >= 9:
                    self.chica_door = True
                    self.chica_wait = 4 * FPS
            else:
                if self.chica_wait <= 0:
                    if self.door_r:
                        self.chica_step = random.randint(1, 3)
                        self.chica_door = False
                        self.chica_wait = random.randint(14 * FPS, 22 * FPS)
                    else:
                        self.mode = "lose"
                        self.lose_t = 5 * FPS
                        self.stop_fan()
                        self.play("scream")

    def draw(self):
        s = self.screen
        if self.mode == "menu":
            s.blit(self.menu_bg, (0, 0))
            y = 40
            for t in ("Five", "Nights", "at", "Freddy's"):
                s.blit(self.big.render(t, True, (255, 255, 255)), (40, y))
                y += 52
            opts = ["New Game", "Continue"]
            for i, o in enumerate(opts):
                pref = ">> " if i == self.menu_sel else "   "
                col = (255, 255, 0) if i == self.menu_sel else (220, 220, 220)
                s.blit(self.font.render(pref + o, True, col), (40, 280 + i * 40))
            if self.continue_night > 1:
                s.blit(
                    self.font.render(f"   Night {self.continue_night}", True, (180, 180, 180)),
                    (40, 360),
                )
            tip = "Mouse look | Click doors/lights | Bottom bar = cameras | Esc = menu"
            s.blit(self.font.render(tip, True, (160, 160, 160)), (40, H - 40))
        elif self.mode == "transition":
            s.blit(self.loading, (0, 0))
            s.blit(self.big.render(f"Night {self.night}", True, (255, 255, 255)), (W // 2 - 100, H // 2))
        elif self.mode in ("game", "cameras"):
            if self.cams_open:
                s.blit(self.cam_imgs[self.cam % len(self.cam_imgs)], (0, 0))
                s.blit(self.font.render(f"CAM {self.cam + 1:02d}", True, (255, 0, 0)), (40, 20))
                for i in range(11):
                    r = pygame.Rect(40 + (i % 6) * 70, H - 120 + (i // 6) * 40, 60, 32)
                    pygame.draw.rect(s, (200, 40, 40) if i == self.cam else (80, 80, 80), r)
                    s.blit(self.font.render(str(i + 1), True, (255, 255, 255)), (r.x + 18, r.y + 4))
            else:
                s.blit(self.office, (-self.scroll, 0))
                # door / light visual markers
                pygame.draw.rect(s, (100, 100, 100), (20 - self.scroll, 280, 50, 80), 2)
                pygame.draw.rect(s, (180, 180, 40), (20 - self.scroll, 380, 50, 70), 2)
                pygame.draw.rect(s, (100, 100, 100), (OFFICE_W - 70 - self.scroll, 280, 50, 80), 2)
                pygame.draw.rect(s, (180, 180, 40), (OFFICE_W - 70 - self.scroll, 380, 50, 70), 2)
                if self.door_l:
                    pygame.draw.rect(s, (40, 40, 40), (0 - self.scroll, 0, 80, H))
                if self.door_r:
                    pygame.draw.rect(s, (40, 40, 40), (OFFICE_W - 80 - self.scroll, 0, 80, H))
                if self.light_l and self.bonnie_door:
                    pygame.draw.circle(s, (80, 40, 120), (120 - self.scroll, H // 2), 40)
                if self.light_r and self.chica_door:
                    pygame.draw.circle(s, (200, 180, 40), (OFFICE_W - 120 - self.scroll, H // 2), 40)
            pygame.draw.rect(s, (30, 30, 30), (W // 2 - 80, H - 36, 160, 28))
            s.blit(self.font.render("CAMERAS", True, (200, 200, 200)), (W // 2 - 55, H - 32))
            am = 12 if self.hour == 0 else self.hour
            hud = f"PWR {max(0, self.power)}%   {am} AM   N{self.night}   U{self.usage}"
            s.blit(self.font.render(hud, True, (255, 255, 255)), (20, H - 70))
        elif self.mode == "lose":
            s.fill((0, 0, 0))
            s.blit(self.big.render("GAME OVER", True, (200, 0, 0)), (W // 2 - 140, H // 2))
        elif self.mode == "win":
            s.fill((0, 0, 0))
            s.blit(self.big.render("6 AM", True, (255, 255, 255)), (W // 2 - 60, H // 2))

    def on_click(self, pos, button):
        if button != 1:
            return
        x, y = pos
        if self.mode == "menu":
            if 40 <= x <= 400 and 280 <= y <= 320:
                self.menu_sel = 0
                self.night = 1
                self.play("blip")
                self.start_night()
            elif 40 <= x <= 400 and 320 <= y <= 360:
                self.menu_sel = 1
                self.night = self.continue_night
                self.play("blip")
                self.start_night()
            return
        if self.mode not in ("game", "cameras"):
            return
        if W // 2 - 80 <= x <= W // 2 + 80 and y >= H - 36:
            self.cams_open = not self.cams_open
            self.mode = "cameras" if self.cams_open else "game"
            if self.cams_open:
                self.light_l = self.light_r = False
            self.play("put")
            self.recalc_usage()
            return
        if self.cams_open:
            for i in range(11):
                r = pygame.Rect(40 + (i % 6) * 70, H - 120 + (i // 6) * 40, 60, 32)
                if r.collidepoint(x, y):
                    self.cam = i
                    self.play("blip")
            return
        ox = x + self.scroll
        if 20 <= ox <= 70 and 280 <= y <= 360:
            self.door_l = not self.door_l
            self.play("door")
            self.recalc_usage()
            return
        if OFFICE_W - 70 <= ox <= OFFICE_W - 20 and 280 <= y <= 360:
            self.door_r = not self.door_r
            self.play("door")
            self.recalc_usage()
            return

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    if self.mode in ("game", "cameras"):
                        self.stop_fan()
                        self.mode = "menu"
                    else:
                        pygame.quit()
                        return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click(e.pos, e.button)
            # Hold lights like original (mouse held on light zone)
            if self.mode == "game" and pygame.mouse.get_pressed()[0]:
                x, y = pygame.mouse.get_pos()
                ox = x + self.scroll
                hl = 20 <= ox <= 70 and 380 <= y <= 450
                hr = OFFICE_W - 70 <= ox <= OFFICE_W - 20 and 380 <= y <= 450
                if hl or hr:
                    self.light_l = hl
                    self.light_r = hr
                    self.recalc_usage()
            elif self.mode == "game":
                if self.light_l or self.light_r:
                    self.light_l = False
                    self.light_r = False
                    self.recalc_usage()

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
