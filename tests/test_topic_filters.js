'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const taxonomy=JSON.parse(fs.readFileSync('topic-taxonomy.json','utf8'));
for(const prefix of ['', 'dist/']){
 const archive=JSON.parse(fs.readFileSync(prefix+'data.json','utf8'));
 const elements=new Map();
 const element=id=>{if(!elements.has(id))elements.set(id,{value:'',options:[{outerHTML:'<option value="">Tutti gli argomenti</option>'}],innerHTML:'',textContent:'',hidden:true,disabled:false,addEventListener(){},classList:{toggle(){}},setAttribute(){}});return elements.get(id);};
 const context=vm.createContext({document:{head:{insertAdjacentHTML(){}},getElementById:element,querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener(){}},location:{hash:''},history:{},fetch:()=>new Promise(()=>{}),setInterval(){},URL,console,Date});
 vm.runInContext(fs.readFileSync(prefix+'app.js','utf8'),context);
 // Reverse the stored order: the UI must sort dynamically, even for a sparse
 // archive such as dist. It must always expose exactly the authorized 14 labels.
 context.archive=archive;context.taxonomy={...taxonomy,categories:[...taxonomy.categories].reverse()};
 vm.runInContext('data=archive;topicTaxonomy=taxonomy;validateTopics(data,topicTaxonomy);render()',context);
 const labels=taxonomy.categories.map(c=>c.label).sort((a,b)=>a.localeCompare(b,'it',{sensitivity:'base'}));
 const displayed=[...element('topic').innerHTML.matchAll(/<option value="([^"]+)">/g)].map(m=>m[1]);
 assert.deepEqual(displayed,labels,prefix+'ordine A–Z indipendente dal JSON');
 assert.equal(new Set(labels).size,labels.length);
 assert.equal((element('topic').innerHTML.match(/<option/g)||[]).length,labels.length+1);
 for(const label of labels){
  element('topic').value=label;
  const ids=Array.from(vm.runInContext('selected().map(r=>r.id)',context));
  assert.deepEqual([...ids].sort(),archive.records.filter(r=>r.topics.includes(label)).map(r=>r.id).sort(),prefix+label);
  assert.equal(new Set(ids).size,ids.length,prefix+'nessuna duplicazione');
  for(const region of ['Lombardia','Sardegna','Trentino-Alto Adige']){
   for(const level of ['', 'Nazionale','Distrettuale','Provinciale']){
    element('region').value=region;element('level').value=level;
    const actual=Array.from(vm.runInContext('selected().map(r=>r.id)',context));
    const expected=archive.records.filter(r=>r.topics.includes(label)&&(r.regions.includes(region)||r.regions.includes('Italia'))&&(!level||r.level===level)).map(r=>r.id);
    assert.deepEqual([...actual].sort(),expected.sort(),prefix+label+region+level);
   }
  }
  element('region').value='';element('level').value='';
 }
 element('topic').value='';
 assert.equal(vm.runInContext('selected().length',context),archive.records.length);
 const rd=archive.records.find(r=>r.id==='rd523');
 assert.equal(rd.topics.length,2);
 for(const t of rd.topics){element('topic').value=t;assert.equal(vm.runInContext("selected().some(r=>r.id==='rd523')",context),true);}
 element('search').value='rd523';element('search').value='523';element('topic').value='';
 assert.equal(vm.runInContext("selected().some(r=>r.id==='rd523')",context),true);
 context.invalid={records:[{id:'invalid',topics:['PAI']}]};
 assert.throws(()=>vm.runInContext('validateTopics(invalid,taxonomy)',context));
 for(const invalid of [{records:[{id:'empty',topics:[],topic_classification:{status:'argomento da classificare'}}]}, {records:[rd,rd]}]){
  context.invalid=invalid;assert.throws(()=>vm.runInContext('validateTopics(invalid,taxonomy)',context));
 }
 element('search').value='';element('region').value='';element('level').value='';
 for(const sort of ['date','title']){
  element('sort').value=sort;
  const rows=Array.from(vm.runInContext('selected()',context));
  assert.equal(rows.length,archive.records.length);
  for(let i=1;i<rows.length;i++)assert.ok(sort==='date'?rows[i-1].date.localeCompare(rows[i].date)>=0:rows[i-1].title.localeCompare(rows[i].title,'it')<=0);
 }
 // Search and topic together must intersect, not add results.
 element('topic').value=rd.topics[0];element('search').value='523';
 assert.deepEqual(Array.from(vm.runInContext('selected().map(r=>r.id)',context)),['rd523']);
 console.log(prefix+'frontend: 14 filtri A–Z, 168 combinazioni territorio/livello, ricerca, ordinamento e multitag OK');
}
