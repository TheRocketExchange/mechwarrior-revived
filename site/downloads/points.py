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
def expected_damage(attack, defense, damage, armor=0, piercing=False, cap=None, reduction=0, final_cap=None):
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
        result = max(0, result - max(0, armor - int(piercing)) - reduction)
        total += min(result, final_cap) if final_cap is not None else result
    return total / 216


def number(click, key):
    return click.get(key, {}).get("value") or 0


def color(click, key):
    return click.get(key, {}).get("color", "white")


def heat_output_factor(unit, weapon_type, slot="primary", action_heat=1, shutdown_after=False):
    """Best Fire/Vent schedule over a fixed horizon, using the actual heat track."""
    if unit["category"] != "Mech" or not unit["heat"]:
        return 1.0
    track = tuple((click.get(slot, {}).get("value") or 0,
                   any(cell["shutdown"] for cell in click.values()),
                   any(cell["color"] not in ("white", "green") for cell in click.values())) for click in unit["heat"])
    return _heat_factor(track, max(1, unit["vent"]), action_heat + int(weapon_type == "E"), shutdown_after,
                        CONFIG["heat_rounds"], CONFIG["heat_damage_reference"], CONFIG["stress_output_factor"])


@lru_cache(maxsize=None)
def _heat_factor(track, vent, gain, shutdown_after, horizon, reference, stress):
    shutdown = next((i for i, row in enumerate(track) if row[1]), len(track))
    if shutdown <= 0:
        return 0.0
    @lru_cache(maxsize=None)
    def best(rounds, level):
        if not rounds:
            return 0.0
        cool = best(rounds - 1, max(0, level - vent))
        if level >= shutdown:
            return cool
        modifier, _, warned = track[level]
        damage_factor = max(0.0, 1 + modifier / reference)
        if warned:
            damage_factor *= stress
        fire = damage_factor + best(rounds - 1, shutdown if shutdown_after else min(shutdown, level + gain))
        return max(cool, fire)
    return best(horizon, 0) / horizon


def dfa_eligible(unit, click, weapon, target):
    return (unit["category"] == "Mech" and color(click, "speed") == "blue"
            and color(click, "attack") != "black"
            and number(click, "speed") > 0 and number(click, "attack") > 0
            and weapon["slot"] == "primary" and number(click, "primary") > 0
            and target["category"] in ("Mech", "Vehicle"))


def dfa_landing_risk(click, target, exposed=False):
    """Expected 1/2 landing damage; general critical-miss damage is not priced."""
    attack = number(click, "attack") + int(color(click, "attack") == "blue") + 2 * exposed
    defense = target["defense"] - target["cover"] + 2
    hit_chance = expected_damage(attack, defense, 1, cap=1)
    return 2 - hit_chance


def shot(unit, click, weapon, target, moving=False, indirect=False, close=False, exposed=False, dfa=False,
         special=True, alpha=False, flamers=False):
    attack = number(click, "attack")
    damage = number(click, weapon["slot"])
    if attack <= 0 or damage <= 0 or color(click, "attack") == "black":
        return 0.0
    if dfa and (not close or not dfa_eligible(unit, click, weapon, target)):
        return 0.0
    kind = weapon["type"]
    damage_color = color(click, weapon["slot"])
    is_flame = close and flamers and kind == "E" and damage_color == "gray"
    if close and unit["category"] not in ("Mech", "Battle Armor", "Conventional Infantry") and not is_flame:
        return 0.0
    if not close and (kind == "M" or (moving and kind in ("R", "A"))):
        return 0.0
    if indirect and (close or moving or target.get("electronic_camouflage")):
        return 0.0
    streak = indirect and kind in ("B", "R") and damage_color == "black"
    if indirect and not streak and kind not in ("R", "A"):
        return 0.0
    if streak and target.get("shutdown"):
        return 0.0
    if alpha and (close or moving or kind != "E" or damage_color != "black" or unit["category"] != "Mech" or not unit["heat"]):
        return 0.0
    if is_flame and target["category"] == "Mech":
        return 0.0  # Heat inflicted is valued in Support, never as physical damage.
    terrain_cover = target["cover"] if not close else 0
    defense = target["defense"] - target["cover"] + target.get("close_cover", 0) if close else target["defense"]
    if dfa:
        defense += 2
        damage += 2
    attack_color = color(click, "attack")
    piercing = 2 if not close and kind in ("B", "R") and damage_color == "red" else int(kind == "E" and not close)
    attack += int(attack_color == "blue")
    if close and exposed:
        attack += 2
    infantry = target["category"] in ("Conventional Infantry", "Battle Armor")
    larger = not infantry
    if not close:
        if kind == "B":
            attack -= int(moving)
            damage += int(infantry and not terrain_cover)
        if indirect:
            attack -= 0 if streak else 2
            damage -= 1
    damage += int((not close and damage_color == "purple" and (kind in ("B", "R") or (kind == "E" and special)))
                  or (close and kind == "M" and damage_color == "gray") or is_flame)
    damage += 2 if alpha else 0
    cap = None
    if unit["category"] == "Conventional Infantry" and larger:
        cap = 2 if close and exposed else 1
        piercing = max(piercing, int(close and exposed))
    elif unit["category"] == "Battle Armor" and larger and close:
        damage += 1
        piercing = max(piercing, 1)
    if kind == "E" and not close and target["category"] == "Conventional Infantry":
        cap = 2
    result = expected_damage(attack, defense, max(0, damage), target["armor"], piercing, cap)
    if special and close and kind == "M" and damage_color == "red":
        replacement = mean(expected_damage(attack, defense, max(0, roll + damage - number(click, weapon["slot"])), target["armor"], piercing, cap) for roll in range(1, 7))
        result = max(result, replacement)
    hit = expected_damage(attack, defense, 1, cap=1)
    if special and not dfa:
        if (not close and kind == "E" and damage_color == "red") or (close and kind == "M" and damage_color == "blue"):
            second = expected_damage(attack - (2 if not close else 0), defense, max(0, damage), target["armor"], piercing, cap)
            result += hit * second
        if not close and kind in ("B", "R") and damage_color == "blue":
            result += hit * CONFIG["anti_personnel_extra_target_share"]
    return result


def dfa_rating(unit, click):
    """A limited-use attack option, after expected landing damage and heat."""
    primary = next((w for w in unit["weapons"] if w["slot"] == "primary"), None)
    if primary is None:
        return 0.0
    net = 0.0
    for target in CONFIG["targets"]:
        if not dfa_eligible(unit, click, primary, target):
            continue
        for rear in (False, True):
            damage = shot(unit, click, primary, target, close=True, exposed=rear, dfa=True)
            net += target["weight"] * max(0, damage - dfa_landing_risk(click, target, rear)) / 2
    if not net:
        return 0.0
    reach = CONFIG["close_reach_factor"] + CONFIG["range_per_inch"] * max(0, number(click, "speed"))
    return CONFIG["dfa_access_weight"] * net * reach * heat_output_factor(unit, "M", "primary", action_heat=2)


def offensive_rating(unit, click):
    if color(click, "attack") == "black":
        return 0.0
    choices = []
    seen = set()
    for weapon in unit["weapons"]:
        if weapon["type"] == "M" or (weapon["type"] == "A" and unit["core_legal"]):
            continue
        kind, tint = weapon["type"], color(click, weapon["slot"])
        extra_heat = int(kind == "E" and tint in ("red", "purple"))
        def output(moving=False, indirect=False, alpha=False):
            values = []
            for special in (False, True):
                damage = sum(target["weight"] * shot(unit, click, weapon, target, moving=moving, indirect=indirect, special=special, alpha=alpha) for target in CONFIG["targets"])
                heat = heat_output_factor(unit, kind, weapon["slot"], action_heat=1 + int(moving) + (extra_heat if special else 0), shutdown_after=alpha)
                values.append(damage * heat)
            return max(values)
        normal, mobile = output(), output(moving=True)
        indirect = output(indirect=True) if kind in ("R", "A") or (kind == "B" and tint == "black") else 0
        minimum = weapon["min_range"]
        reach = max(0.25, 1 + CONFIG["range_per_inch"] * weapon["max_range"] - CONFIG["minimum_range_cost"] * minimum)
        arc = 360 if unit["category"] in ("Conventional Infantry", "Battle Armor") else unit["arc"]
        arc_factor = 1 + CONFIG["firing_arc_weight"] * (arc / 180 - 1)
        advance = math.ceil(number(click, "speed") * CONFIG["advance_speed_fraction"])
        moving_reach = (reach + CONFIG["range_per_inch"] * advance) * arc_factor
        reach *= arc_factor
        signature = (kind, number(click,weapon["slot"]), tint, minimum, weapon["max_range"], normal, mobile, indirect)
        if signature in seen:
            continue
        seen.add(signature)
        value = ((CONFIG["stationary_share"] * normal
                  + CONFIG["indirect_access_weight"] * indirect) * reach
                 + CONFIG["moving_share"] * mobile * moving_reach)
        choices.append(value)
        if kind == "E" and tint == "black" and unit["category"] == "Mech" and unit["heat"]:
            choices.append(CONFIG["stationary_share"] * output(alpha=True) * reach)
    for weapon in unit["weapons"]:
        kind, tint = weapon["type"], color(click, weapon["slot"])
        ordinary = unit["category"] in ("Mech", "Battle Armor", "Conventional Infantry") and (weapon["slot"] == "primary" or kind == "M")
        flame = kind == "E" and tint == "gray"
        for use_flame in ([False] if ordinary else []) + ([True] if flame else []):
            values = []
            for special in (False, True):
                value = sum(target["weight"] * (shot(unit, click, weapon, target, close=True, special=special, flamers=use_flame) + shot(unit, click, weapon, target, close=True, exposed=True, special=special, flamers=use_flame)) / 2 for target in CONFIG["targets"])
                if special and kind == "M" and tint == "green":
                    value *= 1 + CONFIG["full_strike_extra_target_share"]
                heat = heat_output_factor(unit, "M", weapon["slot"], action_heat=1 + int(special and kind == "M" and tint == "blue"))
                values.append(value * CONFIG["close_reach_factor"] * heat)
            choices.append(max(values))
    choices.sort(reverse=True)
    return ((choices[0] if choices else 0)
            + CONFIG["alternative_attack_weight"] * (choices[1] if len(choices) > 1 else 0)
            + dfa_rating(unit, click))


def toughness(unit, click):
    reference = expected_damage(CONFIG["reference_attack"], CONFIG["reference_defense"], CONFIG["reference_damage"])
    terrain_defense = CONFIG["infantry_terrain_defense"].get(unit["category"])
    fieldworks_share = CONFIG["infantry_fieldworks_share"] if terrain_defense else 0
    terrains = {"open": 1 - CONFIG["cover_share"],
                "woods": CONFIG["cover_share"] - fieldworks_share,
                "fieldworks": fieldworks_share}
    incoming = 0.0
    for kind in ("B", "E", "R", "close"):
        share = CONFIG["incoming_ranged_share"] / 3 if kind != "close" else 1 - CONFIG["incoming_ranged_share"]
        for terrain, cover_share in terrains.items():
            if not cover_share:
                continue
            in_cover = terrain != "open"
            defense = number(click, "defense")
            defense_color = color(click, "defense")
            armor = 2 if defense_color == "black" or (defense_color == "red" and kind == "E") or (defense_color == "blue" and kind in ("B", "R")) else int(defense_color == "gray")
            equipment = int(kind != "close" and (defense_color == "green" or color(click, "speed") == "red" or (color(click, "speed") == "green" and in_cover)))
            if unit["category"] == "Conventional Infantry":
                equipment = min(1, equipment + armor)
                armor = 0
            if terrain_defense:
                defense += terrain_defense.get(f"{terrain}_{'close' if kind == 'close' else 'ranged'}", 0)
            elif in_cover and kind != "close":
                defense += 1
            ams = int(defense_color == "purple" and kind in ("B", "R"))
            agility = kind == "close" and any(w["type"] == "M" and color(click, w["slot"]) == "black" for w in unit["weapons"])
            blocked = CONFIG["ecm_blocked_share"].get(kind, 0) if color(click, "speed") == "black" else 0
            incoming += share * cover_share * (1 - blocked) * expected_damage(CONFIG["reference_attack"], defense + equipment, CONFIG["reference_damage"], armor, kind == "E", reduction=ams, final_cap=1 if agility else None)
    return reference / max(incoming, 1 / 216)


def readiness_profile(ratings, horizon=None, cap_at_start=False, can_attack=None):
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
    can_attack = [True] * len(ratings) if can_attack is None else can_attack
    if len(can_attack) != len(ratings):
        raise ValueError("Each readiness click needs an attack permission")

    @lru_cache(maxsize=None)
    def best(remaining, click, state, ceiling):
        if not remaining or click >= len(ratings):
            return 0.0
        recover_state, _ = order(state, "Hold")
        recover = best(remaining - 1, click, recover_state, ceiling)
        if state == Readiness.SPENT or not can_attack[click]:
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


def support_rating(unit, click):
    """Shared utility allowances; direct damage and self-protection are priced elsewhere."""
    tint = color(click, "attack")
    support = CONFIG["attack_support"].get(tint, 0)
    if tint == "red" and number(click, "attack") <= 0:
        support = 0
    if color(click, "defense") == "purple":
        support += CONFIG["ams_ally_support"]
    # Duplicate systems offer no stacking benefit on one unit.
    abilities = {(w["type"] if w["type"] != "R" else "B", color(click, w["slot"])) for w in unit["weapons"]}
    if ("B", "gray") in abilities:
        support += CONFIG["point_defense_support"] * max(0, number(click, "defense") - CONFIG["point_defense_reference"]) / CONFIG["point_defense_step"]
    if tint != "black":
        usable = {(w["type"] if w["type"] != "R" else "B", color(click, w["slot"])) for w in unit["weapons"] if number(click, w["slot"]) > 0}
        if ("E", "blue") in abilities:
            support += CONFIG["grapple_support"]
        if number(click, "attack") > 0:
            for kind, shade, weight in (("B", "green", "homing_support"), ("E", "green", "tsemp_support"), ("E", "gray", "flamer_heat_support")):
                if (kind, shade) in usable:
                    support += CONFIG[weight]
    return support


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
    outputs = ratings if unit["category"] == "Mech" else readiness_profile(ratings, cap_at_start=True, can_attack=[color(c, "attack") != "black" for c in live])
    unrestricted = weighted(ratings)
    firepower = weighted(outputs)
    readiness_factor = firepower / unrestricted if unrestricted else 1.0
    movements = [max(0, number(click, "speed")) * CONFIG["mobility_per_inch"]
                    + (CONFIG["hover_mobility"] if unit["movement"].lower() == "hover" else 0)
                    + (CONFIG["jump_mobility"] if color(click, "speed") == "blue" and number(click, "speed") > 0 else 0)
                    + (CONFIG["free_disengage_mobility"] if color(click, "speed") in ("blue", "red") and number(click, "speed") > 0 else 0)
                    + (CONFIG["recon_mobility"] if color(click, "speed") == "purple" and number(click, "speed") > 0 else 0)
                    + (CONFIG["infiltrate_start_mobility"] if index == 0 and color(click, "speed") == "gray" else 0)
                    for index, click in enumerate(live)]
    supports = [support_rating(unit, click) for click in live]
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
