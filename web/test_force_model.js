"use strict";
const assert=require("node:assert/strict"), fs=require("node:fs"), path=require("node:path");
const createForceModel=require("./force-model.js");
const root=path.join(__dirname,"..");
const catalog=JSON.parse(fs.readFileSync(path.join(root,"site/catalog-data.js"),"utf8").split(" = ")[1].trim().replace(/;$/,""));
const samples=JSON.parse(fs.readFileSync(path.join(root,"playtest/forces.json"),"utf8"));
const model=createForceModel(catalog);
let tests=0;
function test(name,fn){fn();tests++;console.log("PASS",name);}
function base(){return model.parse({name:"Test",groups:["AOD108","AOD112","AOD096","AOD104"].map((id,i)=>({id:"M"+(i+1),members:[id],pilot:model.config.pilots[i]}))});}
function fails(force,pattern){assert(model.validate(force).errors.some(message=>pattern.test(message)),JSON.stringify(model.validate(force)));}
test("sample lists agree with catalog prices and limits",()=>{
  for(const sample of samples.forces){const force=model.parse(sample),result=model.validate(force);assert.deepEqual(result.errors,[]);assert.equal(result.points,sample.groups.flatMap(group=>group.members).reduce((sum,id)=>sum+model.units.get(id).cost.points,0));assert.equal(model.cards(force).length,result.counts.models);}
});
test("ranks and named variants share the chassis limit",()=>{
  const force=base();force.groups[0].members=["AOD105"];force.groups[1].members=["AOD106"];force.groups[2].members=["AOD107"];assert.deepEqual(model.validate(force).errors,[]);force.groups[3].members=["AOD108"];fails(force,/Dasher II: 4/);
});
test("infantry limits count squads, including mixed families",()=>{
  const force=base();for(let i=0;i<3;i++)force.groups.push({id:"C"+(i+1),members:["D006","D006","D009"]});assert.deepEqual(model.validate(force).errors,[]);force.groups.push({id:"C4",members:["D009","D009"]});fails(force,/Hoverbike Squad: 4 squads/);assert(!model.validate(force).errors.some(error=>error.includes("Standard Foot")));
});
test("type, squad-size, pilot, Unique, and points caps",()=>{
  let force=base();force.groups.pop();fails(force,/4–8/);
  force=base();for(let i=0;i<7;i++)model.addUnit(force,["AOD050","AOD038","AOD066"][i%3]);fails(force,/6 vehicles/);
  force=base();for(let i=0;i<10;i++)model.addUnit(force,["D006","D009","D003","AOD030"][i%4]);fails(force,/9 infantry squads/);
  force=base();model.addUnit(force,"D006");force.groups.at(-1).members.pop();fails(force,/2–3 bases/);
  force=base();for(const group of force.groups)group.pilot="Gunner";fails(force,/Gunner: at most 2/);
  force=base();force.groups[0].members=["D115"];force.groups[1].members=["D115"];fails(force,/Unique/);
  force=model.parse(samples.forces[0]);model.addUnit(force,"AOD112");fails(force,/points over/);
});
test("carrier assignments must name a squad once",()=>{
  const force=base();model.addUnit(force,"D006");model.addUnit(force,"AOD050");model.addUnit(force,"AOD038");
  for(const group of force.groups.slice(-2)){group.carrier=true;group.passengers="C1";}fails(force,/more than one carrier/);
  force.groups.at(-1).passengers="M1";fails(force,/assign an infantry squad/);
});
test("Rocket cost uses catalog and only one substitute is allowed",()=>{
  const force=base(),before=model.validate(force).points;force.groups[0].rocket_slot="secondary";
  assert.equal(model.validate(force).points,before-model.units.get("AOD108").cost.points+model.units.get("AOD108").rocket_options.secondary.points);
  force.groups[3].rocket_slot=Object.keys(model.units.get("AOD104").rocket_options)[0];fails(force,/one Rocket/);
});
test("save format never imports prices and rejects broken records",()=>{
  const force=base();const before=model.validate(force).points;force.points=1;force.groups[0].cost=1;force.formula_version="0.3-alpha-1";const updated=model.parse(force);assert.equal(model.validate(updated).points,before);assert.equal(updated.formula_version,catalog.points_formula.version);assert.deepEqual(updated.groups,model.parse(base()).groups);
  assert.throws(()=>model.parse({groups:[{id:"M1",members:["NOT-REAL"]}]}),/unknown catalog ID/);
  assert.throws(()=>model.parse({groups:[{id:"M1",members:[]}]}));
  assert.throws(()=>model.parse({groups:[force.groups[0],force.groups[0]]}),/different roster ID/);
  assert.throws(()=>model.parse({groups:[{id:"M1",members:["AOD108"],pilot:{}}]}),/invalid pilot/);
  assert.throws(()=>model.parse({groups:[{id:"M1",members:["AOD108"],pilot:"Invented"}]}),/unknown pilot/);
  assert.throws(()=>model.parse({groups:[{id:"M1",members:["AOD108"],rocket_slot:"third"}]}),/unavailable Rocket/);
  assert.throws(()=>model.parse({groups:[{id:"V1",members:["AOD050"],passengers:"C999"}]}),/assigned squad/);
  assert.deepEqual(model.parse(JSON.parse(JSON.stringify(force))),model.parse(force));
});
test("selected cards contain each model and its assignments",()=>{
  const force=base();model.addUnit(force,"D006");model.addUnit(force,"D009","C1");model.addUnit(force,"AOD050");
  force.groups.at(-1).carrier=true;force.groups.at(-1).passengers="C1";
  const cards=model.cards(force);assert.equal(cards.length,8);assert.deepEqual(cards.filter(card=>card.squad).map(card=>[card.rosterId,card.unit.id,card.carrier]),[["C1a","D006","V1"],["C1b","D006","V1"],["C1c","D009","V1"]]);
  assert.equal(cards.find(card=>card.rosterId==="V1").passengers,"C1");assert.equal(cards[0].pilot,"Gunner");
  assert.throws(()=>model.addUnit(force,"D006","C1"),/room/);
  assert.throws(()=>model.addUnit(force,"AOD030","C1"),/same infantry type/);
  const unique=base();model.addUnit(unique,"CA129");assert.equal(unique.groups.at(-1).members.length,1);model.addUnit(unique,"AOD030","A1");assert(!model.validate(unique).errors.some(error=>/Unique|2–3/.test(error)));
});
console.log(`${tests} force-builder model checks passed.`);
