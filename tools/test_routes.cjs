/* Pure routing tests in a Node VM. This is not a network or browser test. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');const d=JSON.parse(fs.readFileSync(path.join(root,'content/library.json'),'utf8'));
d.prompts=d.promptFiles.map(f=>JSON.parse(fs.readFileSync(path.join(root,'content',f),'utf8')));
let app=fs.readFileSync(path.join(root,'templates/app.js'),'utf8');
const end=app.indexOf("  $('language').addEventListener('change'");assert(end>0,'Test export boundary changed; update the harness');
app=app.slice(0,end)+"state=parseRoute(); globalThis.testExports={parseRoute,target,normalize,state,selectedPrompts,promptText};})();";
function run(url,relative='../../../',indexRoot=false,siteURL=d.site.url){
 const location=new URL(url);const info={root:relative,indexRoot,route:{lang:'en',view:'library',level:'all',prompt:null}};
 const fixture={...d,site:{...d.site,url:siteURL}};
 const sandbox={URL,URLSearchParams,location,navigator:{languages:['en']},localStorage:{getItem:()=>null},document:{getElementById:id=>({textContent:JSON.stringify(id==='library-data'?fixture:info)})}};
 vm.createContext(sandbox);vm.runInContext(app,sandbox);return sandbox.testExports;
}
let t=run('https://example.test/prompt-folio/zh-CN/project/paper-mentor/');
assert.equal(t.state.prompt,'paper-mentor');assert.equal(t.state.lang,'zh-CN');
assert.equal(t.target({view:'library',prompt:null,level:'all'}),'/prompt-folio/zh-CN/');
assert.equal(t.target({with:['direct-first']},true),'https://example.test/prompt-folio/zh-CN/project/paper-mentor/?with=direct-first');
t=run('https://example.test/prompt-folio/#prompt=paper-mentor&lang=az&with=direct-first','./',true);
assert.equal(t.state.prompt,'paper-mentor');assert.equal(t.state.lang,'az');assert.equal(t.state.with[0],'direct-first');
assert(t.promptText().includes('Əvvəl əsas fikir'));
t=run('https://example.test/prompt-folio/#lang=zh-CN','./',true);assert.equal(t.state.view,'library');assert.equal(t.state.lang,'zh-CN');
t=run('https://example.test/prompt-folio/en/?q=paper+mentor','../');assert.equal(t.state.q,'paper mentor');assert.equal(t.state.level,'all');
t=run('https://example.test/prompt-folio/en/user/direct-first/');assert.equal(t.state.with.length,0);assert.equal(t.normalize('PAPER_mentor'),'paper mentor');
t=run('https://example.test/prompt-folio/#prompt=unknown&lang=en','./',true);assert.equal(t.state.view,'library');
t=run('https://example.test/prompt-folio/zh-CN/chat/','../../');
assert.equal(t.state.level,'chat');assert.equal(t.state.view,'library');
assert.equal(t.target({view:'prompt',prompt:'dnd-dungeon-master'}),'/prompt-folio/zh-CN/chat/dnd-dungeon-master/');
t=run('https://example.test/prompt-folio/#view=library&level=chat&lang=zh-CN','./',true);
assert.equal(t.state.level,'chat');
t=run('https://example.test/prompt-folio/ar/chat/dnd-dungeon-master/');
assert.equal(t.state.prompt,'dnd-dungeon-master');
assert.equal(t.promptText(),d.prompts.find(p=>p.id==='dnd-dungeon-master').locales.ar.body);
t=run('https://prompts.example.com/zh-CN/chat/dnd-dungeon-master/','../../../',false,'https://prompts.example.com/');
assert.equal(t.state.prompt,'dnd-dungeon-master');
assert.equal(t.target({view:'library',prompt:null,level:'chat'}),'/zh-CN/chat/');
assert.equal(t.target({},true),'https://prompts.example.com/zh-CN/chat/dnd-dungeon-master/');
console.log('Routing VM: passed (project paths, root custom domains, chat scope, legacy links, composition and aliases).');
