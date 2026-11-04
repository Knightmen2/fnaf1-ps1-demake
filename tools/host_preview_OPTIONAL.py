#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC host preview (tkinter + Pillow) — 320x240 scaled, cooked PS1 assets.
Controls (keyboard ≈ DualShock):
  Enter          — New Game / OK
  A/D or Left/Right — look / switch cam
  W/S            — cam grid up/down
  Q              — left door
  E              — right door
  Z hold         — left light
  C hold         — right light
  Space          — flip monitor
  Esc            — quit
  F1             — DEV: skip wake timers (animatronics active now)
"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
GFX = ROOT / "ps1_assets" / "graphics"
FNT = ROOT / "ps1_assets" / "fonts"
MAP = json.loads((ROOT / "ps1_assets" / "atlas_map.json").read_text(encoding="utf-8"))

SCALE = 3
W, H = 320, 240

# Frame timings (NTSC) — shortened for preview feel
FR_HOUR = 900          # was 2580 — faster nights for testing
FR_BONNIE_WAKE = 600   # was 5160
FR_CHICA_WAKE = 900
FR_POWER = [180, 120, 90, 60, 45]
FR_WAIT_SCREAM = 180
FR_LOSE = 240
FR_TRANSITION = 90
FR_WIN = 300

OFFICE_STEMS = ["39", "58", "127", "225", "227"]  # dark, Ll, Rl, bonnie, chica


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


class Game:
    def __init__(self):
        self.mode = "menu"
        self.night = 1
        self.hour = 0
        self.power = 100
        self.usage = 1
        self.scroll = 96
        self.door_l = self.door_r = 0
        self.light_l = self.light_r = 0
        self.light_ok = 1
        self.cam = 0
        self.noise = 0
        self.record = 0
        self.bonnie_step = 0
        self.chica_step = 0
        self.bonnie_door = 0
        self.chica_door = 0
        self.bonnie_wait = 0
        self.chica_wait = 0
        self.bonnie_sdelay = 0
        self.chica_sdelay = 0
        self.bonnie_active = 0
        self.chica_active = 0
        self.bonnie_atk = 0
        self.chica_atk = 0
        self.bonnie_sf = 0
        self.chica_sf = 0
        self.bonnie_seen = 0
        self.chica_seen = 0
        self.power_t = FR_POWER[0]
        self.hour_t = FR_HOUR
        self.bon_wake = FR_BONNIE_WAKE
        self.chi_wake = FR_CHICA_WAKE
        self.trans_t = 0
        self.lose_t = 0
        self.win_t = 0
        self.tick = 0
        self.status = "MENU — Enter=New Game"

        self.office = {}
        for stem in OFFICE_STEMS:
            self.office[stem] = (
                load_rgb(GFX / f"office_{stem}_L.png"),
                load_rgb(GFX / f"office_{stem}_R.png"),
            )
        cams_files = sorted(GFX.glob("cam_*.png"))
        self.cams = [load_rgb(p) for p in cams_files[:11]]
        if len(self.cams) < 11:
            raise RuntimeError(f"expected 11 cams, got {len(self.cams)}")
        self.ui = load_rgb(GFX / "ui_atlas.png")
        self.bonnie_atl = load_rgb(GFX / "bonnie_atlas.png")
        self.chica_atl = load_rgb(GFX / "chica_atlas.png")
        self.font_atl = load_rgb(FNT / "font_atlas.png") if (FNT / "font_atlas.png").exists() else None
        self.door_l_img = load_rgb(GFX / "door_L.png") if (GFX / "door_L.png").exists() else None
        self.door_r_img = load_rgb(GFX / "door_R.png") if (GFX / "door_R.png").exists() else None

    def recalc_usage(self):
        u = 1 + self.door_l + self.door_r + self.light_l + self.light_r + (1 if self.mode == "cameras" else 0)
        self.usage = max(1, min(5, u))

    def office_stem(self):
        if self.light_l and self.bonnie_door:
            return "225"
        if self.light_r and self.chica_door:
            return "227"
        if self.light_l:
            return "58"
        if self.light_r:
            return "127"
        return "39"

    def start_night(self):
        self.mode = "transition"
        self.trans_t = FR_TRANSITION
        self.status = "12 AM..."

    def enter_game(self):
        self.mode = "game"
        self.hour = 0
        self.power = 100
        self.door_l = self.door_r = 0
        self.light_l = self.light_r = 0
        self.light_ok = 1
        self.cam = 0
        self.bonnie_step = self.chica_step = 0
        self.bonnie_door = self.chica_door = 0
        self.bonnie_active = self.chica_active = 0
        self.bonnie_atk = self.chica_atk = 0
        self.bonnie_sf = self.chica_sf = 0
        self.bonnie_seen = self.chica_seen = 0
        self.bonnie_wait = self.chica_wait = 0
        self.bonnie_sdelay = self.chica_sdelay = 0
        self.power_t = FR_POWER[0]
        self.hour_t = FR_HOUR
        self.bon_wake = FR_BONNIE_WAKE
        self.chi_wake = FR_CHICA_WAKE
        self.recalc_usage()
        self.status = "GAME"

    def update(self, keys):
        self.tick += 1
        pressed = keys["pressed"]
        held = keys["held"]

        if self.mode == "menu":
            if "ok" in pressed:
                self.start_night()
            return

        if self.mode == "transition":
            self.trans_t -= 1
            if self.trans_t <= 0:
                self.enter_game()
            return

        if self.mode == "lose":
            self.lose_t -= 1
            self.noise = (self.noise + 1) & 7
            if self.lose_t <= 0:
                self.mode = "menu"
                self.status = "MENU — Enter=New Game"
            return

        if self.mode == "win":
            self.win_t -= 1
            if self.win_t <= 0:
                self.mode = "menu"
                self.status = "WIN — star earned"
            return

        # Input
        if self.mode == "game":
            if "left" in held:
                self.scroll = max(0, self.scroll - 4)
            if "right" in held:
                self.scroll = min(192, self.scroll + 4)
            if "doorl" in pressed and self.light_ok:
                self.door_l ^= 1
                self.recalc_usage()
            if "doorr" in pressed and self.light_ok:
                self.door_r ^= 1
                self.recalc_usage()
            self.light_l = 1 if ("lightl" in held and self.light_ok) else 0
            self.light_r = 1 if ("lightr" in held and self.light_ok) else 0
            if self.light_l and self.bonnie_door and not self.bonnie_seen:
                self.bonnie_seen = 1
            if self.light_r and self.chica_door and not self.chica_seen:
                self.chica_seen = 1
            self.recalc_usage()
            if "cam" in pressed:
                self.mode = "cameras"
                self.light_l = self.light_r = 0
                self.recalc_usage()
                self.status = f"CAM {self.cam+1}"
        elif self.mode == "cameras":
            if "left" in pressed:
                self.cam = max(0, self.cam - 1)
            if "right" in pressed:
                self.cam = min(10, self.cam + 1)
            if "up" in pressed and self.cam >= 3:
                self.cam -= 3
            if "down" in pressed and self.cam + 3 <= 10:
                self.cam += 3
            if "cam" in pressed:
                self.mode = "game"
                self.recalc_usage()
                self.status = "GAME"
            self.noise = (self.noise + 1) & 7
            if (self.tick & 31) == 0:
                self.record ^= 1

        if "dev" in pressed:
            self.bon_wake = 0
            self.chi_wake = 0
            self.bonnie_active = self.chica_active = 1
            self.bonnie_wait = self.chica_wait = 30
            self.status = "DEV: AI awake"

        if self.mode not in ("game", "cameras"):
            return

        # Wake
        if self.bon_wake > 0:
            self.bon_wake -= 1
            if self.bon_wake == 0:
                self.bonnie_active = 1
                self.bonnie_wait = 60
        if self.chi_wake > 0:
            self.chi_wake -= 1
            if self.chi_wake == 0:
                self.chica_active = 1
                self.chica_wait = 60

        # Power / hour
        self.power_t -= 1
        if self.power_t <= 0:
            self.power -= 1
            self.power_t = FR_POWER[self.usage - 1]
            if self.power < 0:
                self.mode = "outpower"
                self.lose_t = 300
                self.status = "POWER OUT"
                return
        self.hour_t -= 1
        if self.hour_t <= 0:
            self.hour += 1
            self.hour_t = FR_HOUR
            if self.hour >= 6:
                self.mode = "win"
                self.win_t = FR_WIN
                self.status = "6 AM"
                return

        # Bonnie AI
        if self.bonnie_atk:
            if self.bonnie_sf == 0:
                pass
            if (self.tick & 1) == 0:
                self.bonnie_sf += 1
            if self.bonnie_sf >= 8:
                self.mode = "lose"
                self.lose_t = FR_LOSE
                self.status = "Bonnie got you"
            return
        if self.chica_atk:
            if (self.tick & 1) == 0:
                self.chica_sf += 1
            if self.chica_sf >= 8:
                self.mode = "lose"
                self.lose_t = FR_LOSE
                self.status = "Chica got you"
            return

        if self.bonnie_active:
            if self.bonnie_sdelay > 0:
                self.bonnie_sdelay -= 1
                if self.bonnie_sdelay == 0:
                    if self.door_l:
                        self.bonnie_step = 1 + (self.tick % 3)
                        self.bonnie_door = 0
                        self.bonnie_wait = 120
                    else:
                        self.bonnie_atk = 1
                        self.bonnie_sf = 0
                        self.light_ok = 0
            elif self.bonnie_wait > 0:
                self.bonnie_wait -= 1
            elif not self.bonnie_door and self.bonnie_step < 7:
                self.bonnie_step += 1
                if self.bonnie_step >= 7:
                    self.bonnie_door = 1
                    self.bonnie_sdelay = FR_WAIT_SCREAM
                else:
                    self.bonnie_wait = 90 + (self.tick % 90)

        if self.chica_active:
            if self.chica_sdelay > 0:
                self.chica_sdelay -= 1
                if self.chica_sdelay == 0:
                    if self.door_r:
                        self.chica_step = 1 + (self.tick % 3)
                        self.chica_door = 0
                        self.chica_wait = 120
                    else:
                        self.chica_atk = 1
                        self.chica_sf = 0
                        self.light_ok = 0
            elif self.chica_wait > 0:
                self.chica_wait -= 1
            elif not self.chica_door and self.chica_step < 9:
                self.chica_step += 1
                if self.chica_step >= 9:
                    self.chica_door = 1
                    self.chica_sdelay = FR_WAIT_SCREAM
                else:
                    self.chica_wait = 100 + (self.tick % 100)

        self.status = (
            f"{self.mode.upper()} | {self.hour if self.hour else 12}AM N{self.night} "
            f"PWR{self.power}% U{self.usage} | B{self.bonnie_step}{'!' if self.bonnie_door else ''} "
            f"C{self.chica_step}{'!' if self.chica_door else ''} scroll={self.scroll}"
        )

    def blit_atlas(self, canvas, atlas, slot_key, dx, dy, atlas_map_key="ui_atlas"):
        slots = MAP.get(atlas_map_key, {}).get("slots", {})
        s = slots.get(slot_key)
        if not s:
            return
        crop = atlas.crop((s["x"], s["y"], s["x"] + s["w"], s["y"] + s["h"]))
        canvas.paste(crop, (dx, dy), crop)

    def render(self) -> Image.Image:
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        draw = ImageDraw.Draw(frame)

        if self.mode == "menu":
            L, R = self.office["39"]
            frame.paste(L, (0, 0), L)
            frame.paste(R.crop((0, 0, 64, 240)), (256, 0), R.crop((0, 0, 64, 240)))
            draw.text((20, 200), "FNAF PS1 DEMAKE — ENTER", fill=(255, 255, 255))
        elif self.mode == "transition":
            draw.text((110, 110), "12 AM", fill=(255, 255, 255))
        elif self.mode in ("game", "outpower") and not (self.bonnie_atk or self.chica_atk):
            stem = self.office_stem()
            L, R = self.office[stem]
            # panoramic: draw L at -scroll, R at 256-scroll
            frame.paste(L, (-self.scroll, 0), L)
            frame.paste(R, (256 - self.scroll, 0), R)
            if self.door_l and self.door_l_img:
                frame.paste(self.door_l_img, (20 - self.scroll, 0), self.door_l_img)
            if self.door_r and self.door_r_img:
                frame.paste(self.door_r_img, (430 - self.scroll, 0), self.door_r_img)
            # HUD
            self.blit_atlas(frame, self.ui, f"battery_{self.usage-1}", 8, 210)
            draw.text((8, 8), f"{12 if self.hour==0 else self.hour} AM", fill=(255, 255, 255))
            draw.text((8, 190), f"{max(self.power,0)}%", fill=(255, 255, 255))
        elif self.mode == "cameras":
            cam = self.cams[self.cam % len(self.cams)]
            frame.paste(cam, (32, 0), cam)
            self.blit_atlas(frame, self.ui, "cam_nav", 200, 160)
            draw.text((40, 8), f"CAM-{self.cam+1}", fill=(255, 80, 80))
            draw.text((8, 190), f"{max(self.power,0)}%", fill=(255, 255, 255))
        elif self.bonnie_atk:
            cell = 64
            f = min(self.bonnie_sf, 15)
            u, v = (f % 4) * cell, (f // 4) * cell
            crop = self.bonnie_atl.crop((u, v, u + cell, v + cell)).resize((256, 240), Image.NEAREST)
            frame.paste(crop, (32, 0), crop)
        elif self.chica_atk:
            cell = 64
            f = min(self.chica_sf, 15)
            u, v = (f % 4) * cell, (f // 4) * cell
            crop = self.chica_atl.crop((u, v, u + cell, v + cell)).resize((256, 240), Image.NEAREST)
            frame.paste(crop, (32, 0), crop)
        elif self.mode == "lose":
            draw.rectangle((0, 0, W, H), fill=(20, 20, 20))
            draw.text((120, 110), "STATIC", fill=(200, 200, 200))
        elif self.mode == "win":
            draw.text((140, 110), "6 AM", fill=(255, 255, 255))

        return frame


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FNAF PS1 — Host Preview")
        self.game = Game()
        self.canvas = tk.Canvas(self.root, width=W * SCALE, height=H * SCALE, highlightthickness=0)
        self.canvas.pack()
        self.label = tk.Label(self.root, text="", anchor="w", font=("Consolas", 10))
        self.label.pack(fill="x")
        self.held = set()
        self.pressed = set()
        self.photo = None
        self.root.bind("<KeyPress>", self.on_down)
        self.root.bind("<KeyRelease>", self.on_up)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.tick()

    def map_key(self, event):
        k = event.keysym.lower()
        m = {
            "return": "ok", "space": "cam",
            "a": "left", "left": "left", "d": "right", "right": "right",
            "w": "up", "up": "up", "s": "down", "down": "down",
            "q": "doorl", "e": "doorr",
            "z": "lightl", "c": "lightr",
            "f1": "dev", "escape": "quit",
        }
        return m.get(k)

    def on_down(self, event):
        a = self.map_key(event)
        if a == "quit":
            self.root.destroy()
            return
        if a and a not in self.held:
            self.pressed.add(a)
            self.held.add(a)

    def on_up(self, event):
        a = self.map_key(event)
        if a in self.held:
            self.held.discard(a)

    def tick(self):
        self.game.update({"pressed": set(self.pressed), "held": set(self.held)})
        self.pressed.clear()
        img = self.game.render().resize((W * SCALE, H * SCALE), Image.NEAREST)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.label.config(text=self.game.status)
        self.root.after(16, self.tick)  # ~60Hz

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
