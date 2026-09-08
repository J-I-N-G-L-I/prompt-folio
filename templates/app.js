'use strict';
(() => {
  const data = JSON.parse(document.getElementById('library-data').textContent);
  const $ = id => document.getElementById(id);
  const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const H = escapeHTML;
  const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  const getPrompt = id => data.prompts.find(p => p.id === id);
  const validLevel = id => data.levels.some(level => level.id === id);
  const storageKey = 'prompt-handbook-language';
  let searchTerm = '', toastTimer, revision = 0;
  function matchLocale(value) {
    if (typeof value !== 'string') return null;
    const tag = value.replaceAll('_','-').toLowerCase();
    const exact = Object.keys(data.locales).find(code => code.toLowerCase() === tag);
    if (exact) return exact;
    if (tag === 'zh' || tag.startsWith('zh-')) return /hant|tw|hk|mo/.test(tag) ? 'zh-TW' : 'zh-CN';
    if (tag === 'pt' || tag.startsWith('pt-')) return 'pt-BR';
    return has(data.locales,tag.split('-')[0]) ? tag.split('-')[0] : null;
  }
  function defaultLocale() {
    try {
      for (const key of [storageKey, 'direct-first-language']) {
        const saved = matchLocale(localStorage.getItem(key)); if (saved) return saved;
      }
    } catch (_) { /* The handbook also works when browser storage is blocked. */ }
    for (const lang of navigator.languages || [navigator.language]) {
      const match = matchLocale(lang); if (match) return match;
    }
    return 'en';
  }
  let state;
  function parseRoute() {
    const hash = new URLSearchParams(location.hash.slice(1));
    const query = new URLSearchParams(location.search);
    const lang = matchLocale(hash.get('lang')) || matchLocale(query.get('lang')) || (state && state.lang) || defaultLocale();
    let id = hash.get('prompt');
    // Legacy Direct First links only contained #lang=xx. New home links include view=library.
    const legacy = (hash.has('lang') || query.has('lang')) && !hash.has('view') && !hash.has('level') && !hash.has('prompt');
    if (legacy) id = 'direct-first';
    const prompt = getPrompt(id);
    const view = prompt ? 'prompt' : (hash.get('view') === 'guide' ? 'guide' : 'library');
    return {lang, view, prompt:prompt ? prompt.id : null, level:prompt ? prompt.level : (validLevel(hash.get('level')) ? hash.get('level') : 'all'), combined:!!(prompt && prompt.level==='project' && hash.get('with')==='direct-first')};
  }
  function href(next) {
    const s = {...state, ...next}; const params = new URLSearchParams();
    if (s.view === 'prompt' && getPrompt(s.prompt)) {
      params.set('prompt',s.prompt);
      if (s.combined && getPrompt(s.prompt).level === 'project') params.set('with','direct-first');
    } else {
      params.set('view',s.view === 'guide' ? 'guide' : 'library');
      if (validLevel(s.level) && s.view !== 'guide') params.set('level',s.level);
    }
    params.set('lang',s.lang); return '#' + params.toString();
  }
  function icon(name, classes='icon', tile=false) {
    return `<svg class="${H(classes)}" viewBox="0 0 ${tile ? '64 64' : '24 24'}" aria-hidden="true" focusable="false"><use href="#${tile ? 'tile-' : 'i-'}${H(name)}"/></svg>`;
  }
  function localized(prompt) { return prompt.locales[state.lang]; }
  function counterText() {
    return data.locales[state.lang].countText.replace('{prompts}',String(data.prompts.length)).replace('{levels}',String(data.levels.length));
  }
  function appNavigation() {
    const t = data.locales[state.lang];
    let nav = `<p class="nav-caption">${H(t.library)}</p><nav class="nav-list" aria-label="${H(t.library)}"><a class="nav-link ${state.view==='library' && state.level==='all' ? 'active' : ''}" ${state.view==='library' && state.level==='all' ? 'aria-current="page"' : ''} data-nav href="${H(href({view:'library',level:'all',prompt:null,combined:false}))}">${icon('grid')}<span>${H(t.all)}</span><span class="nav-count">${data.prompts.length}</span></a>`;
    for (const level of data.levels) {
      const prompts = data.prompts.filter(p => p.level===level.id);
      const active = state.level===level.id && state.view!=='guide';
      nav += `<a class="nav-link ${active?'active':''}" ${active?'aria-current="true"':''} data-nav href="${H(href({view:'library',level:level.id,prompt:null,combined:false}))}">${icon(level.icon)}<span>${H(t[level.id])}</span><span class="nav-count">${prompts.length}</span></a>`;
      for (const p of prompts) nav += `<a class="nav-child ${state.prompt===p.id?'active':''}" ${state.prompt===p.id?'aria-current="page"':''} data-nav href="${H(href({view:'prompt',prompt:p.id,combined:false}))}">${H(localized(p).title)}</a>`;
    }
    nav += `</nav><div class="nav-bottom"><a class="nav-link ${state.view==='guide'?'active':''}" ${state.view==='guide'?'aria-current="page"':''} data-nav href="${H(href({view:'guide',level:'all',prompt:null,combined:false}))}">${icon('book')}<span>${H(t.how)}</span></a></div><p class="rail-note"><b>${H(data.site.title)}</b><br>${H(counterText()).replace(/ · (?=[^·]*$)/,'<br>')}<br><span dir="ltr">v${H(data.site.version)}</span></p>`;
    $('sidebar').innerHTML = nav;
    $('sidebar').setAttribute('aria-label',t.library);
  }
  function notes(includeProject=false) {
    const t = data.locales[state.lang];
    return `<details class="details-note"><summary>${H(t.notesTitle)}</summary><p>${H(t.scopeNote)}</p>${includeProject?`<p>${H(t.projectNote)} <a href="${H(data.guides.project[0].url)}" target="_blank" rel="noopener noreferrer">ChatGPT ↗</a> · <a href="${H(data.guides.user[2].url)}" target="_blank" rel="noopener noreferrer">Gemini ↗</a></p>`:''}<p>${H(t.notes)}</p><p>${H(t.lengthNote)}</p><p>${H(t.quality)}</p><p>${H(t.checked)}</p></details>`;
  }
  function guide(level, standalone=false) {
    const t = data.locales[state.lang];
    const routes = t[level+'Routes'];
    const entries = data.guides[level].map((service,i) => `<details class="service" ${i===0?'open':''}><summary><span dir="auto">${H(service.name)}</span></summary><p>${H(routes[i])}</p>${state.lang!=='en'?`<code class="path" lang="en" dir="ltr">${H(service.path)}</code>`:''}<a class="source-link" href="${H(service.url)}" target="_blank" rel="noopener noreferrer">${H(t.sources)} ${icon('external','icon')}</a></details>`).join('');
    return `<section class="aside-card"><h2>${H(standalone?t[level]:t.how)}</h2><p class="intro">${H(level==='user'?t.intro:t.projectDesc)}</p>${entries}<details class="service"><summary>${H(t.commonTitle)}</summary><p>${H(t.common)}</p><p dir="auto">Grok · DeepSeek · Qwen · Kimi · Doubao</p></details></section>`;
  }
  function renderLibrary() {
    const t = data.locales[state.lang];
    const cats = data.levels.map((level,i) => {
      const count=data.prompts.filter(p=>p.level===level.id).length;
      return `<a class="scope-card ${state.level===level.id?'selected':''}" data-nav href="${H(href({view:'library',level:level.id,prompt:null,combined:false}))}"><div class="scope-top">${icon(level.icon,'icon-tile',true)}<span class="scope-no" aria-hidden="true">0${i+1}</span></div><h2>${H(t[level.id])}</h2><p>${H(t[level.id+'Desc'])}</p><div class="scope-foot"><span>${H(t.entries)} · ${count}</span>${icon('arrow','icon small-icon flip')}</div></a>`;
    }).join('');
    $('main').innerHTML = `<section class="hero"><p class="eyebrow">${H(data.site.title)}</p><h1>${H(state.level==='all'?t.heroTitle:t[state.level])}</h1><p>${H(state.level==='all'?t.heroDesc:t[state.level+'Desc'])}</p></section>${state.level==='all'?`<section aria-labelledby="browse-title"><h2 class="section-title" id="browse-title">${H(t.browse)}</h2><div class="categories">${cats}</div></section>`:''}<section aria-labelledby="collection-title"><div class="collection-head"><h2 id="collection-title">${H(state.level==='all'?t.entries:t[state.level])}</h2><span class="result-count" id="result-count" role="status" aria-live="polite"></span></div><div class="search-wrap">${icon('search')}<input type="search" id="search" aria-label="${H(t.search)}" placeholder="${H(t.search)}" value="${H(searchTerm)}" autocomplete="off" spellcheck="false"><button id="clear-search" type="button" aria-label="${H(t.clear)}" title="${H(t.clear)}" hidden>${icon('close')}</button></div><div class="entries" id="entries"></div></section><section class="quick">${icon('book')}<div><h2>${H(t.quickTitle)}</h2><p>${H(t.quickText)} <a data-nav href="${H(href({view:'guide',level:'all',prompt:null}))}">${H(t.how)} ↗</a></p></div></section>${notes(true)}`;
    $('search').addEventListener('input', () => { searchTerm=$('search').value; updateResults(); });
    $('clear-search').addEventListener('click', () => { searchTerm=''; $('search').value=''; updateResults(); $('search').focus(); });
    updateResults();
  }
  function updateResults() {
    const t=data.locales[state.lang], query=searchTerm.trim().normalize('NFKC').toLocaleLowerCase(state.lang);
    const prompts=data.prompts.filter(p => {
      const loc=localized(p), search=[p.id,loc.title,loc.description,loc.body,t[p.level]].join(' ').normalize('NFKC').toLocaleLowerCase(state.lang);
      return (state.level==='all' || p.level===state.level) && (!query || search.includes(query));
    });
    $('entries').innerHTML=prompts.length ? prompts.map(p=>`<a class="entry" data-nav href="${H(href({view:'prompt',prompt:p.id,combined:false}))}" aria-label="${H(t.open+': '+localized(p).title)}">${icon(p.icon,'icon-tile',true)}<div class="entry-content"><div class="entry-tag"><span>${H(t[p.level])}</span><span class="dot" aria-hidden="true"></span><span dir="ltr">v${H(p.version)}</span></div><h3>${H(localized(p).title)}</h3><p>${H(localized(p).description)}</p></div>${icon('arrow','entry-arrow icon flip')}</a>`).join('') : `<div class="empty">${H(t.empty)}</div>`;
    $('result-count').textContent=String(prompts.length).padStart(2,'0');
    $('clear-search').hidden=!searchTerm;
  }
  function promptText() {
    const p=getPrompt(state.prompt); if(!p) return '';
    const t=data.locales[state.lang];
    if(p.level==='project' && state.combined) return `## ${t.combinedUser}\n\n${localized(getPrompt('direct-first')).body}\n\n## ${t.combinedProject.split(' · ')[0]} · ${localized(p).title}\n\n${localized(p).body}`;
    return localized(p).body;
  }
  function updatePreview() {
    const text=promptText(), t=data.locales[state.lang];
    $('prompt-text').textContent=text;
    $('character-count').textContent=`${Array.from(text).length.toLocaleString(state.lang)} ${t.characters}`;
  }
  function renderPrompt() {
    const p=getPrompt(state.prompt), loc=localized(p), t=data.locales[state.lang];
    const combine=p.level==='project'?`<div class="combine"><label><input type="checkbox" id="combine" ${state.combined?'checked':''}>${H(t.attach)}</label><p>${H(t.attachHelp)}</p></div>`:'';
    const extra=p.level==='project'?`${loc.starter?`<section class="aside-card"><h2>${H(loc.starterTitle || t.commonTitle)}</h2><p class="starter-body">${H(loc.starter)}</p><button class="button" id="copy-starter" type="button">${icon('copy')}<span>${H(t.starterCopy)}</span></button></section>`:''}<section class="aside-card"><p class="scope-explainer">${H(t.projectNote)}</p><p style="margin:10px 0 0"><a class="source-link" href="${H(data.guides.project[0].url)}" target="_blank" rel="noopener noreferrer">ChatGPT ↗</a> · <a class="source-link" href="${H(data.guides.user[2].url)}" target="_blank" rel="noopener noreferrer">Gemini ↗</a></p></section>`:`<section class="aside-card"><p class="scope-explainer">${H(t.scopeNote)}</p></section>`;
    $('main').innerHTML=`<a class="back-link" data-nav href="${H(href({view:'library',level:p.level,prompt:null,combined:false}))}">${icon('back','icon small-icon flip')}${H(t.backLibrary)}</a><section class="detail-hero"><div class="detail-title-row">${icon(p.icon,'icon-tile',true)}<div><div class="detail-meta"><span>${H(t[p.level])}</span><span class="dot" aria-hidden="true"></span><span dir="ltr">v${H(p.version)}</span></div><h1>${H(loc.title)}</h1><p>${H(loc.description)}</p></div></div></section><div class="detail-layout"><div><section class="reader" aria-label="${H(t.promptTitle)}"><div class="reader-tools"><span class="tool-label" id="character-count"></span><div class="tool-buttons"><button class="button primary" id="copy-prompt" type="button">${icon('copy')}<span>${H(t.copy)}</span></button><button class="button" id="download" type="button" title="${H(t.download)}">${icon('download')}<span>.md</span><span class="sr-only" hidden>${H(t.download)}</span></button></div></div>${combine}<div class="reader-content"><pre class="prompt" id="prompt-text" tabindex="0" aria-label="${H(t.promptTitle)}"></pre></div><p class="reader-foot">${H(p.level==='user'?t.hint:t.lengthNote)}</p></section><div style="margin-top:14px"><button class="button" id="share" type="button">${icon('link')}<span>${H(t.share)}</span></button></div><div id="fallback-slot"></div>${notes(false)}</div><aside class="detail-aside" aria-label="${H(t.how)}">${guide(p.level)}${extra}</aside></div>`;
    $('download').setAttribute('aria-label',t.download);
    updatePreview();
    if($('combine')) $('combine').addEventListener('change',()=>{
      state.combined=$('combine').checked;revision++;
      const hash=href(state);try{history.replaceState(null,'',hash);}catch(_){location.hash=hash;}
      hideToast();updatePreview();
    });
    $('copy-prompt').addEventListener('click',event=>copyText(promptText(),event.currentTarget,t.copied));
    $('share').addEventListener('click',event=>copyText(shareURL(),event.currentTarget,t.copiedLink));
    if($('copy-starter')) $('copy-starter').addEventListener('click',event=>copyText(loc.starter,event.currentTarget,t.copied));
    $('download').addEventListener('click',downloadPrompt);
  }
  function renderGuide() {
    const t=data.locales[state.lang];
    $('main').innerHTML=`<section class="hero"><p class="eyebrow">${H(data.site.title)}</p><h1>${H(t.how)}</h1><p>${H(t.quickText)}</p></section><div class="standalone-guide"><p class="guide-intro">${H(t.scopeNote)}</p><div class="guide-grid">${guide('user',true)}${guide('project',true)}</div>${notes(true)}</div>`;
  }
  function render({focus=false}={}) {
    revision++;hideToast();
    const t=data.locales[state.lang];
    document.documentElement.lang=state.lang;document.documentElement.dir=t.dir;
    document.title=state.view==='prompt'?`${localized(getPrompt(state.prompt)).title} · ${data.site.title}`:`${data.site.title} — ${t.heroTitle}`;
    $('language').value=state.lang;$('language-label').textContent=t.language;
    $('privacy').textContent=t.privacy;$('license').textContent=t.license;
    $('footer-guide').textContent=t.how;$('footer-guide').href=href({view:'guide',level:'all',prompt:null,combined:false});$('footer-guide').dataset.nav='';
    $('brand').href=href({view:'library',level:'all',prompt:null,combined:false});$('brand').dataset.nav='';
    $('skip').textContent=t.skip;
    appNavigation();
    if(state.view==='prompt')renderPrompt();else if(state.view==='guide')renderGuide();else renderLibrary();
    if(focus){$('main').focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
  }
  function navigate(hash,focus=true) {
    searchTerm='';
    try {history.pushState(null,'',hash);state=parseRoute();render({focus});}
    catch (_) {location.hash=hash;}
  }
  function hideToast(){clearTimeout(toastTimer);$('toast').hidden=true;$('toast').textContent='';}
  function toast(text){hideToast();$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(hideToast,3500);}
  function legacyCopy(text){
    const area=document.createElement('textarea');area.value=text;area.readOnly=true;
    area.style.cssText='position:fixed;top:0;left:-9999px;width:1px;height:1px;';
    document.body.append(area);area.focus();area.select();area.setSelectionRange(0,text.length);
    let result=false;try{result=document.execCommand('copy');}catch(_){}finally{area.remove();}return result;
  }
  async function copyText(text,button,success){
    const startedRevision=revision;button.disabled=true;let ok=false;
    try {if(navigator.clipboard && window.isSecureContext){await navigator.clipboard.writeText(text);ok=true;}}catch(_){}
    // Do not alter the current view when an old asynchronous permission request finishes.
    if(!ok && startedRevision===revision)ok=legacyCopy(text);
    if(button.isConnected)button.disabled=false;
    if(startedRevision!==revision)return;
    if(ok){if($('fallback-slot'))$('fallback-slot').replaceChildren();button.focus({preventScroll:true});toast(success);}
    else {
      const slot=$('fallback-slot');
      slot.innerHTML=`<div class="copy-fallback"><p>${H(data.locales[state.lang].copyFail)}</p><textarea readonly aria-label="${H(data.locales[state.lang].copy)}"></textarea></div>`;
      const area=slot.querySelector('textarea');area.value=text;area.focus();area.select();area.setSelectionRange(0,text.length);
      toast(data.locales[state.lang].copyFail);
    }
  }
  function shareURL(){
    const base=/^https?:$/.test(location.protocol)?location.href:data.site.url;
    const url=new URL(base);url.search='';url.hash=href(state).slice(1);return url.href;
  }
  function downloadPrompt(){
    const blob=new Blob([promptText()+'\n'],{type:'text/markdown;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=`${state.prompt}${state.combined?'-with-direct-first':''}.${state.lang}.md`;
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  $('language').addEventListener('change',()=>{
    const lang=$('language').value;if(!has(data.locales,lang))return;
    try{localStorage.setItem(storageKey,lang);}catch(_){}
    state.lang=lang;
    try{history.replaceState(null,'',href(state));}catch(_){}
    render();
  });
  $('skip').addEventListener('click',event=>{event.preventDefault();$('main').focus();});
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[data-nav]');
    if(!link || event.button!==0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)return;
    event.preventDefault();navigate(link.getAttribute('href'));
  });
  function onHistory(){if(location.hash==='#main')return;searchTerm='';state=parseRoute();render();}
  window.addEventListener('hashchange',onHistory);window.addEventListener('popstate',onHistory);
  state=parseRoute();render();
})();
