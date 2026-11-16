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
from points import CONFIG, calculate, dial_weights, expected_damage, heat_output_factor, offensive_rating, readiness_output, readiness_profile, shot
from readiness import Readiness, order, finish_action
from force_org import DEFAULT_SIZE, GAME_SIZES, PILOTS, unit_family, validate_force

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
    def force(self, mechs=("AOD108", "AOD112", "AOD096", "AOD104")):
        return {"groups": [{"id": f"M{i+1}", "members": [key], "pilot": PILOTS[i % 4]}
                           for i, key in enumerate(mechs)]}

    def add(self, force, key, count=1, **extra):
        force["groups"].append({"id": f"G{len(force['groups'])}", "members": [key] * count, **extra})

    def test_game_sizes_have_legal_real_rosters_and_legacy_default(self):
        expected = {"skirmish": (600, 2, 4, 3, 4, 1, 1, 48),
                    "standard": (1200, 4, 8, 6, 9, 2, 2, 48),
                    "large": (1800, 6, 12, 9, 13, 3, 3, 72),
                    "grand": (2400, 8, 16, 12, 18, 4, 4, 72)}
        self.assertEqual(set(GAME_SIZES), set(expected))
        candidates = sorted((u for u in UNITS.values() if u["core_legal"] and u["category"] == "Mech" and "Unique" not in u["rank"]), key=lambda u:u["cost"]["points"])
        from collections import Counter
        for key, (points, low, high, vehicles, squads, carriers, pilots, width) in expected.items():
            size = GAME_SIZES[key]
            self.assertEqual((size["points_limit"], size["board_width"], size["board_depth"]), (points, width, 48))
            self.assertEqual(size["limits"], dict(mechs_min=low, mechs_max=high, vehicles_max=vehicles, squads_max=squads, carriers_max=carriers, pilot_max=pilots, family_max=3))
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
            force["groups"] = force["groups"][:low-1]
            with self.assertRaisesRegex(ValueError, "Force needs"):
                validate_force(force, UNITS)
        legacy = self.force()
        self.assertEqual(validate_force(legacy, UNITS), validate_force(dict(legacy, game_size=DEFAULT_SIZE), UNITS))
        for invalid in ("unknown", "", None, 600, {}):
            with self.assertRaisesRegex(ValueError, "game size"):
                validate_force(dict(legacy, game_size=invalid), UNITS)

    def test_each_size_enforces_budget_pilots_carriers_and_type_caps(self):
        # Cheap, distinct test units isolate force limits from catalog pricing.
        fixtures = {}
        for category, source, prefix in (("Mech", "AOD108", "M"), ("Vehicle", "AOD050", "V"), ("Conventional Infantry", "D006", "C")):
            for i in range(20):
                unit = copy.deepcopy(UNITS[source])
                unit.update(id=f"{prefix}{i}", name=f"Test {prefix}{i}", rank="Regular")
                unit["cost"]["points"] = 1
                fixtures[unit["id"]] = unit
        for size_id, size in GAME_SIZES.items():
            limits = size["limits"]
            force = {"game_size": size_id, "groups": [{"id": f"M{i}", "members": [f"M{i}"], "pilot": PILOTS[i%4]} for i in range(limits["mechs_min"])]}
            validate_force(force, fixtures)
            # Exact budget is legal; the same roster one point over is not.
            priced = copy.deepcopy(fixtures)
            priced["M0"]["cost"]["points"] = size["points_limit"] - len(force["groups"]) + 1
            self.assertEqual(validate_force(force, priced)["total"], size["points_limit"])
            priced["M0"]["cost"]["points"] += 1
            with self.assertRaisesRegex(ValueError, "above"):
                validate_force(force, priced)
            for category, prefix, cap, pattern in (("Vehicle", "V", limits["vehicles_max"], "vehicles"), ("Conventional Infantry", "C", limits["squads_max"], "squads"), ("Mech", "M", limits["mechs_max"], "Force needs")):
                changed = copy.deepcopy(force)
                if category == "Mech":
                    changed["groups"] = []
                for i in range(cap):
                    group = {"id": f"{prefix}{i}", "members": [f"{prefix}{i}"] * (2 if category in ("Conventional Infantry",) else 1)}
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
        for count in (3, 9):
            force = self.force(("AOD108", "AOD112", "AOD096") * 3)
            force["groups"] = force["groups"][:count]
            with self.assertRaisesRegex(ValueError, "4-8"):
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


class PricingChecks(unittest.TestCase):
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
        for category in ("Mech", "Vehicle", "Conventional Infantry", "Battle Armor"):
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
        for category in ("Mech", "Vehicle", "Conventional Infantry", "Battle Armor"):
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
        self.assertGreater(offensive_rating(unit, click), half)
        unit["weapons"][0]["type"] = "R"
        rocket = offensive_rating(unit, click)
        with patch.dict(CONFIG, advance_speed_fraction=1.0):
            self.assertEqual(offensive_rating(unit, click), rocket)

    def test_readiness_only_applies_to_non_mechs(self):
        for category in ("Vehicle", "Conventional Infantry", "Battle Armor", "Mech"):
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


class ReadinessChecks(unittest.TestCase):
    def test_combat_push_and_recovery_sequences(self):
        state, damage = Readiness.READY, 0
        for action in ("Fire", "Fire", "Move", "Fire", "Hold", "Fire"):
            state, push = order(state, action)
            damage += push
        self.assertEqual((state, damage), (Readiness.COMMITTED, 1))
        for action in ("Fire", "Advance", "Assault", "Rush", "Repair", "Embark", "Disembark"):
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
