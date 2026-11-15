"""Print every catalog figure as a photo card, four per US Letter page."""
from __future__ import annotations

import io
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
INK, MUTED, RED, LINE = (0.16, 0.18, 0.15), (0.38, 0.41, 0.34), (0.57, 0.22, 0.18), (0.75, 0.77, 0.71)


def safe(text):
    return str(text).translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "×": "x"})).encode("cp1252", "replace").decode("cp1252")


def wrap(text, width, size):
    words, lines, line = safe(text).split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) * size * 0.54 > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


class PDF:
    def __init__(self):
        self.objects = [b"", b""]
        self.regular = self.add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        self.bold = self.add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        self.images, self.pages = {}, []

    def add(self, value):
        self.objects.append(value)
        return len(self.objects)

    def image(self, path):
        if path in self.images:
            return self.images[path]
        with Image.open(path) as source:
            width, height = source.size
            if source.format == "JPEG" and source.mode in ("RGB", "L"):
                data, mode = path.read_bytes(), source.mode
            else:
                memory = io.BytesIO()
                source.convert("RGB").save(memory, format="JPEG", quality=92)
                data, mode = memory.getvalue(), "RGB"
        colorspace = "DeviceGray" if mode == "L" else "DeviceRGB"
        index = self.add(f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /{colorspace} /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream")
        self.images[path] = (index, width, height)
        return self.images[path]

    def page(self, commands, images):
        stream = "\n".join(commands).encode("cp1252")
        content = self.add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        resources = " ".join(f"/{name} {index} 0 R" for name, index in images.items())
        self.pages.append(self.add(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {self.regular} 0 R /F2 {self.bold} 0 R >> /XObject << {resources} >> >> /Contents {content} 0 R >>".encode()))

    def save(self, path):
        self.objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
        self.objects[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{page} 0 R" for page in self.pages) + f"] /Count {len(self.pages)} >>").encode()
        result, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), [0]
        for index, obj in enumerate(self.objects, 1):
            offsets.append(len(result))
            result.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(result)
        result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
        for offset in offsets[1:]:
            result.extend(f"{offset:010d} 00000 n \n".encode())
        result.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        path.write_bytes(result)


def rgb(value):
    return " ".join(str(v) for v in value)


def text(commands, x, y, value, size=9, bold=False, color=INK):
    value = safe(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    commands.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {rgb(color)} rg 1 0 0 1 {x:.2f} {y:.2f} Tm ({value}) Tj ET")


def card(pdf, commands, images, unit, x, y):
    commands.append(f"{rgb(LINE)} RG 0.5 w {x} {y} 252 342 re S")
    text(commands, x+12, y+328, f"{unit['id']}  /  {unit['set']}", 7, color=MUTED)
    name_size = 13
    lines = wrap(unit["name"], 225, name_size)
    while len(lines) > 3 and name_size > 9:
        name_size -= 1
        lines = wrap(unit["name"], 225, name_size)
    assert len(lines) <= 3, unit["id"]
    for i, line in enumerate(lines):
        text(commands, x+12, y+309-i*14, line, name_size, True)
    if unit["photo"]:
        image_id, width, height = pdf.image(ROOT / unit["photo"])
        name = f"Im{image_id}"
        images[name] = image_id
        scale = min(145/width, 120/height)
        w, h = width*scale, height*scale
        commands.append(f"q {w:.3f} 0 0 {h:.3f} {x+12+(145-w)/2:.3f} {y+146+(120-h)/2:.3f} cm /{name} Do Q")
    else:
        text(commands, x+18, y+205, "Photo unavailable", 9, color=MUTED)
    text(commands, x+173, y+242, unit["cost"]["points"], 27, True, RED)
    text(commands, x+173, y+228, "REVIVED POINTS", 6.5, color=MUTED)
    text(commands, x+173, y+214, f"Printed: {unit['printed_points']}", 7, color=MUTED)
    for i, line in enumerate(wrap(unit["category"], 70, 8)):
        text(commands, x+173, y+195-i*10, line, 8, True)
    text(commands, x+173, y+167, unit["rank"], 8, color=MUTED)
    text(commands, x+173, y+152, "ID: __________", 7, color=MUTED)
    click = unit["track"][unit["start"]]
    for i, (label, value) in enumerate([(k.title(), click[k]["value"]) for k in ("speed", "attack", "defense")] + [("Live clicks", len(unit["track"])-unit["start"]) ]):
        bx = x+12+i*58
        text(commands, bx, y+132, label.upper(), 6.5, color=MUTED)
        text(commands, bx, y+114, value, 15, True)
    for i, weapon in enumerate(unit["weapons"][:2]):
        kind = {"E":"Energy", "B":"Ballistic", "R":"Rocket", "M":"Melee", "A":"Artillery"}[weapon["type"]]
        damage = click.get(weapon["slot"], {}).get("value")
        attack_range = "contact" if weapon["type"] == "M" else f"{weapon['min_range']}-{weapon['max_range']} in"
        text(commands, x+12, y+94-i*14, f"{weapon['slot'].title()}: {kind} {damage}  |  {attack_range}", 8.5, True)
    if unit["category"] == "Mech":
        text(commands, x+12, y+64, f"Vent {unit['vent']}   Pilot: __________________", 8)
    else:
        text(commands, x+12, y+64, "Squad / carrier: ____________________", 8)
    note = "Starting values. Use the current dial during play." if unit["core_legal"] else "Outside the current core rules. Cost is an estimate."
    for i,line in enumerate(wrap(note,225,7)):
        text(commands,x+12,y+47-i*9,line,7,color=MUTED)
    photo_label = "Photo / dial: WarrenBorn"
    if unit.get("photo_variant"):
        photo_label += " (photo: " + unit["photo_variant"] + ")"
    text(commands,x+12,y+20,photo_label,6,color=MUTED)
    text(commands,x+12,y+9,f"warrenborn.com/Unit.php?ID={unit['id']}  |  Revived 0.2",6,color=MUTED)


def main():
    units = CATALOG["units"]
    assert all("cost" in unit for unit in units), "Run points.py first"
    pdf = PDF()
    positions = [(45,405),(315,405),(45,45),(315,45)]
    for offset in range(0,len(units),4):
        commands, images = [], {}
        for unit,(x,y) in zip(units[offset:offset+4],positions):
            card(pdf,commands,images,unit,x,y)
        text(commands,45,775,"MECHWARRIOR REVIVED / UNIT CARDS",9,True,RED)
        text(commands,45,27,"Print at 100%. Cut on borders. Cards: 3.5 x 4.75 inches. Formula "+CATALOG["points_formula"]["version"],7,color=MUTED)
        text(commands,530,27,f"{offset//4+1}/{math.ceil(len(units)/4)}",7,color=MUTED)
        pdf.page(commands,images)
    output=ROOT/"revived-unit-cards.pdf"
    pdf.save(output)
    print(f"Generated {len(units)} cards on {len(pdf.pages)} Letter pages: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
