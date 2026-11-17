"use strict";
(() => {
  window.addEventListener("hashchange",()=>location.reload());
  document.body.classList.add("force-cards-page");
  const output=document.getElementById("force-card-output"), status=document.getElementById("force-card-status");
  const model=createForceModel(MW_CATALOG);
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const codes={red:"R",blue:"B",black:"K",gray:"Gy",green:"Gn",yellow:"Y",purple:"P"};
  const layout=document.getElementById('force-print-layout'), button=document.getElementById('print-force-cards');
  function assignment(entry) {
    const {unit,pilot,squad,carrier,isCarrier,passengers}=entry;
    return unit.category==='Mech'?`Pilot: ${esc(pilot||'__________')}`:squad?`Squad: ${esc(squad)} · Assigned carrier: ${esc(carrier||'None')}`:unit.category==='Vehicle'?`Carrier: ${isCarrier?'Yes':'No'}${isCarrier?' · Starts with squad: '+esc(passengers||'Empty'):''}`:'';
  }
  function weapons(entry) {
    const labels={E:'Energy',B:'Ballistic',R:'Rocket',M:'Melee',A:'Artillery'};
    return entry.unit.weapons.map(weapon=>`${weapon.slot==='primary'?'Primary':'Secondary'}: ${labels[weapon.slot===entry.rocketSlot?'R':weapon.type]} · ${weapon.type==='M'?'Contact':weapon.min_range+'–'+weapon.max_range+' in'}`);
  }
  function cell(value={},heat=false) {
    const number=value.shutdown?"SD":value.dead?"X":value.value==null?"—":heat&&value.value>0?"+"+value.value:String(value.value);
    return `<td class="pc-${esc(value.color||'white')}">${esc(number)}${!value.dead&&!value.shutdown&&codes[value.color]?`<small>${codes[value.color]}</small>`:''}</td>`;
  }
  function dial(unit,heat=false) {
    const track=heat?unit.heat:unit.track;
    const fields=heat?[['primary','Primary dmg'],['secondary','Secondary dmg'],['speed','Speed']].filter(([key])=>track.some(click=>key in click)):unit.weapons.map(weapon=>[weapon.slot,weapon.slot==='primary'?'Primary dmg':'Secondary dmg']).concat([['speed','Speed'],['attack','Attack'],['defense','Defense']]);
    return `<table class="pc-dial ${track.length>17?'pc-long':''}"><thead><tr><th>${heat?'Heat':'Click'}</th>${track.map((_,i)=>`<th>${heat&&i===0?'Start':heat?i:i+1}</th>`).join('')}${heat?'':'<th>End</th>'}</tr></thead><tbody>${fields.map(([key,label])=>`<tr><th>${label}</th>${track.map(click=>cell(click[key],heat)).join('')}${heat?'':cell({dead:true,color:'gray'})}</tr>`).join('')}${heat?'':`<tr><th>Marks</th>${track.map((click,i)=>`<td>${i===unit.start?'Start':click.markers?.repair?'Stop':''}</td>`).join('')}<td>End</td></tr>`}</tbody></table>`;
  }
  function card(entry) {
    const {unit,rosterId,rocketSlot}=entry;
    const points=unit.rocket_options[rocketSlot]?.points??unit.cost.points;
    return `<section class="print-unit-card" data-card-id="${esc(rosterId)}" data-catalog-id="${esc(unit.id)}">
      <header><p>Catalog ID: ${esc(unit.id)} / ${esc(unit.set)}</p><h2>${esc(unit.name)}</h2></header>
      <div class="pc-profile"><img src="${esc(unit.photo)}" alt="${esc(unit.name)} miniature"><div class="pc-meta"><strong>Family: ${esc(unit.family)}</strong><p>${esc(unit.category)} / ${esc(unit.rank)} / ${esc(unit.movement)}</p><p>Faction: ${esc(unit.faction)}</p>${weapons(entry).map(value=>`<p class="pc-weapon">${value}</p>`).join('')}<p class="pc-assignment"><strong>Roster ID: ${esc(rosterId)}</strong><br>${assignment(entry)}</p></div><div class="pc-points"><strong>${points}</strong><span>POINTS</span></div></div>
      <div class="pc-dial-heading"><strong>COMBAT DIAL</strong><span>Clicks: ${unit.track.length-unit.start} (damage from Start to End)</span>${unit.core_legal?'':'<em>Outside core rules</em>'}</div>${dial(unit)}
      <div class="pc-lower">${unit.heat.length?`<h3>HEAT DIAL / Vent ${unit.vent}</h3>${dial(unit,true)}`:`${unit.category==='Turret'?'':'<p><strong>READINESS: Ready / Committed / Spent</strong></p>'}<p>Each column is one dial position. Damage moves right; repairs move left.</p><p>Squad and carrier fields record assignments, not current boarding status.</p>`}</div>
      <footer><p>Stop = repair stop; End = destroyed; X = lost value; SD = shutdown. Heat modifies the combat dial.</p><p>Colors: R red / B blue / K black / Gy gray / Gn green / Y yellow / P purple. Use Revived rules.</p><p>Photo / dial: warrenborn.com/Unit.php?ID=${esc(unit.id)}${unit.photo_variant?' (photo: '+esc(unit.photo_variant)+')':''} · Formula ${esc(unit.cost.version)}${rocketSlot?' · '+esc(rocketSlot)+' Rocket substitute':''}</p></footer>
    </section>`;
  }
  function dialCard(entry) {
    const {unit,rosterId,rocketSlot}=entry, points=unit.rocket_options[rocketSlot]?.points??unit.cost.points;
    return `<section class="print-unit-card print-dial-card" data-card-id="${esc(rosterId)}" data-catalog-id="${esc(unit.id)}">
      <header><p>Catalog ID: ${esc(unit.id)} / ${esc(unit.faction)} / ${esc(unit.rank)}</p><h2>${esc(unit.name)} <span>${points} pts</span></h2></header>
      <div class="pc-strip-meta"><p><strong>Roster ID: ${esc(rosterId)}</strong> · ${assignment(entry)||esc(unit.category)} · ${esc(unit.movement)}</p><p class="pc-weapon">${weapons(entry).join(' / ')}</p></div>
      <div class="pc-dial-heading"><strong>COMBAT DIAL</strong><span>Clicks: ${unit.track.length-unit.start}</span>${unit.core_legal?'':'<em>Outside core rules</em>'}</div>${dial(unit)}
      <div class="pc-lower">${unit.heat.length?`<h3>HEAT DIAL / Vent ${unit.vent}</h3>${dial(unit,true)}`:`${unit.category==='Turret'?'':'<p><strong>READINESS: Ready / Committed / Spent</strong></p>'}<p>Damage moves right; repairs move left. Use the current column.</p>`}</div>
      <footer><p>Start = starting click; Stop = repair stop; End = destroyed; X = lost value; SD = shutdown. Heat modifies the combat dial.</p><p>R red / B blue / K black / Gy gray / Gn green / Y yellow / P purple · Formula ${esc(unit.cost.version)}${rocketSlot?' · '+esc(rocketSlot)+' Rocket substitute':''} · Dial: warrenborn.com</p></footer>
    </section>`;
  }
  try {
    const params=new URLSearchParams(location.hash.slice(1));
    let encoded=params.get('list');
    if(!params.has('list')) {
      try {encoded=localStorage.getItem('mw-revived-force-v1');} catch {}
    }
    if(!encoded)throw new Error('Choose Print cards / dials in the force builder.');
    const force=model.parse(JSON.parse(encoded)), result=model.validate(force), cards=model.cards(force);
    layout.value=params.get('layout')==='dials'?'dials':'cards';
    function render() {
      const onlyDials=layout.value==='dials', perPage=onlyDials?3:2;
      document.title=force.name+(onlyDials?' · Dials':' · Unit cards');
      document.querySelector('h1').textContent=force.name+(onlyDials?' — dials':' — unit cards');
      status.textContent=`${result.size.name} · ${result.points} / ${result.size.points_limit} points · ${cards.length} models. `+(result.errors.length?`Draft list: ${result.errors.length} force limits need attention. `:'')+`${perPage} per Letter page. Print at 100% or save as PDF. Colors also have letter codes.`;
      const pages=[];
      for(let i=0;i<cards.length;i+=perPage)pages.push(`<div class="card-sheet${onlyDials?' dial-sheet':''}"><p class="card-sheet-label">${esc(result.size.name)} · ${result.points} / ${result.size.points_limit} points${result.errors.length?' · Draft':''} · ${esc(force.name)} / ${esc(force.faction||'Mixed factions')}</p>${cards.slice(i,i+perPage).map(onlyDials?dialCard:card).join('')}</div>`);
      output.innerHTML=pages.join('')||'<p>This list has no models yet. Add some in the force builder.</p>';
      button.disabled=!cards.length;
    }
    layout.addEventListener('change',()=>{
      params.set('list',JSON.stringify(force));params.set('layout',layout.value);
      history.replaceState(null,'','#'+params.toString());render();
    });
    render();
    button.addEventListener('click',async()=>{
      button.disabled=true;
      try {
        await Promise.all([...output.querySelectorAll('img')].map(img=>img.decode().catch(()=>{})));
        window.print();
      } finally {button.disabled=!cards.length;}
    });
  } catch(error) {status.textContent=error.message;button.disabled=true;layout.disabled=true;}
})();
