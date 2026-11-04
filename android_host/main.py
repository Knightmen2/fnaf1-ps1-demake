#!/usr/bin/env python3
"""FNAF1 demake Android host — touch + duplicated on-screen controls, no PS1 HW limits."""
from __future__ import annotations

import os
import sys
import random
from pathlib import Path

# Kivy preferred on Android; pygame fallback for desktop smoke-test
USE_KIVY = True
try:
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle, Line
    from kivy.graphics.texture import Texture
    from kivy.uix.widget import Widget
    from kivy.core.audio import SoundLoader
except Exception:
    USE_KIVY = False

ROOT = Path(__file__).resolve().parent
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

FPS = 60
OFFICE_W = 1600
LOGIC_W, LOGIC_H = 1280, 720


def find_sound(name: str):
    for base in (MUSIC, ROOT / "music"):
        if not base.exists():
            continue
        for f in base.iterdir():
            if f.is_file() and name.lower() in f.stem.lower():
                return str(f)
    return None


# ---------------------------------------------------------------------------
# Shared game logic (integer-friendly timers in frames)
# ---------------------------------------------------------------------------
class FnafLogic:
    def __init__(self):
        self.mode = "menu"
        self.night = 1
        self.continue_night = 1
        self.hour = 0
        self.power = 100
        self.usage = 1
        self.power_interval = 4 * FPS
        self.scroll = OFFICE_W // 2 - LOGIC_W // 2
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.hour_t = 30 * FPS
        self.power_t = 4 * FPS
        self.bonnie_wake = 40 * FPS
        self.chica_wake = 50 * FPS
        self.bonnie_step = self.chica_step = 0
        self.bonnie_wait = self.chica_wait = 0
        self.bonnie_door = self.chica_door = False
        self.lose_t = self.win_t = self.trans_t = 0
        self.look_dir = 0  # -1 left, 0 none, 1 right (touch buttons)

    def recalc_usage(self):
        u = 1 + int(self.door_l) + int(self.door_r) + int(self.light_l) + int(self.light_r) + int(self.cams_open)
        self.usage = min(5, u)
        speeds = {1: 4.0, 2: 3.0, 3: 1.7, 4: 1.4, 5: 1.0}
        self.power_interval = max(1, int(speeds.get(self.usage, 4.0) * FPS))

    def start_night(self, night=None):
        if night is not None:
            self.night = night
        self.mode = "transition"
        self.trans_t = 3 * FPS
        self.hour = 0
        self.power = 100
        self.door_l = self.door_r = False
        self.light_l = self.light_r = False
        self.cams_open = False
        self.cam = 0
        self.scroll = OFFICE_W // 2 - LOGIC_W // 2
        self.bonnie_step = self.chica_step = 0
        self.bonnie_door = self.chica_door = False
        self.bonnie_wake = 40 * FPS
        self.chica_wake = 50 * FPS
        self.bonnie_wait = self.chica_wait = 0
        self.look_dir = 0
        self.recalc_usage()
        self.power_t = self.power_interval
        self.hour_t = 30 * FPS

    def tick(self):
        if self.mode == "transition":
            self.trans_t -= 1
            if self.trans_t <= 0:
                self.mode = "game"
            return "entered" if self.trans_t <= 0 else None
        if self.mode == "lose":
            self.lose_t -= 1
            if self.lose_t <= 0:
                self.mode = "menu"
            return None
        if self.mode == "win":
            self.win_t -= 1
            if self.win_t <= 0:
                self.continue_night = min(5, self.night + 1)
                self.mode = "menu"
            return None
        if self.mode not in ("game", "cameras"):
            return None

        if self.mode == "game" and not self.cams_open:
            if self.look_dir < 0:
                self.scroll = max(0, self.scroll - 10)
            elif self.look_dir > 0:
                self.scroll = min(OFFICE_W - LOGIC_W, self.scroll + 10)

        if self.bonnie_wake > 0:
            self.bonnie_wake -= 1
        if self.chica_wake > 0:
            self.chica_wake -= 1

        self.hour_t -= 1
        if self.hour_t <= 0:
            self.hour += 1
            self.hour_t = 30 * FPS
            if self.hour >= 6:
                self.mode = "win"
                self.win_t = 8 * FPS
                return "win"

        self.power_t -= 1
        if self.power_t <= 0:
            self.power -= 1
            self.power_t = self.power_interval
            if self.power < 0:
                self.mode = "lose"
                self.lose_t = 5 * FPS
                return "lose"

        if self.bonnie_wake <= 0:
            if self.bonnie_wait > 0:
                self.bonnie_wait -= 1
            elif not self.bonnie_door:
                self.bonnie_step += 1
                self.bonnie_wait = random.randint(12 * FPS, 20 * FPS)
                if self.bonnie_step >= 7:
                    self.bonnie_door = True
                    self.bonnie_wait = 4 * FPS
            elif self.bonnie_wait <= 0:
                if self.door_l:
                    self.bonnie_step = random.randint(1, 3)
                    self.bonnie_door = False
                    self.bonnie_wait = random.randint(12 * FPS, 20 * FPS)
                else:
                    self.mode = "lose"
                    self.lose_t = 5 * FPS
                    return "lose"

        if self.chica_wake <= 0:
            if self.chica_wait > 0:
                self.chica_wait -= 1
            elif not self.chica_door:
                self.chica_step += 1
                self.chica_wait = random.randint(14 * FPS, 22 * FPS)
                if self.chica_step >= 9:
                    self.chica_door = True
                    self.chica_wait = 4 * FPS
            elif self.chica_wait <= 0:
                if self.door_r:
                    self.chica_step = random.randint(1, 3)
                    self.chica_door = False
                    self.chica_wait = random.randint(14 * FPS, 22 * FPS)
                else:
                    self.mode = "lose"
                    self.lose_t = 5 * FPS
                    return "lose"
        return None

    def toggle_cams(self):
        self.cams_open = not self.cams_open
        self.mode = "cameras" if self.cams_open else "game"
        if self.cams_open:
            self.light_l = self.light_r = False
        self.recalc_usage()


if USE_KIVY:
    from kivy.core.image import Image as CoreImage

    class GameWidget(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.g = FnafLogic()
            self.tex = {}
            self._load_textures()
            self.sounds = {}
            for k, n in [("blip", "blip3"), ("door", "door"), ("put", "put_down"), ("scream", "xscream")]:
                p = find_sound(n)
                if p:
                    self.sounds[k] = SoundLoader.load(p)
            self.fan = None
            fp = find_sound("buzz_fan")
            if fp:
                self.fan = SoundLoader.load(fp)
                if self.fan:
                    self.fan.loop = True
            Clock.schedule_interval(self._frame, 1.0 / FPS)
            self.bind(size=self._redraw, pos=self._redraw)
            self._held = set()

        def _load_textures(self):
            mapping = {
                "menu": "431.png",
                "loading": "453_.png",
                "office": "39.png",
            }
            cams = ["19.png", "48.png", "66.png", "337.png", "0.png", "62.png",
                    "67.png", "49.png", "83.png", "42.png", "41.png"]
            for k, f in mapping.items():
                p = IMG / f
                if p.exists():
                    self.tex[k] = CoreImage(str(p)).texture
            for i, f in enumerate(cams):
                p = IMG / f
                if p.exists():
                    self.tex[f"cam{i}"] = CoreImage(str(p)).texture

        def _play(self, k):
            s = self.sounds.get(k)
            if s:
                s.play()

        def _frame(self, dt):
            ev = self.g.tick()
            if ev == "entered" and self.fan:
                self.fan.play()
            if ev in ("lose", "win") and self.fan:
                self.fan.stop()
            if ev == "lose":
                self._play("scream")
            self._redraw()

        def _btn_rects(self):
            w, h = self.size
            # duplicated touch HUD
            return {
                "look_l": (10, h * 0.35, w * 0.12, h * 0.3),
                "look_r": (w * 0.88, h * 0.35, w * 0.12, h * 0.3),
                "door_l": (w * 0.14, h * 0.45, w * 0.1, h * 0.12),
                "door_r": (w * 0.76, h * 0.45, w * 0.1, h * 0.12),
                "light_l": (w * 0.14, h * 0.28, w * 0.1, h * 0.12),
                "light_r": (w * 0.76, h * 0.28, w * 0.1, h * 0.12),
                "cams": (w * 0.35, 8, w * 0.3, h * 0.08),
                "new": (w * 0.05, h * 0.45, w * 0.4, h * 0.08),
                "cont": (w * 0.05, h * 0.35, w * 0.4, h * 0.08),
            }

        def on_touch_down(self, touch):
            self._handle_touch(touch, True)
            return True

        def on_touch_up(self, touch):
            self._handle_touch(touch, False)
            return True

        def _in(self, touch, r):
            x, y, bw, bh = r
            return x <= touch.x <= x + bw and y <= touch.y <= y + bh

        def _handle_touch(self, touch, down):
            g = self.g
            btns = self._btn_rects()
            if g.mode == "menu" and down:
                if self._in(touch, btns["new"]):
                    g.start_night(1)
                    self._play("blip")
                elif self._in(touch, btns["cont"]):
                    g.start_night(g.continue_night)
                    self._play("blip")
                return
            if g.mode not in ("game", "cameras"):
                return
            if self._in(touch, btns["cams"]) and down:
                g.toggle_cams()
                self._play("put")
                return
            if g.cams_open and down:
                # cam grid
                w, h = self.size
                for i in range(11):
                    cx = 20 + (i % 6) * (w * 0.14)
                    cy = 40 + (i // 6) * (h * 0.08)
                    if cx <= touch.x <= cx + w * 0.12 and cy <= touch.y <= cy + h * 0.07:
                        g.cam = i
                        self._play("blip")
                return
            # look hold
            if self._in(touch, btns["look_l"]):
                g.look_dir = -1 if down else 0
            elif self._in(touch, btns["look_r"]):
                g.look_dir = 1 if down else 0
            if down and self._in(touch, btns["door_l"]):
                g.door_l = not g.door_l
                self._play("door")
                g.recalc_usage()
            if down and self._in(touch, btns["door_r"]):
                g.door_r = not g.door_r
                self._play("door")
                g.recalc_usage()
            # lights hold
            if self._in(touch, btns["light_l"]):
                g.light_l = down
                if down:
                    g.light_r = False
                g.recalc_usage()
            if self._in(touch, btns["light_r"]):
                g.light_r = down
                if down:
                    g.light_l = False
                g.recalc_usage()

        def _redraw(self, *a):
            self.canvas.clear()
            g = self.g
            w, h = float(self.width), float(self.height)
            with self.canvas:
                Color(0, 0, 0, 1)
                Rectangle(pos=self.pos, size=self.size)
                if g.mode == "menu":
                    t = self.tex.get("menu")
                    if t:
                        Color(1, 1, 1, 1)
                        Rectangle(texture=t, pos=self.pos, size=self.size)
                elif g.mode == "transition":
                    t = self.tex.get("loading")
                    if t:
                        Color(1, 1, 1, 1)
                        Rectangle(texture=t, pos=self.pos, size=self.size)
                elif g.mode in ("game", "cameras"):
                    if g.cams_open:
                        t = self.tex.get(f"cam{g.cam}")
                        if t:
                            Color(1, 1, 1, 1)
                            Rectangle(texture=t, pos=self.pos, size=self.size)
                    else:
                        t = self.tex.get("office")
                        if t:
                            Color(1, 1, 1, 1)
                            # pan: show window into wide office
                            scale = h / LOGIC_H
                            ow = OFFICE_W * (w / LOGIC_W)
                            Rectangle(
                                texture=t,
                                pos=(self.x - g.scroll * (w / LOGIC_W), self.y),
                                size=(ow, h),
                            )
                    # HUD buttons overlay
                    Color(0.2, 0.2, 0.2, 0.55)
                    for key in ("look_l", "look_r", "door_l", "door_r", "light_l", "light_r", "cams"):
                        x, y, bw, bh = self._btn_rects()[key]
                        Rectangle(pos=(x, y), size=(bw, bh))
                elif g.mode == "lose":
                    Color(0.6, 0, 0, 1)
                    Rectangle(pos=self.pos, size=self.size)
                elif g.mode == "win":
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(self.x + w * 0.4, self.y + h * 0.45), size=(w * 0.2, h * 0.1))

    class FnafApp(App):
        def build(self):
            self.title = "FNAF1 PS1 Demake APK"
            return GameWidget()


def run_pygame_fallback():
    """Desktop smoke-test with touch-like on-screen buttons via mouse."""
    import pygame

    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((LOGIC_W, LOGIC_H))
    pygame.display.set_caption("FNAF1 APK host (touch HUD / pygame fallback)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
    g = FnafLogic()

    def limg(name, size=None):
        p = IMG / name
        if not p.exists():
            s = pygame.Surface(size or (256, 240))
            s.fill((30, 30, 30))
            return s
        im = pygame.image.load(str(p)).convert()
        return pygame.transform.smoothscale(im, size) if size else im

    menu = limg("431.png", (LOGIC_W, LOGIC_H))
    loading = limg("453_.png", (LOGIC_W, LOGIC_H))
    office = limg("39.png", (OFFICE_W, LOGIC_H))
    cams = [limg(f, (LOGIC_W, LOGIC_H)) for f in
            ["19.png", "48.png", "66.png", "337.png", "0.png", "62.png",
             "67.png", "49.png", "83.png", "42.png", "41.png"]]

    def btns():
        return {
            "look_l": pygame.Rect(10, 250, 100, 200),
            "look_r": pygame.Rect(LOGIC_W - 110, 250, 100, 200),
            "door_l": pygame.Rect(120, 320, 90, 70),
            "door_r": pygame.Rect(LOGIC_W - 210, 320, 90, 70),
            "light_l": pygame.Rect(120, 220, 90, 70),
            "light_r": pygame.Rect(LOGIC_W - 210, 220, 90, 70),
            "cams": pygame.Rect(LOGIC_W // 2 - 80, LOGIC_H - 50, 160, 40),
            "new": pygame.Rect(40, 280, 300, 40),
            "cont": pygame.Rect(40, 330, 300, 40),
        }

    while True:
        b = btns()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if g.mode == "menu":
                    if b["new"].collidepoint(e.pos):
                        g.start_night(1)
                    elif b["cont"].collidepoint(e.pos):
                        g.start_night(g.continue_night)
                elif g.mode in ("game", "cameras"):
                    if b["cams"].collidepoint(e.pos):
                        g.toggle_cams()
                    elif g.cams_open:
                        for i in range(11):
                            r = pygame.Rect(40 + (i % 6) * 70, 40 + (i // 6) * 40, 60, 32)
                            if r.collidepoint(e.pos):
                                g.cam = i
                    else:
                        if b["door_l"].collidepoint(e.pos):
                            g.door_l = not g.door_l
                            g.recalc_usage()
                        if b["door_r"].collidepoint(e.pos):
                            g.door_r = not g.door_r
                            g.recalc_usage()
        pressed = pygame.mouse.get_pressed()[0]
        pos = pygame.mouse.get_pos()
        g.look_dir = 0
        g.light_l = g.light_r = False
        if pressed and g.mode == "game" and not g.cams_open:
            if b["look_l"].collidepoint(pos):
                g.look_dir = -1
            if b["look_r"].collidepoint(pos):
                g.look_dir = 1
            if b["light_l"].collidepoint(pos):
                g.light_l = True
            if b["light_r"].collidepoint(pos):
                g.light_r = True
            g.recalc_usage()

        g.tick()
        if g.mode == "menu":
            screen.blit(menu, (0, 0))
            screen.blit(font.render("NEW GAME (touch)", True, (255, 255, 0)), (50, 290))
            screen.blit(font.render("CONTINUE (touch)", True, (255, 255, 0)), (50, 340))
        elif g.mode == "transition":
            screen.blit(loading, (0, 0))
            screen.blit(font.render(f"Night {g.night}", True, (255, 255, 255)), (LOGIC_W // 2 - 40, LOGIC_H // 2))
        elif g.mode in ("game", "cameras"):
            if g.cams_open:
                screen.blit(cams[g.cam], (0, 0))
                for i in range(11):
                    r = pygame.Rect(40 + (i % 6) * 70, 40 + (i // 6) * 40, 60, 32)
                    pygame.draw.rect(screen, (200, 40, 40) if i == g.cam else (70, 70, 70), r)
            else:
                screen.blit(office, (-g.scroll, 0))
            for name, col in (("look_l", (80, 80, 120)), ("look_r", (80, 80, 120)),
                              ("door_l", (100, 100, 100)), ("door_r", (100, 100, 100)),
                              ("light_l", (180, 180, 40)), ("light_r", (180, 180, 40)),
                              ("cams", (40, 40, 40))):
                pygame.draw.rect(screen, col, b[name], 2)
                screen.blit(font.render(name, True, (220, 220, 220)), (b[name].x + 4, b[name].y + 4))
            am = 12 if g.hour == 0 else g.hour
            screen.blit(font.render(f"PWR {max(0,g.power)}%  {am}AM  N{g.night}", True, (255, 255, 255)), (20, LOGIC_H - 80))
        elif g.mode == "lose":
            screen.fill((40, 0, 0))
        elif g.mode == "win":
            screen.fill((0, 0, 0))
            screen.blit(font.render("6 AM", True, (255, 255, 255)), (LOGIC_W // 2 - 20, LOGIC_H // 2))
        pygame.display.flip()
        clock.tick(FPS)


def main():
    if USE_KIVY and not os.environ.get("FNAF_FORCE_PYGAME"):
        # On desktop without proper GL, allow override
        try:
            FnafApp().run()
            return
        except Exception as ex:
            print("Kivy failed, pygame fallback:", ex)
    run_pygame_fallback()


if __name__ == "__main__":
    main()
