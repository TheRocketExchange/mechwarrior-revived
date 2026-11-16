"""Build a self-contained Letter-size pilot card PDF without third-party libraries."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "units"))
from force_org import GAME_SIZES
DATA = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
WIDTH, HEIGHT = 612, 792
CARD_W, CARD_H = 180, 252
INK = (0.10, 0.16, 0.19)
TEAL = (0.08, 0.32, 0.37)
GRAY = (0.42, 0.46, 0.48)
WHITE = (1, 1, 1)
commands = []
drawing = []


def color(rgb):
    return " ".join(str(v) for v in rgb)


def text(x, y, value, size=9, bold=False, rgb=INK):
    # ASCII text uses the viewer's standard Helvetica fonts; no external files.
    value.encode("ascii")
    escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    commands.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {color(rgb)} rg 1 0 0 1 {x} {y} Tm ({escaped}) Tj ET")
    drawing.append(("text", x, y, value, size, bold, rgb))


def rect(x, y, width, height, rgb, stroke=False):
    commands.append(f"{color(rgb)} {'RG' if stroke else 'rg'} 0.6 w {x} {y} {width} {height} re {'S' if stroke else 'f'}")
    drawing.append(("rect", x, y, width, height, rgb, stroke))


def width_estimate(value, size):
    # Conservative widths for Helvetica; wrapping leaves additional side margins.
    widths = {" ": 278, "i": 278, "l": 278, "I": 278, "f": 333,
              "j": 278, "t": 333, "r": 389, ".": 278, ",": 278,
              "'": 222, ":": 278, "!": 278, "M": 889, "W": 1000,
              "m": 889, "w": 778, "-": 333, "(": 333, ")": 333}
    return sum(widths.get(c, 722 if c.isupper() else 600) for c in value) * size / 1000


def paragraph(x, y, value, width=152, size=9, leading=12, rgb=INK):
    lines, current = [], ""
    for word in value.split():
        candidate = (current + " " + word).strip()
        if width_estimate(candidate, size) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    for line in lines:
        assert width_estimate(line, size) <= width, line
        text(x, y, line, size=size, rgb=rgb)
        y -= leading
    return y


text(72, 747, "MECHWARRIOR REVIVED", 21, True, TEAL)
text(72, 726, f"Pilot cards | Playtest {DATA['version']} | Print at 100% on US Letter", 10)
role_limits = " / ".join(f"{size['name'].removesuffix(' Battle')} {size['limits']['pilot_max']}" for size in GAME_SIZES.values())
text(72, 709, f"Each role: {role_limits}. One pilot per 'Mech; no extra points.", 9)
positions = [(90, 414), (324, 414), (90, 120), (324, 120)]
assert len(DATA["cards"]) == len(positions)
for card, (x, y) in zip(DATA["cards"], positions):
    rect(x, y, CARD_W, CARD_H, WHITE)
    rect(x, y, CARD_W, CARD_H, GRAY, stroke=True)
    rect(x, y + CARD_H - 55, CARD_W, 55, TEAL)
    text(x + 14, y + 234, f"REVIVED PILOT / v{DATA['version']}", 8, rgb=WHITE)
    text(x + 14, y + 211, card["role"].upper(), 18, True, WHITE)
    text(x + 14, y + 177, "Pilot: _______________________", 8, rgb=GRAY)
    text(x + 14, y + 160, "Unit: ________________________", 8, rgb=GRAY)
    text(x + 14, y + 137, card["ability"], 10, True, TEAL)
    end = paragraph(x + 14, y + 119, card["text"])
    assert end >= y + 23, (card["role"], "ability overflows")
    end = paragraph(x + 14, y + 30, card["reminder"], size=7, leading=9, rgb=GRAY)
    assert end >= y + 8, (card["role"], "reminder overflows")

text(72, 87, "Cut on the four card borders. Finished size: 2.5 x 3.5 inches.", 9)
text(72, 72, "Print extra sheets as needed. Abilities affect only the assigned unit.", 9)
text(72, 57, "No advancement or usage tokens. Engineer works during shutdown; other abilities do not.", 8, rgb=GRAY)

stream = "\n".join(commands).encode("ascii")
objects = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
]
pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
offsets = [0]
for index, obj in enumerate(objects, 1):
    offsets.append(len(pdf))
    pdf.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
xref = len(pdf)
pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
for offset in offsets[1:]:
    pdf.extend(f"{offset:010d} 00000 n \n".encode())
pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
(ROOT / "revived-pilot-cards.pdf").write_bytes(pdf)
print("Generated Letter PDF: four 2.5 x 3.5 inch pilot cards.")

# Optional preview uses the same coordinates and wrapped lines as the PDF.
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow unavailable; PDF generated, preview skipped.")
else:
    canvas = Image.new("RGB", (WIDTH * 2, HEIGHT * 2), "white")
    pen = ImageDraw.Draw(canvas)
    fonts = Path("C:/Windows/Fonts")
    normal = fonts / "arial.ttf"
    bold_font = fonts / "arialbd.ttf"
    if normal.exists() and bold_font.exists():
        for item in drawing:
            if item[0] == "rect":
                _, x, y, w, h, rgb, stroke = item
                box = (x * 2, (HEIGHT - y - h) * 2, (x + w) * 2, (HEIGHT - y) * 2)
                ink = tuple(round(v * 255) for v in rgb)
                pen.rectangle(box, outline=ink if stroke else None, fill=None if stroke else ink)
            else:
                _, x, y, value, size, is_bold, rgb = item
                font = ImageFont.truetype(str(bold_font if is_bold else normal), round(size * 2))
                pen.text((x * 2, (HEIGHT - y) * 2), value, font=font,
                         fill=tuple(round(v * 255) for v in rgb), anchor="ls")
        canvas.save(ROOT / "revived-pilot-cards-preview.png")
        print("Generated matching layout preview.")
    else:
        print("Arial unavailable; PDF generated, preview skipped.")
