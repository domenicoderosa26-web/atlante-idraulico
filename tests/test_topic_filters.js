'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const taxonomy=JSON.parse(fs.readFileSync('topic-taxonomy.json','utf8'));
async function main(){
 const prefix='';
 const archive=JSON.parse(fs.readFileSync(prefix+'data.json','utf8'));
 const elements=new Map();
 const element=id=>{if(!elements.has(id))elements.set(id,{value:'',options:[{outerHTML:'<option value="">Tutti gli argomenti</option>'}],innerHTML:'',textContent:'',hidden:true,disabled:false,addEventListener(){},classList:{toggle(){}},setAttribute(){},insertAdjacentHTML(position,html){this.innerHTML+=html;}});return elements.get(id);};
 const context=vm.createContext({document:{head:{insertAdjacentHTML(){}},getElementById:element,querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener(){}},location:{hash:''},history:{},fetch:()=>new Promise(()=>{}),setInterval(){},URL,console,Date});
 vm.runInContext(fs.readFileSync(prefix+'app.js','utf8'),context);
 // Reverse the stored order: the UI must sort dynamically and always expose
 // exactly the authorized 14 labels.
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
 // Exercise the real loading path, including optional national metadata.
 const requests=[];
 const national=JSON.parse(fs.readFileSync('national.json','utf8'));
 const status=JSON.parse(fs.readFileSync('update-status.json','utf8'));
 context.fetch=async(url,options)=>{
  requests.push(url);assert.equal(options.cache,'no-store');
  assert.ok(['data.json','topic-taxonomy.json','national.json','update-status.json','monitoring-status.json'].includes(url));
  return {ok:url!=='monitoring-status.json',json:async()=>({'data.json':archive,'topic-taxonomy.json':taxonomy,'national.json':national,'update-status.json':status}[url])};
 };
 await vm.runInContext('load()',context);
 assert.deepEqual(requests,['data.json','topic-taxonomy.json','national.json','update-status.json','monitoring-status.json']);
 assert.equal(vm.runInContext('data.records.length',context),archive.records.length);
 assert.equal(vm.runInContext('national.acts.length',context),national.acts.length);
 assert.equal(element('load-error').hidden,true);
 context.fetch=async url=>{if(url==='national.json')throw Error('unavailable');return {ok:true,json:async()=>({'data.json':archive,'topic-taxonomy.json':taxonomy,'update-status.json':status}[url])};};
 context.console={...console,warn(){}};
 await vm.runInContext('load()',context);
 assert.equal(element('load-error').hidden,true);
 context.fetch=async()=>({ok:true,json:async()=>({records:[]})});
 await vm.runInContext('load()',context);
 assert.equal(element('load-error').hidden,false);
 assert.equal(vm.runInContext('data.records.length',context),archive.records.length);
 context.monitorStatus={outcome:'completato',last_completed_at:'2026-10-08T07:30:00+02:00',changes_detected:0,changes_published:0};
 context.monitorArchive={...archive,runs:[{date:'2026-10-08',type:'Ciclo automatico territoriale · parziale',checked:['fonte A'],errors:['timeout fonte A'],territories:['Sardegna']}]};
 const undocumented=vm.runInContext('monitoringLabels(null,null,monitorArchive)',context);
 assert.equal(undocumented.nationalDate,'Non ancora documentato');
 assert.ok(undocumented.territorialDate.includes('08/10/2026'));
 assert.ok(undocumented.territorialText.includes('parziale'));
 context.pendingStatus={outcome:'verificato',verification_completed_at:'2026-10-08T10:00:00Z',changes_detected:2,changes_published:0,last_successful_result:context.monitorStatus};
 assert.ok(vm.runInContext('monitoringLabels(pendingStatus,null,monitorArchive).nationalText',context).includes('pubblicazione non confermata'));
 context.health={checked_at:'2026-10-08T11:00:00Z',national:{state:'fallito',checkpoint_consistent:true}};
 assert.ok(vm.runInContext('monitoringLabels(monitorStatus,health,monitorArchive).nationalText',context).includes('tentativo fallito'));
 context.health.national={state:'non_allineato',checkpoint_consistent:false,checkpoint_end:'2026-10-06T10:00:00Z'};
 const mismatch=vm.runInContext('monitoringLabels(monitorStatus,health,monitorArchive)',context);
 assert.ok(mismatch.nationalDate.includes('6/10/2026'));assert.ok(mismatch.nationalText.includes('non certifica'));
 console.log('Stati di monitoraggio nazionale/territoriale, parzialità e pubblicazione non confermata OK');
 console.log('Caricamento dalla radice, registro nazionale facoltativo e conservazione dopo errore OK');
 console.log(prefix+'frontend: 14 filtri A–Z, 168 combinazioni territorio/livello, ricerca, ordinamento e multitag OK');
}

main().catch(error=>{console.error(error);process.exitCode=1;});
