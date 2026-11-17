"""Print every figure with complete combat and heat dials, two per Letter page."""
from __future__ import annotations

import io
import json
import math
import zlib
from pathlib import Path

from PIL import Image
from reportlab.pdfbase.pdfmetrics import stringWidth

from force_org import unit_family

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
INK, MUTED, RED, LINE = (0.16, 0.18, 0.15), (0.38, 0.41, 0.34), (0.57, 0.22, 0.18), (0.75, 0.77, 0.71)


def safe(text):
    return str(text).translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "×": "x"})).encode("cp1252", "replace").decode("cp1252")


def wrap(text, width, size):
    words, lines, line = safe(text).split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if stringWidth(candidate, "Helvetica-Bold", size) > width and line:
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
        stream = zlib.compress("\n".join(commands).encode("cp1252"))
        content = self.add(f"<< /Length {len(stream)} /Filter /FlateDecode >>\nstream\n".encode() + stream + b"\nendstream")
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


PALETTE = {
    "white": ((1, 1, 1), ""), "red": ((.96, .82, .79), "R"),
    "blue": ((.83, .90, .95), "B"), "black": ((.27, .28, .25), "K"),
    "gray": ((.85, .85, .82), "Gy"), "green": ((.84, .92, .78), "Gn"),
    "yellow": ((.97, .93, .74), "Y"), "purple": ((.90, .84, .93), "P"),
}


def cell_label(cell, heat=False):
    if cell.get("shutdown"):
        return "SD"
    if cell.get("dead"):
        return "X"
    value = cell.get("value")
    if value is None:
        return "-"
    number = f"{value:+d}" if heat and value else str(value)
    return number + PALETTE[cell.get("color", "white")][1]


def grid(commands, x, top, headers, rows, row_height=14):
    """All columns fit on one card; even the longest dial has 18-point cells."""
    label_width, width = 72, 516
    cell_width = (width - label_width) / len(headers)
    for row_index, (label, cells) in enumerate([("Click", headers)] + rows):
        bottom = top - (row_index + 1) * row_height
        commands.append(f"{rgb((.94, .94, .91))} rg {x} {bottom} {label_width} {row_height} re f")
        text(commands, x+4, bottom+4, label, 7, True)
        for index, cell in enumerate(cells):
            value, color = cell if isinstance(cell, tuple) else (str(cell), "white")
            left = x + label_width + index * cell_width
            fill = PALETTE[color][0]
            commands.append(f"{rgb(fill)} rg {left:.3f} {bottom} {cell_width:.3f} {row_height} re f")
            size = min(8, 7 if row_index == len(rows) and label == "Marks" else 8)
            while stringWidth(safe(value), "Helvetica", size) > cell_width - 2:
                size -= .25
            assert size >= 6, (label, value, cell_width)
            tw = stringWidth(safe(value), "Helvetica", size)
            text(commands, left+(cell_width-tw)/2, bottom+4, value, size, color=(1, 1, 1) if color == "black" else INK)
        commands.append(f"{rgb(LINE)} RG .3 w {x} {bottom} {width} {row_height} re S")
    bottom = top - (len(rows)+1) * row_height
    for index in range(len(headers)+1):
        left = x + label_width + index * cell_width
        commands.append(f"{rgb(LINE)} RG .3 w {left:.3f} {top} m {left:.3f} {bottom} l S")


def card(pdf, commands, images, unit, x, y, assignment=None):
    commands.append(f"{rgb(LINE)} RG 0.5 w {x} {y} 540 360 re S")
    identity = f"Catalog ID: {unit['id']}  /  {unit['set']}"
    if assignment:
        identity += "  /  " + assignment['force_name']
    text(commands, x+12, y+346, identity, 7, color=MUTED)
    lines = wrap(unit["name"], 510, 14)
    assert len(lines) <= 2, unit["id"]
    for i, line in enumerate(lines):
        text(commands, x+12, y+329-i*15, line, 14, True)
    if unit["photo"]:
        image_id, width, height = pdf.image(ROOT / unit["photo"])
        image_name = f"Im{image_id}"
        images[image_name] = image_id
        scale = min(108/width, 80/height)
        w, h = width*scale, height*scale
        commands.append(f"q {w:.3f} 0 0 {h:.3f} {x+12+(108-w)/2:.3f} {y+227+(80-h)/2:.3f} cm /{image_name} Do Q")
    text(commands, x+132, y+300, "Family: " + unit_family(unit), 8, True)
    text(commands, x+132, y+289, f"{unit['category']} / {unit['rank']} / {unit['movement']}", 7, color=MUTED)
    text(commands, x+132, y+278, "Faction: " + unit['faction'], 7, color=MUTED)
    text(commands, x+464, y+285, unit["cost"]["points"], 26, True, RED)
    text(commands, x+464, y+273, "POINTS", 7, color=MUTED)
    for i, weapon in enumerate(unit["weapons"]):
        kind = {"E":"Energy", "B":"Ballistic", "R":"Rocket", "M":"Melee", "A":"Artillery"}[weapon["type"]]
        attack_range = "contact" if weapon["type"] == "M" else f"{weapon['min_range']}-{weapon['max_range']} in"
        text(commands, x+132, y+266-i*10, f"{weapon['slot'].title()}: {kind}  |  {attack_range}", 8, True)
    category = unit["category"]
    example = {"Mech": "M1", "Vehicle": "V1", "Conventional Infantry": "C1a", "Battle Armor": "A1a"}.get(category, "T1")
    roster_label = f"Roster ID: {assignment['roster_id']} / {assignment['callsign']}" if assignment else f"Roster ID: __________  (e.g. {example})"
    text(commands, x+132, y+244, roster_label, 8)
    if category == "Mech":
        assignment_label = f"Pilot: {assignment['pilot_name']} / {assignment['pilot']}" if assignment else "Pilot: ____________________"
    elif category in ("Conventional Infantry", "Battle Armor"):
        assignment_label = f"Squad: {assignment['squad']}    Assigned carrier: None" if assignment else "Squad: ______    Assigned carrier: ______"
    elif category == "Vehicle":
        assignment_label = "Carrier: No    Assigned squad: None" if assignment else "Carrier: Yes / No    Assigned squad: ______"
    else:
        assignment_label = "Uses rules beyond this edition."
    text(commands, x+132, y+231, assignment_label, 8)
    text(commands, x+12, y+216, "COMBAT DIAL", 8, True, RED)
    text(commands, x+112, y+216, f"Clicks: {len(unit['track'])-unit['start']} (damage from Start to End)", 7)
    if not unit["core_legal"]:
        text(commands, x+335, y+216, "Outside core rules; cost is an estimate.", 7, color=RED)
    fields = [(weapon["slot"], weapon["slot"].title()+" dmg") for weapon in unit["weapons"]]
    fields += [("speed", "Speed"), ("attack", "Attack"), ("defense", "Defense")]
    rows = [(label, [(cell_label(click.get(key, {})), click.get(key, {}).get("color", "white")) for click in unit["track"]] + [("X", "gray")]) for key, label in fields]
    marks = ["Start" if i == unit["start"] else "Stop" if click.get("markers", {}).get("repair") else "" for i, click in enumerate(unit["track"])]
    rows.append(("Marks", marks + ["End"]))
    grid(commands, x+12, y+207, list(range(1, len(unit["track"])+1)) + ["End"], rows)
    if unit["heat"]:
        text(commands, x+12, y+95, f"HEAT DIAL  /  Vent {unit['vent']}", 8, True, RED)
        fields = [("primary", "Primary dmg"), ("secondary", "Secondary dmg"), ("speed", "Speed")]
        rows = [(label, [(cell_label(click.get(key, {}), heat=True), click.get(key, {}).get("color", "white")) for click in unit["heat"]]) for key, label in fields if any(key in click for click in unit["heat"])]
        grid(commands, x+12, y+87, ["Start"] + list(range(1, len(unit["heat"]))), rows, 13)
    else:
        if category != "Turret":
            text(commands, x+12, y+92, "READINESS:  Ready  /  Committed  /  Spent", 8, True)
        text(commands, x+12, y+72, "Roster ID is your label for this figure. Squad and carrier fields record assignments.", 8)
        text(commands, x+12, y+56, "Each column is one dial position. Damage moves right; repairs move left.", 8)
        text(commands, x+12, y+42, "Use the current column. Stop marks limit repairs; End is destroyed.", 8)
    text(commands, x+12, y+23, "Stop = repair stop; End = destroyed; X = lost value; SD = shutdown. Heat numbers modify the combat dial.", 6.5, color=MUTED)
    text(commands, x+12, y+13, "Colors: R red / B blue / K black / Gy gray / Gn green / Y yellow / P purple. Use Revived equipment and heat rules.", 6.5, color=MUTED)
    credit = f"Photo / dial: warrenborn.com/Unit.php?ID={unit['id']}"
    if unit.get("photo_variant"):
        credit += f" (photo shows {unit['photo_variant']})"
    text(commands, x+12, y+3, credit + "  |  Revived 0.3", 6, color=MUTED)


def main():
    units = CATALOG["units"]
    assert all("cost" in unit for unit in units), "Run points.py first"
    pdf = PDF()
    positions = [(36,405),(36,27)]
    for offset in range(0,len(units),2):
        commands, images = [], {}
        for unit,(x,y) in zip(units[offset:offset+2],positions):
            card(pdf,commands,images,unit,x,y)
        text(commands,36,778,"MECHWARRIOR REVIVED / FULL-DIAL UNIT CARDS",9,True,RED)
        text(commands,36,13,"Print at 100%. Cut on borders. Cards: 7.5 x 5 inches. Formula "+CATALOG["points_formula"]["version"],7,color=MUTED)
        text(commands,540,13,f"{offset//2+1}/{math.ceil(len(units)/2)}",7,color=MUTED)
        pdf.page(commands,images)
    output=ROOT/"revived-unit-cards.pdf"
    pdf.save(output)
    print(f"Generated {len(units)} cards on {len(pdf.pages)} Letter pages: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
