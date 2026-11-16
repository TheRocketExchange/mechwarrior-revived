"use strict";
(() => {
  const catalog = window.MW_CATALOG;
  if (!catalog) return;
  const units = catalog.units;
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const num = (click, key) => click[key]?.value ?? "—";
  const labels = { E: "Energy", B: "Ballistic", R: "Rocket", M: "Melee", A: "Artillery" };
  const photo = unit => unit.photo ? `<img src="${esc(unit.photo)}" alt="${esc(unit.name)} miniature, ${esc(unit.photo_variant || unit.id)}" loading="lazy">` : '<p class="photo-missing">Photo not available in the archive</p>';
  const stat = (label, value) => `<div><span>${label}</span><strong>${esc(value)}</strong></div>`;

  function miniatureCard(unit) {
    const click = unit.track[unit.start];
    return `<a class="unit-tile" href="unit.html?id=${encodeURIComponent(unit.id)}"><div class="unit-photo">${photo(unit)}</div><div class="unit-tile-body"><p class="unit-id">${esc(unit.id)} · ${esc(unit.rank)}</p><h2>${esc(unit.name)}</h2><p class="unit-category">${esc(unit.category)} · ${esc(unit.faction)}</p><div class="unit-tile-bottom"><span class="unit-points">${unit.cost.points}<small>pts</small></span><span>${unit.track.length - unit.start} clicks${unit.core_legal ? "" : ' · <em>Other rules</em>'}</span></div><div class="unit-mini-stats">${stat("Speed",num(click,"speed"))}${stat("Attack",num(click,"attack"))}${stat("Defense",num(click,"defense"))}</div></div></a>`;
  }
  const grid = document.getElementById("unit-grid");
  if (grid) {
    const form = document.getElementById("unit-filters");
    const query = document.getElementById("unit-query");
    const selectors = { set: document.getElementById("unit-set"), category: document.getElementById("unit-category"), faction: document.getElementById("unit-faction") };
    for (const [key, select] of Object.entries(selectors)) {
      for (const value of [...new Set(units.map(unit=>unit[key]).filter(Boolean))].sort()) {
        const option = document.createElement("option"); option.value = value; option.textContent = value; select.append(option);
      }
    }
    const rules = document.getElementById("unit-status");
    const sort = document.getElementById("unit-sort");
    const params = new URLSearchParams(location.search);
    query.value = params.get("q") || "";
    let page = 0;
    const pageSize = 24;
    function render() {
      const words = query.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      let matches = units.filter(unit => words.every(word => `${unit.id} ${unit.name} ${unit.family} ${unit.variant}`.toLowerCase().includes(word)) && Object.entries(selectors).every(([key,select])=>!select.value || unit[key]===select.value) && (!rules.value || (rules.value==="core" ? unit.core_legal : !unit.core_legal)));
      if (sort.value === "name") matches.sort((a,b)=>a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
      if (sort.value.startsWith("points")) matches.sort((a,b)=>(a.cost.points-b.cost.points)*(sort.value==="points-desc"?-1:1)||a.id.localeCompare(b.id));
      const pages = Math.max(1, Math.ceil(matches.length / pageSize)); page = Math.min(page, pages-1);
      grid.innerHTML = matches.length ? matches.slice(page*pageSize,(page+1)*pageSize).map(miniatureCard).join("") : '<p class="empty-catalog">No units match. Try a shorter name or clear the filters.</p>';
      document.getElementById("unit-count").textContent = `${matches.length.toLocaleString()} of ${units.length.toLocaleString()} figures · points formula ${catalog.points_formula.version}`;
      document.getElementById("unit-page").textContent = `Page ${page+1} of ${pages}`;
      document.getElementById("unit-prev").disabled = !page;
      document.getElementById("unit-next").disabled = page >= pages-1;
    }
    form.addEventListener("submit",event=>event.preventDefault());
    form.addEventListener("input",()=>{page=0;render();});
    form.addEventListener("reset",()=>setTimeout(()=>{page=0;render();},0));
    document.getElementById("unit-prev").addEventListener("click",()=>{page--;render();form.scrollIntoView({block:"start"});});
    document.getElementById("unit-next").addEventListener("click",()=>{page++;render();form.scrollIntoView({block:"start"});});
    render();
  }

  const detail = document.getElementById("unit-detail");
  if (!detail) return;
  const id = new URLSearchParams(location.search).get("id");
  const unit = units.find(unit=>unit.id===id);
  if (!unit) { detail.innerHTML = '<p>Unit not found. <a href="units.html">Browse the catalog</a>.</p>'; return; }
  document.title = `${unit.name} (${unit.id}) · MechWarrior Revived`;
  document.querySelector("h1").textContent = unit.name;
  document.querySelector(".eyebrow").textContent = `Catalog ID: ${unit.id} / ${unit.set}`;
  document.body.classList.add("unit-page");
  let position = unit.start;
  let rocketSlot = "";
  const colorCodes = { red: 'R', blue: 'B', black: 'K', gray: 'Gy', green: 'Gn', yellow: 'Y', purple: 'P' };
  function dialCell(cell = {}, heat = false) {
    if (cell.shutdown) return 'SD';
    if (cell.dead) return 'X';
    const value = cell.value;
    const number = value == null ? '—' : heat && value > 0 ? '+' + value : value;
    return `${esc(number)}${colorCodes[cell.color] ? `<small>${colorCodes[cell.color]}</small>` : ''}`;
  }
  function trackTable(forPrint = false) {
    const fields = unit.weapons.map(weapon=>[weapon.slot,`${weapon.slot==='primary'?'Primary':'Secondary'} damage`]).concat([["speed","Speed"],["attack","Attack"],["defense","Defense"]]);
    const tables = [];
    const positions = [...unit.track.map((_,i)=>i), null];
    const chunkSize = forPrint ? positions.length : 8;
    for (let offset = 0; offset < positions.length; offset += chunkSize) {
      const columns = positions.slice(offset, offset+chunkSize);
      const header = `<thead><tr><th>Click</th>${columns.map(i=>i===null?'<th>End</th>':forPrint?`<th>${i+1}</th>`:`<th><button type="button" data-click="${i}" aria-label="Show combat click ${i+1}" ${i===position?'aria-pressed="true"':''}>${i+1}</button></th>`).join('')}</tr></thead>`;
      const rows = fields.map(([key,label])=>`<tr><th>${label}</th>${columns.map(i=>{const cell=i===null?{dead:true,color:'gray'}:unit.track[i][key]||{};return `<td class="dial-${esc(cell.color||'white')} ${i===position?'dial-selected':''}" title="${esc(cell.color||'white')} equipment">${dialCell(cell)}</td>`;}).join('')}</tr>`).join('');
      const marks = `<tr><th>Marks</th>${columns.map(i=>`<td>${i===null?'End':i===unit.start?'Start':unit.track[i].markers?.repair?'Stop':''}</td>`).join('')}</tr>`;
      tables.push(`<div class="table-scroll"><table class="dial-table"><caption>Combat dial · ${offset+1}–${columns.at(-1)===null?'End':columns.at(-1)+1}</caption>${header}<tbody>${rows}${marks}</tbody></table></div>`);
    }
    return tables.join('');
  }
  function assignmentFields() {
    const category = unit.category;
    const example = {Mech:'M1',Vehicle:'V1','Conventional Infantry':'C1a','Battle Armor':'A1a'}[category] || 'T1';
    const fields = category==='Mech' ? '<br>Pilot: __________' : ['Conventional Infantry','Battle Armor'].includes(category) ? '<br>Squad: __________<br>Assigned carrier: __________' : category==='Vehicle' ? '<br>Carrier: Yes / No<br>Assigned squad: __________' : '';
    const readiness = category!=='Mech' && category!=='Turret' ? '<br>Readiness: Ready / Committed / Spent' : '';
    return `<p class="unit-assignment">Roster ID: __________ <small>(e.g. ${example})</small>${fields}${readiness}</p><p class="card-help"><a href="units.html#reading-a-unit-card">What these card labels mean</a></p>`;
  }
  function heatTable() {
    if (!unit.heat.length) return "";
    const fields = [...new Set(unit.heat.flatMap(click=>Object.keys(click)))];
    return `<h2>Heat dial</h2><p>Vent ${unit.vent}. Add these modifiers to the current combat dial. SD means shutdown; colored warnings follow the <a href="rules.html#8-heat">Revived heat rules</a>.</p><div class="table-scroll"><table class="dial-table"><thead><tr><th>Heat</th>${unit.heat.map((_,i)=>`<th>${i===0?'Start':i}</th>`).join("")}</tr></thead><tbody>${fields.map(key=>`<tr><th>${key==='speed'?'Speed':key==='primary'?'Primary damage':'Secondary damage'}</th>${unit.heat.map(click=>{const cell=click[key]||{};return `<td class="dial-${esc(cell.color||'white')}">${dialCell(cell,true)}</td>`;}).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  function renderDetail() {
    const click = unit.track[position];
    const cost = rocketSlot ? unit.rocket_options[rocketSlot] : unit.cost;
    const b = cost.breakdown;
    detail.innerHTML = `<section class="unit-profile"><div class="profile-photo">${photo(unit)}<p class="photo-credit">${esc(unit.photo_credit)}${unit.photo_variant?` · Photo shows ${esc(unit.photo_variant)}`:''}</p></div><div class="profile-summary"><p class="unit-id">${esc(unit.rank)} · ${esc(unit.category)}${unit.class?' · '+esc(unit.class):''}</p><p>${esc(unit.faction)}${unit.variant?'<br>'+esc(unit.variant):''}</p><div class="profile-points">${cost.points}<span>Points</span></div><p class="formula-version">Formula ${esc(cost.version)}</p>${unit.core_legal?'':'<p class="catalog-restriction">'+esc(unit.restriction)+' This is a calculated catalog estimate.</p>'}<p class="unit-family"><a href="rules.html#rule-of-three">Unit family</a>: <strong>${esc(unit.family)}</strong></p>${assignmentFields()}</div></section>
<section class="current-dial"><div class="dial-controls"><h2>Combat click ${position+1}${position===unit.start?' · Starting dial':''}</h2><div><button type="button" id="dial-back" ${position<=unit.start?'disabled':''}>← Previous</button><button type="button" id="dial-reset">Starting dial</button><button type="button" id="dial-forward" ${position>=unit.track.length-1?'disabled':''}>Next →</button></div></div><div class="profile-stats">${stat('Speed',num(click,'speed'))}${stat('Attack',num(click,'attack'))}${stat('Defense',num(click,'defense'))}${stat('Clicks',unit.track.length-unit.start)}</div><p class="dial-note">Clicks is the damage needed to reach destruction from Start. It is the starting total, not remaining health. The buttons preview positions; use the miniature’s current dial during play.</p>
<table class="weapon-table"><thead><tr><th>Weapon</th><th>Type</th><th>Damage</th><th>Range</th><th>Equipment</th></tr></thead><tbody>${unit.weapons.map(weapon=>`<tr><td>${weapon.slot==='primary'?'Primary':'Secondary'}</td><td>${labels[rocketSlot===weapon.slot?'R':weapon.type]}</td><td>${num(click,weapon.slot)}</td><td>${weapon.type==='M'?'Contact':weapon.min_range+'–'+weapon.max_range+' in'}</td><td>${esc(click[weapon.slot]?.color||'white')}</td></tr>`).join('')}</tbody></table>
<p>Speed equipment: <strong>${esc(click.speed.color)}</strong> · Attack: <strong>${esc(click.attack.color)}</strong> · Defense: <strong>${esc(click.defense.color)}</strong>. Use the <a href="equipment.html">equipment reference</a>.</p></section>
${Object.keys(unit.rocket_options).length?`<label class="rocket-choice">Rocket test substitute<select id="rocket-choice"><option value="">None</option>${Object.keys(unit.rocket_options).map(slot=>`<option value="${slot}" ${rocketSlot===slot?'selected':''}>${slot==='primary'?'Primary':'Secondary'} as Rocket</option>`).join('')}</select></label><p class="dial-note">At most one such weapon on one ’Mech per force. This changes the card’s points; it does not identify the original weapon.</p>`:''}
<section class="full-track"><h2>Full combat dial</h2><p><strong>Clicks: ${unit.track.length-unit.start}</strong> from Start to End. Read left to right, then continue on the next table. Damage moves one column right per point; repairs move left. Start is the starting position, Stop is a repair stop, and End is destroyed. X marks a lost value.</p><div class="screen-dials">${trackTable()}</div><div class="print-dials">${trackTable(true)}</div><p class="dial-key">Colors: R red · B blue · K black · Gy gray · Gn green · Y yellow · P purple. Use <a href="equipment.html">Revived equipment rules</a>; circle and square equipment work alike.</p></section>${heatTable()}
<details class="cost-details"><summary>How the ${cost.points} points are calculated</summary><p>Formula ${esc(cost.version)}. All units use the same <a href="points.html">points formula</a>.</p><dl><dt>Toughness across the dial</dt><dd>${b.durability.toFixed(2)}</dd><dt>Mobility</dt><dd>${b.mobility.toFixed(2)}</dd><dt>Firepower before readiness</dt><dd>${b.firepower_before_readiness.toFixed(2)}</dd><dt>Readiness multiplier (estimate)</dt><dd>${unit.category==='Mech'?'Uses heat instead':b.readiness_factor.toFixed(3)}</dd><dt>Firepower used in cost</dt><dd>${b.firepower.toFixed(2)}</dd><dt>Support</dt><dd>${b.support.toFixed(2)}</dd><dt>Pilot allowance</dt><dd>${b.pilot_allowance}</dd></dl><p>${catalog.points_formula.scale} × ${b.durability.toFixed(2)} × (${catalog.points_formula.base} + ${b.mobility.toFixed(2)} + ${catalog.points_formula.firepower_weight} × ${b.firepower.toFixed(2)} + ${b.support.toFixed(2)}) + ${b.pilot_allowance} ≈ <strong>${cost.points} points</strong>.</p><p>The calculation uses unrounded ratings. For non-’Mechs, the readiness estimate follows 24 attack/recover choices through the actual damage dial.</p></details>
<p class="unit-builder-link"><a href="builder.html?add=${encodeURIComponent(unit.id)}">${["Conventional Infantry","Battle Armor"].includes(unit.category)?(unit.rank.includes("Unique")?"Start a squad with this Unique figure":"Add a two-base squad to your force"):"Add this model to your force"}</a></p><p class="unit-source">Photo and original dial: <a href="${esc(unit.source_url)}">WarrenBorn · ${esc(unit.id)}</a>${unit.photo_source?' · <a href="'+esc(unit.photo_source)+'">Original photograph</a>':''}. Cost is a Revived playtest estimate.</p>`;
    document.getElementById('dial-back').addEventListener('click',()=>{position=Math.max(unit.start,position-1);renderDetail();});
    document.getElementById('dial-forward').addEventListener('click',()=>{position=Math.min(unit.track.length-1,position+1);renderDetail();});
    document.getElementById('dial-reset').addEventListener('click',()=>{position=unit.start;renderDetail();});
    for (const button of detail.querySelectorAll('[data-click]')) button.addEventListener('click',()=>{position=Number(button.dataset.click);renderDetail();});
    document.getElementById('rocket-choice')?.addEventListener('change',event=>{rocketSlot=event.target.value;renderDetail();});
  }
  renderDetail();
})();
