"""Checks for catalog integrity, rules interactions, and reproducible pricing."""
import copy
import json
import math
import unittest
from pathlib import Path

from PIL import Image

from parse_catalog import parse_unit
from points import CONFIG, calculate, expected_damage, heat_output_factor, shot

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
UNITS = {unit["id"]: unit for unit in CATALOG["units"]}


def basic(category="Vehicle", kind="B"):
    cell = lambda n: {"value": n, "color": "white", "dead": False, "shutdown": False}
    return {"category": category, "start": 0, "movement": "Tracked", "arc": 180,
            "core_legal": True, "heat": [], "vent": 2,
            "track": [{key: cell(n) for key, n in (("speed",6),("attack",8),("defense",18),("primary",3))} for _ in range(6)],
            "weapons": [{"slot":"primary", "type":kind, "min_range":0, "max_range":12}]}


class CatalogChecks(unittest.TestCase):
    def test_full_manifest_and_photographs(self):
        manifest = json.loads((ROOT / "source/manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(CATALOG["errors"])
        self.assertEqual(set(UNITS), set(manifest["figure_ids"]))
        self.assertEqual(len(UNITS), len(CATALOG["units"]))
        for unit in UNITS.values():
            with self.subTest(unit=unit["id"]):
                self.assertTrue(unit["photo"])
                with Image.open(ROOT / unit["photo"]) as photo:
                    photo.verify()
                self.assertTrue(unit["source_url"].endswith("ID="+unit["id"]))
                self.assertTrue(unit["weapons"])

    def test_all_costs_reproduce_from_current_formula(self):
        self.assertEqual(CATALOG["points_formula"], CONFIG)
        for unit in UNITS.values():
            with self.subTest(unit=unit["id"]):
                self.assertEqual(unit["cost"], calculate(unit))
                self.assertGreater(unit["cost"]["points"], 0)
                self.assertTrue(all(math.isfinite(n) for n in unit["cost"]["breakdown"].values()))
                for slot, cost in unit["rocket_options"].items():
                    alternate = copy.deepcopy(unit)
                    next(w for w in alternate["weapons"] if w["slot"]==slot)["type"] = "R"
                    self.assertEqual(cost, calculate(alternate))

    def test_quad_and_colossus_categories(self):
        for unit in UNITS.values():
            if unit["original_type"] in ("Quad", "Colossus"):
                self.assertEqual(unit["category"], "Mech")
                self.assertTrue(unit["heat"])
            if unit["original_type"] == "Colossus":
                self.assertFalse(unit["core_legal"])
            if unit["name"] == "Gray Death Scout Armor":
                self.assertEqual(unit["category"], "Battle Armor")

    def test_turret_survives_lost_weapon_clicks(self):
        turret = parse_unit(ROOT / "source/pages/P001.html")
        self.assertEqual(len(turret["track"]), 15)
        self.assertTrue(turret["track"][-1]["attack"]["dead"])
        self.assertIsInstance(turret["track"][-1]["defense"]["value"], int)
        self.assertFalse(turret["core_legal"])

    def test_known_source_dials(self):
        self.assertIn("Stärke", parse_unit(ROOT / "source/pages/WS093.html")["name"])
        unit = parse_unit(ROOT / "source/pages/AOD108.html")
        self.assertEqual(unit["name"], "Dasher II")
        self.assertEqual(unit["printed_points"], 144)
        self.assertEqual(len(unit["track"]), 14)
        self.assertEqual([unit["track"][0][k]["value"] for k in ("speed","attack","defense","primary","secondary")], [8,9,19,3,2])
        self.assertEqual([w["type"] for w in unit["weapons"]], ["E","B"])
        self.assertEqual(unit["heat"][3]["speed"]["value"], -1)
        self.assertTrue(all(cell["shutdown"] for cell in unit["heat"][-1].values()))


class PricingChecks(unittest.TestCase):
    def test_only_stats_affect_price(self):
        unit = copy.deepcopy(UNITS["AOD050"])
        before = calculate(unit)
        unit.update(printed_points=99999, faction="Different", name="New name", rank="Unique", id="TEST")
        self.assertEqual(before, calculate(unit))

    def test_increasing_stats_does_not_reduce_price(self):
        for key in ("speed","attack","defense","primary"):
            unit = basic()
            before = calculate(unit)["points"]
            for click in unit["track"]:
                click[key]["value"] += 1
            self.assertGreaterEqual(calculate(unit)["points"], before, key)
        unit = basic()
        before = calculate(unit)["points"]
        unit["track"].append(copy.deepcopy(unit["track"][-1]))
        self.assertGreater(calculate(unit)["points"], before)

    def test_full_track_matters(self):
        unit = basic()
        before = calculate(unit)
        unit["track"][-1]["defense"]["value"] += 4
        self.assertNotEqual(calculate(unit), before)

    def test_critical_dice_and_limits(self):
        self.assertAlmostEqual(expected_damage(0, 100, 3), 4/36)
        self.assertAlmostEqual(expected_damage(100, 0, 3), (35*3+1)/36)
        self.assertAlmostEqual(expected_damage(0, 100, 3, cap=2), 2/36)
        self.assertEqual(expected_damage(100, 0, 3, armor=1, cap=1), 0)
        self.assertAlmostEqual(expected_damage(0, 100, 0), 1/36)

    def test_weapon_tradeoffs(self):
        target = {"category":"Vehicle", "defense":18, "armor":1, "cover":0}
        unit = basic()
        click, weapon = unit["track"][0], unit["weapons"][0]
        ballistic = shot(unit, click, weapon, target)
        self.assertLess(shot(unit, click, weapon, target, moving=True), ballistic)
        weapon["type"] = "E"
        self.assertGreater(shot(unit, click, weapon, target), ballistic)
        self.assertEqual(shot(unit, click, weapon, target, moving=True), shot(unit, click, weapon, target))
        weapon["type"] = "R"
        self.assertEqual(shot(unit, click, weapon, target, moving=True), 0)
        self.assertLess(shot(unit, click, weapon, target, indirect=True), shot(unit, click, weapon, target))

    def test_infantry_close_limits_and_armor(self):
        target = {"category":"Mech", "defense":18, "armor":1, "cover":0}
        unit = basic("Conventional Infantry")
        click, weapon = unit["track"][0], unit["weapons"][0]
        self.assertEqual(shot(unit, click, weapon, target, close=True), 0)
        self.assertGreater(shot(unit, click, weapon, target, close=True, exposed=True), 0)
        unit["category"] = "Battle Armor"
        self.assertGreater(shot(unit, click, weapon, target, close=True), 0)

    def test_energy_heat_and_vent(self):
        unit = copy.deepcopy(UNITS["AOD108"])
        self.assertLessEqual(heat_output_factor(unit,"E"), heat_output_factor(unit,"B"))
        before = heat_output_factor(unit,"E")
        unit["vent"] += 2
        self.assertGreaterEqual(heat_output_factor(unit,"E"), before)


if __name__ == "__main__":
    unittest.main()
