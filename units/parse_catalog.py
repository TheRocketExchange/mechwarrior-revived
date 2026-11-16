"""Read cached figure pages into a reproducible, source-linked unit catalog."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

from lxml import html

ROOT = Path(__file__).resolve().parent


def cell_data(cell):
    text = " ".join(cell.text_content().split())
    images = [Path(image.get("src", "")).name.lower() for image in cell.xpath(".//img")]
    color = Path(cell.get("background", "")).name.lower().split("_")[0]
    return {"value": int(text) if re.fullmatch(r"[+-]?\d+", text) else None,
            "color": color if color else "white", "dead": "bullets.jpg" in images,
            "shutdown": "shutdown.gif" in images, "start": "start.gif" in images,
            "repair": "repair.gif" in images}


def read_rows(table):
    rows, damage_number = {}, 0
    for row in table.xpath("./tr|./tbody/tr"):
        cells = row.xpath("./td")
        if not cells:
            continue
        icons = [Path(image.get("src", "")).stem for image in cells[0].xpath(".//img")]
        icon = icons[0] if icons else ""
        if "Damage" in icon:
            key = "primary" if damage_number == 0 else "secondary"
            damage_number += 1
        elif "Speed" in icon:
            key = "speed"
        elif icon.lower() in ("attack", "defense"):
            key = icon.lower()
        elif any(cell.xpath('.//img[contains(@src,"Start.gif") or contains(@src,"Repair.gif")]') for cell in cells):
            key = "markers"
        else:
            continue
        rows[key] = {"symbol": icon, "cells": [cell_data(cell) for cell in cells[1:]]}
    return rows


def metadata(document):
    result = {}
    for bold in document.xpath("//b"):
        label = bold.text_content().strip().rstrip(":")
        if not label or len(label) > 35:
            continue
        parts = [bold.tail or ""]
        for sibling in bold.itersiblings():
            if sibling.tag == "br":
                break
            parts.append(sibling.text_content())
            parts.extend(sibling.xpath(".//img/@alt"))
            parts.append(sibling.tail or "")
        result[label] = " ".join(" ".join(parts).split())
    return result


def parse_unit(path):
    raw = path.read_bytes()
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        source = raw.decode("cp1252")
    source = re.sub(r"(<td\b[^<>]*)</td>", r"\1></td>", source, flags=re.I)
    document = html.fromstring(source)
    meta = metadata(document)
    tables = document.xpath('//table[@border="2"]')
    if not meta.get("Name"):
        raise ValueError("missing name")
    if not tables:
        raise ValueError("no combat-dial table: " + meta.get("Unit Type", "unknown"))
    combat = read_rows(tables[0])
    # DropShip turret records explicitly list speed 0 and have no speed dial.
    if "speed" not in combat and meta.get("Unit Type") == "Turret" and meta.get("Max Speed") == "0" and "attack" in combat:
        combat["speed"] = {"symbol": "StationarySpeed", "cells": [dict(cell, value=None if cell["dead"] else 0, color="white") for cell in combat["defense"]["cells"]]}
    if not all(key in combat for key in ("speed", "attack", "defense")):
        raise ValueError("missing combat rows")
    unit_type = meta.get("Unit Type", "")
    name = meta["Name"]
    if "mech" in unit_type.lower() or unit_type in ("Quad", "Colossus"):
        category = "Mech"
    elif "infantry" in unit_type.lower():
        category = "Battle Armor" if re.search(r"battle\s*armor|\bPAL\s+Suit\b|Gray Death Scout Armor", name, re.I) else "Conventional Infantry"
    elif unit_type == "Turret":
        category = "Turret"
    else:
        category = "Vehicle"
    photos = document.xpath('//img[contains(@src,"UnitSection/")]/@src')
    photo = urljoin("https://www.warrenborn.com/", photos[0]).replace("http://", "https://") if photos else None
    local_photo = "photos/" + path.stem + Path(photos[0]).suffix.lower() if photos else None
    start = next((i for i, cell in enumerate(combat.get("markers", {}).get("cells", [])) if cell["start"]), 0)
    columns = max(len(row["cells"]) for row in combat.values())
    track = []
    for i in range(columns):
        click = {key: row["cells"][i] for key, row in combat.items() if i < len(row["cells"])}
        if all(click.get(key, {}).get("dead", False) for key in ("speed", "attack", "defense")):
            break
        track.append(click)
    if not track or start >= len(track):
        raise ValueError("invalid live combat track")
    heat = []
    if len(tables) > 1:
        heat_rows = read_rows(tables[1])
        if heat_rows:
            for i in range(max(len(row["cells"]) for row in heat_rows.values())):
                heat.append({key: row["cells"][i] for key, row in heat_rows.items() if i < len(row["cells"])})
    weapons = []
    for key, label in (("primary", "Primary"), ("secondary", "Secondary")):
        if key not in combat:
            continue
        symbol = combat[key]["symbol"]
        weapon_type = "E" if "Energy" in symbol else "M" if "Melee" in symbol else "A" if "Artillery" in symbol else "B"
        ranges = re.search(r"(\d+)\s*target\(s\) at\s*(\d+)\s*/\s*(\d+)", meta.get(label, ""))
        weapons.append({"slot": key, "symbol": symbol, "type": weapon_type,
                        "targets": int(ranges[1]) if ranges else 1,
                        "min_range": int(ranges[2]) if ranges else 0,
                        "max_range": int(ranges[3]) if ranges else 0})
    # An unambiguous missile-only vehicle name identifies its single B weapon.
    if len(weapons) == 1 and weapons[0]["type"] == "B" and re.search(r"missile carrier|\b(?:LRM|SRM)\s+(?:battery|team|launcher)", name, re.I):
        weapons[0]["type"] = "R"
        weapons[0]["identification"] = "Single ranged weapon on a named missile/LRM/SRM unit; archive unit name."
    unsupported = []
    if re.search(r"vtol|helicopter|aerospace|fighter|dropship", unit_type + " " + name, re.I):
        unsupported.append("Aircraft and DropShips need rules beyond this edition.")
    if weapons and all(weapon["type"] == "A" for weapon in weapons):
        unsupported.append("Artillery-only unit; no ordinary ranged weapon in this record.")
    if re.search(r"colossal|colossus|aquatic|submarine", unit_type + " " + name, re.I):
        unsupported.append("This unit type needs rules beyond this edition.")
    for key in ("speed", "attack", "defense"):
        if any(click.get(key, {}).get("value") is None and not (unit_type == "Turret" and click.get(key, {}).get("dead")) for click in track[start:]):
            raise ValueError("missing numeric " + key + " on a live click")
    return {"id": path.stem, "name": name, "variant": meta.get("Variant Name", ""),
            "set": meta.get("Expansion", ""), "faction": meta.get("Faction", ""),
            "rank": meta.get("Rank", ""), "class": meta.get("Class", ""),
            "printed_points": int(meta.get("Points", "0")), "category": category,
            "original_type": unit_type, "movement": combat["speed"]["symbol"].replace("Speed", ""),
            "arc": int(meta.get("Arc", "0")), "rear_arc": int(meta.get("Rear Arc", "0")),
            "vent": int(meta.get("Vent", "0")), "start": start, "track": track, "heat": heat,
            "weapons": weapons, "core_legal": not unsupported, "restriction": " ".join(unsupported),
            "photo": local_photo if local_photo and (ROOT / local_photo).exists() else None,
            "photo_source": photo, "photo_credit": "WarrenBorn miniature archive",
            "source_url": "https://www.warrenborn.com/Unit.php?ID=" + path.stem}


def main():
    manifest = json.loads((ROOT / "source/manifest.json").read_text(encoding="utf-8"))
    units, errors = [], []
    for unit_id in manifest["figure_ids"]:
        path = ROOT / "source/pages" / (unit_id + ".html")
        if not path.exists():
            errors.append({"id": unit_id, "error": "not downloaded"})
            continue
        try:
            units.append(parse_unit(path))
        except Exception as exc:
            errors.append({"id": unit_id, "error": str(exc)})
    catalog = {"version": "0.3", "source": manifest["source"], "expected_count": len(manifest["figure_ids"]),
               "units": units, "errors": errors}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    summary = {"expected": catalog["expected_count"], "parsed": len(units),
               "with_photo": sum(bool(unit["photo"]) for unit in units),
               "categories": dict(Counter(unit["category"] for unit in units)),
               "errors": errors}
    (ROOT / "coverage.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "errors"}))
    print("Errors:", dict(Counter(error["error"] for error in errors)))


if __name__ == "__main__":
    main()
