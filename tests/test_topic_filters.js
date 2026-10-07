'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const taxonomy=JSON.parse(fs.readFileSync('topic-taxonomy.json','utf8'));
for(const prefix of ['', 'dist/']){
 const archive=JSON.parse(fs.readFileSync(prefix+'data.json','utf8'));
 const elements=new Map();
 const element=id=>{if(!elements.has(id))elements.set(id,{value:'',options:[{outerHTML:'<option value="">Tutti gli argomenti</option>'}],innerHTML:'',textContent:'',hidden:true,disabled:false,addEventListener(){},classList:{toggle(){}},setAttribute(){}});return elements.get(id);};
 const context=vm.createContext({document:{head:{insertAdjacentHTML(){}},getElementById:element,querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener(){}},location:{hash:''},history:{},fetch:()=>new Promise(()=>{}),setInterval(){},URL,console,Date});
 vm.runInContext(fs.readFileSync(prefix+'app.js','utf8'),context);
 context.archive=archive;context.taxonomy=taxonomy;
 vm.runInContext('data=archive;topicTaxonomy=taxonomy;validateTopics(data,topicTaxonomy);render()',context);
 const labels=taxonomy.categories.filter(c=>archive.records.some(r=>r.topics.includes(c.label))).map(c=>c.label);
 assert.equal(new Set(labels).size,labels.length);
 assert.equal((element('topic').innerHTML.match(/<option/g)||[]).length,labels.length+1);
 for(const label of labels){
  element('topic').value=label;
  const ids=Array.from(vm.runInContext('selected().map(r=>r.id)',context));
  assert.deepEqual([...ids].sort(),archive.records.filter(r=>r.topics.includes(label)).map(r=>r.id).sort(),prefix+label);
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
 console.log(prefix+'frontend: '+labels.length+' filtri canonici, ricerca e norma multiargomento OK');
}
