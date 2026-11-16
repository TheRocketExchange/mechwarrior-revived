/* Roster data and rules shared by the builder and its printable cards. */
"use strict";
function createForceModel(catalog) {
  const units = new Map(catalog.units.map(unit => [unit.id, unit]));
  const config = catalog.force_organization;
  function size(force) {
    const id=force.game_size===undefined?config.default_size:force.game_size;
    if (typeof id!=="string" || !Object.hasOwn(config.sizes,id)) throw new Error("Choose a supported game size.");
    return config.sizes[id];
  }
  const infantry = new Set(config.infantry);
  const cost = group => group.members.reduce((sum, id) => {
    const unit = units.get(id);
    return sum + (unit?.rocket_options[group.rocket_slot]?.points ?? unit?.cost.points ?? 0);
  }, 0);
  function parse(value) {
    if (!value || typeof value !== "object" || !Array.isArray(value.groups) || value.groups.length > 200) throw new Error("Choose a Revived list JSON file with up to 200 groups.");
    size(value);
    let models = 0;
    const ids = new Set();
    const groups = value.groups.map(raw => {
      if (!raw || typeof raw.id !== "string" || !raw.id.trim() || raw.id.length > 24 || ids.has(raw.id)) throw new Error("Each group needs a different roster ID of up to 24 characters.");
      ids.add(raw.id);
      if (!Array.isArray(raw.members) || !raw.members.length || raw.members.length > 30 || raw.members.some(id => typeof id !== "string" || !units.has(id))) throw new Error(`${raw.id}: a model is missing or has an unknown catalog ID.`);
      models += raw.members.length;
      const group = {id: raw.id, members: [...raw.members]};
      for (const key of ["pilot", "passengers", "rocket_slot"]) {
        if (raw[key] != null && (typeof raw[key] !== "string" || raw[key].length > 40)) throw new Error(`${raw.id}: invalid ${key}.`);
        if (raw[key]) group[key] = raw[key];
      }
      if (raw.carrier === true) group.carrier = true;
      const unit=units.get(group.members[0]);
      if (group.members.some(id=>units.get(id).category!==unit.category) || (!infantry.has(unit.category)&&group.members.length!==1)) throw new Error(`${group.id}: each ’Mech or vehicle needs its own group; keep infantry categories separate.`);
      if (group.pilot&&!config.pilots.includes(group.pilot)) throw new Error(`${group.id}: unknown pilot role.`);
      if (group.rocket_slot&&(unit.category!=="Mech"||!unit.rocket_options[group.rocket_slot])) throw new Error(`${group.id}: unavailable Rocket substitute.`);
      return group;
    });
    for (const group of groups) if(group.passengers&&!groups.some(squad=>squad.id===group.passengers&&infantry.has(units.get(squad.members[0]).category))) throw new Error(`${group.id}: its assigned squad is missing or is not infantry.`);
    if (models > 1000) throw new Error("A saved list can contain up to 1,000 models.");
    return {version: 1, name: typeof value.name === "string" ? value.name.slice(0,80).trim() || "My force" : "My force", game_size: value.game_size===undefined?config.default_size:value.game_size, formula_version: catalog.points_formula.version, groups};
  }
  function validate(force) {
    const selected=size(force), limits=selected.limits;
    const errors = [], counts = {Mech:0, Vehicle:0, squads:0, carriers:0, models:0};
    const families = new Map(), uniques = new Map(), pilots = new Map(), passengers = new Set();
    const add = (map, key) => map.set(key, (map.get(key) || 0)+1);
    const byId = new Map(force.groups.map(group => [group.id, group]));
    let points = 0, rockets = 0;
    for (const group of force.groups) {
      const members = group.members.map(id => units.get(id));
      points += cost(group);
      counts.models += members.length;
      const category = members[0].category;
      if (members.some(unit => unit.category !== category)) errors.push(`${group.id}: keep conventional infantry and battle armor in separate squads.`);
      if (members.some(unit => !unit.core_legal)) errors.push(`${group.id}: contains a unit outside the core rules.`);
      if (infantry.has(category)) {
        counts.squads++;
        if (members.length < 2 || members.length > 3) errors.push(`${group.id}: a squad needs 2–3 bases.`);
      } else {
        if (members.length !== 1) errors.push(`${group.id}: each ’Mech or vehicle is its own group.`);
        counts[category] = (counts[category] || 0) + members.length;
      }
      for (const family of new Set(members.map(unit => `${unit.category}|${unit.family.toLowerCase()}`))) add(families, family);
      for (const unit of members) if (unit.rank.includes("Unique")) add(uniques, unit.id);
      if (category === "Mech") {
        if (!config.pilots.includes(group.pilot)) errors.push(`${group.id}: choose a pilot.`);
        else add(pilots, group.pilot);
      } else if (group.pilot) errors.push(`${group.id}: only ’Mechs take pilots.`);
      if (group.carrier) {
        counts.carriers++;
        if (category !== "Vehicle") errors.push(`${group.id}: only vehicles can be carriers.`);
      }
      if (group.passengers) {
        const squad = byId.get(group.passengers);
        if (!group.carrier || !squad || !infantry.has(units.get(squad.members[0]).category)) errors.push(`${group.id}: assign an infantry squad to a carrier on this list.`);
        if (passengers.has(group.passengers)) errors.push(`${group.passengers}: assigned to more than one carrier.`);
        passengers.add(group.passengers);
      }
      if (group.rocket_slot) {
        rockets++;
        if (category !== "Mech" || !members[0].rocket_options[group.rocket_slot]) errors.push(`${group.id}: that Rocket substitute is unavailable.`);
      }
    }
    if (counts.Mech > limits.mechs_max) errors.push(`At most ${limits.mechs_max} ’Mechs; you have ${counts.Mech}.`);
    if (counts.Vehicle > limits.vehicles_max) errors.push(`At most ${limits.vehicles_max} vehicles; you have ${counts.Vehicle}.`);
    if (counts.squads > limits.squads_max) errors.push(`At most ${limits.squads_max} infantry squads; you have ${counts.squads}.`);
    for (const [key, count] of families) if (count > limits.family_max) {
      const [category, family] = key.split("|");
      const name = catalog.units.find(unit => unit.category===category && unit.family.toLowerCase()===family).family;
      errors.push(`${name}: ${count} ${infantry.has(category)?"squads":"models"}; the limit is ${limits.family_max}.`);
    }
    for (const [id, count] of uniques) if (count > 1) errors.push(`${id}: a Unique figure may appear only once.`);
    for (const [pilot, count] of pilots) if (count > limits.pilot_max) errors.push(`${pilot}: at most ${limits.pilot_max} per force.`);
    if (counts.carriers > limits.carriers_max) errors.push(`At most ${limits.carriers_max} carriers.`);
    if (rockets > 1) errors.push("At most one Rocket test substitute per force.");
    if (points > selected.points_limit) errors.push(`${points-selected.points_limit} points over the ${selected.points_limit.toLocaleString()}-point limit.`);
    return {points, counts, errors, size:selected, escape: Math.ceil(points*.3)};
  }
  function newId(force, category) {
    const prefix = {Mech:"M", Vehicle:"V", "Conventional Infantry":"C", "Battle Armor":"A"}[category] || "T";
    let number=1;
    while (force.groups.some(group => group.id===prefix+number)) number++;
    return prefix+number;
  }
  function addUnit(force, id, destination="") {
    const limits=size(force).limits;
    const unit=units.get(id);
    if (!unit) throw new Error("Unit not found.");
    if (infantry.has(unit.category) && destination) {
      const group=force.groups.find(group => group.id===destination);
      if (!group || units.get(group.members[0]).category!==unit.category || group.members.length>=3) throw new Error("Choose a squad of the same infantry type with room for another base.");
      group.members.push(id);
      return group.id;
    }
    if (force.groups.length >= 200) throw new Error("This list already has 200 groups. Export it and start another list.");
    const group={id:newId(force,unit.category),members:infantry.has(unit.category)&&!unit.rank.includes("Unique")?[id,id]:[id]};
    if (unit.category==="Mech") group.pilot=config.pilots.find(pilot => force.groups.filter(group => group.pilot===pilot).length<limits.pilot_max) || config.pilots[0];
    force.groups.push(group);
    return group.id;
  }
  function cards(force) {
    return force.groups.flatMap(group => group.members.map((id,index) => {
      const unit=units.get(id), isSquad=infantry.has(unit.category);
      const carrier=force.groups.find(vehicle => vehicle.carrier && vehicle.passengers===group.id);
      return {unit, rosterId:group.id+(isSquad?String.fromCharCode(97+index):""), squad:isSquad?group.id:"", carrier:carrier?.id||"", pilot:group.pilot||"", isCarrier:!!group.carrier, passengers:group.passengers||"", rocketSlot:group.rocket_slot||""};
    }));
  }
  return {units, config, infantry, cost, size, parse, validate, addUnit, cards};
}
if (typeof module !== "undefined") module.exports = createForceModel;
else window.createForceModel = createForceModel;
