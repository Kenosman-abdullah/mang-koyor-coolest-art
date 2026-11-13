"""Polishing the Moon.

Entry for the make.fun bounty "Make the coolest art".
A deterministic program (Python standard library only) that draws one
ukiyo-e-inspired picture and writes it to output/entry.png.

The picture riffs on the leaderboard's top three: a giant golden moon
over a great wave, tiny workers at work on a cosmic scale. The twist:
here the crew does not mend, knit or iron anything -- they polish the
moon, and the patch they have already polished shines the brightest.
"""

import math
import os
import random
import struct
import zlib
from hashlib import sha256

W = 1024
H = 1024
SKY_BOTTOM = 700
MOON = (512, 420)
MOON_R = 320

NAVY_DEEP = (8, 20, 38)
NAVY = (16, 42, 84)
NAVY_MID = (24, 62, 112)
TEAL = (31, 122, 140)
TEAL_DARK = (20, 88, 116)
SEA_TOP = (14, 38, 76)
CREAM = (242, 232, 213)
GOLD_LIGHT = (255, 233, 168)
GOLD = (232, 184, 75)
GOLD_DEEP = (192, 138, 46)
GOLD_DARK = (146, 98, 28)
RED = (179, 58, 43)
RED_SOFT = (196, 84, 58)
INK = (10, 12, 20)
LANTERN = (255, 178, 92)
WHITE = (255, 250, 230)

buf = bytearray(W * H * 3)
rng = random.Random(20261113)


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def set_px(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = col[0]
        buf[i + 1] = col[1]
        buf[i + 2] = col[2]


def blend_px(x, y, col, a):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        b = 1.0 - a
        buf[i] = int(buf[i] * b + col[0] * a)
        buf[i + 1] = int(buf[i + 1] * b + col[1] * a)
        buf[i + 2] = int(buf[i + 2] * b + col[2] * a)


def row_fill(y, col):
    i = y * W * 3
    buf[i:i + W * 3] = bytes(col) * W


def circle(cx, cy, r, col, a=1.0):
    r2 = r * r
    y0 = max(0, int(cy - r))
    y1 = min(H - 1, int(cy + r))
    for y in range(y0, y1 + 1):
        dy = y - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        x0 = max(0, int(cx - dx))
        x1 = min(W - 1, int(cx + dx))
        if a >= 1.0:
            for x in range(x0, x1 + 1):
                set_px(x, y, col)
        else:
            for x in range(x0, x1 + 1):
                blend_px(x, y, col, a)


def ellipse(cx, cy, rx, ry, col):
    for y in range(max(0, int(cy - ry)), min(H - 1, int(cy + ry)) + 1):
        t = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        for x in range(max(0, int(cx - dx)), min(W - 1, int(cx + dx)) + 1):
            set_px(x, y, col)


def line(x0, y0, x1, y1, col, width=1):
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy))) + 1
    r = width // 2
    for s in range(steps + 1):
        t = s / steps
        x = int(x0 + dx * t)
        y = int(y0 + dy * t)
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                if ox * ox + oy * oy <= r * r + r:
                    set_px(x + ox, y + oy, col)


def ring(cx, cy, r, thick, col, a=1.0, start=0.0, end=6.2832):
    steps = max(16, int(2 * math.pi * r / 2))
    for s in range(steps + 1):
        t = start + (end - start) * s / steps
        for k in range(-thick // 2, thick // 2 + 1):
            rr = r + k
            x = int(cx + rr * math.cos(t))
            y = int(cy + rr * math.sin(t))
            if a >= 1.0:
                set_px(x, y, col)
            else:
                blend_px(x, y, col, a)


def poly(points, col):
    ys = [p[1] for p in points]
    for y in range(max(0, int(min(ys))), min(H - 1, int(max(ys))) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[i])), min(W - 1, int(xs[i + 1])) + 1):
                set_px(x, y, col)


def sparkle(x, y, size, col):
    line(x - size, y, x + size, y, col, 1)
    line(x, y - size, x, y + size, col, 1)


def sky():
    for y in range(SKY_BOTTOM):
        row_fill(y, lerp(NAVY_DEEP, NAVY_MID, y / SKY_BOTTOM))
    for y in range(SKY_BOTTOM, H):
        row_fill(y, lerp(SEA_TOP, TEAL_DARK, (y - SKY_BOTTOM) / (H - SKY_BOTTOM)))


def stars():
    for _ in range(170):
        x = rng.randrange(0, W)
        y = rng.randrange(0, 660)
        dx = x - MOON[0]
        dy = y - MOON[1]
        if dx * dx + dy * dy < (MOON_R + 12) ** 2:
            continue
        bright = rng.random()
        if bright < 0.12:
            circle(x, y, 2, WHITE)
            sparkle(x, y, 5, WHITE)
        elif bright < 0.5:
            circle(x, y, 1, CREAM)
        else:
            set_px(x, y, GOLD_LIGHT)


def red_clouds():
    for cx, cy, rx, ry, col in [
        (140, 120, 185, 44, RED), (265, 92, 150, 36, RED_SOFT),
        (95, 185, 125, 30, RED), (905, 105, 175, 40, RED_SOFT),
        (800, 165, 130, 30, RED), (980, 180, 110, 28, RED),
    ]:
        ellipse(cx, cy, rx, ry, col)


def moon():
    cx, cy = MOON
    r = MOON_R
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
            d = math.sqrt((x - cx) ** 2 + dy * dy) / r
            set_px(x, y, lerp(GOLD_LIGHT, GOLD_DEEP, d ** 0.65))
    ring(cx, cy, r - 2, 5, GOLD_DARK)
    for rr in range(46, r - 8, 24):
        ring(cx, cy, rr, 2, GOLD_DARK, a=0.10)
    for _ in range(26):
        ang = rng.uniform(0, 6.2832)
        dist = rng.uniform(0, r * 0.85)
        bx = int(cx + dist * math.cos(ang))
        by = int(cy + dist * math.sin(ang))
        circle(bx, by, rng.randrange(10, 46), GOLD_DARK, a=rng.uniform(0.06, 0.16))
    for pts in [
        [(770, 620), (740, 585), (705, 570), (680, 540)],
        [(800, 520), (760, 500), (735, 465), (700, 450)],
        [(690, 700), (665, 660), (640, 645), (620, 610)],
    ]:
        for a, b in zip(pts, pts[1:]):
            line(a[0], a[1], b[0], b[1], GOLD_DARK, 3)
    ring(cx, cy, r - 30, 26, GOLD_LIGHT, a=0.55,
         start=math.radians(185), end=math.radians(280))
    for sx, sy in [(300, 190), (350, 150), (270, 260), (400, 130), (240, 330)]:
        sparkle(sx, sy, 6, WHITE)


def scaffolding():
    for x in (270, 330, 390, 450):
        line(x, 560, x, 745, INK, 3)
    for y in (600, 650, 700):
        line(250, y, 470, y, INK, 3)
    line(250, 745, 470, 560, INK, 2)
    line(470, 745, 250, 560, INK, 2)
    spots = [(300, 600), (360, 650), (420, 600), (330, 700), (400, 700)]
    for fx, fy in spots:
        circle(fx, fy - 20, 4, INK)
        line(fx, fy - 16, fx, fy - 6, INK, 3)
        line(fx, fy - 6, fx - 5, fy, INK, 2)
        line(fx, fy - 6, fx + 5, fy, INK, 2)
        tx, ty = fx + 55, fy - 80
        line(fx + 2, fy - 13, tx, ty, INK, 2)
        circle(tx, ty, 4, GOLD_LIGHT)


def sea():
    def band(y_base, amp, length, phase, col, thick=12):
        for x in range(W):
            y = int(y_base + amp * math.sin(2 * math.pi * x / length + phase))
            for k in range(-thick // 2, thick // 2 + 1):
                set_px(x, y + k, col)
            for k in range(-2, 3):
                set_px(x, y - thick // 2 + k, CREAM)
    band(770, 26, 300, 0.0, TEAL)
    band(850, 30, 240, 1.3, NAVY_MID)
    band(940, 34, 200, 2.6, (28, 100, 130))
    for _ in range(130):
        x = rng.randrange(0, W)
        y = rng.randrange(715, 1000)
        circle(x, y, rng.randrange(2, 5), CREAM, a=rng.uniform(0.25, 0.6))
    for rr in range(60, 180, 16):
        col = CREAM if (rr // 16) % 2 == 0 else NAVY_MID
        ring(895, 800, rr, 7, col, start=math.radians(-30), end=math.radians(205))
    for y in range(720, 1020, 6):
        wdt = 24 + int(18 * math.sin(y / 37.0))
        a = 0.10 + 0.10 * abs(math.sin(y / 23.0))
        for x in range(512 - wdt, 512 + wdt + 1):
            blend_px(x, y, GOLD, a)


def boat():
    poly([(272, 905), (332, 905), (318, 926), (284, 926)], RED)
    line(302, 905, 302, 868, INK, 3)
    circle(302, 864, 5, LANTERN)
    circle(302, 864, 12, LANTERN, a=0.35)
    circle(318, 897, 3, INK)
    line(318, 894, 318, 886, INK, 2)
    for y in range(930, 990, 5):
        for x in range(292, 313):
            blend_px(x, y, LANTERN, 0.12)


def write_png(path):
    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return png


def preview():
    chars = " .:-=+*#%@"
    print("preview 64x40 (brightness):")
    for row in range(40):
        out = []
        for col in range(64):
            x = col * W // 64 + 8
            y = row * H // 40 + 12
            i = (y * W + x) * 3
            lum = (buf[i] * 30 + buf[i + 1] * 59 + buf[i + 2] * 11) // 100
            out.append(chars[min(9, lum * 10 // 256)])
        print("".join(out))


def main():
    sky()
    stars()
    red_clouds()
    moon()
    scaffolding()
    sea()
    boat()
    png = write_png("output/entry.png")
    print("PNG bytes:", len(png))
    print("SHA256:", sha256(png).hexdigest())
    print("limit: 1048576 bytes, 1024x1024")
    preview()


if __name__ == "__main__":
    main()
