#!/usr/bin/env python3
"""Draw the 21 November 2026 world-news front page (1024x1024 PNG).

A newspaper-style infographic: a navy masthead naming the day, six
verified stories of Saturday 21 November 2026 in a 2x3 card grid (each
with a tag, a headline, a one-line summary, a flat pictogram and a
dateline), an "also today" strip with five more headlines, and a footer
with sources. Drawn from scratch with Pillow and DejaVu Sans; no copied
art, no network. Palette and pictograms are new for this edition.
"""
import math

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "news.png"

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PAPER = (250, 248, 243)
INK = (22, 22, 22)
SOFT = (72, 72, 72)
NAVY = (13, 27, 62)
NAVY_SOFT = (148, 163, 196)
AMBER = (226, 135, 32)
CRIMSON = (164, 30, 34)
CARD = (255, 255, 255)
EDGE = (222, 216, 200)


def load(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(text, face, max_w):
    """Greedy word wrap: lines that fit max_w pixels."""
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if face.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def tint(color, frac=0.15):
    """Tint a color toward white."""
    return tuple(int(c + (255 - c) * frac) for c in color)


def pictogram(d, kind, cx, cy, r, color):
    """Flat pictogram inside a tinted disc; one drawing per story kind."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tint(color, 0.16))
    s = r * 0.6
    if kind == "missile":
        # cruise missile flying up-right, with a flame trail
        d.line([cx - s * 0.9, cy + s * 0.9, cx - s * 0.3, cy + s * 0.3],
               fill=(226, 135, 32), width=7)
        d.polygon([(cx - s * 0.55, cy + s * 0.75), (cx + s * 0.25, cy - s * 0.05),
                   (cx + s * 0.05, cy - s * 0.25), (cx + s * 0.75, cy - s * 0.55)],
                  fill=color)
        d.polygon([(cx - s * 0.15, cy + s * 0.35), (cx + s * 0.45, cy + s * 0.95),
                   (cx + s * 0.75, cy + s * 0.45)], fill=color)
        d.ellipse([cx + s * 0.5, cy - s * 0.75, cx + s * 0.85, cy - s * 0.4],
                  fill=color)
    elif kind == "chart":
        # falling line chart: axes, a jagged down-trend and an arrow
        d.line([cx - s * 0.8, cy + s * 0.8, cx + s * 0.9, cy + s * 0.8],
               fill=color, width=4)
        d.line([cx - s * 0.8, cy + s * 0.8, cx - s * 0.8, cy - s * 0.8],
               fill=color, width=4)
        pts = [(cx - s * 0.7, cy - s * 0.55), (cx - s * 0.35, cy - s * 0.2),
               (cx, cy - s * 0.45), (cx + s * 0.35, cy + s * 0.15),
               (cx + s * 0.7, cy + s * 0.55)]
        d.line(pts, fill=color, width=6, joint="curve")
        d.polygon([(cx + s * 0.7, cy + s * 0.55), (cx + s * 0.42, cy + s * 0.55),
                   (cx + s * 0.7, cy + s * 0.83)], fill=color)
    elif kind == "bridge":
        # suspension bridge: two towers, a sagging cable and a deck
        d.line([cx - s * 0.6, cy - s * 0.6, cx - s * 0.6, cy + s * 0.8],
               fill=color, width=6)
        d.line([cx + s * 0.6, cy - s * 0.6, cx + s * 0.6, cy + s * 0.8],
               fill=color, width=6)
        d.arc([cx - s * 0.6, cy - s * 1.1, cx + s * 0.6, cy + s * 0.5],
              0, 180, fill=color, width=5)
        d.line([cx - s * 0.9, cy + s * 0.55, cx + s * 0.9, cy + s * 0.55],
               fill=color, width=6)
        for dx in (-0.45, -0.15, 0.15, 0.45):
            d.line([cx + dx * s, cy + s * 0.15, cx + dx * s, cy + s * 0.55],
                   fill=color, width=3)
    elif kind == "globe":
        # planet: circle outline, meridian arcs and a polar cap
        d.ellipse([cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8],
                  outline=color, width=5)
        d.arc([cx - s * 0.35, cy - s * 0.8, cx + s * 0.35, cy + s * 0.8],
              270, 90, fill=color, width=4)
        d.arc([cx - s * 0.35, cy - s * 0.8, cx + s * 0.35, cy + s * 0.8],
              90, 270, fill=color, width=4)
        d.line([cx - s * 0.8, cy, cx + s * 0.8, cy], fill=color, width=4)
        d.arc([cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8],
              200, 340, fill=color, width=4)
    elif kind == "padlock":
        # padlock: shackle arc, body and keyhole
        d.arc([cx - s * 0.45, cy - s * 0.85, cx + s * 0.45, cy + s * 0.05],
              180, 360, fill=color, width=7)
        d.rounded_rectangle([cx - s * 0.62, cy - s * 0.25, cx + s * 0.62,
                             cy + s * 0.75], radius=8, fill=color)
        d.ellipse([cx - 5, cy - s * 0.02, cx + 5, cy + s * 0.08], fill=(255, 255, 255))
        d.polygon([(cx - 4, cy + s * 0.05), (cx + 4, cy + s * 0.05),
                   (cx + 7, cy + s * 0.4), (cx - 7, cy + s * 0.4)],
                  fill=(255, 255, 255))
    elif kind == "dome":
        # missile-defence dome: wide arc over a skyline, three
        # intercepted missiles marked with crosses
        d.arc([cx - s * 0.95, cy - s * 0.55, cx + s * 0.95, cy + s * 0.95],
              180, 360, fill=color, width=7)
        for dx, w in [(-0.52, 0.3), (0.0, 0.42), (0.52, 0.32)]:
            d.rectangle([cx + dx * s - w * s / 2, cy + s * 0.5,
                         cx + dx * s + w * s / 2, cy + s * 0.85], fill=color)
        for dx, dy in [(-0.55, -0.62), (0.05, -0.78), (0.6, -0.55)]:
            px, py = cx + dx * s, cy + dy * s
            d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=color)
            d.line([px - 4, py - 4, px + 4, py + 4], fill=(255, 255, 255),
                   width=3)
            d.line([px - 4, py + 4, px + 4, py - 4], fill=(255, 255, 255),
                   width=3)


# tag, accent colour, pictogram, headline, summary, dateline
STORIES = [
    {"tag": "WAR", "color": (164, 30, 34), "icon": "missile",
     "headline": "Russia strikes Ukraine; missiles hit Poland",
     "summary": "400+ drones and 110 missiles kill 8 in Kyiv; Tusk calls it a provocation.",
     "dateline": "KYIV & POLAND"},
    {"tag": "MARKETS", "color": (176, 106, 18), "icon": "chart",
     "headline": "AI rout drags S&P 500 into correction",
     "summary": "S&P falls 3.7% for a seventh straight loss; Nasdaq wipes out 2026 gains.",
     "dateline": "NEW YORK, USA"},
    {"tag": "DEAL", "color": (14, 110, 110), "icon": "bridge",
     "headline": "UK and EU seal biggest post-Brexit deal",
     "summary": "Food trade, carbon markets and youth mobility for 100,000 agreed.",
     "dateline": "BRUSSELS, BELGIUM"},
    {"tag": "CLIMATE", "color": (38, 92, 158), "icon": "globe",
     "headline": "COP31 runs into overtime over fossil fuels",
     "summary": "Draft drops every mention of fossil fuels; talks get an extra day.",
     "dateline": "ANTALYA, TURKEY"},
    {"tag": "CYBER", "color": (104, 72, 160), "icon": "padlock",
     "headline": "FBI crime database hacked, CNN reports",
     "summary": "National Crime Information Center breached; second FBI hack in months.",
     "dateline": "WASHINGTON, USA"},
    {"tag": "MISSILE", "color": (34, 112, 74), "icon": "dome",
     "headline": "Saudi defences down three Houthi missiles",
     "summary": "Third straight night of alerts over Riyadh; no casualties reported.",
     "dateline": "RIYADH, SAUDI ARABIA"},
]

ALSO_TODAY = [
    "Peru 6.9 quake shakes Andes, felt in Lima",
    "Anthropic shares fall 8.5% on day two after IPO",
    "Trump calls Putin \u2018my friend\u2019; Zelensky: \u2018killer\u2019",
    "Gen Z protests spread across 25 European nations",
    "Bayer pays $7.25bn to settle Roundup claims",
]


def draw_card(d, story, x, y, bw, bh):
    color = story["color"]
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=12, fill=CARD,
                        outline=EDGE, width=1)
    # accent bar across the top of the card
    d.rounded_rectangle([x, y, x + bw, y + 6], radius=3, fill=color)
    f_tag = load(BOLD, 18)
    f_head = load(BOLD, 26)
    f_sum = load(REG, 21)
    f_date = load(BOLD, 14)
    # tag chip
    tw = f_tag.getlength(story["tag"]) + 20
    d.rounded_rectangle([x + 18, y + 18, x + 18 + tw, y + 18 + 26],
                        radius=6, fill=color)
    d.text((x + 28, y + 22), story["tag"], font=f_tag, fill=(255, 255, 255))
    # pictogram, top right
    pictogram(d, story["icon"], x + bw - 62, y + 60, 44, color)
    # headline, left of the pictogram, at most two lines
    lines = wrap_text(story["headline"], f_head, bw - 36 - 100)[:2]
    hy = y + 56
    for ln in lines:
        d.text((x + 18, hy), ln, font=f_head, fill=INK)
        hy += 33
    # summary, full width, at most two lines
    slines = wrap_text(story["summary"], f_sum, bw - 36)[:2]
    sy = y + 56 + 2 * 33 + 8
    for ln in slines:
        d.text((x + 18, sy), ln, font=f_sum, fill=SOFT)
        sy += 27
    # dateline at the bottom
    d.text((x + 18, y + bh - 28), story["dateline"], font=f_date, fill=color)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    d.rectangle([0, 0, W, 118], fill=NAVY)
    d.text((32, 18), "THE WORLD IN ONE DAY", font=load(BOLD, 21),
           fill=NAVY_SOFT)
    d.text((32, 46), "21 NOVEMBER 2026", font=load(BOLD, 54),
           fill=(255, 255, 255))
    d.text((W - 32, 22), "SATURDAY", font=load(BOLD, 30), fill=AMBER,
           anchor="ra")
    d.text((W - 32, 60), "KYIV \u00b7 WARSAW \u00b7 NEW YORK \u00b7 BRUSSELS",
           font=load(BOLD, 15), fill=NAVY_SOFT, anchor="ra")
    d.rectangle([0, 118, W, 124], fill=CRIMSON)

    # ---- story grid: 2 columns x 3 rows ----
    gx, gy = 16, 140
    bw, bh, gap = 488, 232, 12
    for i, story in enumerate(STORIES):
        x = gx + (i % 2) * (bw + gap)
        y = gy + (i // 2) * (bh + gap)
        draw_card(d, story, x, y, bw, bh)

    # ---- "also today" strip, three lines ----
    ay = gy + 3 * bh + 2 * gap + 12
    d.rounded_rectangle([16, ay, W - 16, ay + 96], radius=10, fill=CARD,
                        outline=EDGE, width=1)
    f_also = load(REG, 17)
    f_also_b = load(BOLD, 17)
    lead = "ALSO TODAY \u2014 "
    lead_w = f_also_b.getlength(lead)
    joined = " \u00b7 ".join(ALSO_TODAY)
    lines = wrap_text(joined, f_also, W - 32 - lead_w - 16)[:3]
    d.text((32, ay + 8), lead, font=f_also_b, fill=INK)
    d.text((32 + lead_w, ay + 8), lines[0], font=f_also, fill=INK)
    if len(lines) > 1:
        d.text((32, ay + 34), lines[1], font=f_also, fill=INK)
    if len(lines) > 2:
        d.text((32, ay + 60), lines[2], font=f_also, fill=INK)

    # ---- footer ----
    fy = ay + 96 + 8
    d.rectangle([0, fy, W, H], fill=NAVY)
    d.text((32, fy + 5), "21 NOVEMBER 2026", font=load(BOLD, 20),
           fill=(255, 255, 255))
    d.text((32, fy + 27),
           "Sources: Reuters \u00b7 Associated Press \u00b7 CNN \u00b7 BBC News \u00b7 "
           "Al Jazeera \u00b7 AP",
           font=load(REG, 14), fill=NAVY_SOFT)

    img.save(OUT, optimize=True)
    print("saved", OUT, img.size)


if __name__ == "__main__":
    main()
