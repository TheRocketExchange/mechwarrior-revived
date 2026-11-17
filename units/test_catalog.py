"""Checks for catalog integrity, rules interactions, and reproducible pricing."""
import copy
import json
import math
import unittest
import itertools
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from parse_catalog import parse_unit
from points import CONFIG, calculate, dfa_eligible, dfa_landing_risk, dfa_rating, dial_weights, expected_damage, heat_output_factor, offensive_rating, readiness_output, readiness_profile, shot, toughness
from readiness import Readiness, order, finish_action
from force_org import DEFAULT_SIZE, GAME_SIZES, INFANTRY, PILOTS, unit_family, validate_force

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


class ForceOrganizationChecks(unittest.TestCase):
    def test_single_faction_checks_every_model_and_legacy_mixed_lists(self):
        unit = UNITS["D006"]
        force = {"faction": unit["faction"], "groups": [{"id":"C1", "members":["D006", "D006"]}]}
        self.assertGreater(validate_force(force, UNITS)["total"], 0)
        other = next(u for u in UNITS.values() if u["core_legal"] and u["category"] == unit["category"] and u["faction"] != unit["faction"])
        force["groups"][0]["members"][1] = other["id"]
        with self.assertRaisesRegex(ValueError, "every model"):
            validate_force(force, UNITS)
        mixed = dict(force, faction="")
        self.assertEqual(validate_force(mixed, UNITS), validate_force({"groups":force["groups"]}, UNITS))
        for invalid in (None, {}, "Invented", 12):
            with self.assertRaisesRegex(ValueError, "faction"):
                validate_force(dict(force, faction=invalid), UNITS)

    def force(self, mechs=("AOD108", "AOD112", "AOD096", "AOD104")):
        return {"groups": [{"id": f"M{i+1}", "members": [key], "pilot": PILOTS[i % 4]}
                           for i, key in enumerate(mechs)]}

    def add(self, force, key, count=1, **extra):
        force["groups"].append({"id": f"G{len(force['groups'])}", "members": [key] * count, **extra})

    def test_game_sizes_have_legal_real_rosters_and_legacy_default(self):
        expected = {"skirmish": (600, 4, 3, 4, 1, 1, 48),
                    "standard": (1200, 8, 6, 9, 2, 2, 48),
                    "large": (1800, 12, 9, 13, 3, 3, 72),
                    "grand": (2400, 16, 12, 18, 4, 4, 72)}
        self.assertEqual(set(GAME_SIZES), set(expected))
        candidates = sorted((u for u in UNITS.values() if u["core_legal"] and u["category"] == "Mech" and "Unique" not in u["rank"]), key=lambda u:u["cost"]["points"])
        from collections import Counter
        for key, (points, high, vehicles, squads, carriers, pilots, width) in expected.items():
            size = GAME_SIZES[key]
            self.assertEqual((size["points_limit"], size["board_width"], size["board_depth"]), (points, width, 48))
            self.assertEqual(size["limits"], dict(mechs_max=high, vehicles_max=vehicles, squads_max=squads, carriers_max=carriers, pilot_max=pilots, family_max=3))
            force, families = {"game_size": key, "groups": []}, Counter()
            for unit in candidates:
                family = unit_family(unit)
                if families[family] >= 3:
                    continue
                i = len(force["groups"])
                force["groups"].append({"id": f"M{i+1}", "members": [unit["id"]], "pilot": PILOTS[i % 4]})
                families[family] += 1
                if len(force["groups"]) == high:
                    break
            result = validate_force(force, UNITS)
            self.assertEqual(result["mechs"], high)
            self.assertLessEqual(result["total"], points)
            repeated = copy.deepcopy(force)
            for group in repeated["groups"][:4]:
                group["members"] = ["AOD108"]
            with self.assertRaisesRegex(ValueError, "Rule of three"):
                validate_force(repeated, UNITS)
            for count in (1, 2, 3):
                small = self.force(("AOD108", "AOD112", "AOD096")[:count])
                small["game_size"] = key
                self.assertEqual(validate_force(small, UNITS)["mechs"], count)
        legacy = self.force()
        self.assertEqual(validate_force(legacy, UNITS), validate_force(dict(legacy, game_size=DEFAULT_SIZE), UNITS))
        for invalid in ("unknown", "", None, 600, {}):
            with self.assertRaisesRegex(ValueError, "game size"):
                validate_force(dict(legacy, game_size=invalid), UNITS)

    def test_zero_mechs_allows_vehicles_infantry_and_mixed_forces_at_every_size(self):
        for size_id in GAME_SIZES:
            for choices in (("AOD050",), ("D006",), ("AOD030",), ("AOD050", "D006", "AOD030")):
                with self.subTest(size=size_id, choices=choices):
                    force = {"game_size": size_id, "groups": []}
                    for key in choices:
                        self.add(force, key, 2 if UNITS[key]["category"] in INFANTRY else 1)
                    result = validate_force(force, UNITS)
                    self.assertEqual(result["mechs"], 0)
                    self.assertEqual(result["groups"], len(choices))
                    self.assertGreater(result["total"], 0)

    def test_each_size_enforces_budget_pilots_carriers_and_type_caps(self):
        # Cheap, distinct test units isolate force limits from catalog pricing.
        fixtures = {}
        for category, source, prefix in (("Mech", "AOD108", "M"), ("Vehicle", "AOD050", "V"), ("Infantry", "D006", "C")):
            for i in range(20):
                unit = copy.deepcopy(UNITS[source])
                unit.update(id=f"{prefix}{i}", name=f"Test {prefix}{i}", rank="Regular")
                unit["cost"]["points"] = 1
                fixtures[unit["id"]] = unit
        for size_id, size in GAME_SIZES.items():
            limits = size["limits"]
            force = {"game_size": size_id, "groups": [{"id": f"M{i}", "members": [f"M{i}"], "pilot": PILOTS[i%4]} for i in range(2 * limits["pilot_max"])]}
            validate_force(force, fixtures)
            # Exact budget is legal; the same roster one point over is not.
            priced = copy.deepcopy(fixtures)
            priced["M0"]["cost"]["points"] = size["points_limit"] - len(force["groups"]) + 1
            self.assertEqual(validate_force(force, priced)["total"], size["points_limit"])
            priced["M0"]["cost"]["points"] += 1
            with self.assertRaisesRegex(ValueError, "above"):
                validate_force(force, priced)
            for category, prefix, cap, pattern in (("Vehicle", "V", limits["vehicles_max"], "vehicles"), ("Infantry", "C", limits["squads_max"], "squads"), ("Mech", "M", limits["mechs_max"], "Mechs")):
                changed = copy.deepcopy(force)
                if category == "Mech":
                    changed["groups"] = []
                for i in range(cap):
                    group = {"id": f"{prefix}{i}", "members": [f"{prefix}{i}"] * (2 if category in ("Infantry",) else 1)}
                    if category == "Mech":
                        group["pilot"] = PILOTS[i%4]
                    changed["groups"].append(group)
                validate_force(changed, fixtures)
                extra = copy.deepcopy(changed["groups"][-1])
                extra["id"] = "Extra"
                changed["groups"].append(extra)
                with self.assertRaisesRegex(ValueError, pattern):
                    validate_force(changed, fixtures)
            changed = copy.deepcopy(force)
            for i in range(limits["carriers_max"]):
                changed["groups"].append({"id": f"V{i}", "members": [f"V{i}"], "carrier": True})
            validate_force(changed, fixtures)
            changed["groups"].append({"id": "Extra", "members": ["V19"], "carrier": True})
            with self.assertRaisesRegex(ValueError, "carriers"):
                validate_force(changed, fixtures)
            changed = copy.deepcopy(force)
            for group in changed["groups"][:limits["pilot_max"]]:
                group["pilot"] = "Gunner"
            # Ensure no other group already uses that role.
            for i, group in enumerate(changed["groups"][limits["pilot_max"]:]):
                group["pilot"] = PILOTS[1+i%3]
            validate_force(changed, fixtures)
            changed["groups"][limits["pilot_max"]]["pilot"] = "Gunner"
            with self.assertRaisesRegex(ValueError, "each pilot"):
                validate_force(changed, fixtures)

    def test_sample_forces_are_legal_and_close(self):
        roster = json.loads((ROOT.parent / "playtest/forces.json").read_text(encoding="utf-8"))
        results = [validate_force(f, UNITS, roster["limit"]) for f in roster["forces"]]
        self.assertEqual([r["mechs"] for r in results], [8, 6, 4])
        self.assertEqual([r["squads"] for r in results], [3, 5, 9])
        self.assertTrue(all(r["carriers"] == 2 for r in results))
        self.assertLessEqual(max(r["total"] for r in results) - min(r["total"] for r in results), roster["limit"] * .02)

    def test_family_ignores_rank_variant_and_named_version(self):
        for names, family in [
            (["Dasher II", "Dasher II 'Vulpes'"], "Dasher II"),
            (["Atlas", "Dereck Hasbani (Atlas)"], "Atlas"),
            (["AgroMech", "AgroMech MOD", "AgroMech MOD B"], "AgroMech"),
            (["AgroMech MkII MOD", "AgroMech Mk II"], "AgroMech Mk II"),
            (["Kitfox", "Uller"], "Uller"),
            (["Hellbringer 'Brimstone'", "Loki 'Kaze'"], "Loki"),
            (["Cave Lion 'Rosse's Revenge'"], "Cave Lion"),
            (["Hitotsune Kozo 'Kuro Ha (Black Blade)'"], "Hitotsune Kozo"),
            (["Ti Ts'ang"], "Ti Ts'ang"),
        ]:
            for name in names:
                self.assertEqual(unit_family({"name": name}), family)
        self.assertNotEqual(unit_family({"name": "Phoenix Hawk"}), unit_family({"name": "Phoenix Hawk IIC"}))
        force = self.force(("AOD105", "AOD106", "AOD107", "AOD096"))
        validate_force(force, UNITS)
        force["groups"][-1]["members"] = ["AOD108"]
        with self.assertRaisesRegex(ValueError, "Rule of three"):
            validate_force(force, UNITS)

    def test_infantry_counts_squads_and_each_family_in_mixed_squads(self):
        force = self.force()
        for _ in range(3):
            self.add(force, "D006", 3)
        self.assertEqual(validate_force(force, UNITS)["conventional"], 9)
        force["groups"][-1]["members"][0] = "D009"
        self.add(force, "D009", 2)
        self.add(force, "D009", 3)
        validate_force(force, UNITS)
        self.add(force, "D009", 2)
        with self.assertRaisesRegex(ValueError, "Rule of three"):
            validate_force(force, UNITS)

    def test_type_and_squad_size_boundaries(self):
        force = self.force(("AOD108", "AOD112", "AOD096") * 3)
        with self.assertRaisesRegex(ValueError, "at most 8 Mechs"):
            validate_force(force, UNITS, 10000)
        force = self.force()
        for key in ("AOD050", "AOD038", "AOD042"):
            for _ in range(2):
                self.add(force, key)
        validate_force(force, UNITS)
        self.add(force, "AOD066")
        with self.assertRaisesRegex(ValueError, "6 vehicles"):
            validate_force(force, UNITS)
        force = self.force()
        for key in ("D006", "D009", "D003"):
            for _ in range(3):
                self.add(force, key, 2)
        validate_force(force, UNITS)
        self.add(force, "AOD030", 2)
        with self.assertRaisesRegex(ValueError, "9 infantry squads"):
            validate_force(force, UNITS)
        for count in (1, 4):
            force = self.force()
            self.add(force, "D006", count)
            with self.assertRaisesRegex(ValueError, "2-3 bases"):
                validate_force(force, UNITS)
        force = self.force()
        force["groups"].append({"id": "Mixed", "members": ["D006", "AOD030"]})
        with self.assertRaisesRegex(ValueError, "mix unit categories"):
            validate_force(force, UNITS)

    def test_unique_and_pilot_limits(self):
        force = self.force(("D115", "AOD108", "D115", "AOD096"))
        with self.assertRaisesRegex(ValueError, "Unique"):
            validate_force(force, UNITS, 10000)
        force = self.force()
        for group in force["groups"][:3]:
            group["pilot"] = "Gunner"
        with self.assertRaisesRegex(ValueError, "2 of each pilot"):
            validate_force(force, UNITS)

    def test_carriers_and_passengers(self):
        force = self.force()
        self.add(force, "D006", 2)
        self.add(force, "AOD050", carrier=True, passengers="G4")
        validate_force(force, UNITS)
        self.add(force, "AOD038", carrier=True, passengers="G4")
        with self.assertRaisesRegex(ValueError, "two carriers"):
            validate_force(force, UNITS)
        force["groups"][-1]["passengers"] = "M1"
        with self.assertRaisesRegex(ValueError, "infantry squad"):
            validate_force(force, UNITS)
        force["groups"][-1].pop("passengers")
        self.add(force, "AOD066", carrier=True)
        with self.assertRaisesRegex(ValueError, "2 carriers"):
            validate_force(force, UNITS)

    def test_costs_rocket_options_and_catalog_eligibility(self):
        force = self.force()
        base = validate_force(force, UNITS)["total"]
        force["groups"][0]["rocket_slot"] = "secondary"
        actual = validate_force(force, UNITS)["total"]
        self.assertEqual(actual, base - UNITS["AOD108"]["cost"]["points"] + UNITS["AOD108"]["rocket_options"]["secondary"]["points"])
        with self.assertRaisesRegex(ValueError, "above"):
            validate_force(force, UNITS, actual - 1)
        force = self.force()
        self.add(force, "AOD018", 2)
        with self.assertRaisesRegex(ValueError, "outside the core"):
            validate_force(force, UNITS)


class StarterScenarioChecks(unittest.TestCase):
    def test_patrols_and_map_support_the_four_round_starter(self):
        scenario = json.loads((ROOT.parent / "scenarios/first-contact.json").read_text(encoding="utf-8"))
        self.assertEqual(scenario["game_size"], "skirmish")
        self.assertEqual(scenario["board"], {"width": 48, "depth": 48})
        self.assertEqual(scenario["rounds"], 4)
        self.assertEqual(scenario["scoring_rounds"], [2, 3, 4])
        self.assertEqual(scenario["objective"], {"name": "Relay", "x": 24, "y": 24, "radius": 3})
        totals = []
        for force in scenario["forces"]:
            result = validate_force(force, UNITS)
            self.assertEqual((result["mechs"], result["vehicles"], result["squads"], result["groups"], result["carriers"]), (3, 1, 1, 5, 0))
            self.assertEqual(sum(len(g["members"]) for g in force["groups"]), 7)
            self.assertFalse(any(g.get("rocket_slot") for g in force["groups"]))
            totals.append(result["total"])
        self.assertEqual(len(totals), 2)
        self.assertLessEqual(max(totals)-min(totals), 12)
        self.assertEqual(scenario["deployment"], {"south": [0,8], "north": [40,48]})
        terrain = scenario["terrain"]
        self.assertEqual(len({t["id"] for t in terrain}), 6)
        for t in terrain:
            self.assertTrue(0 <= t["x"] < t["x"]+t["width"] <= 48)
            self.assertTrue(8 < t["y"] < t["y"]+t["depth"] < 40)
            self.assertTrue(any(other["kind"] == t["kind"] and other["x"] == 48-t["x"]-t["width"] and other["y"] == 48-t["y"]-t["depth"] and other["width"] == t["width"] and other["depth"] == t["depth"] for other in terrain))
            near_x = max(t["x"], min(24, t["x"]+t["width"]))
            near_y = max(t["y"], min(24, t["y"]+t["depth"]))
            self.assertGreater(math.hypot(near_x-24, near_y-24), 3)


class PricingChecks(unittest.TestCase):
    def test_original_equipment_identities_and_salvage(self):
        names = json.loads((ROOT / "equipment.json").read_text())
        self.assertEqual([names["attack"][c] for c in ("green", "gray", "black")], ["Repair", "Command", "Salvage"])
        self.assertEqual([names[k]["red"] for k in ("B", "E", "M")], ["Armor Piercing", "Pulse", "Hand-to-Hand Weapon"])
        unit = basic("Mech")
        before = calculate(unit)
        for click in unit["track"]:
            click["attack"]["color"] = "black"
            click["speed"]["color"] = "blue"
            self.assertEqual(offensive_rating(unit, click), 0)
            self.assertEqual(dfa_rating(unit, click), 0)
        self.assertEqual(calculate(unit)["breakdown"]["firepower"], 0)
        self.assertLess(calculate(unit)["points"], before["points"])
        self.assertGreater(calculate(unit)["points"], 1)  # Survivability and movement still matter.
        self.assertEqual(readiness_profile([10, 0, 10], horizon=6, can_attack=[True, False, True])[1], 0)

    def test_armor_grades_piercing_and_agility(self):
        unit = basic("Mech", "M")
        click = unit["track"][0]
        none = toughness(unit, click)
        click["defense"]["color"] = "gray"
        heavy = toughness(unit, click)
        click["defense"]["color"] = "black"
        self.assertGreater(toughness(unit, click), heavy)
        self.assertGreater(heavy, none)
        click["primary"]["color"] = "black"
        agile = toughness(unit, click)
        click["primary"]["color"] = "white"
        self.assertGreater(agile, toughness(unit, click))
        target = {"category":"Vehicle", "defense":18, "armor":2, "cover":0}
        weapon = unit["weapons"][0]
        weapon["type"] = "B"
        click["primary"]["color"] = "red"
        self.assertAlmostEqual(shot(unit, click, weapon, target), expected_damage(8,18,3))
        weapon["type"] = "E"
        click["primary"]["color"] = "white"
        self.assertAlmostEqual(shot(unit, click, weapon, target), expected_damage(8,18,3,armor=2,piercing=1))
        self.assertAlmostEqual(expected_damage(8,18,3,armor=1,final_cap=1), expected_damage(8,18,1,cap=1))

    def test_weapon_symbols_control_red_blue_and_gray_equipment(self):
        unit = basic("Mech", "E")
        click, weapon = unit["track"][0], unit["weapons"][0]
        target = {"category":"Vehicle", "defense":18, "armor":0, "cover":0}
        click["primary"]["color"] = "red"
        hit = expected_damage(8,18,1,cap=1)
        self.assertAlmostEqual(shot(unit, click, weapon, target), expected_damage(8,18,3)+hit*expected_damage(6,18,3))
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True), expected_damage(8,18,3))
        weapon["type"] = "M"
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True), sum(expected_damage(8,18,d) for d in range(1,7))/6)
        click["primary"]["color"] = "blue"
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True), (1+hit)*expected_damage(8,18,3))
        click["speed"]["color"] = "blue"
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True,dfa=True), expected_damage(8,20,5))
        unit["category"] = "Vehicle"
        weapon["type"] = "E"
        click["primary"]["color"] = "gray"
        self.assertEqual(shot(unit, click, weapon, target, close=True), 0)
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True,flamers=True), expected_damage(8,18,4))
        self.assertEqual(shot(unit, click, weapon, dict(target,category="Mech"), close=True,flamers=True), 0)

    def test_streak_ecm_and_equipment_cost_premiums(self):
        unit = basic()
        click, weapon = unit["track"][0], unit["weapons"][0]
        target = {"category":"Vehicle", "defense":18, "armor":0, "cover":0}
        click["primary"]["color"] = "black"
        self.assertAlmostEqual(shot(unit, click, weapon, target, indirect=True), expected_damage(8,18,2))
        for extra in ({"electronic_camouflage":True}, {"shutdown":True}):
            self.assertEqual(shot(unit, click, weapon, dict(target, **extra), indirect=True), 0)
            self.assertGreater(shot(unit, click, weapon, dict(target, **extra)), 0)
        for field, shades in (("speed", ("red","blue","green","black","gray","purple")),
                              ("attack", ("red","blue","green","gray","purple")),
                              ("defense", ("red","blue","green","black","gray","purple"))):
            baseline = basic()
            price = calculate(baseline)["breakdown"]["raw"]
            for shade in shades:
                changed = copy.deepcopy(baseline)
                for row in changed["track"]:
                    row[field]["color"] = shade
                with self.subTest(field=field, shade=shade):
                    self.assertGreater(calculate(changed)["breakdown"]["raw"], price)
        early, late = basic(), basic()
        early["track"][0]["speed"]["color"] = "gray"
        late["track"][-1]["speed"]["color"] = "gray"
        self.assertGreater(calculate(early)["points"], calculate(late)["points"])

    def profile(self, damage, defenses=None, category="Mech"):
        unit = basic(category)
        unit["track"] = [copy.deepcopy(unit["track"][0]) for _ in damage]
        for i, value in enumerate(damage):
            unit["track"][i]["primary"]["value"] = value
            if defenses:
                unit["track"][i]["defense"]["value"] = defenses[i]
        return unit

    def test_strong_opening_and_slower_degradation_are_worth_more(self):
        # Same values and average, different order: earlier power is worth more.
        for category in ("Mech", "Vehicle", "Infantry", "Battle Armor"):
            opening = self.profile([4, 1, 1, 1, 1, 1], category=category)
            late = self.profile([1, 1, 1, 1, 1, 4], category=category)
            self.assertGreater(calculate(opening)["breakdown"]["raw"], calculate(late)["breakdown"]["raw"])
        # Both open at 4 and contain the same values; one keeps its good
        # second click, while the other's recovery comes near destruction.
        sustained = self.profile([4, 4, 1, 1, 1, 1])
        late_rebound = self.profile([4, 1, 1, 1, 1, 4])
        self.assertGreater(calculate(sustained)["points"], calculate(late_rebound)["points"])
        steady = self.profile([4] * 6)
        self.assertGreater(calculate(steady)["points"], calculate(sustained)["points"])

    def test_defense_and_firepower_are_valued_on_the_same_click(self):
        protected_power = self.profile([4, 4, 1, 1], [20, 20, 16, 16])
        protected_tail = self.profile([4, 4, 1, 1], [16, 16, 20, 20])
        # Disable the early-click preference to isolate the interaction.
        with patch.dict(CONFIG, dial_start_weight=1, dial_end_weight=1):
            self.assertGreater(calculate(protected_power)["points"], calculate(protected_tail)["points"])

    def test_dial_weights_preserve_a_flat_profile_and_keep_the_tail(self):
        for length in (1, 2, 6, 23):
            weights = dial_weights(length)
            self.assertAlmostEqual(sum(weights), length)
            self.assertTrue(all(value > 0 for value in weights))
        unit = self.profile([3] * 6)
        preferred = calculate(unit)["breakdown"]["raw"]
        with patch.dict(CONFIG, dial_start_weight=1, dial_end_weight=1):
            self.assertEqual(calculate(unit)["breakdown"]["raw"], preferred)
        # Even a weak last click adds survival and never removes earlier value.
        for category in ("Mech", "Vehicle", "Infantry", "Battle Armor"):
            unit = self.profile([4, 3, 1], category=category)
            before = calculate(unit)["breakdown"]["raw"]
            tail = copy.deepcopy(unit["track"][-1])
            for key in ("primary", "speed", "attack"):
                tail[key]["value"] = 0
            unit["track"].append(tail)
            self.assertGreater(calculate(unit)["breakdown"]["raw"], before)

    def test_each_click_and_printed_contribution_reconciles(self):
        unit = self.profile([4, 3, 2, 1])
        before = calculate(unit)
        for position in range(len(unit["track"])):
            for key in ("primary", "attack", "defense", "speed"):
                changed = copy.deepcopy(unit)
                changed["track"][position][key]["value"] += 1
                self.assertGreaterEqual(calculate(changed)["breakdown"]["raw"], before["breakdown"]["raw"])
        self.assertAlmostEqual(sum(before["dial"]["points"]) + before["breakdown"]["pilot_allowance"], before["breakdown"]["raw"], places=3)
        self.assertEqual(len(before["dial"]["values"]), len(unit["track"]))
        with patch.dict(CONFIG, dial_start_weight=0.5, dial_end_weight=1.5):
            with self.assertRaises(ValueError):
                calculate(unit)

    def test_later_improvements_are_not_charged_to_earlier_clicks(self):
        ratings = [0, 1, 4]
        capped = readiness_profile(ratings, cap_at_start=True)
        self.assertEqual(capped[0], 0)
        self.assertLessEqual(capped[1], 1)
        self.assertGreater(capped[2], capped[1])
        self.assertGreater(readiness_profile(ratings)[0], 0)

    def test_half_speed_only_changes_moving_fire_reach(self):
        unit = basic()
        unit["track"][0]["speed"]["value"] = 7
        click = unit["track"][0]
        half = offensive_rating(unit, click)
        click["speed"]["value"] = 8
        self.assertEqual(offensive_rating(unit, click), half)
        with patch.dict(CONFIG, advance_speed_fraction=1.0):
            self.assertGreater(offensive_rating(unit, click), half)
        click["speed"]["color"] = "blue"
        self.assertEqual(offensive_rating(unit, click), half)
        unit["weapons"][0]["type"] = "R"
        rocket = offensive_rating(unit, click)
        with patch.dict(CONFIG, advance_speed_fraction=1.0):
            self.assertEqual(offensive_rating(unit, click), rocket)

    def test_readiness_only_applies_to_non_mechs(self):
        for category in ("Vehicle", "Infantry", "Battle Armor", "Mech"):
            b = calculate(basic(category))["breakdown"]
            self.assertEqual(b["readiness_factor"] == 1, category == "Mech")
            if category != "Mech":
                self.assertLess(b["firepower"], b["firepower_before_readiness"])

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
        unit = basic("Infantry")
        click, weapon = unit["track"][0], unit["weapons"][0]
        self.assertEqual(shot(unit, click, weapon, target, close=True), 0)
        self.assertGreater(shot(unit, click, weapon, target, close=True, exposed=True), 0)
        unit["category"] = "Battle Armor"
        self.assertGreater(shot(unit, click, weapon, target, close=True), 0)

    def test_infantry_terrain_protection_is_priced_for_ranged_and_close_attacks(self):
        damage = lambda defense: expected_damage(8, defense, 3)
        cases = (("Infantry", 21, 22, 20), ("Battle Armor", 20, 21, 19))
        for category, woods, fieldworks, close in cases:
            unit = basic(category)
            incoming = .8 * (.5*damage(18) + .35*damage(woods) + .15*damage(fieldworks)) + .2 * (.85*damage(18) + .15*damage(close))
            self.assertAlmostEqual(toughness(unit, unit["track"][0]), damage(18)/incoming)
            current = toughness(unit, unit["track"][0])
            old_cover = {"Infantry":{"woods_ranged":2,"fieldworks_ranged":3,"fieldworks_close":1},
                         "Battle Armor":{"woods_ranged":1,"fieldworks_ranged":2,"fieldworks_close":0}}
            with patch.dict(CONFIG, infantry_terrain_defense=old_cover):
                self.assertGreater(current, toughness(unit, unit["track"][0]))
        for category in ("Mech", "Vehicle"):
            unit = basic(category)
            expected = damage(18)/(.8*(.5*damage(18)+.5*damage(19))+.2*damage(18))
            self.assertAlmostEqual(toughness(unit, unit["track"][0]), expected)
            with patch.dict(CONFIG, infantry_fieldworks_share=0):
                self.assertAlmostEqual(toughness(unit, unit["track"][0]), expected)

    def test_fieldworks_close_protection_and_ranged_cover_interactions(self):
        unit = basic("Mech")
        click, weapon = unit["track"][0], unit["weapons"][0]
        woods = {"category":"Infantry", "defense":21, "armor":0, "cover":3}
        fieldworks = dict(woods, defense=22, cover=4, close_cover=2)
        self.assertAlmostEqual(shot(unit, click, weapon, woods, close=True), expected_damage(8,18,3))
        self.assertAlmostEqual(shot(unit, click, weapon, fieldworks, close=True), expected_damage(8,20,3))
        self.assertAlmostEqual(shot(unit, click, weapon, fieldworks), expected_damage(8,22,3))
        click["attack"]["color"] = "black"
        self.assertEqual(shot(unit, click, weapon, fieldworks), 0)
        self.assertEqual(shot(unit, click, weapon, fieldworks, close=True), 0)
        click["attack"]["color"] = "white"
        weapon["type"] = "R"
        self.assertAlmostEqual(shot(unit, click, weapon, fieldworks, indirect=True), expected_damage(6,22,2))

    def test_stronger_cover_hit_rates_keep_white_dice_criticals(self):
        for bonus, hits in ((0,135),(2,81),(3,56),(4,36)):
            self.assertAlmostEqual(expected_damage(8,18+bonus,1,cap=1), hits/216)
        self.assertAlmostEqual(expected_damage(8,100,1,cap=1), 1/36)

    def test_dfa_hit_damage_and_landing_risk_include_critical_results(self):
        unit = basic("Mech")
        click, weapon = unit["track"][0], unit["weapons"][0]
        click["speed"]["color"] = "blue"
        target = {"category":"Vehicle", "defense":18, "armor":1, "cover":0}
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True, dfa=True), expected_damage(8, 20, 5, armor=1))
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True, exposed=True, dfa=True), expected_damage(10, 20, 5, armor=1))
        # Independently enumerate hits: a critical miss fails regardless of total.
        rolls = list(itertools.product(range(1,7), repeat=3))
        hits = sum((a == b == 6) or (not a == b == 1 and a+b+c+8 >= 20) for a,b,c in rolls)
        self.assertAlmostEqual(dfa_landing_risk(click, target), (hits + 2*(216-hits))/216)
        click["primary"]["color"] = "gray"
        weapon["type"] = "M"
        self.assertAlmostEqual(shot(unit, click, weapon, target, close=True, dfa=True), expected_damage(8, 20, 6, armor=1))
        # A high defense still allows white 6/6; armor does not change hit cost.
        target["defense"] = 100
        self.assertAlmostEqual(dfa_landing_risk(click, target), 71/36)

    def test_dfa_requires_a_mobile_jump_mech_and_a_large_target(self):
        unit = basic("Mech")
        click, weapon = unit["track"][0], unit["weapons"][0]
        click["speed"]["color"] = "blue"
        target = {"category":"Mech", "defense":18, "armor":0, "cover":0}
        self.assertTrue(dfa_eligible(unit, click, weapon, target))
        for field in ("speed", "attack", "primary"):
            changed = copy.deepcopy(click)
            changed[field]["value"] = 0
            self.assertEqual(shot(unit, changed, weapon, target, close=True, dfa=True), 0)
            self.assertEqual(dfa_rating(unit, changed), 0)
        for category in ("Vehicle", "Battle Armor", "Infantry"):
            self.assertFalse(dfa_eligible(dict(unit, category=category), click, weapon, target))
        for category in ("Battle Armor", "Infantry"):
            self.assertEqual(shot(unit, click, weapon, dict(target, category=category), close=True, dfa=True), 0)
        self.assertFalse(dfa_eligible(unit, click, dict(weapon, slot="secondary"), target))
        click["speed"]["color"] = "white"
        self.assertEqual(dfa_rating(unit, click), 0)

    def test_dfa_price_uses_current_click_damage_risk_heat_and_availability(self):
        unit = basic("Mech")
        click = unit["track"][0]
        click["speed"]["color"] = "blue"
        click["attack"]["value"] = 10
        click["primary"]["value"] = 5
        allowance = dfa_rating(unit, click)
        self.assertGreater(allowance, 0)
        normal = offensive_rating(unit, click)
        with patch.dict(CONFIG, dfa_access_weight=0):
            self.assertAlmostEqual(normal - offensive_rating(unit, click), allowance)
        with patch("points.dfa_landing_risk", return_value=0):
            self.assertGreater(dfa_rating(unit, click), allowance)
        with patch("points.heat_output_factor", return_value=0.5) as heat:
            self.assertAlmostEqual(dfa_rating(unit, click), allowance / 2)
            heat.assert_called_once_with(unit, "M", "primary", action_heat=2)
        damaged = copy.deepcopy(click)
        damaged["primary"]["value"] = 1
        self.assertLess(dfa_rating(unit, damaged), allowance)

    def test_real_blue_speed_mechs_can_jump_and_use_dfa(self):
        unit = UNITS["AOD104"]  # Starter Hatchetman; original Jump Jets are blue.
        primary = next(w for w in unit["weapons"] if w["slot"] == "primary")
        target = {"category":"Mech", "defense":18, "armor":0, "cover":0}
        blue = [c for c in unit["track"][unit["start"]:] if c["speed"]["color"] == "blue"]
        self.assertTrue(blue)
        self.assertTrue(any(dfa_eligible(unit, click, primary, target) for click in blue))
        self.assertTrue(any(dfa_rating(unit, click) > 0 for click in blue))
        with_jump = calculate(unit)
        with patch.dict(CONFIG, jump_mobility=0):
            self.assertGreater(with_jump["breakdown"]["mobility"], calculate(unit)["breakdown"]["mobility"])

    def test_energy_heat_and_vent(self):
        unit = copy.deepcopy(UNITS["AOD108"])
        self.assertLessEqual(heat_output_factor(unit,"E"), heat_output_factor(unit,"B"))
        before = heat_output_factor(unit,"E")
        unit["vent"] += 2
        self.assertGreaterEqual(heat_output_factor(unit,"E"), before)


class ReadinessChecks(unittest.TestCase):
    def test_combat_push_and_recovery_sequences(self):
        state, damage = Readiness.READY, 0
        for action in ("Fire", "Fire", "Move", "Fire", "Hold", "Fire"):
            state, push = order(state, action)
            damage += push
        self.assertEqual((state, damage), (Readiness.COMMITTED, 1))
        for action in ("Fire", "Advance", "Assault", "Bypass", "Rush", "Repair", "Coolant Flush", "Embark", "Disembark"):
            with self.assertRaises(ValueError):
                order(Readiness.SPENT, action)
        for action in ("Move", "Hold", "Disengage", "Regroup"):
            self.assertEqual(order(Readiness.SPENT, action), (Readiness.READY, 0))

    def test_other_orders_preserve_readiness_and_passengers_are_separate(self):
        passenger, carrier = Readiness.COMMITTED, Readiness.COMMITTED
        for action in ("Embark", "Disembark", "Repair", "Rush"):
            passenger, push = order(passenger, action)
            self.assertEqual((passenger, push), (Readiness.COMMITTED, 0))
        passenger, _ = order(passenger, "Hold")
        self.assertEqual(passenger, Readiness.READY)
        self.assertEqual(carrier, Readiness.COMMITTED)

    def test_skipped_shots_critical_misses_and_push_deaths(self):
        state, push = order(Readiness.COMMITTED, "Advance")
        # Shared order, three independent bases: legal shot, no shot, critical miss.
        live_after = [finish_action(live, miss, push) for live, miss in [(3, 0), (3, 0), (2, 1)]]
        self.assertEqual((state, live_after), (Readiness.SPENT, [2, 2, 0]))
        self.assertEqual(finish_action(1, 0, push), 0)  # final attack resolves, then death
        self.assertEqual(finish_action(1, 1, push), 0)  # dies before pushing, no negative dial
        self.assertEqual(finish_action(3, 0, 0), 3)  # another member never inherits a cost

    def test_optimizer_matches_exhaustive_small_schedules(self):
        # Independent oracle enumerates every attack/rest sequence, including
        # weak later clicks, improving dials, and death during a push.
        horizon = 7
        for ratings in ([1], [10, 0], [0, 2, 4], [4, 2, 1], [0, 0]):
            totals = []
            for start in range(len(ratings)):
                best = 0
                for actions in itertools.product((False, True), repeat=horizon):
                    click, state, value, legal = start, 0, 0, True
                    for attack in actions:
                        if click >= len(ratings):
                            break
                        if not attack:
                            state = 0
                        elif state == 2:
                            legal = False
                            break
                        else:
                            value += ratings[click]
                            click += int(state == 1)
                            state += 1
                    if legal:
                        best = max(best, value)
                totals.append(best / horizon)
            self.assertAlmostEqual(readiness_output(ratings, horizon), sum(totals) / len(totals))

    def test_recovering_early_preserves_a_strong_click(self):
        # F/H/F/H/F/F earns 40 on the good click, then pushes onto the dead weapon.
        self.assertAlmostEqual(readiness_output([10, 0], 6), (40 / 6 + 0) / 2)
        self.assertAlmostEqual(readiness_output([1], 24), 13 / 24)
        self.assertEqual(readiness_output([0, 0]), 0)
        with self.assertRaises(ValueError):
            readiness_output([], 24)


if __name__ == "__main__":
    unittest.main()
