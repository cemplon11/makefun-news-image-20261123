"""Draw the world's news of Monday 23 November 2026 as one 1024x1024 image.

Pure Python standard library only: no third-party packages, no network,
no randomness, no clock. The program draws a newspaper front page -- a
masthead, two lead stories with pictures, three mid stories with pictures,
and a twenty-item brief -- and writes it as a PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (default: ./out/entry.png).

Run it twice and the bytes are identical.

Stories were verified against live reporting on 23 November 2026; the full
list with sources is in STORIES.md.
"""

import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# Palette: newsprint cream, ink, and a small set of flat accent colours.
PAPER = (247, 242, 231)
INK = (20, 20, 20)
RED = (185, 28, 28)
DARK_RED = (127, 29, 29)
BLUE = (29, 78, 216)
NAVY = (15, 23, 42)
SEA = (30, 64, 175)
SKY = (186, 214, 235)
SAND = (226, 205, 160)
GREY = (107, 114, 128)
LIGHT_GREY = (209, 213, 219)
DARK_GREY = (55, 65, 81)
ORANGE = (234, 88, 12)
FLAME = (249, 115, 22)
YELLOW = (250, 204, 21)
GREEN = (21, 128, 61)
TEAL = (13, 148, 136)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SMOKE = (148, 163, 184)

# 5x7 bitmap font. Each glyph is seven rows of five bits, "1" = ink.
# Uppercase letters, digits and the punctuation the front page needs.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}

FONT.update({
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
})


class Canvas:
    """An RGB canvas backed by one bytearray, drawn with flat shapes."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        """Bresenham line with a square brush of thickness t."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = t // 2
        while True:
            self.rect(x0 - half, y0 - half, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            span = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.rect(cx - span, yy, span * 2 + 1, 1, c)

    def poly(self, pts, c):
        """Fill a polygon by scanline intersection (deterministic)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[k])), y,
                          int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1,
                          1, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(0, 360, 2):
            rad = math.radians(a)
            self.rect(int(cx + r * math.cos(rad)) - t // 2,
                      int(cy + r * math.sin(rad)) - t // 2, t, t, c)


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    """Draw uppercase text (lowercase is folded up) at scale."""
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.rect(cx + col * scale, y + row * scale,
                            scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_c(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = s.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- scenes
# Each scene draws inside the box (x, y, w, h) with flat shapes only.

def flame(cv, x, y, s):
    """A stylised flame of height ~2*s at (x, y) = base centre."""
    cv.poly([(x - s, y), (x - s // 2, y - s), (x - s // 4, y - s // 2),
             (x, y - 2 * s), (x + s // 4, y - s // 2), (x + s // 2, y - s),
             (x + s, y)], FLAME)
    cv.poly([(x - s // 2, y), (x - s // 4, y - s // 2),
             (x, y - s), (x + s // 4, y - s // 2), (x + s // 2, y)],
            YELLOW)


def smoke(cv, x, y, r):
    cv.circle(x, y, r, SMOKE)
    cv.circle(x + r, y - r // 2, r * 3 // 4, GREY)
    cv.circle(x - r, y - r // 2, r * 2 // 3, SMOKE)


def scene_hormuz(cv, x, y, w, h):
    """Burning tanker in the Strait of Hormuz at dusk."""
    cv.rect(x, y, w, h, NAVY)
    cv.rect(x, y + h * 2 // 5, w, h // 5, (58, 28, 20))       # dusk band
    cv.rect(x, y + h * 3 // 5, w, h * 2 // 5, SEA)             # sea
    for i in range(3):                                          # wave lines
        wy = y + h * 3 // 5 + 12 + i * 14
        for wx in range(x + 8, x + w - 8, 26):
            cv.hline(wx, wy + (3 if i % 2 else 0), 14, (96, 165, 250))
    # tanker hull and superstructure
    hx, hy = x + w // 2 - 160, y + h * 3 // 5 - 26
    cv.rect(hx, hy, 320, 34, BLACK)
    cv.rect(hx + 196, hy - 34, 84, 34, WHITE)
    cv.rect(hx + 206, hy - 28, 64, 7, INK)
    cv.rect(hx + 206, hy - 16, 64, 7, INK)
    cv.rect(hx + 280, hy - 44, 8, 12, DARK_GREY)
    for cx in range(hx + 8, hx + 180, 34):                     # containers
        cv.rect(cx, hy - 20, 28, 20, DARK_RED if (cx // 34) % 2 else TEAL)
    # flames and smoke from the bow
    flame(cv, hx + 50, hy - 4, 18)
    flame(cv, hx + 110, hy - 4, 14)
    smoke(cv, hx + 70, hy - 36, 9)
    smoke(cv, hx + 130, hy - 44, 8)
    # missile arcs overhead
    cv.line(x + 30, y + 14, x + 130, y + 60, ORANGE, 3)
    cv.line(x + w - 30, y + 10, x + w - 140, y + 56, ORANGE, 3)
    cv.circle(x + 130, y + 60, 4, YELLOW)
    cv.circle(x + w - 140, y + 56, 4, YELLOW)
    # strait label
    draw_text(cv, x + 10, y + h - 18, "STRAIT OF HORMUZ", 1, WHITE)


def scene_cop31(cv, x, y, w, h):
    """A cracked globe: the climate talks end with no deal."""
    cv.rect(x, y, w, h, SKY)
    gx, gy, gr = x + 88, y + h // 2 + 2, 50
    cv.circle(gx, gy, gr, SEA)                                 # globe
    cv.circle(gx - 14, gy - 14, 13, GREEN)                     # land
    cv.circle(gx + 13, gy + 7, 16, GREEN)
    cv.circle(gx + 19, gy - 21, 8, GREEN)
    cv.ring(gx, gy, gr, NAVY, 3)
    # crack across the globe
    cv.line(gx - 32, gy - 42, gx - 10, gy - 14, DARK_RED, 4)
    cv.line(gx - 10, gy - 14, gx + 5, gy + 5, DARK_RED, 4)
    cv.line(gx + 5, gy + 5, gx + 27, gy + 35, DARK_RED, 4)
    # crossed-out words on the right
    tx = x + 168
    draw_text(cv, tx, y + 26, "FOSSIL", 3, INK)
    draw_text(cv, tx, y + 54, "FUELS", 3, INK)
    cv.line(tx - 6, y + 36, tx + 128, y + 76, RED, 5)
    cv.line(tx - 6, y + 76, tx + 128, y + 36, RED, 5)
    draw_text(cv, tx, y + 86, "NO DEAL", 3, RED)
    draw_text(cv, x + 10, y + h - 18, "ANTALYA, TURKIYE", 1, INK)


def scene_kyiv(cv, x, y, w, h):
    """A five-storey block in Dymer, its middle floors collapsed."""
    cv.rect(x, y, w, h, (233, 226, 211))
    bx, by = x + (w - 220) // 2, y + 6
    bw, bh = 220, h - 12
    cv.rect(bx, by, bw, bh, LIGHT_GREY)                        # block
    cv.rect(bx, by, bw, 8, DARK_GREY)                          # roof
    step_x, step_y = bw // 5, bh // 5
    for row in range(5):                                        # windows
        for col in range(5):
            if col == 2 and row in (1, 2, 3):
                continue                                        # collapsed
            cv.rect(bx + 10 + col * step_x, by + 14 + row * step_y,
                    step_x - 14, step_y - 8,
                    NAVY if (row + col) % 3 else YELLOW)
    # collapsed middle section
    cx0, cx1 = bx + 2 * step_x, bx + 3 * step_x
    cv.poly([(cx0, by + 8), (cx1, by + 8), (cx1 + 8, by + bh // 2),
             (cx1 - 6, by + bh - 8), (cx0 + 4, by + bh // 2 + 8),
             (cx0 - 6, by + bh // 3)], (38, 38, 38))
    cv.poly([(cx0 - 12, by + bh), (cx0 + step_x // 2, by + bh - 26),
             (cx1 + 12, by + bh)], DARK_GREY)                   # rubble
    cv.poly([(cx0 + 2, by + bh), (cx0 + step_x // 2, by + bh - 16),
             (cx1 + 2, by + bh)], GREY)
    # rescue ladder and light
    cv.line(bx + 4, by + bh, bx + 52, by + bh // 2, YELLOW, 4)
    cv.circle(bx + bw - 16, by + bh - 8, 6, RED)


def scene_java(cv, x, y, w, h):
    """The candy factory in Banten: flames, smoke, searchlights."""
    cv.rect(x, y, w, h, (26, 26, 34))
    fw, fh = w - 56, h * 2 // 5
    fx, fy = x + 28, y + h - fh - 6
    cv.rect(fx, fy, fw, fh, DARK_GREY)                         # factory
    for i in range(4):                                          # sawtooth roof
        cv.poly([(fx + i * fw // 4, fy), (fx + (i + 1) * fw // 4, fy),
                 (fx + (i + 1) * fw // 4, fy - 12)], GREY)
    for i in range(6):                                          # windows
        cv.rect(fx + 10 + i * (fw - 20) // 6, fy + fh // 3,
                (fw - 20) // 6 - 8, fh // 3,
                YELLOW if i % 2 else ORANGE)
    fs = max(10, h // 7)
    flame(cv, fx + fw // 4, fy - 8, fs)
    flame(cv, fx + 3 * fw // 4, fy - 8, fs - 2)
    flame(cv, fx + fw // 2, fy - 8, fs + 2)
    smoke(cv, fx + fw // 4, fy - 2 * fs - 8, 10)
    smoke(cv, fx + 3 * fw // 4, fy - 2 * fs - 16, 8)
    # searchlight beams
    cv.line(x + 6, y + 4, fx + fw // 4, fy - 6, YELLOW, 2)
    cv.line(x + w - 6, y + 4, fx + 3 * fw // 4, fy - 6, YELLOW, 2)


def scene_un_ai(cv, x, y, w, h):
    """A robot head: talks on killer robots go on."""
    cv.rect(x, y, w, h, (219, 234, 244))
    cx, cy = x + w // 2, y + h // 2 + 2
    hw, hh = min(w // 2 - 8, 62), min(h // 2 - 4, 40)
    cv.rect(cx - hw, cy - hh, hw * 2, hh * 2, WHITE)            # head
    cv.rect(cx - hw, cy - hh, hw * 2, 8, BLUE)                  # brow band
    cv.vline(cx, cy - hh - 6, 6, DARK_GREY, 4)                  # antenna
    cv.circle(cx, cy - hh - 8, 4, RED)
    er = max(7, hh // 3)
    cv.circle(cx - hw // 2, cy - hh // 4, er, NAVY)             # eyes
    cv.circle(cx + hw // 2, cy - hh // 4, er, NAVY)
    cv.circle(cx - hw // 2, cy - hh // 4, er // 3, (96, 165, 250))
    cv.circle(cx + hw // 2, cy - hh // 4, er // 3, (96, 165, 250))
    cv.rect(cx - hw // 2, cy + hh // 2, hw, 5, DARK_GREY)       # mouth grille
    for dx in (-hw // 3, 0, hw // 3):
        cv.vline(cx + dx, cy + hh // 2, 5, DARK_GREY, 3)
    cv.rect(cx - hw - 10, cy - hh // 2, 10, hh, LIGHT_GREY)     # ears
    cv.rect(cx + hw, cy - hh // 2, 10, hh, LIGHT_GREY)


# ---------------------------------------------------------------- layout

BRIEFS = [
    "NEPAL PM SHAH IN TALKS WITH MODI",
    "DEMOCRATS WIN 258 HOUSE SEATS",
    "INDIA 720/9D: RECORD IN WELLINGTON",
    "CALIFORNIA CONCERT SHOOTING: 9 HURT",
    "SPARTA II STILL BURNING OFF FINLAND",
    "LISBON MARCHES OVER LIVING COSTS",
    "MYANMAR SLAMS ASEAN DECISION",
    "SOUTH SUDAN: 24 CIVILIANS KILLED",
    "WHO: FIGHTING NEAR CONGO EBOLA ZONE",
    "BOLSONARO 'STABLE' IN INTENSIVE CARE",
    "US PROBES NVIDIA CHIP SALES TO CHINA",
    "OPENROUTER CUTS 3 AI PROVIDERS",
    "SWIMMER CROSSES HORMUZ AMID WAR",
    "BEIJING BARS RED-CHIP LISTINGS",
    "DELTA GLITCH DELAYS HOLIDAY FLIGHTS",
    "PAOLO BULGARI DIES, AGED 89",
    "SEOUL MINISTER QUITS OVER AI CHEATING",
    "N. KOREA'S KIM: SECURITY, NOT SUPREMACY",
    "POLAND: 3 RUSSIAN MISSILES HIT FRIDAY",
    "TATA STEEL IN RS28,000-CR DEAL",
]


def panel(cv, x, y, w, h, kicker, head_lines, scene, sub, head_scale=4):
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, h, INK)  # border via four thin rects below
    cv.rect(x + 2, y + 2, w - 4, h - 4, WHITE)
    cv.hline(x, y, w, INK, 2)
    cv.hline(x, y + h - 2, w, INK, 2)
    cv.vline(x, y, h, INK, 2)
    cv.vline(x + w - 2, y, h, INK, 2)
    draw_text(cv, x + 12, y + 10, kicker, 2, RED)
    yy = y + 32
    for line in head_lines:
        draw_text(cv, x + 12, yy, line, head_scale, INK)
        yy += 7 * head_scale + 4
    scene_y = yy + 4
    scene_h = y + h - 64 - scene_y
    scene(cv, x + 10, scene_y, w - 20, scene_h)
    yy = y + h - 58
    for line in wrap(sub, 2, w - 24):
        draw_text(cv, x + 12, yy, line, 2, DARK_GREY)
        yy += 16


def draw_front_page():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    draw_text_c(cv, W // 2, 14, "THE WORLD IN ONE DAY", 6, INK)
    cv.hline(24, 64, W - 48, INK, 2)
    draw_text_c(cv, W // 2, 72, "MONDAY 23 NOVEMBER 2026", 3, RED)
    draw_text_c(cv, W // 2, 96, "25 STORIES FROM AROUND THE WORLD",
                2, DARK_GREY)
    cv.hline(24, 120, W - 48, INK, 3)

    # Two leads.
    panel(cv, 24, 132, 481, 288, "LEAD 1 - THE WAR AT SEA",
          ["SIXTH TANKER HIT", "IN HORMUZ"], scene_hormuz,
          "Iran claims a sixth tanker hit since Sunday as the US blockade "
          "enters day 130. Crews safe; oil trade on edge.")
    panel(cv, 519, 132, 481, 288, "LEAD 2 - CLIMATE",
          ["COP31 COLLAPSES"], scene_cop31,
          "Antalya talks end with no pact as the draft drops all mention "
          "of fossil fuels.")

    # Three mids.
    panel(cv, 24, 432, 312, 236, "UKRAINE",
          ["14 STILL MISSING", "IN KYIV"], scene_kyiv,
          "A drone flattens a block in Dymer; rescuers hunt for survivors.",
          head_scale=3)
    panel(cv, 356, 432, 312, 236, "INDONESIA",
          ["JAVA FACTORY:", "SEARCH RESUMES"], scene_java,
          "Search resumes at 7am after Saturday's blaze; dozens still "
          "missing.", head_scale=3)
    panel(cv, 688, 432, 312, 236, "UNITED NATIONS",
          ["TALKS ON KILLER", "ROBOTS GO ON"], scene_un_ai,
          "States agree to keep talking on killer robots - but no binding "
          "ban.", head_scale=3)

    # The day in brief: two columns of ten one-liners.
    draw_text(cv, 24, 682, "THE DAY IN BRIEF", 3, INK)
    draw_text(cv, 1024 - 24 - text_w("20 MORE STORIES", 2), 686,
              "20 MORE STORIES", 2, RED)
    cv.hline(24, 708, W - 48, INK, 2)
    for i, item in enumerate(BRIEFS):
        col = i // 10
        row = i % 10
        bx = 24 + col * 495
        by = 720 + row * 27
        cv.rect(bx, by + 2, 10, 10, RED)
        draw_text(cv, bx + 18, by, item, 2, INK)

    # Footer.
    cv.hline(24, 996, W - 48, INK, 2)
    draw_text_c(cv, W // 2, 1004,
                "ALL 25 STORIES VERIFIED AGAINST REPORTING OF 23 NOV 2026 - "
                "SOURCES IN STORIES.MD", 1, DARK_GREY)
    return cv


# ---------------------------------------------------------------- PNG

def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        return out + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_front_page()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print(f"wrote {path} ({cv.w}x{cv.h}, {size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
