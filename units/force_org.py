"""Shared game sizes, unit families, and roster checks."""
from collections import Counter
import math
import re

INFANTRY = {"Conventional Infantry", "Battle Armor"}
PILOTS = ("Gunner", "Skirmisher", "Brawler", "Engineer")
DEFAULT_SIZE = "standard"


def game_size(name, points, mechs, vehicles, squads, carriers, pilots, width):
    return {"name": name, "points_limit": points, "board_width": width, "board_depth": 48,
            "limits": {"mechs_max": mechs, "vehicles_max": vehicles,
                       "squads_max": squads, "family_max": 3, "carriers_max": carriers, "pilot_max": pilots}}


GAME_SIZES = {
    "skirmish": game_size("Skirmish", 600, 4, 3, 4, 1, 1, 48),
    "standard": game_size("Standard", 1200, 8, 6, 9, 2, 2, 48),
    "large": game_size("Large Battle", 1800, 12, 9, 13, 3, 3, 72),
    "grand": game_size("Grand Battle", 2400, 16, 12, 18, 4, 4, 72),
}

# Archive spelling differences and modified versions share a family. Mk II,
# IIC and other distinct chassis generations keep their own family names.
ALIASES = {
    "Di Morgan Assault Tank": "DI Morgan Assault Tank",
    "JES III Missile Carrier": "JESIII Missile Carrier",
    "Kite Reconnaisance Vehicle": "Kite Reconnaissance Vehicle",
    "Madcat Mk IV": "Mad Cat Mk IV",
    "Gray Death Scout Battle Armor": "Gray Death Scout Armor",
    "Combat Technicans": "Combat Technicians",
    "ForestryMech B": "ForestryMech",
    "Phoenix Hawk I": "Phoenix Hawk",
    "Kitfox": "Uller",
    "Hellbringer": "Loki",
}


def unit_family(unit):
    name = unit["name"].replace("’", "'").strip()
    parenthetical = re.search(r"\(([^()]+)\)$", name)
    if parenthetical:
        name = parenthetical.group(1)  # named crew (chassis)
    name = re.split(r"\s+'", name, maxsplit=1)[0]  # chassis 'nickname'
    name = re.sub(r"\s+MOD(?:[ -]?B)?$", "", name, flags=re.I)
    name = re.sub(r"\bMk\s*II\b", "Mk II", name, flags=re.I)
    return ALIASES.get(name, name)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_force(force, catalog, limit=None):
    """Validate an explicit roster; each group lists its individual catalog IDs."""
    size_id = force.get("game_size", DEFAULT_SIZE)
    require(isinstance(size_id, str) and size_id in GAME_SIZES, "Choose a supported game size")
    size = GAME_SIZES[size_id]
    limits = size["limits"]
    limit = size["points_limit"] if limit is None else limit
    faction = force.get("faction", "")
    require(isinstance(faction, str) and (not faction or faction in {u["faction"] for u in catalog.values()}),
            "Choose a catalog faction or Mixed factions")
    groups = force["groups"]
    ids = [group["id"] for group in groups]
    require(all(ids) and len(ids) == len(set(ids)), "Group IDs must be nonempty and unique")
    categories, group_types, families, unique, pilots = Counter(), {}, Counter(), Counter(), Counter()
    total = squads = carriers = rocket_count = 0
    for group in groups:
        require(bool(group["members"]), f"{group['id']}: empty group")
        require(all(key in catalog for key in group["members"]), f"{group['id']}: unknown catalog ID")
        members = [catalog[key] for key in group["members"]]
        require(not faction or all(unit["faction"] == faction for unit in members),
                f"{group['id']}: every model must belong to {faction}")
        kinds = {unit["category"] for unit in members}
        require(len(kinds) == 1, f"{group['id']}: do not mix unit categories in a squad")
        category = members[0]["category"]
        require(category in INFANTRY | {"Mech", "Vehicle"}, f"{group['id']}: unsupported unit type")
        require(all(unit["core_legal"] for unit in members), f"{group['id']}: unit outside the core rules")
        require(2 <= len(members) <= 3 if category in INFANTRY else len(members) == 1,
                f"{group['id']}: infantry squads need 2-3 bases; other groups need one")
        group_types[group["id"]] = category
        categories[category] += len(members)
        squads += int(category in INFANTRY)
        # A mixed infantry squad uses one choice of each family it contains.
        families.update({(category, unit_family(unit).casefold()) for unit in members})
        unique.update(unit["id"] for unit in members if "Unique" in unit["rank"])
        if category == "Mech":
            require(group.get("pilot") in PILOTS, f"{group['id']}: choose one pilot")
            pilots[group["pilot"]] += 1
        else:
            require(not group.get("pilot"), f"{group['id']}: only Mechs take pilots")
        if group.get("carrier"):
            require(category == "Vehicle", f"{group['id']}: only vehicles may be carriers")
            carriers += 1
        require(not group.get("passengers") or group.get("carrier"), f"{group['id']}: passengers need a carrier")
        slot = group.get("rocket_slot")
        if slot:
            require(category == "Mech" and slot in members[0]["rocket_options"], f"{group['id']}: invalid Rocket substitute")
            rocket_count += 1
            total += members[0]["rocket_options"][slot]["points"]
        else:
            total += sum(unit["cost"]["points"] for unit in members)
    require(categories["Mech"] <= limits["mechs_max"], f"Force allows at most {limits['mechs_max']} Mechs")
    require(categories["Vehicle"] <= limits["vehicles_max"], f"Force allows at most {limits['vehicles_max']} vehicles")
    require(squads <= limits["squads_max"], f"Force allows at most {limits['squads_max']} infantry squads")
    require(all(count <= limits["family_max"] for count in families.values()), "Rule of three: a family exceeds 3 choices")
    require(all(count <= 1 for count in unique.values()), "A Unique catalog ID may appear only once")
    require(all(count <= limits["pilot_max"] for count in pilots.values()), f"At most {limits['pilot_max']} of each pilot role")
    require(carriers <= limits["carriers_max"], f"At most {limits['carriers_max']} carriers")
    require(rocket_count <= 1, "At most one Rocket test substitute")
    passengers = [group["passengers"] for group in groups if group.get("passengers")]
    require(len(passengers) == len(set(passengers)), "A squad cannot start in two carriers")
    require(all(group_types.get(key) in INFANTRY for key in passengers), "Each passenger must be an infantry squad on the roster")
    require(total <= limit, f"Force costs {total}, above the {limit}-point limit")
    return {"total": total, "groups": len(groups), "mechs": categories["Mech"],
            "vehicles": categories["Vehicle"], "conventional": categories["Conventional Infantry"],
            "battle_armor": categories["Battle Armor"], "squads": squads,
            "carriers": carriers, "escape": math.ceil(total * 0.3)}
