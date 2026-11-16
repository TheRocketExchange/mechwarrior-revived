"""Unit families and roster checks for the standard Revived force organization."""
from collections import Counter
import math
import re

INFANTRY = {"Conventional Infantry", "Battle Armor"}
PILOTS = ("Gunner", "Skirmisher", "Brawler", "Engineer")
LIMITS = {"mechs_min": 4, "mechs_max": 8, "vehicles_max": 6,
          "squads_max": 9, "family_max": 3, "carriers_max": 2, "pilot_max": 2}

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


def validate_force(force, catalog, limit=1200):
    """Validate an explicit roster; each group lists its individual catalog IDs."""
    groups = force["groups"]
    ids = [group["id"] for group in groups]
    require(all(ids) and len(ids) == len(set(ids)), "Group IDs must be nonempty and unique")
    categories, group_types, families, unique, pilots = Counter(), {}, Counter(), Counter(), Counter()
    total = squads = carriers = rocket_count = 0
    for group in groups:
        require(bool(group["members"]), f"{group['id']}: empty group")
        require(all(key in catalog for key in group["members"]), f"{group['id']}: unknown catalog ID")
        members = [catalog[key] for key in group["members"]]
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
    require(LIMITS["mechs_min"] <= categories["Mech"] <= LIMITS["mechs_max"], "Force needs 4-8 Mechs")
    require(categories["Vehicle"] <= LIMITS["vehicles_max"], "Force allows at most 6 vehicles")
    require(squads <= LIMITS["squads_max"], "Force allows at most 9 infantry squads")
    require(all(count <= LIMITS["family_max"] for count in families.values()), "Rule of three: a family exceeds 3 choices")
    require(all(count <= 1 for count in unique.values()), "A Unique catalog ID may appear only once")
    require(all(count <= LIMITS["pilot_max"] for count in pilots.values()), "At most 2 of each pilot role")
    require(carriers <= LIMITS["carriers_max"], "At most 2 carriers")
    require(rocket_count <= 1, "At most one Rocket test substitute")
    passengers = [group["passengers"] for group in groups if group.get("passengers")]
    require(len(passengers) == len(set(passengers)), "A squad cannot start in two carriers")
    require(all(group_types.get(key) in INFANTRY for key in passengers), "Each passenger must be an infantry squad on the roster")
    require(total <= limit, f"Force costs {total}, above the {limit}-point limit")
    return {"total": total, "groups": len(groups), "mechs": categories["Mech"],
            "vehicles": categories["Vehicle"], "conventional": categories["Conventional Infantry"],
            "battle_armor": categories["Battle Armor"], "squads": squads,
            "carriers": carriers, "escape": math.ceil(total * 0.3)}
