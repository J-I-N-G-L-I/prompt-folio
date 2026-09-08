'use strict';
(() => {
  const data = JSON.parse(document.getElementById('library-data').textContent);
  const page = JSON.parse(document.getElementById('page-data').textContent);
  const $ = id => document.getElementById(id);
  const H = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  const getPrompt=id=>data.prompts.find(p=>p.id===id);
  const validLevel=id=>data.levels.some(l=>l.id===id);
  const http=/^https?:$/.test(location.protocol);
  // Compute the root once. Later pushState navigations must never change it.
  const baseURL=page.notFound&&http ? new URL(new URL(data.site.url).pathname,location.origin) : (http||location.protocol==='file:') ? new URL(page.root,location.href) : new URL(data.site.url);
  const storageKey='prompt-folio-language';
  let state, revision=0, toastTimer;
  function matchLocale(v){
    if(typeof v!=='string')return null;const tag=v.replaceAll('_','-').toLowerCase();
    const exact=Object.keys(data.locales).find(c=>c.toLowerCase()===tag);if(exact)return exact;
    if(tag==='zh'||tag.startsWith('zh-'))return /hant|tw|hk|mo/.test(tag)?'zh-TW':'zh-CN';
    if(tag==='pt'||tag.startsWith('pt-'))return 'pt-BR';
    return has(data.locales,tag.split('-')[0])?tag.split('-')[0]:null;
  }
  function defaultLocale(){
    try{for(const key of [storageKey,'prompt-handbook-language','direct-first-language']){const c=matchLocale(localStorage.getItem(key));if(c)return c;}}catch(_){/* Storage is optional. */}
    for(const c of navigator.languages||[navigator.language]){const m=matchLocale(c);if(m)return m;}return 'en';
  }
  function pathRoute(){
    if(!http)return {...page.route,lang:page.indexRoot?defaultLocale():page.route.lang};
    const parts=location.pathname.slice(baseURL.pathname.length).replace(/index\.html$/,'').split('/').filter(Boolean);
    const lang=matchLocale(parts[0]);
    if(!lang)return {lang:defaultLocale(),view:'library',level:'all',prompt:null};
    const p=getPrompt(parts[2]);
    return {lang,view:p?'prompt':parts[1]==='guide'?'guide':'library',level:p?p.level:validLevel(parts[1])?parts[1]:'all',prompt:p?p.id:null};
  }
  function parseRoute(){
    const r=pathRoute(),h=new URLSearchParams(location.hash.slice(1)),q=new URLSearchParams(location.search);
    const legacy=h.has('lang')||h.has('view')||h.has('prompt')||h.has('level');
    if(legacy){
      const p=getPrompt(h.get('prompt'));
      r.view=p?'prompt':h.get('view')==='guide'?'guide':'library';r.prompt=p?p.id:null;r.level=p?p.level:validLevel(h.get('level'))?h.get('level'):'all';
    }
    r.lang=matchLocale(h.get('lang'))||matchLocale(q.get('lang'))||r.lang;
    const p=getPrompt(r.prompt),allowed=p?.recommendedWith||[];
    r.with=(h.get('with')||q.get('with')||'').split(',').filter((id,i,a)=>allowed.includes(id)&&a.indexOf(id)===i);
    r.q=q.get('q')||'';return r;
  }
  function target(next={},absolute=false){
    const s={...state,...next};let p=getPrompt(s.prompt);if(s.view!=='prompt')p=null;
    if(!http){const h=new URLSearchParams();if(p)h.set('prompt',p.id);else{h.set('view',s.view||'library');if(validLevel(s.level))h.set('level',s.level);}h.set('lang',s.lang);if(p&&s.with?.length)h.set('with',s.with.join(','));return '#'+h;}
    let path=s.lang+'/';if(p)path+=p.level+'/'+p.id+'/';else if(s.view==='guide')path+='guide/';else if(validLevel(s.level))path+=s.level+'/';
    const u=new URL(path,baseURL);if(p&&s.with?.length)u.searchParams.set('with',s.with.join(','));if(!p&&s.q)u.searchParams.set('q',s.q);
    return absolute?u.href:u.pathname+u.search;
  }
  const loc=p=>p.locales[state.lang]||p.locales[p.sourceLanguage];
  const locLang=p=>has(p.locales,state.lang)?state.lang:p.sourceLanguage;
  const t=()=>data.locales[state.lang];
  const icon=(name,cls='icon',tile=false)=>`<svg class="${H(cls)}" viewBox="0 0 ${tile?'64 64':'24 24'}" aria-hidden="true" focusable="false"><use href="#${tile?'tile-':'i-'}${H(name)}"/></svg>`;
  function counter(){return t().countText.replace('{prompts}',String(data.prompts.length)).replace('{levels}',String(data.levels.length)).replace('{languages}',String(data.languageCount));}
  function guide(level){
    const tr=t();let out=`<section class="aside-card"><h2>${H(tr[level])}</h2><p class="intro">${H(level==='user'?tr.intro:tr[level+'Desc'])}</p>`;
    for(const [i,id] of data.guides[level].entries()){
      const s=data.services[id];out+=`<details class="service" ${i===0?'open':''}><summary>${H(s.name)}</summary><p>${H(tr.routes[id])}</p>${state.lang!=='en'?`<code class="path" lang="en" dir="ltr">${H(s.path)}</code>`:''}<a class="source-link" href="${H(s.url)}" target="_blank" rel="noopener noreferrer">${H(tr.sources)} ↗</a><span class="sr-only">${H(s.checked)}</span></details>`;
    }
    return out+`<details class="service"><summary>${H(tr.commonTitle)}</summary><p>${H(level==='chat'?tr.chatUse:tr.common)}</p>${level==='chat'?'':'<p dir="auto">Grok · DeepSeek · Qwen · Kimi · Doubao</p>'}</details></section>`;
  }
  function notes(project=false){const tr=t();return `<details class="details-note"><summary>${H(tr.notesTitle)}</summary><p>${H(tr.languageHelp)}</p><p>${H(tr.scopeNote)}</p>${project?`<p>${H(tr.projectNote)}</p>`:''}<p>${H(tr.notes)}</p><p>${H(tr.lengthNote)}</p><p>${H(tr.quality)}</p><p>${H(tr.checked)}</p></details>`;}
  function navigation(){
    const tr=t();let out=`<p class="nav-caption">${H(tr.library)}</p><nav class="nav-list" aria-label="${H(tr.library)}"><a class="nav-link ${state.view==='library'&&state.level==='all'?'active':''}" data-nav href="${H(target({view:'library',level:'all',prompt:null,with:[],q:''}))}" ${state.view==='library'&&state.level==='all'?'aria-current="page"':''}>${icon('grid')}<span>${H(tr.all)}</span><span class="nav-count">${data.prompts.length}</span></a>`;
    for(const l of data.levels){const active=state.level===l.id&&state.view!=='guide';const prompts=data.prompts.filter(p=>p.level===l.id);
      out+=`<a class="nav-link ${active?'active':''}" data-nav href="${H(target({view:'library',level:l.id,prompt:null,with:[],q:''}))}" ${active?'aria-current="true"':''}>${icon(l.icon)}<span>${H(tr[l.id])}</span><span class="nav-count">${prompts.length}</span></a>`;
      for(const p of prompts)out+=`<a class="nav-child ${p.id===state.prompt?'active':''}" data-nav href="${H(target({view:'prompt',prompt:p.id,with:[],q:''}))}" ${p.id===state.prompt?'aria-current="page"':''}>${H(loc(p).title)}</a>`;
    }
    $('sidebar').innerHTML=out+`</nav><div class="nav-bottom"><a class="nav-link" data-nav href="${H(target({view:'guide',prompt:null,level:'all',q:''}))}">${icon('book')}${H(tr.usageToggle)}</a></div><p class="rail-note"><b>${H(data.site.title)}</b><br>${H(counter())}<br><span dir="ltr">v${H(data.site.version)}</span></p>`;
    $('sidebar').setAttribute('aria-label',tr.library);
  }
  function renderLibrary(){
    const tr=t();const cats=data.levels.map((l,i)=>`<a class="scope-card" data-nav href="${H(target({view:'library',level:l.id,prompt:null,q:''}))}"><div class="scope-top">${icon(l.icon,'icon-tile',true)}<span class="scope-no">0${i+1}</span></div><h2>${H(tr[l.id])}</h2><p>${H(tr[l.id+'Desc'])}</p><div class="scope-foot"><span>${H(tr.entries)} · ${data.prompts.filter(p=>p.level===l.id).length}</span>${icon('arrow','icon small-icon flip')}</div></a>`).join('');
    $('main').innerHTML=`${page.notFound?`<p class="fallback-notice">${H(tr.notFound)}</p>`:''}<section class="hero"><p class="eyebrow">${H(data.site.title)}</p><h1>${H(state.level==='all'?tr.heroTitle:tr[state.level])}</h1><p>${H(state.level==='all'?tr.heroDesc:tr[state.level+'Desc'])}</p></section>${state.level==='all'?`<section class="scope-intro" aria-label="${H(tr.browse)}"><div class="categories">${cats}</div></section>`:''}<section aria-labelledby="collection-title"><div class="collection-head"><h2 id="collection-title">${H(tr.entries)}</h2><span id="result-count" class="result-count" role="status" aria-live="polite"></span></div><div class="search-wrap">${icon('search')}<input type="search" id="search" aria-label="${H(tr.search)}" placeholder="${H(tr.search)}" value="${H(state.q)}" autocomplete="off" spellcheck="false"><button id="clear-search" type="button" aria-label="${H(tr.clear)}" hidden>${icon('close')}</button></div><div id="entries" class="entries"></div></section><section class="quick">${icon('book')}<div><h2>${H(tr.quickTitle)}</h2><p>${H(tr.quickText)} <a data-nav href="${H(target({view:'guide',level:'all',prompt:null,q:''}))}">${H(tr.usageToggle)} ↗</a></p></div></section>${notes(true)}`;
    $('search').addEventListener('input',()=>{state.q=$('search').value;updateResults();try{history.replaceState(null,'',target());}catch(_){}});
    $('clear-search').addEventListener('click',()=>{state.q='';$('search').value='';updateResults();try{history.replaceState(null,'',target());}catch(_){}$('search').focus();});
    updateResults();
  }
  function normalize(value){return String(value).normalize('NFKC').toLowerCase().replace(/[\p{Pd}_]+/gu,' ').replace(/\s+/g,' ').trim();}
  function updateResults(){
    const tr=t(),words=normalize(state.q).split(' ').filter(Boolean);
    const results=data.prompts.filter(p=>{
      // Titles, aliases and descriptions across languages; body in the chosen language.
      const text=normalize([p.id,...(p.aliases||[]),...Object.values(p.locales).flatMap(l=>[l.title,l.description]),loc(p).body,tr[p.level]].join(' '));
      return (state.level==='all'||p.level===state.level)&&words.every(w=>text.includes(w));
    });
    $('entries').innerHTML=results.length?results.map(p=>`<a class="entry" data-nav href="${H(target({view:'prompt',prompt:p.id,with:[],q:''}))}" aria-label="${H(tr.open+': '+loc(p).title)}">${icon(p.icon,'icon-tile',true)}<div class="entry-content"><div class="entry-tag"><span>${H(tr[p.level])}</span><span class="dot"></span><span dir="ltr">v${H(p.version)}</span></div><h3 lang="${locLang(p)}" dir="auto">${H(loc(p).title)}</h3><p lang="${locLang(p)}" dir="auto">${H(loc(p).description)}</p>${!has(p.locales,state.lang)?`<span class="locale-count">${H(tr.statusMissing.replace('{language}',data.locales[p.sourceLanguage].name))}</span>`:''}</div>${icon('arrow','entry-arrow icon flip')}</a>`).join(''):`<div class="empty">${H(tr.empty)}</div>`;
    $('result-count').textContent=String(results.length);$('clear-search').hidden=!state.q;
  }
  function selectedPrompts(){const p=getPrompt(state.prompt);if(!p)return [];return [...(p.recommendedWith||[]).filter(id=>state.with.includes(id)).map(getPrompt),p];}
  function promptText(){const list=selectedPrompts();return list.length===1?loc(list[0]).body:list.map(p=>`## ${t()[p.level]} · ${loc(p).title}\n\n${loc(p).body}`).join('\n\n');}
  function updatePreview(){
    const text=promptText();
    // Formatting only: textContent remains exactly equal to the copied source.
    $('prompt-text').innerHTML=H(text).replace(/^(\d+[.、].+|#{1,3} .+)$/gm,'<span class="prompt-heading">$1</span>');
    const first=getPrompt(state.prompt);$('prompt-text').lang=has(first.locales,state.lang)?state.lang:first.sourceLanguage;
    $('prompt-text').dir=data.locales[$('prompt-text').lang].dir;
    $('character-count').textContent=Array.from(text).length.toLocaleString(state.lang)+' '+t().characters;
  }
  function quality(p){
    const tr=t(),m=loc(p).translation,key={source:'statusSource','ai-assisted':'statusAI',reviewed:'statusReviewed',stale:'statusStale'}[m.effectiveStatus];
    return `<details class="quality-box" open><summary>${H(tr.reviewTitle)}</summary><dl><dt>${H(tr.sourceLabel)}</dt><dd>${H(data.locales[p.sourceLanguage].name)}</dd><dt>${H(tr.versionLabel)}</dt><dd dir="ltr">${H(p.version)}</dd><dt>${H(tr.updatedLabel)}</dt><dd dir="ltr">${H(p.updated)}</dd><dt>${H(tr.translationLabel)}</dt><dd>${H(has(p.locales,state.lang)?tr[key]:tr.statusMissing.replace('{language}',data.locales[p.sourceLanguage].name))}</dd><dt>${H(tr.available)}</dt><dd>${Object.keys(p.locales).map(c=>H(data.locales[c].name)).join(' · ')}</dd></dl><p>${H(tr.evaluationNote)}</p><a href="${H(data.site.repository+'/issues/new/choose')}" target="_blank" rel="noopener noreferrer">${H(tr.feedback)} ↗</a></details>`;
  }
  function renderPrompt(){
    const p=getPrompt(state.prompt),l=loc(p),tr=t();
    const combine=(p.recommendedWith||[]).length?`<div class="combine"><fieldset><legend>${H(tr.optional)}</legend>${p.recommendedWith.map(id=>`<label><input type="checkbox" class="combine-toggle" value="${H(id)}" ${state.with.includes(id)?'checked':''}>${H(tr.include.replace('{title}',loc(getPrompt(id)).title))}</label>`).join('')}<p>${H(tr.attachHelp)}</p></fieldset></div>`:'';
    const starter=l.starter?`<section class="aside-card"><h2>${H(tr.starter)}</h2><p class="starter-hint">${H(tr.starterHelp)}</p><pre class="starter-body" lang="${has(p.locales,state.lang)?state.lang:p.sourceLanguage}" dir="auto">${H(l.starter)}</pre><button class="button" id="copy-starter" type="button">${icon('copy')}${H(tr.starterCopy)}</button></section>`:'';
    const back=target({view:'library',level:'all',prompt:null,with:[],q:''});
    $('main').innerHTML=`<a class="back-link" data-nav href="${H(back)}">${icon('back','icon small-icon flip')}${H(tr.backLibrary)}</a><section class="detail-hero"><div class="detail-title-row">${icon(p.icon,'icon-tile',true)}<div><div class="detail-meta"><span>${H(tr[p.level])}</span><span class="dot"></span><span dir="ltr">v${H(p.version)}</span></div><h1 lang="${locLang(p)}" dir="auto">${H(l.title)}</h1><p lang="${locLang(p)}" dir="auto">${H(l.description)}</p></div></div></section>${!has(p.locales,state.lang)?`<p class="fallback-notice">${H(tr.statusMissing.replace('{language}',data.locales[p.sourceLanguage].name))}</p>`:''}<details class="usage-panel" id="usage-panel"><summary>${icon('book')}<span>${H(tr.usageToggle)}</span><span class="scope-chip">${H(tr[p.level])}</span></summary><div class="usage-grid ${starter?'':'only-guide'}">${guide(p.level)}${starter}${p.level==='project'?`<p class="scope-explainer project-inheritance">${H(tr.projectNote)} <a href="${H(data.services['chatgpt-project'].url)}" target="_blank" rel="noopener noreferrer">ChatGPT ↗</a> · <a href="${H(data.services['gemini-user'].url)}" target="_blank" rel="noopener noreferrer">Gemini ↗</a></p>`:''}</div></details><div class="detail-layout"><div><section class="reader" aria-label="${H(tr.promptTitle)}"><div class="reader-tools"><span class="tool-label" id="character-count"></span><div class="tool-buttons"><button class="button primary" id="copy-prompt" type="button">${icon('copy')}<span>${H(tr.copy)}</span></button><button class="button" id="download" type="button" aria-label="${H(tr.download)}" title="${H(tr.download)}">${icon('download')}<span>.md</span></button><button class="button" id="share" type="button">${icon('link')}<span>${H(tr.share)}</span></button></div></div>${combine}<div class="reader-content"><pre id="prompt-text" class="prompt" tabindex="0" aria-label="${H(tr.promptTitle)}"></pre></div><p class="reader-foot">${H(p.level==='user'?tr.hint:tr.lengthNote)}</p></section><div id="fallback-slot"></div>${notes(false)}</div><aside class="detail-aside">${quality(p)}</aside></div>`;
    updatePreview();
    for(const box of document.querySelectorAll('.combine-toggle'))box.addEventListener('change',()=>{state.with=[...document.querySelectorAll('.combine-toggle:checked')].map(x=>x.value);revision++;hideToast();try{history.replaceState(null,'',target());}catch(_){}updatePreview();});
    $('copy-prompt').addEventListener('click',ev=>copyText(promptText(),ev.currentTarget,tr.copied));
    $('share').addEventListener('click',ev=>copyText(shareURL(),ev.currentTarget,tr.copiedLink));
    $('download').addEventListener('click',downloadPrompt);
    if($('copy-starter'))$('copy-starter').addEventListener('click',ev=>copyText(l.starter,ev.currentTarget,tr.copied));
  }
  function renderGuide(){const tr=t();$('main').innerHTML=`<section class="hero"><h1>${H(tr.usageToggle)}</h1><p>${H(tr.quickText)}</p></section><p class="guide-intro">${H(tr.scopeNote)}</p><div class="guide-grid">${data.levels.map(l=>guide(l.id)).join('')}</div>${notes(true)}`;}
  function metadata(){
    const p=getPrompt(state.prompt),title=p?loc(p).title+' · '+data.site.title:data.site.title+' — '+t().heroTitle;
    document.title=title;document.querySelector('meta[property="og:title"]').content=title;
    const desc=p?loc(p).description:t().heroDesc;document.querySelector('meta[name="description"]').content=desc;document.querySelector('meta[property="og:description"]').content=desc;
    const clean=target({lang:p&&!has(p.locales,state.lang)?p.sourceLanguage:state.lang,with:[],q:''},true);const canonical=http?new URL(new URL(clean).pathname,data.site.url).href:data.site.url;
    $('canonical').href=canonical;document.querySelector('meta[property="og:url"]').content=canonical;
    for(const el of document.querySelectorAll('link[rel="alternate"][hreflang]'))el.remove();
    const langs=p?Object.keys(p.locales):Object.keys(data.locales);
    for(const code of [...langs,'x-default']){const el=document.createElement('link');el.rel='alternate';el.hreflang=code;const c=code==='x-default'?(p?p.sourceLanguage:'en'):code;const to=target({lang:c,with:[],q:''},true);el.href=http?new URL(new URL(to).pathname,data.site.url).href:data.site.url;document.head.append(el);}
  }
  function render(focus=false){
    revision++;hideToast();const tr=t();document.documentElement.lang=state.lang;document.documentElement.dir=tr.dir;
    $('language').value=state.lang;$('language-label').textContent=tr.language;$('language').title=tr.languageHelp;
    document.querySelector('.brand-sub').textContent=tr.brandSub;$('brand').href=target({view:'library',prompt:null,level:'all',q:'',with:[]});
    $('privacy').textContent=tr.privacy;$('license').textContent=tr.license;$('license').href=new URL('LICENSE',baseURL).href;
    $('skip').textContent=tr.skip;$('footer-guide').textContent=tr.usageToggle;$('footer-guide').href=target({view:'guide',prompt:null,level:'all',q:''});$('footer-guide').dataset.nav='';
    navigation();if(state.view==='prompt')renderPrompt();else if(state.view==='guide')renderGuide();else renderLibrary();metadata();
    if(focus){$('main').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
  }
  function hideToast(){clearTimeout(toastTimer);$('toast').hidden=true;$('toast').textContent='';}
  function toast(text){hideToast();$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(hideToast,3500);}
  function legacyCopy(text){const area=document.createElement('textarea');area.value=text;area.readOnly=true;area.style.cssText='position:fixed;left:-9999px;top:0;';document.body.append(area);area.select();let ok=false;try{ok=document.execCommand('copy');}catch(_){}finally{area.remove();}return ok;}
  async function copyText(text,button,success){
    const r=revision;button.disabled=true;let ok=false;
    try{if(navigator.clipboard&&isSecureContext){await navigator.clipboard.writeText(text);ok=true;}}catch(_){}
    if(!ok&&r===revision)ok=legacyCopy(text);if(button.isConnected)button.disabled=false;if(r!==revision)return;
    if(ok){$('fallback-slot')?.replaceChildren();button.focus({preventScroll:true});toast(success);return;}
    const slot=$('fallback-slot');if(slot){slot.innerHTML=`<div class="copy-fallback"><p>${H(t().copyFail)}</p><textarea readonly aria-label="${H(t().promptTitle)}"></textarea></div>`;const area=slot.querySelector('textarea');area.value=text;area.focus();area.select();area.setSelectionRange(0,text.length);}toast(t().copyFail);
  }
  function shareURL(){if(http)return target({},true);const u=new URL(data.site.url);u.hash=target().slice(1);return u.href;}
  function downloadPrompt(){const text=promptText();const url=URL.createObjectURL(new Blob([text+'\n'],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`${state.prompt}${state.with.length?'-with-'+state.with.join('-'):''}.${locLang(getPrompt(state.prompt))}.md`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function navigate(url){page.notFound=false;try{history.pushState(null,'',url);state=parseRoute();render(true);}catch(_){location.href=url;}}
  $('language').addEventListener('change',()=>{const code=$('language').value;if(!has(data.locales,code))return;try{localStorage.setItem(storageKey,code);}catch(_){}state.lang=code;state.q='';try{history.replaceState(null,'',target());}catch(_){}render();});
  $('skip').addEventListener('click',ev=>{ev.preventDefault();$('main').focus();});
  document.addEventListener('click',ev=>{const a=ev.target.closest('a[data-nav]');if(!a||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.altKey||ev.shiftKey)return;ev.preventDefault();navigate(a.getAttribute('href'));});
  const historyChanged=()=>{if(location.hash==='#main')return;state=parseRoute();render();};
  addEventListener('popstate',historyChanged);addEventListener('hashchange',historyChanged);
  state=parseRoute();render();
})();
