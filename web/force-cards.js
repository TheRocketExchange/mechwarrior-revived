"use strict";
(() => {
  window.addEventListener("hashchange",()=>location.reload());
  document.body.classList.add("force-cards-page");
  const output=document.getElementById("force-card-output"), status=document.getElementById("force-card-status");
  const model=createForceModel(MW_CATALOG);
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const codes={red:"R",blue:"B",black:"K",gray:"Gy",green:"Gn",yellow:"Y",purple:"P"};
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
    const {unit,rosterId,pilot,squad,carrier,isCarrier,passengers,rocketSlot}=entry;
    const points=unit.rocket_options[rocketSlot]?.points??unit.cost.points;
    const labels={E:'Energy',B:'Ballistic',R:'Rocket',M:'Melee',A:'Artillery'};
    let assignment=unit.category==='Mech'?`Pilot: ${esc(pilot||'__________')}`:squad?`Squad: ${esc(squad)} · Assigned carrier: ${esc(carrier||'None')}`:unit.category==='Vehicle'?`Carrier: ${isCarrier?'Yes':'No'}${isCarrier?' · Starts with squad: '+esc(passengers||'Empty'):''}`:'';
    return `<section class="print-unit-card" data-card-id="${esc(rosterId)}" data-catalog-id="${esc(unit.id)}">
      <header><p>Catalog ID: ${esc(unit.id)} / ${esc(unit.set)}</p><h2>${esc(unit.name)}</h2></header>
      <div class="pc-profile"><img src="${esc(unit.photo)}" alt="${esc(unit.name)} miniature"><div class="pc-meta"><strong>Family: ${esc(unit.family)}</strong><p>${esc(unit.category)} / ${esc(unit.rank)} / ${esc(unit.movement)}</p>${unit.weapons.map(weapon=>`<p class="pc-weapon">${weapon.slot==='primary'?'Primary':'Secondary'}: ${labels[weapon.slot===rocketSlot?'R':weapon.type]} · ${weapon.type==='M'?'Contact':weapon.min_range+'–'+weapon.max_range+' in'}</p>`).join('')}<p class="pc-assignment"><strong>Roster ID: ${esc(rosterId)}</strong><br>${assignment}</p></div><div class="pc-points"><strong>${points}</strong><span>POINTS</span></div></div>
      <div class="pc-dial-heading"><strong>COMBAT DIAL</strong><span>Clicks: ${unit.track.length-unit.start} (damage from Start to End)</span>${unit.core_legal?'':'<em>Outside core rules</em>'}</div>${dial(unit)}
      <div class="pc-lower">${unit.heat.length?`<h3>HEAT DIAL / Vent ${unit.vent}</h3>${dial(unit,true)}`:`${unit.category==='Turret'?'':'<p><strong>READINESS: Ready / Committed / Spent</strong></p>'}<p>Each column is one dial position. Damage moves right; repairs move left.</p><p>Squad and carrier fields record assignments, not current boarding status.</p>`}</div>
      <footer><p>Stop = repair stop; End = destroyed; X = lost value; SD = shutdown. Heat modifies the combat dial.</p><p>Colors: R red / B blue / K black / Gy gray / Gn green / Y yellow / P purple. Use Revived rules.</p><p>Photo / dial: warrenborn.com/Unit.php?ID=${esc(unit.id)}${unit.photo_variant?' (photo: '+esc(unit.photo_variant)+')':''} · Formula ${esc(unit.cost.version)}${rocketSlot?' · '+esc(rocketSlot)+' Rocket substitute':''}</p></footer>
    </section>`;
  }
  try {
    const encoded=new URLSearchParams(location.hash.slice(1)).get('list');
    if(!encoded)throw new Error('Open this page using Generate unit cards in the force builder.');
    const force=model.parse(JSON.parse(encoded)), result=model.validate(force), cards=model.cards(force);
    document.title=force.name+' · Unit cards';
    document.querySelector('h1').textContent=force.name+' — unit cards';
    status.textContent=`${cards.length} cards · ${result.points} points. `+(result.errors.length?`Draft list: ${result.errors.length} force limits need attention. `:'')+'Two cards per Letter page. Print at 100%, with backgrounds enabled, or choose Save as PDF.';
    const pages=[];
    for(let i=0;i<cards.length;i+=2)pages.push(`<div class="card-sheet">${cards.slice(i,i+2).map(card).join('')}</div>`);
    output.innerHTML=pages.join('')||'<p>This list has no models yet. Add some in the force builder.</p>';
    const button=document.getElementById('print-force-cards');
    button.disabled=!cards.length;
    button.addEventListener('click',async()=>{
      button.disabled=true;
      await Promise.all([...output.querySelectorAll('img')].map(img=>img.decode().catch(()=>{})));
      window.print();button.disabled=false;
    });
  } catch(error) {status.textContent=error.message;document.getElementById('print-force-cards').disabled=true;}
})();
