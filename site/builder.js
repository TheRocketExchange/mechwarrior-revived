"use strict";
(() => {
  const model=window.createForceModel(window.MW_CATALOG);
  const key="mw-revived-force-v1";
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const empty=()=>model.parse({name:"My force",groups:[]});
  let force=empty(), page=0, saveFailed=false;
  const message=text=>{$("force-message").textContent=text;};
  try {
    const saved=localStorage.getItem(key);
    if(saved) {
      const previous=JSON.parse(saved);
      force=model.parse(previous);
      if(previous.formula_version && previous.formula_version!==force.formula_version)
        message("Points updated. Review the total and regenerate cards.");
    }
  }
  catch {message("The saved list could not be loaded. Import a backup or start a new list.");}
  function save() {
    force.formula_version=MW_CATALOG.points_formula.version;
    try {localStorage.setItem(key,JSON.stringify(force)); saveFailed=false;}
    catch {saveFailed=true;}
    $("force-save").textContent=saveFailed?"Could not save. Export your list to keep it.":"Saved in this browser";
    printLink();
  }
  function printLink() {
    const link=$("force-cards"), hasModels=force.groups.length>0;
    link.setAttribute("aria-disabled",String(!hasModels));
    if(hasModels)link.href="force-cards.html#list="+encodeURIComponent(JSON.stringify(force));
    else link.removeAttribute("href");
  }
  function option(value,label,selected) {return `<option value="${esc(value)}" ${value===selected?'selected':''}>${esc(label)}</option>`;}
  function squadOptions(category,selected="",unique=false) {
    return option("",unique?"New squad (1 Unique base)":"New squad (2 bases)",selected)+force.groups.filter(group=>model.units.get(group.members[0]).category===category&&group.members.length<3).map(group=>option(group.id,`Add to ${group.id} (${group.members.length}/3)`,selected)).join("");
  }
  function renderResults() {
    const words=$("force-query").value.trim().toLowerCase().split(/\s+/).filter(Boolean), type=$("force-type").value;
    const matches=MW_CATALOG.units.filter(unit=>(!force.faction||unit.faction===force.faction)&&words.every(word=>`${unit.name} ${unit.id} ${unit.family} ${unit.variant} ${unit.faction}`.toLowerCase().includes(word))&&(!type||unit.category===type)&&($("force-scope").value==="all"||unit.core_legal));
    const pages=Math.max(1,Math.ceil(matches.length/12)); page=Math.min(page,pages-1);
    $("force-results-count").textContent=`${matches.length.toLocaleString()} unit${matches.length===1?'':'s'}`;
    $("force-results").innerHTML=matches.slice(page*12,page*12+12).map(unit=>`<div class="force-unit"><img src="${esc(unit.photo)}" alt="${esc(unit.name)} miniature" loading="lazy"><div><a href="unit.html?id=${encodeURIComponent(unit.id)}">${esc(unit.name)}</a><small>${esc(unit.id)} · ${esc(unit.rank)} · ${unit.cost.points} pts${model.infantry.has(unit.category)?' / base':''}</small><small>${esc(unit.faction)}</small>${!unit.core_legal?'<small>Outside core rules</small>':''}<div class="force-add">${model.infantry.has(unit.category)?`<select aria-label="Squad for ${esc(unit.id)}" data-destination="${esc(unit.id)}">${squadOptions(unit.category,"",unit.rank.includes("Unique"))}</select>`:''}<button type="button" data-add="${esc(unit.id)}">${model.infantry.has(unit.category)?'Add infantry':'Add model'}</button></div></div></div>`).join("")||"<p>No matching units.</p>";
    $("force-page").textContent=`${page+1} / ${pages}`;
    $("force-prev").disabled=!page; $("force-next").disabled=page===pages-1;
  }
  function render() {
    $("force-name").value=force.name;
    $("force-size").value=force.game_size;
    $("force-faction").value=force.faction;
    const result=model.validate(force);
    const selected=result.size, limits=selected.limits;
    $("force-totals").innerHTML=`<p class="force-points"><strong>${result.points.toLocaleString()}</strong> / ${selected.points_limit.toLocaleString()} points</p><p class="force-counts"><span>’Mechs ${result.counts.Mech} / ${limits.mechs_max}</span><span>Vehicles ${result.counts.Vehicle} / ${limits.vehicles_max}</span><span>Squads ${result.counts.squads} / ${limits.squads_max}</span><span>${result.counts.models} models</span></p>`;
    $("force-size-guide").textContent=`${selected.board_width} × ${selected.board_depth}″ table`;
    $("force-checks").hidden=!force.groups.length;
    $("force-check-title").textContent=result.errors.length?`${result.errors.length} issue${result.errors.length===1?'':'s'}`:"Within force limits";
    $("force-checks").classList.toggle("force-valid",!result.errors.length);
    $("force-errors").innerHTML=result.errors.map(error=>`<li>${esc(error)}</li>`).join("");
    $("force-errors").hidden=!result.errors.length;
    printLink();
    const squads=force.groups.filter(group=>model.infantry.has(model.units.get(group.members[0]).category));
    $("force-groups").innerHTML=force.groups.map(group=>{
      const unit=model.units.get(group.members[0]), isSquad=model.infantry.has(unit.category);
      let controls="";
      if(unit.category==="Mech") controls=`<label>Pilot<select data-group="${esc(group.id)}" data-field="pilot">${option("","Choose a pilot",group.pilot||"")}${model.config.pilots.map(pilot=>option(pilot,pilot,group.pilot)).join("")}</select></label>${Object.keys(unit.rocket_options).length?`<label>Rocket substitute<select data-group="${esc(group.id)}" data-field="rocket_slot">${option("","None",group.rocket_slot||"")}${Object.keys(unit.rocket_options).map(slot=>option(slot,`${slot.charAt(0).toUpperCase()+slot.slice(1)}: ${unit.rocket_options[slot].points} pts`,group.rocket_slot)).join("")}</select></label>`:''}`;
      if(unit.category==="Vehicle") controls=`<label class="carrier-toggle"><input type="checkbox" data-group="${esc(group.id)}" data-field="carrier" ${group.carrier?'checked':''}> Carrier</label>${group.carrier?`<label>Starts with squad<select data-group="${esc(group.id)}" data-field="passengers">${option("","Empty",group.passengers||"")}${squads.map(squad=>option(squad.id,squad.id,group.passengers)).join("")}</select></label>`:''}`;
      return `<div class="force-group" data-roster-group="${esc(group.id)}"><div class="force-group-heading"><h3>${esc(group.id)} · ${isSquad?esc(unit.category)+' squad':esc(unit.name)}</h3><strong>${model.cost(group)} pts</strong><button type="button" data-remove-group="${esc(group.id)}" aria-label="Remove ${esc(group.id)}">Remove</button></div>${group.members.map((id,index)=>{const member=model.units.get(id);return `<div class="force-member"><a class="force-member-preview" href="unit.html?id=${encodeURIComponent(id)}"><img src="${esc(member.photo)}" alt="${esc(member.name)} miniature" width="80" height="80" loading="lazy" decoding="async"><span class="force-member-info"><strong>${isSquad?esc(group.id+String.fromCharCode(97+index))+': ':''}${esc(member.name)}</strong><small>${esc(id)} / ${esc(member.rank)}</small><small>${esc(member.faction)}</small></span></a>${isSquad?`<span class="force-member-actions"><button type="button" data-copy="${esc(group.id)}" data-member="${index}" ${group.members.length>=3?'disabled':''} aria-label="Add another ${esc(id)} to ${esc(group.id)}">+</button><button type="button" data-remove-member="${esc(group.id)}" data-member="${index}" aria-label="Remove ${esc(group.id+String.fromCharCode(97+index))}">−</button></span>`:''}</div>`;}).join("")}<div class="force-group-controls">${controls}</div></div>`;
    }).join("")||'<p class="force-empty">No models yet.</p>';
    renderResults();
  }
  function change() {save();render();}
  function removeGroup(id) {
    force.groups=force.groups.filter(group=>group.id!==id);
    for(const group of force.groups) if(group.passengers===id) delete group.passengers;
  }
  $("force-name").addEventListener("input",()=>{force.name=$("force-name").value;save();});
  for(const [id,size] of Object.entries(model.config.sizes)) $("force-size").insertAdjacentHTML("beforeend",option(id,`${size.name} · ${size.points_limit.toLocaleString()} points`,force.game_size));
  $("force-size").addEventListener("change",()=>{force.game_size=$("force-size").value;change();message("");});
  for(const name of model.factions) $("force-faction").insertAdjacentHTML("beforeend",option(name,name,force.faction));
  $("force-faction").addEventListener("change",()=>{force.faction=$("force-faction").value;page=0;change();message("");});
  $("force-filters").addEventListener("submit",event=>event.preventDefault());
  $("force-filters").addEventListener("input",()=>{page=0;renderResults();});
  for(const category of [...new Set(MW_CATALOG.units.map(unit=>unit.category))].sort()) $("force-type").insertAdjacentHTML("beforeend",option(category,category,""));
  $("force-prev").addEventListener("click",()=>{page--;renderResults();});
  $("force-next").addEventListener("click",()=>{page++;renderResults();});
  $("force-results").addEventListener("click",event=>{
    const button=event.target.closest("[data-add]"); if(!button) return;
    try {const select=[...document.querySelectorAll('[data-destination]')].find(select=>select.dataset.destination===button.dataset.add);const id=model.addUnit(force,button.dataset.add,select?.value||"");change();message(`Added to ${id}.`);}
    catch(error){message(error.message);}
  });
  $("force-groups").addEventListener("click",event=>{
    const button=event.target.closest("button"); if(!button) return;
    if(button.dataset.removeGroup) removeGroup(button.dataset.removeGroup);
    else {const id=button.dataset.copy||button.dataset.removeMember, group=force.groups.find(group=>group.id===id);if(!group) return;const index=Number(button.dataset.member);if(button.dataset.copy&&group.members.length<3) group.members.push(group.members[index]);else if(button.dataset.removeMember){group.members.splice(index,1);if(!group.members.length)removeGroup(id);}}
    change();message("");
  });
  $("force-groups").addEventListener("change",event=>{
    const field=event.target.dataset.field, group=force.groups.find(group=>group.id===event.target.dataset.group);if(!group) return;
    if(field==="carrier") {group.carrier=event.target.checked;if(!group.carrier)delete group.passengers;}
    else if(["pilot","rocket_slot","passengers"].includes(field)) {if(event.target.value)group[field]=event.target.value;else delete group[field];}
    change();
  });
  $("force-new").addEventListener("click",()=>{if(force.groups.length&&!confirm("Start a new list? Export this list first if you want to keep it."))return;force=empty();change();message("");});
  function loadSample(id) {
    const sample=MW_SAMPLE_FORCES.forces.find(force=>force.id===id);
    if(!sample){message("Sample army not found. Choose one from the list.");return;}
    if(force.groups.length&&!confirm("Replace this list with the sample army? Export first to keep the current list."))return;
    force=model.parse(sample);change();message("");
  }
  $("force-sample").addEventListener("change",event=>{if(event.target.value)loadSample(event.target.value);event.target.value="";});
  $("force-export").addEventListener("click",()=>{
    const blob=new Blob([JSON.stringify(force,null,2)+"\n"],{type:"application/json"}), url=URL.createObjectURL(blob), link=document.createElement("a");
    link.href=url;link.download=(force.name.replace(/[^a-z0-9]+/gi,"-").replace(/^-|-$/g,"")||"my-force")+".json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message("List exported.");
  });
  $("force-import").addEventListener("change",async event=>{
    const file=event.target.files[0];if(!file)return;
    try {if(file.size>1_000_000)throw new Error("Choose a list file smaller than 1 MB.");const imported=model.parse(JSON.parse(await file.text()));if(force.groups.length&&!confirm("Replace this list with the imported list? Export first to keep the current list."))return;force=imported;change();message("List imported.");}
    catch(error){message(`Could not import: ${error.message}`);}finally{event.target.value="";}
  });
  const params=new URLSearchParams(location.search), add=params.get("add"), sample=params.get("sample");
  if(sample)loadSample(sample);
  else if(add) {try {const id=model.addUnit(force,add);save();message(`Added to ${id}.`);}catch(error){message(error.message);}}
  if(sample||add)history.replaceState(null,"",location.pathname);
  render();
})();
