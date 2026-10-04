"""Romantic garden picnic animation, rendered with Pillow and imageio-ffmpeg."""

from __future__ import annotations

import math
import random
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont


CONFIG = {
    "edwar": {"name": "Edwar", "skin": "#d6a184", "hair": "#45342f", "clothes": "#65775c", "hair_style": "short"},
    "partner": {"name": "Hary", "skin": "#e2b097", "hair": "#49352f", "clothes": "#ad7183", "hair_style": "long"},
    "tommy": {"fur": "#f4f0e8", "markings": "#c9bfb4", "eyes": "#9d9562"},
    "colors": {
        "sky_top": "#45465e", "sky_horizon": "#efa181", "garden": "#334b40",
        "flowers": ["#f6c77e", "#e88891", "#e8d7ac", "#b6a6ca", "#b6c0a1"],
        "blanket": "#985b70", "light": "#ffd78c",
    },
    "duration_seconds": 54,
    "fps": 24,
    "landscape_size": (1280, 720),
    "portrait_size": (720, 1280),
    "make_gif_preview": True,
    "gif_size": (400, 225),
    "gif_fps": 5,
    "gif_colors": 64,
}

ROOT = Path(__file__).resolve().parent
TAU = math.tau
W, H = CONFIG["landscape_size"]
PICNIC_START = 4.0
WALK_START = 38.0
CLOSING_START = 46.0
FONT_CACHE = {}


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def mix(a: str, b: str, amount: float) -> tuple[int, int, int]:
    first, second = rgb(a), rgb(b)
    return tuple(round(x + (y - x) * amount) for x, y in zip(first, second))


def cubic(p0, p1, p2, p3, count=32):
    points = []
    for index in range(count + 1):
        t = index / count
        u = 1 - t
        points.append((
            u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
        ))
    return points


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def get_font(size: int, script: bool = False):
    key = (size, script)
    if key not in FONT_CACHE:
        folder = Path("C:/Windows/Fonts")
        names = ("segoesc.ttf", "georgiai.ttf", "georgia.ttf", "arial.ttf") if script else ("georgia.ttf", "segoeui.ttf", "arial.ttf")
        for name in names:
            try:
                FONT_CACHE[key] = ImageFont.truetype(str(folder / name), size)
                break
            except OSError:
                continue
        else:
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def tinted(image: Image.Image, color: str, alpha: int) -> Image.Image:
    overlay = Image.new("RGBA", image.size, (*rgb(color), alpha))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def centered_text(draw, text: str, y: int, font, fill, **kwargs):
    draw.text((W // 2, y), text, font=font, fill=fill, anchor="mm", **kwargs)


def flower(draw, x, y, size, color, phase=0.0):
    for petal in range(7):
        angle = TAU * petal / 7 + phase
        px = x + math.cos(angle) * size * 0.58
        py = y + math.sin(angle) * size * 0.58
        radius = size * 0.39
        draw.ellipse((px - radius, py - radius * 0.72, px + radius, py + radius * 0.72), fill=color)
    draw.ellipse((x - size * 0.23, y - size * 0.23, x + size * 0.23, y + size * 0.23), fill="#8e633c")
    draw.ellipse((x - size * 0.11, y - size * 0.11, x + size * 0.11, y + size * 0.11), fill="#f5d58d")


def leaf(draw, x, y, length, angle, color):
    dx, dy = math.cos(angle) * length, math.sin(angle) * length
    px, py = -math.sin(angle) * length * 0.32, math.cos(angle) * length * 0.32
    draw.polygon([(x, y), (x + dx * 0.48 + px, y + dy * 0.48 + py), (x + dx, y + dy),
                  (x + dx * 0.48 - px, y + dy * 0.48 - py)], fill=color)
    draw.line((x, y, x + dx, y + dy), fill=mix(color, "#d2c59a", 0.30), width=1)


def draw_background():
    image = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(image)
    top, horizon = CONFIG["colors"]["sky_top"], CONFIG["colors"]["sky_horizon"]
    for y in range(H):
        if y < 390:
            color = mix(top, horizon, smoothstep(y / 390))
        else:
            color = mix(horizon, "#65765a", smoothstep((y - 390) / 250))
        draw.line((0, y, W, y), fill=color)

    for radius in range(190, 22, -8):
        shade = mix("#d77d68", "#ffe0a2", 1 - radius / 210)
        draw.ellipse((674 - radius, 267 - radius, 674 + radius, 267 + radius), fill=shade)
    draw.ellipse((619, 211, 729, 321), fill="#ffd49a")
    draw.polygon([(0, 390), (135, 339), (270, 382), (440, 332), (610, 384),
                  (790, 338), (1000, 382), (1160, 326), (1280, 367), (1280, 482), (0, 482)], fill="#596956")
    draw.polygon([(0, 435), (170, 385), (350, 429), (535, 375), (760, 438),
                  (940, 384), (1110, 433), (1280, 390), (1280, 515), (0, 515)], fill="#485d4c")
    draw.polygon([(590, 433), (700, 433), (875, 720), (395, 720)], fill="#88745f")
    draw.polygon([(626, 440), (677, 440), (785, 720), (492, 720)], fill="#a38a6c")

    draw.line(cubic((130, 506), (105, 322), (179, 223), (353, 211)), fill="#493f35", width=18, joint="curve")
    draw.line(cubic((1150, 507), (1175, 321), (1091, 223), (927, 211)), fill="#493f35", width=18, joint="curve")
    draw.line(cubic((345, 214), (490, 177), (780, 177), (935, 214)), fill="#493f35", width=16, joint="curve")
    rng = random.Random(84)
    for side in (0, 1):
        for index in range(38):
            t = index / 37
            x = (160 + 805 * t) if side == 0 else (1120 - 805 * t)
            y = 225 + 80 * math.sin(t * math.pi) + rng.uniform(-16, 18)
            length = rng.uniform(16, 35)
            leaf(draw, x, y, length, rng.uniform(-2.8, 2.8), rng.choice(["#405944", "#536d50", "#647757", "#71815e"]))
    for index in range(15):
        x = 365 + index * 39
        y = 202 - 18 * math.sin(index * 0.38)
        leaf(draw, x, y, 28, math.sin(index) * 1.5, "#59704f")

    # Rose clusters and hanging wisteria give the arbor a layered silhouette.
    for index in range(17):
        x = 355 + index * 35
        y = 211 - 17 * math.sin(index * .38)
        flower(draw, x, y, 13 + (index % 3) * 2, ["#ce8494", "#e9b6a7", "#b59bc7"][index % 3], index * .3)
    for index in range(11):
        x = 403 + index * 46
        drop = 39 + (index * 17) % 48
        draw.line(cubic((x, 220), (x - 8, 245), (x + 7, 246 + drop), (x + 1, 247 + drop), 10),
                  fill="#65734f", width=2)
        for bloom in range(4):
            flower(draw, x + (bloom % 2) * 4, 252 + drop * bloom / 4, 6, ["#baa3d0", "#e6b2bd"][index % 2], bloom * .4)

    cable = cubic((355, 213), (500, 273), (790, 273), (925, 213), 48)
    draw.line(cable, fill="#55483b", width=3)
    for index in range(13):
        x, y = cable[round(index * (len(cable) - 1) / 12)]
        draw.line((x, y, x, y + 12), fill="#5d4b3a", width=2)
        draw.ellipse((x - 6, y + 10, x + 6, y + 22), fill="#ffe2a2")
        draw.ellipse((x - 2, y + 12, x + 2, y + 18), fill="#fff2c7")

    for y, count, seed in ((475, 56, 10), (535, 72, 15), (625, 94, 21)):
        rng = random.Random(seed)
        for _ in range(count):
            x = rng.randrange(-25, W + 25)
            radius = rng.randrange(19, 53)
            cy = y + rng.randrange(-radius // 2, radius // 2)
            color = rng.choice(["#344b3d", "#3d5845", "#4d6549", "#5b704e", "#697954"])
            draw.ellipse((x - radius, cy - radius, x + radius, cy + radius), fill=color)
            if rng.random() < 0.24:
                draw.ellipse((x - radius * .46, cy - radius * .55, x - radius * .1, cy - radius * .19), fill="#81906a")

    palette = CONFIG["colors"]["flowers"]
    rng = random.Random(202)
    for _ in range(250):
        x = rng.randrange(W)
        y = rng.randrange(430, 710)
        if 414 < x < 880 and 520 < y < 690 and rng.random() < .83:
            continue
        height = rng.randrange(13, 54)
        end_x = x + rng.randrange(-28, 29)
        color = rng.choice(["#425b41", "#526846", "#657750", "#788458"])
        draw.line(cubic((x, y + 34), (x - 12, y + 10), (end_x + 10, y + 10), (end_x, y - height), 8), fill=color, width=2)
        if rng.random() < .52:
            leaf(draw, x + 2, y + 16, rng.randrange(10, 22), rng.uniform(-2.8, -.4), "#738359")
        if rng.random() < .78:
            flower(draw, end_x, y - height, rng.randrange(5, 12), rng.choice(palette), rng.random())

    # Foreground flower beds of different scales create a hand-painted frame.
    for index in range(58):
        side = -1 if index % 2 == 0 else 1
        x = rng.choice((rng.randrange(8, 250), rng.randrange(1030, 1272)))
        y = rng.randrange(552, 707)
        stem_height = rng.randrange(30, 100)
        sway = 7 * math.sin(index * 1.6)
        color = rng.choice(palette)
        draw.line(cubic((x, y + 18), (x - 13, y - 4), (x + sway + 11, y - stem_height * .5),
                        (x + sway, y - stem_height), 10), fill=rng.choice(["#536b49", "#70805a", "#83906a"]), width=3)
        leaf(draw, x - 1, y - stem_height * .38, rng.randrange(15, 27), -1.0, "#738459")
        flower(draw, x + sway, y - stem_height, rng.randrange(9, 17), color, index * .27)

    for index, (x, y, size, color) in enumerate(((55, 675, 25, "#d8899a"), (1211, 681, 27, "#c3a1cb"),
                                                  (164, 630, 17, "#eac087"), (1102, 642, 19, "#e3a2a1"))):
        flower(draw, x, y, size, color, index * .3)

    for _ in range(1100):
        x = rng.randrange(W)
        y = rng.randrange(435, H)
        if 380 < x < 895 and 520 < y < 710:
            continue
        shade = rng.choice(["#81906a", "#263e36", "#9d8b67", "#596d4b"])
        draw.line((x, y, x + rng.randrange(2, 9), y - rng.randrange(1, 4)), fill=shade, width=1)
    return image


def draw_picnic(draw):
    # Woven picnic cloth with clipped tartan lines.
    blanket = [(399, 573), (822, 573), (891, 720), (346, 720)]
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(blanket, fill=255)
    cloth = Image.new("RGB", (W, H), CONFIG["colors"]["blanket"])
    texture = ImageDraw.Draw(cloth)
    texture.polygon(blanket, fill=CONFIG["colors"]["blanket"])
    for x in range(325, 920, 35):
        texture.line((x, 565, x + 55, 725), fill="#d28c79", width=5)
    for y in range(586, 740, 28):
        texture.line((330, y, 910, y - 8), fill="#713f43", width=4)
    draw._image.paste(cloth, (0, 0), mask)
    draw.polygon(blanket, outline="#e8c49d", width=3)

    draw.rounded_rectangle((824, 535, 934, 618), radius=13, fill="#a9754d", outline="#e1bd82", width=4)
    draw.arc((835, 489, 925, 584), 180, 360, fill="#d6b177", width=8)
    for y in (555, 573, 591, 608):
        draw.line((829, y, 930, y - 2), fill="#d3a66a", width=3)
    draw.ellipse((849, 527, 906, 555), fill="#eee0c5", outline="#b99f7c", width=2)
    draw.ellipse((861, 525, 890, 546), fill="#ca6f58")
    draw.ellipse((888, 527, 911, 548), fill="#dda451")
    draw.ellipse((477, 610, 512, 637), fill="#d89158", outline="#f2c38b", width=2)
    draw.ellipse((523, 618, 555, 643), fill="#b8534e", outline="#e6a18a", width=2)
    draw.ellipse((759, 608, 800, 640), fill="#8d9a58", outline="#c3c183", width=2)

    draw.rounded_rectangle((452, 541, 477, 601), radius=8, fill="#546d67", outline="#d5c5a4", width=2)
    draw.rectangle((456, 537, 473, 546), fill="#c5a873")
    for x in (591, 728):
        draw.ellipse((x - 18, 548, x + 18, 560), fill="#ede2cd", outline="#9e8164", width=2)
        draw.polygon([(x - 15, 555), (x + 15, 555), (x + 10, 580), (x - 10, 580)], fill="#d8c9b1", outline="#9e8164")
        draw.arc((x + 8, 558, x + 29, 577), 270, 95, fill="#9e8164", width=3)

    # A proper little spread: tart, biscuits, berries, lemonade, and flowers.
    draw.ellipse((622, 589, 724, 627), fill="#f4e4c8", outline="#a98669", width=3)
    draw.polygon([(648, 582), (697, 582), (713, 610), (635, 610)], fill="#d98774", outline="#9e695c")
    draw.rectangle((642, 600, 706, 609), fill="#e6be81")
    for berry_x, berry_y in ((660, 589), (677, 584), (694, 590)):
        draw.ellipse((berry_x - 5, berry_y - 5, berry_x + 5, berry_y + 5), fill="#a84359")
        draw.ellipse((berry_x - 2, berry_y - 7, berry_x + 2, berry_y - 3), fill="#718153")
    for cookie_x, cookie_y in ((573, 620), (590, 625), (608, 619)):
        draw.ellipse((cookie_x - 10, cookie_y - 6, cookie_x + 10, cookie_y + 6), fill="#d9a56c", outline="#a97b54", width=2)
        for crumb_x in (-4, 3):
            draw.ellipse((cookie_x + crumb_x - 1, cookie_y - 1, cookie_x + crumb_x + 1, cookie_y + 1), fill="#815b48")
    draw.rounded_rectangle((763, 542, 788, 596), radius=8, fill="#d5a974", outline="#f1d6a5", width=2)
    draw.rectangle((769, 534, 782, 545), fill="#e5cb98")
    draw.line((768, 556, 783, 556), fill="#faf0d7", width=3)
    draw.ellipse((418, 565, 442, 579), fill="#b5856c", outline="#e6c9a1", width=2)
    for bloom_index, bloom_color in enumerate(("#d48c9a", "#bea2cf", "#edc386")):
        bx = 423 + bloom_index * 8
        draw.line((430, 569, bx, 548 + bloom_index * 2), fill="#687a55", width=2)
        flower(draw, bx, 546 + bloom_index * 2, 6, bloom_color, bloom_index)


def draw_person(draw, person, x, head_y, phase, lean=0, talking=False):
    skin, hair, shirt = person["skin"], person["hair"], person["clothes"]
    breath = math.sin(phase) * 2.0
    torso_y = head_y + 45 + breath
    draw.ellipse((x - 60, torso_y + 74, x + 56, torso_y + 136), fill="#514841")
    draw.ellipse((x - 69, torso_y + 99, x + 12, torso_y + 135), fill="#665347")
    draw.ellipse((x - 9, torso_y + 98, x + 75, torso_y + 134), fill="#665347")
    draw.rounded_rectangle((x - 42, torso_y, x + 43, torso_y + 93), radius=29, fill=shirt, outline=mix(shirt, "#ead0ab", .32), width=2)
    draw.ellipse((x - 50, torso_y + 4, x - 15, torso_y + 48), fill=shirt)
    draw.ellipse((x + 15, torso_y + 3, x + 51, torso_y + 48), fill=shirt)
    neck_x = x + lean
    if person.get("hair_style") == "long":
        draw.rounded_rectangle((neck_x - 34, head_y + 3, neck_x - 23, torso_y + 57), radius=7, fill=hair)
        draw.rounded_rectangle((neck_x + 23, head_y + 3, neck_x + 34, torso_y + 57), radius=7, fill=hair)

    hand_x = x + (44 if x < 630 else -44)
    draw.line(cubic((x + (25 if x < 630 else -25), torso_y + 22),
                    (x + (47 if x < 630 else -47), torso_y + 28),
                    (hand_x, torso_y + 57), (hand_x, torso_y + 68), 14), fill=skin, width=13, joint="curve")
    draw.ellipse((hand_x - 7, torso_y + 62, hand_x + 7, torso_y + 75), fill=skin)
    draw.rounded_rectangle((neck_x - 12, head_y + 26, neck_x + 12, head_y + 55), radius=7, fill=skin)
    face = (neck_x - 29, head_y - 14, neck_x + 29, head_y + 51)
    draw.ellipse(face, fill=skin, outline=mix(skin, "#553c35", .22), width=2)
    # Editable hair silhouettes distinguish the two illustrated figures.
    draw.pieslice((neck_x - 32, head_y - 23, neck_x + 32, head_y + 28), 180, 360, fill=hair)
    if person.get("hair_style") == "long":
        draw.arc((neck_x - 20, head_y - 17, neck_x + 25, head_y + 12), 195, 345, fill=mix(hair, "#c3a077", .28), width=2)
    else:
        draw.ellipse((neck_x - 31, head_y - 3, neck_x - 18, head_y + 31), fill=hair)
        draw.arc((neck_x - 21, head_y - 16, neck_x + 24, head_y + 12), 190, 345, fill=mix(hair, "#c3a077", .28), width=2)
    eye_y = head_y + 19
    for eye_x in (neck_x - 10, neck_x + 10):
        draw.ellipse((eye_x - 2, eye_y - 2, eye_x + 2, eye_y + 2), fill="#473c36")
    draw.line((neck_x, eye_y + 1, neck_x - 2, eye_y + 7), fill=mix(skin, "#6c4739", .42), width=2)
    if talking and math.sin(phase * 5) > .05:
        draw.ellipse((neck_x - 4, head_y + 29, neck_x + 4, head_y + 35), fill="#925d56")
    else:
        draw.arc((neck_x - 8, head_y + 26, neck_x + 8, head_y + 37), 5, 165, fill="#935e50", width=2)
    draw.ellipse((neck_x - 20, head_y + 24, neck_x - 12, head_y + 28), fill="#d8887d")
    draw.ellipse((neck_x + 12, head_y + 24, neck_x + 20, head_y + 28), fill="#d8887d")


def draw_cat(draw, time, duration, x=853, y=561):
    phase = time / duration
    play = smoothstep((phase - .015) / .055) * (1 - smoothstep((phase - .15) / .06))
    curled = 1 - play
    fur = CONFIG["tommy"]["fur"]
    mark = CONFIG["tommy"]["markings"]

    lift = -13 * play + 3 * math.sin(time * TAU / duration)
    draw.ellipse((x - 40, y - 13 + lift, x + 45, y + 39), fill=fur, outline=mix(fur, "#4b392e", .35), width=2)
    draw.ellipse((x - 27, y - 28 + lift, x + 20, y + 17 + lift), fill=fur, outline=mix(fur, "#4b392e", .35), width=2)
    draw.polygon([(x - 22, y - 19 + lift), (x - 19, y - 49 + lift), (x - 2, y - 29 + lift)], fill=fur)
    draw.polygon([(x + 1, y - 28 + lift), (x + 20, y - 47 + lift), (x + 20, y - 17 + lift)], fill=fur)
    draw.polygon([(x - 18, y - 24 + lift), (x - 17, y - 41 + lift), (x - 7, y - 28 + lift)], fill="#c77e76")
    draw.polygon([(x + 7, y - 27 + lift), (x + 17, y - 39 + lift), (x + 16, y - 24 + lift)], fill="#c77e76")
    if play > .35:
        draw.ellipse((x - 19, y - 12 + lift, x - 15, y - 7 + lift), fill=CONFIG["tommy"]["eyes"])
        draw.ellipse((x + 8, y - 12 + lift, x + 12, y - 7 + lift), fill=CONFIG["tommy"]["eyes"])
    else:
        draw.arc((x - 21, y - 14 + lift, x - 12, y - 7 + lift), 200, 340, fill="#65473b", width=2)
        draw.arc((x + 5, y - 14 + lift, x + 14, y - 7 + lift), 200, 340, fill="#65473b", width=2)
    draw.ellipse((x - 7, y - 3 + lift, x + 1, y + 3 + lift), fill="#a96865")
    draw.arc((x - 10, y - 1 + lift, x + 2, y + 10 + lift), 5, 165, fill="#65473b", width=1)
    for whisker in range(2):
        yy = y + whisker * 5 + lift
        draw.line((x - 9, yy, x - 34, yy - 5), fill="#e4d2b7", width=1)
        draw.line((x + 1, yy, x + 25, yy - 5), fill="#e4d2b7", width=1)
    for stripe in range(3):
        sx = x - 24 + stripe * 13
        draw.arc((sx, y + 4 + lift, sx + 27, y + 27 + lift), 185, 280, fill=mark, width=3)

    tail_sway = math.sin(time * TAU / duration) * 7
    tip = (x - 61 + 24 * play + tail_sway, y - 10 - 42 * play + 10 * curled)
    tail = cubic((x - 33, y + 14), (x - 73, y + 24 - 20 * play),
                 (x - 68 - 14 * play, y - 22 - 46 * play), tip, 24)
    draw.line(tail, fill=fur, width=13, joint="curve")
    draw.line(tail, fill=mix(fur, "#f4d6ae", .28), width=3, joint="curve")
    # Ribbon, with a looped bow that drifts a few pixels in a closed orbit.
    ribbon_x = x - 114 + 15 * math.sin(TAU * phase)
    ribbon_y = y + 3 + 9 * math.cos(TAU * phase)
    draw.line(cubic((ribbon_x - 20, ribbon_y + 18), (ribbon_x + 4, ribbon_y - 20),
                    (x - 76, y + 4), (x - 61, y + 11), 20), fill="#dc8076", width=3)
    bow_y = ribbon_y - 18 * play
    draw.ellipse((ribbon_x - 13, bow_y - 6, ribbon_x, bow_y + 6), outline="#e9a08c", width=4)
    draw.ellipse((ribbon_x + 1, bow_y - 6, ribbon_x + 14, bow_y + 6), outline="#e9a08c", width=4)
    draw.ellipse((ribbon_x - 2, bow_y - 3, ribbon_x + 4, bow_y + 3), fill="#f3bc91")
    # A pale chest patch is visible even when Tommy settles down.
    draw.ellipse((x - 12, y + 9, x + 20, y + 32), fill=mix(fur, "#f5dfbd", .57))
    draw.arc((x - 24, y - 13 + lift, x + 17, y + 22 + lift), 5, 172, fill="#b97b82", width=5)
    draw.rounded_rectangle((x - 19, y + 8 + lift, x + 27, y + 25 + lift), radius=5,
                           fill="#e9d7b6", outline="#ad777b", width=1)
    draw.text((x + 4, y + 16 + lift), "Tommy", font=get_font(7), fill="#6f5550", anchor="mm")
    draw.arc((x - 24, y - 13 + lift, x + 17, y + 22 + lift), 5, 172, fill="#b97b82", width=5)
    draw.ellipse((x - 7, y + 9 + lift, x + 7, y + 22 + lift), fill="#e9d7b6", outline="#ad777b", width=1)
    draw.text((x, y + 15 + lift), "T", font=get_font(8), fill="#6f5550", anchor="mm")


def draw_motion(draw, time, duration):
    phase = time / duration
   
    for index in range(11):
        offset = index / 11
        angle = TAU * (phase + offset)
        x = 420 + 380 * ((offset * 1.71) % 1) + 20 * math.sin(angle)
        y = 344 + 95 * math.sin(angle + offset * 4)
        size = 3 + (index % 3)
        draw.ellipse((x - size, y - size * .55, x + size, y + size * .55), fill="#f2b8a0")
        draw.line((x - size, y, x + size, y + 2), fill="#f5d2ad", width=1)

  
    for index in range(17):
        seed = index * 2.399
        x = 115 + (index * 193) % 1050 + 12 * math.sin(TAU * phase + seed)
        y = 309 + (index * 61) % 285 + 10 * math.cos(TAU * phase + seed)
        glow = .5 + .5 * math.sin(TAU * phase + seed)
        radius = 2 + int(glow * 2)
        draw.ellipse((x - radius * 3, y - radius * 3, x + radius * 3, y + radius * 3), fill="#687960")
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#ffe7a6")

    cable = cubic((355, 213), (500, 273), (790, 273), (925, 213), 48)
    for index in range(13):
        x, y = cable[round(index * (len(cable) - 1) / 12)]
        pulse = .45 + .55 * (.5 + .5 * math.sin(TAU * phase + index * 1.7))
        draw.ellipse((x - 5, y + 12, x + 5, y + 22), fill=mix("#a47763", "#fff1bb", pulse))


    for index, (x, y, color) in enumerate(((235, 616, "#d6a1c1"), (1037, 605, "#edb2a0"), (302, 520, "#c2aed2"), (978, 534, "#f2cd89"))):
        sway = 5 * math.sin(TAU * phase + index * 1.9)
        top_x = x + sway
        draw.line(cubic((x, y + 24), (x - 7, y + 3), (top_x + 8, y + 2), (top_x, y - 23), 8), fill="#71815e", width=2)
        leaf(draw, x, y + 7, 17, -1.0 + .10 * math.sin(TAU * phase + index), "#84906a")
        flower(draw, top_x, y - 25, 8, color, phase + index)


    for cup_x in (591, 728):
        for wisp in range(3):
            angle = TAU * phase + wisp * 2.1 + cup_x * .01
            points = cubic((cup_x + wisp * 5 - 5, 546),
                           (cup_x + 11 * math.sin(angle), 536),
                           (cup_x - 10 * math.cos(angle), 528),
                           (cup_x + 3 * math.sin(angle), 516), 12)
            draw.line(points, fill="#f2ddc0", width=2)


def draw_sparkle(draw, x, y, radius, color):
    draw.line((x - radius, y, x + radius, y), fill=color, width=2)
    draw.line((x, y - radius, x, y + radius), fill=color, width=2)
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill="#fff0ce")


def draw_cover(time: float, soft_background: Image.Image, vertical: bool = False) -> Image.Image:
    image = tinted(soft_background, "#292c45", 92)
    draw = ImageDraw.Draw(image)
    panel_width = 405 if vertical else 750
    box = (W // 2 - panel_width // 2, 133, W // 2 + panel_width // 2, 589)
    draw.rounded_rectangle((box[0] + 7, box[1] + 9, box[2] + 7, box[3] + 9), radius=25, fill="#292737")
    draw.rounded_rectangle(box, radius=24, fill="#ecddc7", outline="#f5d99f", width=4)
    draw.rounded_rectangle((box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10), radius=18, outline="#ba876f", width=2)
    centered_text(draw, "UN PEQUENO CUENTO DE AMOR", 215, get_font(16), "#806356")
    centered_text(draw, "Edwar y Hary", 323, get_font(42 if vertical else 60, script=True), "#7d4e55",
                  stroke_width=1, stroke_fill="#e8cbb1")
    flower(draw, 640, 393, 14, "#d18d91", time * .3)
    draw.line((543, 393, 616, 393), fill="#c59a79", width=2)
    draw.line((664, 393, 737, 393), fill="#c59a79", width=2)
    centered_text(draw, "3 meses", 456, get_font(32 if vertical else 38), "#65705a")
    centered_text(draw, "juntos en nuestra historia", 517, get_font(17, script=True), "#906e62")
    for index, (x, y) in enumerate(((box[0] + 30, 179), (box[2] - 30, 179), (box[0] + 34, 540), (box[2] - 34, 540))):
        flower(draw, x, y, 10, ("#d58b8e", "#ba9bc2", "#e5bb78", "#9ca982")[index], time + index)
    for index in range(7):
        angle = TAU * (time / 6 + index / 7)
        sx = 640 + math.cos(angle) * (panel_width * .48)
        sy = 362 + math.sin(angle) * 290
        draw_sparkle(draw, round(sx), round(sy), 5, mix("#c4a982", "#fff1c2", .5 + .5 * math.sin(angle * 3)))
    return image


def draw_closing(time: float, soft_background: Image.Image, vertical: bool = False) -> Image.Image:
    image = tinted(soft_background, "#30273c", 105)
    draw = ImageDraw.Draw(image)
    panel_width = 410 if vertical else 910
    box = (W // 2 - panel_width // 2, 194, W // 2 + panel_width // 2, 535)
    draw.rounded_rectangle((box[0] + 7, box[1] + 8, box[2] + 7, box[3] + 8), radius=24, fill="#282336")
    draw.rounded_rectangle(box, radius=23, fill="#ecddc7", outline="#f0cb91", width=4)
    draw.rounded_rectangle((box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10), radius=17, outline="#b98a72", width=2)
    if vertical:
        closing_lines = ("Con mucho amor por", "nuestros 3 meses — Edwar")
        line_y = (302, 356)
        size = 25
    else:
        closing_lines = ("Con mucho amor por nuestros 3 meses — Edwar",)
        line_y = (322,)
        size = 31
    for text, y in zip(closing_lines, line_y):
        centered_text(draw, text, y, get_font(size, script=True), "#754950", stroke_width=1, stroke_fill="#ead4bb")
    centered_text(draw, "Te amo", 424 if not vertical else 445, get_font(49 if vertical else 57, script=True), "#ad6476")
    for index in range(9):
        angle = TAU * (time / 7 + index / 9)
        sx = 640 + math.cos(angle) * (panel_width * .55)
        sy = 365 + math.sin(angle) * 270
        if 0 <= sx < W:
            draw_sparkle(draw, round(sx), round(sy), 4, "#f4d9a3")
    return image


def draw_name_label(draw, x: int, y: int, name: str):
    draw.rounded_rectangle((x - 48, y - 13, x + 48, y + 13), radius=8,
                           fill="#394a43", outline="#e5c69a", width=2)
    draw.text((x, y), name, font=get_font(14), fill="#fff0d8", anchor="mm")


def draw_heart(draw, x: float, y: float, size: float, color: str):
    half = size / 2
    left = cubic((x, y + half), (x - size * .28, y + size * .25),
                 (x - size * .62, y - size * .05), (x - half, y - half * .35), 10)
    right = cubic((x - half, y - half * .35), (x - half, y - size * .85),
                  (x - size * .12, y - size * .78), (x, y - size * .48), 10)
    other = cubic((x, y - size * .48), (x + size * .12, y - size * .78),
                  (x + half, y - size * .85), (x + half, y - half * .35), 10)
    final = cubic((x + half, y - half * .35), (x + size * .62, y - size * .05),
                  (x + size * .28, y + half * .25), (x, y + half), 10)
    points = left + right[1:] + other[1:] + final[1:]
    draw.polygon(points, fill=color)
    draw.line(points + [points[0]], fill=mix(color, "#fff0d8", .3), width=1, joint="curve")


def draw_romantic_hearts(draw, time: float, intensity: float = 1.0):
    palette = ("#d77c87", "#e59b9a", "#c49ac2", "#f0bf8e", "#e5aeb2")
    for index in range(18):
        seed = index * 2.399
        orbit = TAU * (time / 13 + index / 18)
        x = 54 + (index * 227) % 1172 + 19 * math.sin(orbit + seed)
        y = 255 + (index * 83) % 365 + 14 * math.cos(orbit * .7 + seed)
        # Keep a quiet oval around the faces and subtitles.
        if 500 < x < 760 and 330 < y < 445:
            continue
        size = (13 + index % 6) * intensity
        draw_heart(draw, x, y, size, palette[index % len(palette)])

    if intensity > 1.2:
        for index in range(9):
            orbit = TAU * (time * .08 + index / 9)
            x = 625 + math.cos(orbit) * 120
            y = 450 + math.sin(orbit) * 110
            draw_heart(draw, x, y, 15 + index % 3 * 2, palette[(index + 2) % len(palette)])


def draw_dialogue(draw, text: str):
    box = (279, 223, 1001, 299)
    draw.rounded_rectangle((box[0] + 3, box[1] + 4, box[2] + 3, box[3] + 4), radius=18, fill="#34323d")
    draw.rounded_rectangle(box, radius=18, fill="#f0dfc9", outline="#e6c294", width=3)
    draw.text((W // 2, 240), "EDWAR", font=get_font(12), fill="#a5656e", anchor="mm")
    draw.text((W // 2, 271), text, font=get_font(23, script=True), fill="#51474a", anchor="mm")


def draw_hand_gesture(draw, mode: str, time: float):
    if mode == "hands":
        draw.line(cubic((595, 481), (610, 487), (618, 485), (634, 487), 14), fill="#d6a184", width=12, joint="curve")
        draw.line(cubic((685, 481), (666, 487), (654, 485), (640, 487), 14), fill="#e2b097", width=12, joint="curve")
        draw.ellipse((628, 477, 647, 495), fill="#e4b49b", outline="#f3d9bd", width=2)
        draw.ellipse((636, 480, 651, 493), fill="#d49b83", outline="#f3d9bd", width=1)
    elif mode in ("hug", "kiss"):
        draw.line(cubic((591, 453), (615, 433), (654, 433), (682, 453), 18), fill="#e2b097", width=12, joint="curve")
        draw.line(cubic((682, 468), (662, 481), (610, 481), (590, 466), 18), fill="#d6a184", width=11, joint="curve")
        if mode == "kiss":
            draw.ellipse((621, 391, 637, 399), fill="#a65e65")
            draw_heart(draw, 641, 350 + 3 * math.sin(time * 3), 19, "#d77c87")


def draw_picnic_scene(time: float, background: Image.Image):
    frame = background.copy()
    draw = ImageDraw.Draw(frame)
    draw_picnic(draw)

    hands = smoothstep((time - 10) / 1.8) * (1 - smoothstep((time - 19) / 1.8))
    hug = smoothstep((time - 19) / 1.8) * (1 - smoothstep((time - 28) / 1.8))
    kiss = smoothstep((time - 28) / 1.5) * (1 - smoothstep((time - 34) / 1.7))
    closeness = max(hug, kiss)
    edwar_x = round(563 + 4 * closeness)
    hary_x = round(686 - 4 * closeness)
    lean = round(28 * closeness)
    breath = math.sin(time * 1.2) * 2
    talking = 2 <= time < 7.5 or 10 <= time < 16 or 19 <= time < 23.5
    draw_person(draw, CONFIG["edwar"], edwar_x, round(365 + breath), time * .7, lean, talking)
    draw_person(draw, CONFIG["partner"], hary_x, round(365 - breath), time * .7 + .8, -lean)
    draw_name_label(draw, edwar_x, 314, CONFIG["edwar"]["name"])
    draw_name_label(draw, hary_x, 314, CONFIG["partner"]["name"])
    draw_cat(draw, time, 42)

    if hands > .15:
        draw_hand_gesture(draw, "hands", time)
    if hug > .2:
        draw_hand_gesture(draw, "hug", time)
    if kiss > .45:
        draw_hand_gesture(draw, "kiss", time)

    subtitle = None
    if 2 <= time < 7.5:
        subtitle = "Hary, eres lo mejor que me ha pasado."
    elif 10 <= time < 16:
        subtitle = "Quiero cuidarte siempre."
    elif 19 <= time < 23.5:
        subtitle = "Te amo."
    if subtitle:
        draw_dialogue(draw, subtitle)

    draw_motion(draw, time, 42)
    intensity = 1.45 if hug > .35 or kiss > .35 else 1.0
    draw_romantic_hearts(draw, time, intensity)
    initials = f"{CONFIG['edwar']['name'][:1]}  +  {CONFIG['partner']['name'][:1]}"
    draw.text((604, 681), initials, fill="#f2d2b1", anchor="mm", stroke_width=0)
    return frame


def draw_walking_person(draw, person, x: float, y: float, phase: float, side: int, holding: bool):
    skin, hair, shirt = person["skin"], person["hair"], person["clothes"]
    stride = math.sin(phase * 4 + side * .4)
    head_x, head_y = round(x), round(y)
    draw.ellipse((head_x - 28, head_y - 34, head_x + 28, head_y + 31), fill=skin, outline="#684d45", width=2)
    draw.pieslice((head_x - 31, head_y - 42, head_x + 31, head_y + 18), 180, 360, fill=hair)
    if person.get("hair_style") == "long":
        draw.rounded_rectangle((head_x - 31, head_y - 13, head_x - 21, head_y + 74), radius=6, fill=hair)
        draw.rounded_rectangle((head_x + 21, head_y - 13, head_x + 31, head_y + 75), radius=6, fill=hair)
    else:
        draw.ellipse((head_x - 29, head_y - 13, head_x - 19, head_y + 9), fill=hair)
    draw.ellipse((head_x - 11, head_y - 4, head_x - 7, head_y), fill="#473c36")
    draw.arc((head_x - 5, head_y + 5, head_x + 10, head_y + 14), 5, 165, fill="#935e50", width=2)
    draw.rounded_rectangle((head_x - 13, head_y + 23, head_x + 13, head_y + 45), radius=7, fill=skin)
    draw.rounded_rectangle((head_x - 36, head_y + 38, head_x + 36, head_y + 124), radius=22,
                           fill=shirt, outline=mix(shirt, "#ead0ab", .32), width=2)
    hip_y = head_y + 115
    for leg_side in (-1, 1):
        foot_x = head_x + leg_side * 17 + stride * leg_side * 18
        draw.line((head_x + leg_side * 12, hip_y, foot_x, head_y + 202), fill="#514841", width=13)
        draw.ellipse((foot_x - 13, head_y + 194, foot_x + 13, head_y + 205), fill="#493f3e")
    shoulder_x = head_x + (-29 if side < 0 else 29)
    hand_x = head_x + (38 if side < 0 else -38)
    hand_y = head_y + (121 if holding else 133)
    draw.line(cubic((shoulder_x, head_y + 57), (shoulder_x + side * 9, head_y + 83),
                    (hand_x, hand_y - 13), (hand_x, hand_y), 14), fill=skin, width=11, joint="curve")
    draw.ellipse((hand_x - 6, hand_y - 6, hand_x + 6, hand_y + 6), fill=skin)


def draw_walking_scene(time: float, background: Image.Image, duration: float = 8.0):
    frame = background.copy()
    draw = ImageDraw.Draw(frame)
    draw_picnic(draw)
    progress = smoothstep(time / duration)
    base_x = 565 + 605 * progress
    bob = 3 * math.sin(time * 4)
    edwar_x, hary_x = base_x - 49, base_x + 49
    draw_walking_person(draw, CONFIG["edwar"], edwar_x, 414 + bob, time, -1, True)
    draw_walking_person(draw, CONFIG["partner"], hary_x, 414 - bob, time, 1, True)
    hand_y = round(414 + 121 + bob)
    draw.line((edwar_x + 38, hand_y, hary_x - 38, hand_y), fill="#d9a58f", width=12)
    draw.ellipse((round(base_x - 11), hand_y - 8, round(base_x + 11), hand_y + 8), fill="#e4b49b", outline="#f3d9bd", width=2)
    draw_cat(draw, time + 11, 42, x=round(base_x - 117), y=590 + 2 * math.sin(time * 2.1))
    draw_motion(draw, time + 1, 42)
    draw_romantic_hearts(draw, time + 2, .85)
    return frame


def render_garden_story(scene_time: float, background: Image.Image):
    walk_scene_start = WALK_START - PICNIC_START
    walk_duration = CLOSING_START - WALK_START
    if scene_time < walk_scene_start:
        return draw_picnic_scene(scene_time, background)
    if scene_time < walk_scene_start + 2:
        settled = draw_picnic_scene(walk_scene_start - .01, background)
        walking = draw_walking_scene(scene_time - walk_scene_start, background, walk_duration)
        return Image.blend(settled, walking, smoothstep((scene_time - walk_scene_start) / 2))
    return draw_walking_scene(scene_time - walk_scene_start, background, walk_duration)


def render_sequence(time: float, background: Image.Image, soft_background: Image.Image,
                    vertical: bool = False):
    cover = lambda local_time: draw_cover(local_time, soft_background, vertical)
    garden = lambda local_time: render_garden_story(local_time, background)
    closing = lambda local_time: draw_closing(local_time, soft_background, vertical)

    if time < 3.7:
        image = cover(time)
    elif time < 4.5:
        image = Image.blend(cover(time), garden(time - PICNIC_START), smoothstep((time - 3.7) / .8))
    elif time < CLOSING_START:
        image = garden(time - PICNIC_START)
    elif time < CLOSING_START + .8:
        image = Image.blend(garden(time - PICNIC_START), closing(time - CLOSING_START),
                            smoothstep((time - CLOSING_START) / .8))
    else:
        image = closing(time - CLOSING_START)

    portrait_center = 640
    if PICNIC_START <= time < CLOSING_START:
        scene_time = time - PICNIC_START
        walk_scene_start = WALK_START - PICNIC_START
        if scene_time >= walk_scene_start:
            walk_duration = CLOSING_START - WALK_START
            portrait_center = round(640 + 500 * smoothstep((scene_time - walk_scene_start) / walk_duration))
    return image, portrait_center


def open_encoder(path: Path, size, fps):
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    width, height = size
    command = [executable, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0", "-an",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(path)]
    return subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def write_video_frame(process, image):
    assert process.stdin is not None
    process.stdin.write(image.convert("RGB").tobytes())


def portrait_frame(image: Image.Image, center_x: int) -> Image.Image:
    out_w, out_h = CONFIG["portrait_size"]
    scale = out_h / H
    scaled_w = round(W * scale)
    enlarged = image.resize((scaled_w, out_h), Image.Resampling.LANCZOS)
    left = round(center_x * scale - out_w / 2)
    left = max(0, min(left, scaled_w - out_w))
    return enlarged.crop((left, 0, left + out_w, out_h))


def draw_vertical_subtitle(image: Image.Image, time: float):
    scene_time = time - PICNIC_START
    if 2 <= scene_time < 7.5:
        text = "Hary, eres lo mejor que me ha pasado."
    elif 10 <= scene_time < 16:
        text = "Quiero cuidarte siempre."
    elif 19 <= scene_time < 23.5:
        text = "Te amo."
    else:
        return image
    draw = ImageDraw.Draw(image)
    box = (34, 438, 686, 548)
    draw.rounded_rectangle((box[0] + 3, box[1] + 4, box[2] + 3, box[3] + 4), radius=20, fill="#34323d")
    draw.rounded_rectangle(box, radius=20, fill="#f0dfc9", outline="#e6c294", width=3)
    draw.text((360, 462), "EDWAR", font=get_font(16), fill="#a5656e", anchor="mm")
    draw.text((360, 505), text, font=get_font(25 if len(text) < 30 else 22, script=True),
              fill="#51474a", anchor="mm")
    return image


def build_gif_palette(background, soft_background):
    gif_w, gif_h = CONFIG["gif_size"]
    palette_sheet = Image.new("RGB", (gif_w * 3, gif_h * 2))
    sample_times = (0, 8, 19, 29, 40, 50)
    for index, time in enumerate(sample_times):
        frame, _ = render_sequence(time, background, soft_background)
        thumbnail = frame.resize((gif_w, gif_h), Image.Resampling.LANCZOS)
        palette_sheet.paste(thumbnail, ((index % 3) * gif_w, (index // 3) * gif_h))
    return palette_sheet.convert("P", palette=Image.Palette.ADAPTIVE, colors=CONFIG["gif_colors"])


def main():
    duration = CONFIG["duration_seconds"]
    fps = CONFIG["fps"]
    total_frames = round(duration * fps)
    background = draw_background()
    soft_background = background.filter(ImageFilter.GaussianBlur(radius=8))
    landscape_path = ROOT / "jardin_romantico.mp4"
    portrait_path = ROOT / "jardin_romantico_vertical.mp4"
    landscape = open_encoder(landscape_path, CONFIG["landscape_size"], fps)
    portrait = open_encoder(portrait_path, CONFIG["portrait_size"], fps)
    preview = []
    gif_stride = max(1, round(fps / CONFIG["gif_fps"]))
    gif_palette = build_gif_palette(background, soft_background) if CONFIG["make_gif_preview"] else None
    try:
        for index in range(total_frames):
            time = index / fps
            frame, _ = render_sequence(time, background, soft_background)
            write_video_frame(landscape, frame)
            portrait_scene, crop_center = render_sequence(time, background, soft_background, vertical=True)
            mobile = portrait_frame(portrait_scene, crop_center)
            mobile = draw_vertical_subtitle(mobile, time)
            write_video_frame(portrait, mobile)
            if gif_palette is not None and index % gif_stride == 0:
                thumbnail = frame.resize(CONFIG["gif_size"], Image.Resampling.LANCZOS)
                preview.append(thumbnail.quantize(palette=gif_palette, dither=Image.Dither.NONE))
            if index % fps == 0:
                print(f"Renderizando: {time:04.1f}/{duration}s", flush=True)
    finally:
        for process in (landscape, portrait):
            if process.stdin:
                process.stdin.close()
    for process in (landscape, portrait):
        error = process.stderr.read() if process.stderr else b""
        code = process.wait()
        if code:
            raise RuntimeError(f"FFmpeg fallo ({code}): {error.decode('utf-8', errors='replace')}")

    if preview:
        (ROOT / "vista_previa.gif").write_bytes(b"")
        preview[0].save(ROOT / "vista_previa.gif", save_all=True, append_images=preview[1:],
                        duration=1000 * gif_stride // fps, loop=0, optimize=True, disposal=2)
    print(f"Listo: {landscape_path.name}, {portrait_path.name}" + (", vista_previa.gif" if preview else ""))


if __name__ == "__main__":
    main()