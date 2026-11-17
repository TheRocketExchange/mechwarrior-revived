"""Place credited, unaltered miniature photographs in the HTML rulebook."""
from functools import lru_cache
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNER = ("D115", "D113", "F084")

# Anchors keep photographs beside their subjects as the rules are revised.
# These captions describe the collection; the surrounding text supplies rules.
PHOTOS = {
    "rules.html": [
        ("1-how-the-game-works", ("D115", "AOD050", "D006"), "BattleMechs, vehicles, and infantry."),
        ("2-prepare-the-table", ("D113", "F084"), "Original figures. Original combat dials."),
        ("3-rounds-and-activation", ("AOD050", "D009"), "Vehicles and infantry take their turn."),
        ("4-actions", ("AOD104",), "A Hatchetman from Age of Destruction."),
        ("5-movement-and-facing", ("AOD108", "D009"), "A Dasher II and a Hoverbike Squad."),
        ("6-terrain-and-sight", ("D006", "L024"), "Infantry and battle armor."),
        ("7-combat", ("CA112", "F075"), "A Rifleman and an Arbalest."),
        ("8-heat", ("D116",), "Erin Johnston's Jupiter, from the original Dark Age set."),
        ("9-transport", ("F025", "D006"), "A Saxon APC and foot infantry."),
        ("10-objectives-and-victory", ("D009", "L024"), "Small bases have a place in the battle."),
        ("11-build-your-force", ("D115", "AOD052", "F022"), "Start with the models in your collection."),
    ],
    "weapons.html": [
        ("three-weapon-types", ("CA112", "L118", "D057"), "Ballistic, Energy, and Rocket weapon carriers."),
        ("damage-and-heat", ("D116",), "A Jupiter on its original clix base."),
    ],
    "equipment.html": [
        ("speed", ("AOD108", "D009"), "'Mechs and mobile infantry."),
        ("attack", ("D113",), "Kendrick Fetladral's Mad Cat III."),
        ("defense", ("D115", "F022"), "An Atlas and Fenrir Battle Armor."),
        ("ballistic-and-rocket-damage", ("CA112", "D057"), "A Rifleman and a JES Missile Carrier."),
        ("energy-damage", ("L118",), "Ken Roos's Warhammer IIC."),
        ("melee-damage", ("F084",), "The Hatchetman."),
        ("heat-colors", ("D116",), "Read the heat dial separately from the combat dial."),
    ],
    "points.html": [("why-the-whole-dial-matters", ("AOD108", "D115", "D006"), "Different models, one points formula.")],
    "turn.html": [
        ("each-round", ("D113", "AOD050", "D006"), "A turn for every activation group."),
        ("attacks", ("F084", "CA112"), "Close combat and ranged fire."),
    ],
    "readiness.html": [("recovery", ("AOD050", "D009"), "Vehicles and squads use readiness.")],
    "pilots.html": [(None, ("AOD108", "AOD104"), "Choose a pilot for each 'Mech.")],
    "forces.html": [(None, ("D115", "AOD052", "F022"), "Build around the models you want to field.")],
    "starter-forces.html": [(None, ("AOD106", "AOD104", "AOD112"), "The 'Mechs of Patrol A.")],
    "dead-air.html": [("the-two-patrols", ("AOD104", "AOD108"), "Two patrols. One relay station.")],
    "first-contact.html": [("choose-your-patrols", ("AOD106", "AOD050", "D006"), "A 'Mech, a tank, and a foot squad from the starter patrols.")],
    "seize-and-hold.html": [("set-up", ("D006", "F022"), "Infantry and battle armor at the heart of the fight.")],
    "breakthrough.html": [("set-up", ("AOD108", "AOD050", "D009"), "A fast-moving column.")],
    "hold-the-station.html": [("set-up", ("F084", "L024"), "The fight for the station.")],
    "combat-rhythm.html": [(None, ("AOD108", "AOD050", "D006"), "Heat, readiness, and the next order.")],
    "scenarios.html": [(None, ("D113", "F025", "D006"), "Choose your battlefield.")],
    "aids.html": [(None, ("F084", "D009"), "Bring your models to the table.")],
}


@lru_cache(maxsize=1)
def models():
    return {unit["id"]: unit for unit in json.loads((ROOT / "units/catalog.json").read_text(encoding="utf-8"))["units"]}


def photo_link(unit_id, banner=False):
    unit = models()[unit_id]
    # Name the chassis in a short caption; the linked datasheet identifies its pilot/variant.
    name = unit["name"]
    if "(" in name and name.endswith(")"):
        name = name.rsplit("(", 1)[1][:-1]
    loading = 'fetchpriority="high"' if banner else 'loading="lazy"'
    return (f'<a class="model-photo" href="unit.html?id={unit_id}">'
            f'<img src="{escape(unit["photo"], quote=True)}" alt="{escape(unit["name"], quote=True)} MechWarrior clix miniature" '
            f'width="200" height="190" decoding="async" {loading}>'
            f'<span>{escape(name)}<small>{unit_id}</small></span></a>')


def banner_html():
    return ('<div class="masthead-photography"><div class="masthead-models" aria-label="Original MechWarrior miniatures">'
            + ''.join(photo_link(unit_id, banner=True) for unit_id in BANNER)
            + '</div><a class="masthead-photo-credit" href="sources.html#unit-catalog-and-photographs">Miniature photos: WarrenBorn</a></div>')


def illustrate(filename, body):
    for anchor, unit_ids, caption in PHOTOS.get(filename, []):
        figure = ('<figure class="rule-photo"><div class="rule-photo-models">'
                  + ''.join(photo_link(unit_id) for unit_id in unit_ids)
                  + f'</div><figcaption>{escape(caption)} '
                  '<a href="sources.html#unit-catalog-and-photographs">Photos: WarrenBorn</a></figcaption></figure>')
        if anchor is None:
            body = figure + body
        else:
            # Fail loudly if an edited heading would silently drop its photographs.
            marker = f'<h2 id="{anchor}">'
            if marker not in body:
                raise ValueError(f'Missing photo placement: {filename}#{anchor}')
            end = body.index('</h2>', body.index(marker)) + len('</h2>')
            body = body[:end] + figure + body[end:]
    return body
