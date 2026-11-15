"""Cache public WarrenBorn miniature records and their original photographs.

Run with --fetch to download missing files. Repeated runs reuse the cache.
Two workers and a delay limit load on the archive. No browser credentials are used.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
BASE = "https://www.warrenborn.com/"


def fetch(url, destination):
    if destination.exists() and destination.stat().st_size:
        return
    request = Request(url, headers={"User-Agent": "MechWarriorRevived/0.2 (personal rules reference; cached requests)"})
    last = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=35) as response:
                data = response.read()
            if not data:
                raise ValueError("empty response")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            time.sleep(0.25)
            return
        except Exception as exc:
            last = exc
            if getattr(exc, "code", None) in (403, 404):
                break
            time.sleep(1 + attempt)
    raise RuntimeError(f"{url}: {last}")


def import_one(unit_id):
    page = SOURCE / "pages" / f"{unit_id}.html"
    fetch(BASE + "Unit.php?ID=" + quote(unit_id), page)
    source = page.read_text(encoding="utf-8", errors="replace")
    photos = re.findall(r'<img\b[^>]*\bsrc=[\"\']([^\"\']*UnitSection/[^\"\']+)[\"\']', source, re.I)
    photo_records = []
    for number, photo in enumerate(photos):
        url = urljoin(BASE, photo).replace("http://", "https://")
        suffix = Path(photo).suffix.lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".gif"):
            continue
        filename = unit_id + (f"-{number+1}" if number else "") + suffix
        record = {"url": url, "file": "photos/" + filename}
        try:
            fetch(url, ROOT / record["file"])
        except Exception as exc:
            record["error"] = str(exc)
        photo_records.append(record)
    return {"id": unit_id, "source_url": BASE + "Unit.php?ID=" + unit_id,
            "page": "source/pages/" + page.name, "photos": photo_records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not args.fetch:
        parser.error("Use --fetch to download the public catalog.")
    fetch(BASE + "Search.php", SOURCE / "all-index.html")
    index = (SOURCE / "all-index.html").read_text(encoding="utf-8", errors="replace")
    all_ids = list(dict.fromkeys(re.findall(r'Unit.php\?ID=([^\"<>\s]+)', index)))
    # Hyphenated IDs belong to pilot, gear, and event cards, not miniatures.
    ids = [value for value in all_ids if re.fullmatch(r"[A-Z]+\d+", value)]
    manifest = {"source": BASE + "Search.php", "fetched_date": time.strftime("%Y-%m-%d"),
                "index_entries": len(all_ids), "figure_ids": ids,
                "non_figure_card_ids": [value for value in all_ids if value not in ids]}
    (SOURCE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.limit:
        ids = ids[:args.limit]
    records, errors = [], []
    print(f"Importing {len(ids)} miniature records from {len(all_ids)} archive entries.", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(import_one, unit_id): unit_id for unit_id in ids}
        for number, future in enumerate(as_completed(futures), 1):
            try:
                records.append(future.result())
            except Exception as exc:
                errors.append({"id": futures[future], "error": str(exc)})
            if number % 50 == 0 or number == len(ids):
                print(f"{number}/{len(ids)} records; {len(errors)} page errors", flush=True)
                (SOURCE / "downloads.json").write_text(json.dumps({"records": sorted(records, key=lambda x: x["id"]), "errors": errors}, indent=2), encoding="utf-8")
    print(f"Done. {len(records)} cached records, {len(errors)} page errors.", flush=True)


if __name__ == "__main__":
    main()
