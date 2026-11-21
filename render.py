#!/usr/bin/env python3
"""Render the front page for 21 November 2026: "The World in One Day".

Draws a single 1024x1024 newspaper front page with Pillow. Six lead
stories in a hero + grid + wide-band layout, an "Also today" strip with
five more items, and a navy masthead and footer. Deterministic: no
randomness, no clock, no network — the same input always produces the
same bytes.

Usage:  python3 render.py [output-path]
Default output is news.png next to this script.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- canvas

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 24

PAPER = (246, 243, 236)      # warm off-white page
CARD = (255, 255, 255)       # story cards
INK = (24, 28, 38)           # near-black text
MUTED = (92, 96, 104)        # deck grey
NAVY = (22, 35, 63)          # masthead / footer
NAVY_SOFT = (148, 166, 198)    # masthead secondary text
RED = (178, 34, 34)          # war red / rule
AMBER = (176, 106, 12)       # markets amber
TEAL = (14, 116, 110)        # deal teal
BLUE = (37, 82, 160)         # climate blue
PURPLE = (109, 72, 170)      # cyber purple
GREEN = (28, 122, 80)        # missile green
ORANGE = (245, 158, 11)      # Saturday accent
DISC_INK = (255, 255, 255)   # glyphs drawn on coloured discs

# ------------------------------------------------------------- fonts

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
]

_BOLD_NAMES = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
               "NotoSans-Bold.ttf"]
_REG_NAMES = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf",
              "NotoSans-Regular.ttf"]


def _find_font(names):
    """First existing file from the candidate font names, or None."""
    for directory in _FONT_DIRS:
        for name in names:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                return path
    return None


def load_fonts():
    """Return (bold, regular) font factories: size -> ImageFont."""
    bold_path = _find_font(_BOLD_NAMES)
    reg_path = _find_font(_REG_NAMES)
    cache = {}

    def make(path, size, fallback):
        key = (path, size)
        if key not in cache:
            if path is not None:
                cache[key] = ImageFont.truetype(path, size)
            else:
                cache[key] = fallback
        return cache[key]

    default = ImageFont.load_default()
    return (
        lambda size: make(bold_path, size, default),
        lambda size: make(reg_path, size, default),
    )


BOLD, REG = load_fonts()

# ------------------------------------------------------------- helpers


def wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, x, y, lines, font, fill, leading):
    """Draw stacked lines; returns the y just below the last line."""
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def tag_pill(draw, x, y, label, bg, fg=DISC_INK, size=15, pad_x=10, pad_y=5):
    """A small rounded tag; returns its width."""
    font = BOLD(size)
    w = int(draw.textlength(label, font=font)) + 2 * pad_x
    h = size + 2 * pad_y
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - 1), label, font=font, fill=fg)
    return w


def disc(draw, cx, cy, radius, color):
    """A solid coloured disc used as the backdrop for an icon glyph."""
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=color)


# ------------------------------------------------------------- icons
# Each glyph is drawn with plain Pillow primitives on its disc. All
# coordinates are relative to the disc centre (cx, cy) and radius r.


def icon_burst(draw, cx, cy, r):
    """War: a burst of radiating lines from a solid centre."""
    k = DISC_INK
    draw.ellipse([cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22],
                 fill=k)
    for angle in range(0, 360, 30):
        import math
        a = math.radians(angle)
        x0 = cx + int(math.cos(a) * r * 0.34)
        y0 = cy + int(math.sin(a) * r * 0.34)
        x1 = cx + int(math.cos(a) * r * 0.82)
        y1 = cy + int(math.sin(a) * r * 0.82)
        draw.line([x0, y0, x1, y1], fill=k, width=max(3, r // 12))


def icon_chart(draw, cx, cy, r):
    """Markets: a falling line chart with an arrowhead."""
    k = DISC_INK
    w = max(4, r // 10)
    pts = [
        (cx - r * 0.62, cy - r * 0.30),
        (cx - r * 0.22, cy + r * 0.05),
        (cx + r * 0.10, cy - r * 0.15),
        (cx + r * 0.55, cy + r * 0.45),
    ]
    draw.line(pts, fill=k, width=w, joint="curve")
    tip = pts[-1]
    draw.polygon([
        (tip[0] + r * 0.28, tip[1] - r * 0.05),
        (tip[0] - r * 0.02, tip[1] + r * 0.28),
        (tip[0] - r * 0.10, tip[1] - r * 0.22),
    ], fill=k)
    draw.line([cx - r * 0.62, cy + r * 0.62, cx + r * 0.62, cy + r * 0.62],
              fill=k, width=max(3, r // 14))


def icon_bridge(draw, cx, cy, r):
    """Deal: a bridge arc on two pillars, crossed by a check."""
    k = DISC_INK
    w = max(4, r // 10)
    draw.arc([cx - r * 0.62, cy - r * 0.55, cx + r * 0.62, cy + r * 0.55],
             start=180, end=360, fill=k, width=w)
    draw.line([cx - r * 0.55, cy + r * 0.05, cx - r * 0.55, cy + r * 0.62],
              fill=k, width=w)
    draw.line([cx + r * 0.55, cy + r * 0.05, cx + r * 0.55, cy + r * 0.62],
              fill=k, width=w)
    draw.line([cx - r * 0.30, cy + r * 0.10, cx - r * 0.05, cy + r * 0.35,
               cx + r * 0.38, cy - r * 0.28], fill=k, width=w, joint="curve")


def icon_globe(draw, cx, cy, r):
    """Climate: a globe with latitude and longitude arcs."""
    k = DISC_INK
    w = max(3, r // 12)
    draw.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62],
                 outline=k, width=w)
    draw.ellipse([cx - r * 0.62, cy - r * 0.22, cx + r * 0.62, cy + r * 0.22],
                 outline=k, width=max(2, r // 16))
    draw.arc([cx - r * 0.28, cy - r * 0.62, cx + r * 0.28, cy + r * 0.62],
             start=270, end=90, fill=k, width=w)
    draw.arc([cx - r * 0.28, cy - r * 0.62, cx + r * 0.28, cy + r * 0.62],
             start=90, end=270, fill=k, width=max(2, r // 16))


def icon_lock(draw, cx, cy, r):
    """Cyber: a padlock with a shackle."""
    k = DISC_INK
    w = max(4, r // 10)
    body = [cx - r * 0.42, cy - r * 0.05, cx + r * 0.42, cy + r * 0.55]
    draw.rounded_rectangle(body, radius=r // 8, fill=k)
    draw.arc([cx - r * 0.30, cy - r * 0.58, cx + r * 0.30, cy + r * 0.10],
             start=180, end=360, fill=k, width=w)
    draw.ellipse([cx - r * 0.07, cy + r * 0.16, cx + r * 0.07, cy + r * 0.30],
                 fill=NAVY)
    draw.line([cx, cy + r * 0.26, cx, cy + r * 0.42], fill=NAVY,
              width=max(3, r // 14))


def icon_shield(draw, cx, cy, r):
    """Missile defence: a shield with a check and two stars."""
    k = DISC_INK
    w = max(4, r // 10)
    pts = [
        (cx, cy - r * 0.62),
        (cx + r * 0.55, cy - r * 0.38),
        (cx + r * 0.55, cy + r * 0.08),
        (cx, cy + r * 0.62),
        (cx - r * 0.55, cy + r * 0.08),
        (cx - r * 0.55, cy - r * 0.38),
    ]
    draw.polygon(pts, outline=k, width=w)
    draw.line([cx - r * 0.26, cy + r * 0.02, cx - r * 0.06, cy + r * 0.22,
               cx + r * 0.30, cy - r * 0.22], fill=k, width=w, joint="curve")
    for sx in (-r * 0.30, r * 0.30):
        draw.text((cx + sx - 4, cy - r * 0.52), "*", font=BOLD(14), fill=k)


# ------------------------------------------------------------- cards


def story_card(draw, box, tag, color, headline, deck, dateline, icon):
    """One grid card: tag, headline, deck, dateline, icon disc."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=CARD)
    draw.rectangle([x0 + 10, y0, x1 - 10, y0 + 5], fill=color)
    tag_pill(draw, x0 + 18, y0 + 16, tag, color)
    disc(draw, x1 - 48, y0 + 48, 30, color)
    icon(draw, x1 - 48, y0 + 48, 30)
    text_w = (x1 - x0) - 36
    head_lines = wrap(draw, headline, BOLD(23), text_w - 70)
    y = draw_lines(draw, x0 + 18, y0 + 52, head_lines[:2], BOLD(23), INK, 28)
    deck_lines = wrap(draw, deck, REG(16), text_w)
    draw_lines(draw, x0 + 18, y + 4, deck_lines[:2], REG(16), MUTED, 20)
    draw.text((x0 + 18, y1 - 26), dateline, font=BOLD(13), fill=color)


def hero_card(draw, box, tag, color, headline, deck, dateline, icon):
    """The full-width lead story: big headline, large icon disc."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=CARD)
    draw.rectangle([x0 + 10, y0, x1 - 10, y0 + 6], fill=color)
    tag_pill(draw, x0 + 20, y0 + 18, tag, color, size=16)
    disc(draw, x1 - 108, (y0 + y1) // 2, 78, color)
    icon(draw, x1 - 108, (y0 + y1) // 2, 78)
    text_w = (x1 - x0) - 260
    head_lines = wrap(draw, headline, BOLD(38), text_w)
    y = draw_lines(draw, x0 + 20, y0 + 52, head_lines[:2], BOLD(38), INK, 44)
    deck_lines = wrap(draw, deck, REG(19), text_w)
    y = draw_lines(draw, x0 + 20, y + 6, deck_lines[:3], REG(19), MUTED, 25)
    date_y = min(y + 8, y1 - 24)
    draw.text((x0 + 20, date_y), dateline, font=BOLD(14), fill=color)


def band_card(draw, box, tag, color, headline, deck, dateline, icon):
    """A wide horizontal card: text on the left, icon on the right."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=CARD)
    draw.rectangle([x0 + 10, y0, x1 - 10, y0 + 5], fill=color)
    tag_pill(draw, x0 + 18, y0 + 14, tag, color)
    disc(draw, x1 - 56, (y0 + y1) // 2, 40, color)
    icon(draw, x1 - 56, (y0 + y1) // 2, 40)
    text_w = (x1 - x0) - 160
    head_lines = wrap(draw, headline, BOLD(26), text_w)
    y = draw_lines(draw, x0 + 18, y0 + 46, head_lines[:1], BOLD(26), INK, 32)
    deck_lines = wrap(draw, deck, REG(16), text_w - 190)
    deck_y = y + 2
    draw_lines(draw, x0 + 18, deck_y, deck_lines[:1], REG(16), MUTED, 21)
    deck_w = draw.textlength(deck_lines[0], font=REG(16)) if deck_lines else 0
    draw.text((x0 + 18 + deck_w + 8, deck_y + 1), "— " + dateline,
              font=BOLD(13), fill=color)


# ------------------------------------------------------------- page


def masthead(draw):
    """Navy top band: kicker, date, Saturday, dateline cities, red rule."""
    draw.rectangle([0, 0, PAGE_W, 128], fill=NAVY)
    draw.text((MARGIN, 16), "THE WORLD IN ONE DAY",
              font=BOLD(20), fill=NAVY_SOFT)
    draw.text((MARGIN, 48), "21 NOVEMBER 2026", font=BOLD(50), fill=CARD)
    right = "SATURDAY"
    w = draw.textlength(right, font=BOLD(30))
    draw.text((PAGE_W - MARGIN - w, 14), right, font=BOLD(30), fill=ORANGE)
    cities = "KYIV · WARSAW · NEW YORK · BRUSSELS"
    w2 = draw.textlength(cities, font=REG(15))
    draw.text((PAGE_W - MARGIN - w2, 56), cities, font=REG(15), fill=NAVY_SOFT)
    draw.text((PAGE_W - MARGIN - w2, 82), "EDITION Nº 325",
              font=BOLD(15), fill=CARD)
    draw.rectangle([0, 128, PAGE_W, 134], fill=RED)


def also_today(draw, y0, y1):
    """The strip of five shorter items under the story grid."""
    draw.rounded_rectangle([MARGIN, y0, PAGE_W - MARGIN, y1], radius=10,
                           fill=CARD, outline=(200, 196, 186), width=1)
    label = "ALSO TODAY — "
    font = REG(17)
    x = MARGIN + 16
    y = y0 + 14
    draw.text((x, y), label, font=BOLD(17), fill=INK)
    x += int(draw.textlength(label, font=BOLD(17)))
    items = [
        "Peru 6.9 quake shakes Andes, felt in Lima",
        "Anthropic shares fall 8.5% on day two after IPO",
        "Trump calls Putin \u2018my friend\u2019; Zelensky: \u2018killer\u2019",
        "Gen Z protests spread across 25 European nations",
        "Bayer pays $7.25bn to settle Roundup claims",
    ]
    body = "  ·  ".join(items)
    lines = wrap(draw, body, font, (PAGE_W - MARGIN) - x - 16)
    draw_lines(draw, x, y, lines[:3], font, INK, 23)


def footer(draw):
    """Navy bottom band: date and sources."""
    draw.rectangle([0, 962, PAGE_W, PAGE_H], fill=NAVY)
    draw.text((MARGIN, 972), "21 NOVEMBER 2026", font=BOLD(16), fill=CARD)
    draw.text((MARGIN, 996),
              "Sources: Reuters · Associated Press · CNN · BBC News · "
              "Al Jazeera · AP",
              font=REG(13), fill=NAVY_SOFT)
    mark = "THE WORLD IN ONE DAY"
    w = draw.textlength(mark, font=BOLD(13))
    draw.text((PAGE_W - MARGIN - w, 978), mark, font=BOLD(13), fill=ORANGE)


def build():
    """Compose the whole page and return the PIL image."""
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(img)

    masthead(draw)

    hero_card(
        draw, (MARGIN, 146, PAGE_W - MARGIN, 352),
        "WAR", RED,
        "Russia strikes Ukraine; missiles hit Poland",
        "400+ drones and 110 missiles kill 8 in Kyiv; Tusk calls it "
        "a provocation.",
        "KYIV & POLAND", icon_burst,
    )

    story_card(
        draw, (MARGIN, 366, 494, 546),
        "MARKETS", AMBER,
        "AI rout drags S&P 500 into correction",
        "S&P falls 3.7% for a seventh straight loss; Nasdaq wipes out "
        "2026 gains.",
        "NEW YORK, USA", icon_chart,
    )
    story_card(
        draw, (530, 366, PAGE_W - MARGIN, 546),
        "DEAL", TEAL,
        "UK and EU seal biggest post-Brexit deal",
        "Food trade, carbon markets and youth mobility for 100,000 "
        "agreed.",
        "BRUSSELS, BELGIUM", icon_bridge,
    )
    story_card(
        draw, (MARGIN, 556, 494, 736),
        "CLIMATE", BLUE,
        "COP31 runs into overtime over fossil fuels",
        "Draft drops every mention of fossil fuels; talks get an "
        "extra day.",
        "ANTALYA, TURKEY", icon_globe,
    )
    story_card(
        draw, (530, 556, PAGE_W - MARGIN, 736),
        "CYBER", PURPLE,
        "FBI crime database hacked, CNN reports",
        "National Crime Information Center breached; second FBI hack "
        "in months.",
        "WASHINGTON, USA", icon_lock,
    )

    band_card(
        draw, (MARGIN, 748, PAGE_W - MARGIN, 852),
        "MISSILE", GREEN,
        "Saudi defences down three Houthi missiles",
        "Third straight night of alerts over Riyadh; no casualties "
        "reported.",
        "RIYADH, SAUDI ARABIA", icon_shield,
    )

    also_today(draw, 864, 950)
    footer(draw)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "news.png")
    image = build()
    assert image.size == (PAGE_W, PAGE_H), image.size
    image.save(out, format="PNG")
    print("wrote", out, image.size)


if __name__ == "__main__":
    main()
