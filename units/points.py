"""The sole points calculator. Names, factions, and rarity are not inputs.

Expected damage includes all 216 three-dice outcomes and the two-white-dice
critical rule. Ratings use every live click from the starting mark onward.
All tuning constants are in points-config.json. This is a playtest estimate.
"""
from __future__ import annotations

import copy
import itertools
import json
import math
from functools import lru_cache
from pathlib import Path
from statistics import mean
from readiness import Readiness, order

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "points-config.json").read_text(encoding="utf-8"))
DICE = list(itertools.product(range(1, 7), repeat=3))


@lru_cache(maxsize=None)
def expected_damage(attack, defense, damage, armor=0, piercing=False, cap=None):
    total = 0
    for white_a, white_b, other in DICE:
        if white_a == white_b == 1:
            continue
        critical = white_a == white_b == 6
        if not critical and white_a + white_b + other + attack < defense:
            continue
        result = damage + int(critical)
        if cap is not None:
            result = min(result, cap)
        total += max(0, result - max(0, armor - int(piercing)))
    return total / 216


def number(click, key):
    return click.get(key, {}).get("value") or 0


def color(click, key):
    return click.get(key, {}).get("color", "white")


def heat_output_factor(unit, weapon_type, slot="primary", action_heat=1):
    """Best Fire/Vent schedule over a fixed horizon, using the actual heat track."""
    if unit["category"] != "Mech" or not unit["heat"]:
        return 1.0
    heat = unit["heat"]
    shutdown = next((i for i, click in enumerate(heat) if any(cell["shutdown"] for cell in click.values())), len(heat))
    if shutdown <= 0:
        return 0.0
    gain = action_heat + int(weapon_type == "E")
    @lru_cache(maxsize=None)
    def best(rounds, level):
        if not rounds:
            return 0.0
        cool = best(rounds - 1, max(0, level - max(1, unit["vent"])))
        if level >= shutdown:
            return cool
        modifier = heat[level].get(slot, {}).get("value") or 0
        damage_factor = max(0.0, 1 + modifier / CONFIG["heat_damage_reference"])
        warned = any(cell["color"] not in ("white", "green") for cell in heat[level].values())
        if warned:
            damage_factor *= CONFIG["stress_output_factor"]
        fire = damage_factor + best(rounds - 1, min(shutdown, level + gain))
        return max(cool, fire)
    return best(CONFIG["heat_rounds"], 0) / CONFIG["heat_rounds"]


def shot(unit, click, weapon, target, moving=False, indirect=False, close=False, exposed=False):
    attack = number(click, "attack")
    damage = number(click, weapon["slot"])
    if attack <= 0 or damage <= 0:
        return 0.0
    kind = weapon["type"]
    if not close and (kind == "M" or (moving and kind in ("R", "A"))):
        return 0.0
    terrain_cover = target["cover"] if not close else 0
    defense = target["defense"] - (target["cover"] if close else 0)
    damage_color = color(click, weapon["slot"])
    attack_color = color(click, "attack")
    piercing = damage_color == "red" or (kind == "E" and not close)
    equipment_bonus = 0
    if attack_color == "red" and close:
        equipment_bonus = 1
    elif attack_color == "blue" and not moving and not close:
        equipment_bonus = 1
    elif attack_color == "green" and not terrain_cover and not close:
        equipment_bonus = 1
    attack += equipment_bonus
    if close and exposed:
        attack += 2
    if attack_color == "black" and not close:
        defense -= min(1, terrain_cover)
    infantry = target["category"] in ("Conventional Infantry", "Battle Armor")
    larger = not infantry
    if not close:
        if kind == "B":
            attack -= int(moving)
            damage += int(infantry and not terrain_cover)
        if indirect:
            attack -= 2
            damage -= 1
    equipment_damage = (damage_color == "blue" and infantry) or (damage_color == "gray" and close)
    if damage_color == "green":
        equipment_damage = infantry if unit["category"] == "Conventional Infantry" else larger
    # Black damage depends on rear/shutdown; value it in the exposed half of close cases.
    if damage_color == "black" and exposed:
        equipment_damage = True
    damage += int(equipment_damage)
    cap = None
    if unit["category"] == "Conventional Infantry" and larger:
        cap = 2 if close and exposed else 1
        piercing |= close and exposed
    elif unit["category"] == "Battle Armor" and larger and close:
        damage += 1
        piercing = True
    if kind == "E" and not close and target["category"] == "Conventional Infantry":
        cap = 2
    return expected_damage(attack, defense, max(0, damage), target["armor"], piercing, cap)


def offensive_rating(unit, click):
    choices = []
    seen = set()
    for weapon in unit["weapons"]:
        if weapon["type"] == "M" or (weapon["type"] == "A" and unit["core_legal"]):
            continue
        normal = mobile = indirect = 0.0
        for target in CONFIG["targets"]:
            normal += target["weight"] * shot(unit, click, weapon, target)
            mobile += target["weight"] * shot(unit, click, weapon, target, moving=True)
            if weapon["type"] in ("R", "A"):
                indirect += target["weight"] * shot(unit, click, weapon, target, indirect=True)
        minimum = 0 if color(click, "attack") == "yellow" else weapon["min_range"]
        reach = max(0.25, 1 + CONFIG["range_per_inch"] * weapon["max_range"] - CONFIG["minimum_range_cost"] * minimum)
        arc = 360 if unit["category"] in ("Conventional Infantry", "Battle Armor") else unit["arc"]
        arc_factor = 1 + CONFIG["firing_arc_weight"] * (arc / 180 - 1)
        advance = math.ceil(number(click, "speed") * CONFIG["advance_speed_fraction"])
        if color(click, "speed") == "blue":
            advance += CONFIG["advance_equipment_bonus"]
        moving_reach = (reach + CONFIG["range_per_inch"] * advance) * arc_factor
        reach *= arc_factor
        stationary_heat = heat_output_factor(unit, weapon["type"], weapon["slot"])
        mobile_heat = heat_output_factor(unit, weapon["type"], weapon["slot"], action_heat=2)
        signature = (weapon["type"], number(click,weapon["slot"]), color(click,weapon["slot"]), minimum, weapon["max_range"], stationary_heat, mobile_heat)
        if signature in seen:
            continue
        seen.add(signature)
        value = ((CONFIG["stationary_share"] * normal * stationary_heat
                  + CONFIG["indirect_access_weight"] * indirect * stationary_heat) * reach
                 + CONFIG["moving_share"] * mobile * mobile_heat * moving_reach)
        choices.append(value)
    if unit["category"] in ("Mech", "Battle Armor", "Conventional Infantry"):
        for weapon in unit["weapons"]:
            if weapon["slot"] != "primary" and weapon["type"] != "M":
                continue
            value = sum(target["weight"] * (shot(unit, click, weapon, target, close=True) + shot(unit, click, weapon, target, close=True, exposed=True)) / 2 for target in CONFIG["targets"])
            choices.append(value * CONFIG["close_reach_factor"] * heat_output_factor(unit, "M", weapon["slot"]))
    choices.sort(reverse=True)
    return (choices[0] if choices else 0) + CONFIG["alternative_attack_weight"] * (choices[1] if len(choices) > 1 else 0)


def toughness(unit, click):
    reference = expected_damage(CONFIG["reference_attack"], CONFIG["reference_defense"], CONFIG["reference_damage"])
    incoming = 0.0
    for kind in ("B", "E", "R", "close"):
        share = CONFIG["incoming_ranged_share"] / 3 if kind != "close" else 1 - CONFIG["incoming_ranged_share"]
        for in_cover in (False, True):
            cover_share = CONFIG["cover_share"] if in_cover else 1 - CONFIG["cover_share"]
            defense = number(click, "defense")
            defense_color = color(click, "defense")
            armor = int(defense_color == "black" or (defense_color == "red" and kind == "E") or (defense_color == "blue" and kind in ("B", "R")))
            equipment = int((defense_color == "gray" and kind == "close") or (defense_color == "yellow" and kind != "close") or (defense_color == "green" and in_cover and kind != "close") or (color(click, "speed") == "black" and in_cover and kind != "close"))
            if unit["category"] == "Conventional Infantry":
                equipment = min(1, equipment + armor)
                armor = 0
            if in_cover and kind != "close":
                defense += 2 if unit["category"] == "Conventional Infantry" else 1
            incoming += share * cover_share * expected_damage(CONFIG["reference_attack"], defense + equipment, CONFIG["reference_damage"], armor, kind == "E")
    return reference / max(incoming, 1 / 216)


def readiness_profile(ratings, horizon=None, cap_at_start=False):
    """Best attack/recover output at each possible starting click.

    Pushing uses the current click's attack, then advances the actual dial.
    Recovering costs one opportunity and never repairs that damage. Starting at
    each click separately prices its output alongside that click's defense.
    The pricing cap prevents later upgrades from inflating earlier profiles;
    leave it off to model actual attack/recover schedules in isolation.
    """
    horizon = CONFIG["readiness_actions"] if horizon is None else horizon
    if horizon < 1 or not ratings:
        raise ValueError("Readiness needs live clicks and a positive horizon")

    @lru_cache(maxsize=None)
    def best(remaining, click, state, ceiling):
        if not remaining or click >= len(ratings):
            return 0.0
        recover_state, _ = order(state, "Hold")
        recover = best(remaining - 1, click, recover_state, ceiling)
        if state == Readiness.SPENT:
            return recover
        next_state, push = order(state, "Fire")
        attack = min(ratings[click], ceiling) + best(remaining - 1, click + push, next_state, ceiling)
        return max(recover, attack)

    # In per-click prices, a later improvement is paid for on its own click.
    # Capping that improvement here prevents borrowing its value backwards.
    return [best(horizon, click, Readiness.READY, ratings[click] if cap_at_start else math.inf) / horizon
            for click in range(len(ratings))]


def readiness_output(ratings, horizon=None):
    """Unweighted mean retained for the independent readiness checks."""
    return mean(readiness_profile(ratings, horizon))


def dial_weights(length):
    """Earlier clicks count more; mean weight stays one for a flat dial."""
    start, end = CONFIG["dial_start_weight"], CONFIG["dial_end_weight"]
    if length < 1 or not (math.isfinite(start) and math.isfinite(end) and start >= end > 0):
        raise ValueError("Dial weights need a positive length and finite start >= end > 0")
    if length == 1:
        return [1.0]
    scale = 2 / (start + end)
    return [scale * (start + (end - start) * i / (length - 1)) for i in range(length)]


def calculate(unit):
    live = unit["track"][unit["start"]:]
    if not live:
        raise ValueError("Cannot price an empty damage track")
    weights = dial_weights(len(live))
    toughnesses = [toughness(unit, click) for click in live]
    exposure = [weight * value for weight, value in zip(weights, toughnesses)]
    durability = sum(exposure)
    # Value each profile where it occurs. Strong armor on a later weak click
    # must not amplify an earlier weapon by multiplying unrelated dial means.
    weighted = lambda values: sum(w * value for w, value in zip(exposure, values)) / durability
    ratings = [offensive_rating(unit, click) for click in live]
    outputs = ratings if unit["category"] == "Mech" else readiness_profile(ratings, cap_at_start=True)
    unrestricted = weighted(ratings)
    firepower = weighted(outputs)
    readiness_factor = firepower / unrestricted if unrestricted else 1.0
    movements = [max(0, number(click, "speed")) * CONFIG["mobility_per_inch"]
                    + (CONFIG["hover_mobility"] if unit["movement"].lower() == "hover" else 0)
                    + (CONFIG["jump_mobility"] if color(click, "speed") == "yellow" else 0)
                    + (CONFIG["terrain_mobility"] if color(click, "speed") == "green" else 0)
                    + (CONFIG["free_disengage_mobility"] if color(click, "speed") == "gray" else 0)
                    + (CONFIG["mobility_per_inch"] if color(click, "speed") in ("blue", "red") else 0)
                    for click in live]
    supports = [(CONFIG["repair_support"] if color(click, "attack") == "gray" else 0)
                   + (CONFIG["target_heat_support"] if any(color(click, weapon["slot"]) == "yellow" for weapon in unit["weapons"]) else 0)
                   for click in live]
    mobility, support = weighted(movements), weighted(supports)
    profiles = [t * (CONFIG["base"] + m + CONFIG["firepower_weight"] * f + s)
                for t, m, f, s in zip(toughnesses, movements, outputs, supports)]
    contributions = [CONFIG["scale"] * weight * value for weight, value in zip(weights, profiles)]
    pilot = CONFIG["pilot_allowance"] if unit["category"] == "Mech" else 0
    raw = sum(contributions) + pilot
    return {"points": max(1, math.floor(raw + 0.5)), "version": CONFIG["version"],
            "dial": {"weights": [round(value, 6) for value in weights],
                     "values": [round(value, 4) for value in profiles],
                     "points": [round(value, 4) for value in contributions]},
            "breakdown": {"durability": round(durability, 4), "mobility": round(mobility, 4),
                          "firepower": round(firepower, 4),
                          "firepower_before_readiness": round(unrestricted, 4),
                          "readiness_factor": round(readiness_factor, 4), "support": round(support, 4),
                          "starting_profile": round(profiles[0], 4),
                          "average_profile": round(mean(profiles), 4),
                          "weighted_profile": round(sum(w*v for w,v in zip(weights,profiles)) / len(live), 4),
                          "pilot_allowance": pilot, "raw": round(raw, 4)}}


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    for unit in catalog["units"]:
        unit["cost"] = calculate(unit)
        unit["rocket_options"] = {}
        if unit["category"] == "Mech":
            for weapon in unit["weapons"]:
                if weapon["type"] == "B":
                    variant = copy.deepcopy(unit)
                    next(w for w in variant["weapons"] if w["slot"] == weapon["slot"])["type"] = "R"
                    unit["rocket_options"][weapon["slot"]] = calculate(variant)
    catalog["points_formula"] = CONFIG
    (ROOT / "catalog.json").write_text(json.dumps(catalog, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"Priced {len(catalog['units'])} units with formula {CONFIG['version']}.")
    print(json.dumps({u['id']:u['cost'] for u in catalog['units'] if u['id'] in ('D006','AOD030','AOD050','AOD108')}, indent=2))


if __name__ == "__main__":
    main()
