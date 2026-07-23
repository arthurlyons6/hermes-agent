#!/usr/bin/env python3
"""
BlackGold Brand Assets builder (OFFLINE / PIL-only).

Source of truth (A1, verified by user from live site):
  - Gold token:  #B8960C   (was #EEC050 in on-disk build snapshot)
  - Mark:         gold square (#B8960C) with black "B"
  - Navy:         #04060E
  - Cream:        #F2E8D0
  - Green:        #3DDB78
  - Red:          #F07070
  - Violet:       #A78BFA
  - Fonts:        Fraunces (serif) -> Georgia; Inter (sans) -> Segoe UI;
                  JetBrains Mono (mono) -> Consolas

NOTE: live site (blackgoldequitypartners.com) was unreachable from the
build sandbox at generation time, so the gold token rests on the user's
A1 verification, not an independent fetch.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- tokens
NAVY   = (0x04, 0x06, 0x0E)
GOLD   = (0xB8, 0x96, 0x0C)
CREAM  = (0xF2, 0xE8, 0xD0)
GREEN  = (0x3D, 0xDB, 0x78)
RED    = (0xF0, 0x70, 0x70)
VIOLET = (0xA7, 0x8B, 0xFA)
BLACK  = (0x00, 0x00, 0x00)
WHITE  = (0xFF, 0xFF, 0xFF)
GOLD_HEX   = "#B8960C"
NAVY_HEX   = "#04060E"
CREAM_HEX  = "#F2E8D0"
GREEN_HEX  = "#3DDB78"
RED_HEX    = "#F07070"
VIOLET_HEX = "#A78BFA"

# ---------------------------------------------------------------- fonts (offline subs)
F = "C:/Windows/Fonts"
SERIF_B    = ImageFont.truetype(f"{F}/georgiab.ttf", 64)
SERIF      = ImageFont.truetype(f"{F}/georgia.ttf",   28)
SANS_B     = ImageFont.truetype(f"{F}/segoeuib.ttf",  30)
SANS       = ImageFont.truetype(f"{F}/segoeui.ttf",   22)
SANS_SM    = ImageFont.truetype(f"{F}/segoeui.ttf",   16)
MONO_B     = ImageFont.truetype(f"{F}/consolab.ttf",  20)
MONO       = ImageFont.truetype(f"{F}/consola.ttf",   18)
MONO_SM    = ImageFont.truetype(f"{F}/consola.ttf",   14)

def font_sized(path, size):
    return ImageFont.truetype(path, size)

# ---------------------------------------------------------------- favicon mark
def build_mark(size=256, pad=None):
    """Gold square with black bold 'B' centered (brand favicon, A1)."""
    if pad is None:
        pad = int(size * 0.10)
    img = Image.new("RGB", (size, size), GOLD)
    d = ImageDraw.Draw(img)
    # subtle inner border for definition
    d.rectangle([pad//2, pad//2, size-1-pad//2, size-1-pad//2],
                outline=(0,0,0), width=max(1, size//128))
    b = ImageFont.truetype(f"{F}/georgiab.ttf", int(size*0.66))
    txt = "B"
    bbox = d.textbbox((0,0), txt, font=b)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (size - tw)//2 - bbox[0]
    y = (size - th)//2 - bbox[1]
    d.text((x, y), txt, font=b, fill=BLACK)
    return img

mark256 = build_mark(256)
mark256.save(os.path.join(OUT, "favicon-gold-B.png"))
mark32 = build_mark(32)
mark32.save(os.path.join(OUT, "favicon-gold-B-32.png"))
print("favicon written")

# ---------------------------------------------------------------- PDF pages
PW, PH = 1240, 1754  # A4 @ 150dpi

def new_page(bg=NAVY):
    return Image.new("RGB", (PW, PH), bg)

def rounded(d, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

# --- Page 1 : colors + mark + type
p1 = new_page(NAVY)
d = ImageDraw.Draw(p1)

# header band
rounded(d, [60, 60, PW-60, 200], 16, fill=(10,13,22))
d.text((96, 96), "BLACKGOLD", font=SANS_B, fill=CREAM)
d.text((96, 140), "BRAND STANDARDS  -  A1 verified source", font=MONO_SM, fill=GOLD)
d.text((PW-96, 100), "blackgoldequitypartners.com", font=MONO_SM,
       fill=CREAM, anchor="ra")

# color tokens row
d.text((96, 250), "COLOR TOKENS", font=MONO_B, fill=GOLD)
sw = 150
gap = 28
x0 = 96
y0 = 300
cols = 3
tokens = [
    ("Navy",   NAVY_HEX,   NAVY),
    ("Gold",   GOLD_HEX,   GOLD),
    ("Cream",  CREAM_HEX,  CREAM),
    ("Green",  GREEN_HEX,  GREEN),
    ("Red",    RED_HEX,    RED),
    ("Violet", VIOLET_HEX, VIOLET),
]
for i,(name,hexv,col) in enumerate(tokens):
    r = i // cols
    c = i % cols
    x = x0 + c*(sw+gap)
    y = y0 + r*(sw+70)
    rounded(d, [x, y, x+sw, y+sw], 14, fill=col,
            outline=(255,255,255) if col in (NAVY,) else None, width=2)
    # label below
    lab = name if col != NAVY else f"{name} (border)"
    d.text((x, y+sw+12), lab, font=SANS_SM, fill=CREAM)
    d.text((x, y+sw+38), hexv, font=MONO_SM, fill=GOLD)

# mark display
mx, my = 96, 760
d.text((mx, my), "FAVICON MARK", font=MONO_B, fill=GOLD)
big = build_mark(220)
p1.paste(big, (mx, my+40))
d.text((mx+260, my+60), "Gold square  #B8960C", font=SANS, fill=CREAM)
d.text((mx+260, my+100), "Black 'B'", font=SANS, fill=CREAM)
d.text((mx+260, my+140), "Sizes: 32 / 256 px", font=MONO_SM, fill=GOLD)
d.text((mx+260, my+170), "files: favicon-gold-B.png", font=MONO_SM, fill=(200,200,200))

# typography
ty = 1120
d.text((96, ty), "TYPOGRAPHY", font=MONO_B, fill=GOLD)
rows = [
    ("Fraunces (heading)", "Georgia / Georgia Bold", SERIF_B, "Operator-led conviction."),
    ("Inter (body)", "Segoe UI / Segoe UI Bold", SANS_B, "Clear, neutral, modern."),
    ("JetBrains Mono (meta)", "Consolas / Consolas Bold", MONO_B, "Labels, codes, specs."),
]
yy = ty+50
for brand, sub, fnt, note in rows:
    d.text((96, yy), brand, font=SANS, fill=CREAM)
    d.text((520, yy), sub, font=MONO_SM, fill=GOLD)
    d.text((520, yy+26), note, font=SANS_SM, fill=(200,200,200))
    yy += 70

# footnote
d.text((96, PH-110),
        "Tokens centralized; gold locked to #B8960C per A1 live-source verification.",
        font=SANS_SM, fill=CREAM)
d.text((96, PH-80),
        "Live site was unreachable from build sandbox - gold not independently re-fetched.",
        font=SANS_SM, fill=(190,190,190))

# --- Page 2 : provenance / token change log
p2 = new_page(NAVY)
d = ImageDraw.Draw(p2)
rounded(d, [60, 60, PW-60, 200], 16, fill=(10,13,22))
d.text((96, 96), "PROVENANCE & TOKEN LOG", font=SANS_B, fill=CREAM)
d.text((96, 140), "what changed, why, and what to confirm next", font=MONO_SM, fill=GOLD)

lines = [
    ("SOURCE", "Live site verified as A1 authentic source. On-disk 'logo' PNGs belonged to",
               "other companies and were discarded - good we checked."),
    ("GOLD", "Updated #EEC050 (on-disk build snapshot) -> #B8960C (A1 live favicon/CSS).",
             "User-verified. If wrong, single-line swap in build_assets.py."),
    ("MARK", "Gold square #B8960C + black 'B'. Rendered at 32 & 256 px (favicon set).",
             "On-disk mark assets were other companies' logos - not used."),
    ("FONTS", "Offline substitutes: Fraunces->Georgia, Inter->Segoe UI, JetBrains Mono->Consolas.",
              "Swap to live webfonts at deploy for final fidelity."),
    ("VERIFY", "Live site (blackgoldequitypartners.com) unreachable from build sandbox at gen time.",
               "Re-fetch CSS :root on a networked box to confirm gold + all tokens."),
    ("TOOLING", "No HTML->PDF engine (wkhtmltopdf/weasyprint/chromium) and no pip network.",
               "Fallback: PIL raster -> PDF. Re-render with real engine when available."),
]
yy = 260
for tag, a, b in lines:
    d.text((96, yy), tag, font=MONO_B, fill=GOLD)
    d.text((260, yy), a, font=SANS_SM, fill=CREAM)
    d.text((260, yy+26), b, font=SANS_SM, fill=(200,200,200))
    yy += 92

d.text((96, PH-110),
        "Next: confirm gold on networked box; produce HTML->PDF with real engine;",
        font=SANS_SM, fill=CREAM)
d.text((96, PH-80),
        "wire favicon into blackgold-equity-partners build before Vercel push.",
        font=SANS_SM, fill=(190,190,190))

# ---------------------------------------------------------------- save PDF + page PNGs
preview_dir = os.path.join(OUT, "previews")
os.makedirs(preview_dir, exist_ok=True)
p1.save(os.path.join(preview_dir, "page1.png"))
p2.save(os.path.join(preview_dir, "page2.png"))

pdf_path = os.path.join(OUT, "blackgold-brand-standards.pdf")
p1.save(pdf_path, "PDF", save_all=True, append_images=[p2])
print("PDF written:", pdf_path)
print("pages:", 2)
