#!/usr/bin/env python3
"""Deterministic, dependency-free static generator (Python 3.10+).

python tools/build.py             # update committed outputs AND _site/
python tools/build.py --check     # verify source, outputs, links; no writes
python tools/build.py --check --repository J-I-N-G-L-I/prompt-folio

GitHub Actions builds _site and synchronizes the three committed generated files.
Prompt bodies remain verbatim; presentation and stable routing IDs are separate.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, shutil, sys
from pathlib import Path
from urllib.parse import urlparse, urlencode, urljoin, unquote
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
from icons import MINI
ROOT=Path(__file__).resolve().parents[1]
GENERATED=('index.html','README.md','docs/PAPER-MENTOR.zh-CN.md')
E=lambda x: html.escape(str(x),quote=True)

def require(test:bool,message:str)->None:
    if not test: raise ValueError(message)

def load(root:Path=ROOT)->dict:
    d=json.loads((root/'content/library.json').read_text(encoding='utf-8'))
    require(d.get('schemaVersion')==2,'Unsupported schemaVersion (expected 2)')
    for key in ('title','repository','url','version','branch'):
        require(isinstance(d['site'].get(key),str) and d['site'][key],f'site.{key} is required')
    repo=urlparse(d['site']['repository']); site=urlparse(d['site']['url'])
    require(repo.scheme=='https' and repo.netloc=='github.com' and len(repo.path.strip('/').split('/'))==2,'Invalid repository URL')
    require(site.scheme=='https' and d['site']['url'].endswith('/') and not site.query and not site.fragment,'site.url must be HTTPS and end in /')
    owner,name=repo.path.strip('/').split('/')
    if site.netloc.endswith('.github.io'):
        expected='/' if name.lower()==f'{owner.lower()}.github.io' else f'/{name}/'
        require(site.netloc.lower()==f'{owner.lower()}.github.io' and site.path==expected,'Repository and GitHub Pages URL do not agree')
    require(set(d['locales']) >= {'en','zh-CN'},'English and Simplified Chinese UI are required')
    keys=set(d['locales']['en'])
    for code,t in d['locales'].items():
        require(bool(re.fullmatch(r'[a-z]{2}(?:-[A-Za-z]{2,4})?',code)),f'Invalid locale: {code}')
        require(set(t)==keys and t['dir'] in ('ltr','rtl'),f'Inconsistent UI fields: {code}')
        require(all(isinstance(v,(str,dict)) and bool(v) for v in t.values()),f'Invalid UI text: {code}')
        require(set(t['routes'])==set(d['services']),f'{code}: routes must be keyed by every service ID')
    levels=[x['id'] for x in d['levels']]
    require(len(set(levels))==len(levels) and set(levels)=={'user','project'},'This edition supports user and project scopes')
    for level,ids in d['guides'].items():
        require(level in levels and len(ids)==len(set(ids)) and all(i in d['services'] for i in ids),f'Invalid guide IDs: {level}')
    for sid,s in d['services'].items():
        require(s['id']==sid and urlparse(s['url']).scheme=='https',f'Invalid service {sid}')
        require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',s['checked'])),f'Missing check date: {sid}')
    d['prompts']=[]
    for f in d['promptFiles']:
        path=(root/'content'/f).resolve()
        require(path.is_relative_to((root/'content/prompts').resolve()),'Prompt file must be inside content/prompts/')
        p=json.loads(path.read_text(encoding='utf-8')); d['prompts'].append(p)
    ids=[p['id'] for p in d['prompts']]
    require(len(ids)==len(set(ids)) and bool(ids),'Empty library or duplicate IDs')
    for p in d['prompts']:
        require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',p['id'])),f'Invalid prompt ID: {p["id"]}')
        require(p['level'] in levels and bool(p['locales']),f'Invalid scope/locales: {p["id"]}')
        require(set(p['locales'])<=set(d['locales']) and p['sourceLanguage'] in p['locales'],f'Invalid source language: {p["id"]}')
        require(bool(re.fullmatch(r'\d+\.\d+\.\d+',p['version'])),f'Use semantic version: {p["id"]}')
        require(all(isinstance(a,str) and a.strip() for a in p['aliases']),f'Invalid aliases: {p["id"]}')
        require((root/'assets/icons'/f'{p["icon"]}.svg').is_file(),f'Missing icon: {p["id"]}')
        p['sourceHash']=hashlib.sha256(p['locales'][p['sourceLanguage']]['body'].encode('utf-8')).hexdigest()
        for code,loc in p['locales'].items():
            require(all(isinstance(loc.get(k),str) and loc[k].strip() for k in ('title','description','body')),f'Missing localized text: {p["id"]}/{code}')
            m=loc['translation']
            require(m['status'] in ('source','ai-assisted','reviewed'),f'Unknown review status: {p["id"]}/{code}')
            if m['status']=='reviewed':require(bool(m.get('reviewer')) and bool(m.get('reviewedAt')),'Human-reviewed needs a reviewer and date')
            if code==p['sourceLanguage']:m['effectiveStatus']='source'
            elif m['sourceVersion']!=p['version'] or m['sourceHash']!=p['sourceHash']:m['effectiveStatus']='stale'
            else:m['effectiveStatus']=m['status']
        for other in p.get('recommendedWith',[]):
            require(other in ids and other!=p['id'],f'Unknown composition reference: {other}')
            q=next(x for x in d['prompts'] if x['id']==other)
            require(q['level']=='user' and p['level']=='project','Compose project prompts with user-level preferences only')
    # SVGs are local code assets. Disallow active content or network dependencies.
    for icon in (root/'assets/icons').glob('*.svg'):
        tree=ET.fromstring(icon.read_text(encoding='utf-8'))
        for el in tree.iter():
            require(el.tag.split('}')[-1] not in ('script','foreignObject'),'Active SVG content is not allowed')
            require(not any(k.lower().startswith('on') for k in el.attrib),'SVG event handlers are not allowed')
    d['languageCount']=len({c.split('-')[0] for c in d['locales']})
    return d

def text_for(p:dict,code:str)->dict:
    return p['locales'].get(code) or p['locales'][p['sourceLanguage']]

def status_text(d:dict,p:dict,code:str)->str:
    s=text_for(p,code)['translation']['effectiveStatus']
    return d['locales'][code][{'source':'statusSource','ai-assisted':'statusAI','reviewed':'statusReviewed','stale':'statusStale'}[s]]

def route_path(code='en',level='all',prompt=None,view='library')->str:
    if prompt:return f'{code}/{level}/{prompt}/'
    if view=='guide':return f'{code}/guide/'
    if level in ('user','project'):return f'{code}/{level}/'
    return f'{code}/'

def link(d:dict,code:str,level='all',prompt=None,view='library',with_ids=None)->str:
    out=d['site']['url']+route_path(code,level,prompt,view)
    return out+('?' + urlencode({'with':','.join(with_ids)}) if with_ids else '')

def sprite()->str:
    result=['<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true" focusable="false"><defs>']
    for file in sorted((ROOT/'assets/icons').glob('*.svg')):
        inner=re.sub(r'^.*?<svg\b[^>]*>','',file.read_text(encoding='utf-8'),count=1,flags=re.S)
        inner=re.sub(r'</svg>\s*$','',inner)
        result.append(f'<symbol id="tile-{E(file.stem)}" viewBox="0 0 64 64" fill="none">{inner}</symbol>')
    for name,inner in MINI.items():
        result.append(f'<symbol id="i-{name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{inner}</symbol>')
    return ''.join(result)+'</defs></svg>'

def fenced(text:str)->str:
    # Variable-length fences make literal Markdown examples safe to copy.
    runs=[len(x) for x in re.findall(r'`+',text)]
    f='`'*max(3,(max(runs)+1 if runs else 3))
    return f+'text\n'+text+'\n'+f

def guide_html(d:dict,code:str,level:str)->str:
    t=d['locales'][code];out=f'<section class="aside-card"><h2>{E(t[level])}</h2>'
    out+=f'<p>{E(t["intro"] if level=="user" else t["projectDesc"])}</p>'
    for sid in d['guides'][level]:
        s=d['services'][sid]
        out+=f'<details class="service"><summary>{E(s["name"])}</summary><p>{E(t["routes"][sid])}</p><code class="path" lang="en" dir="ltr">{E(s["path"])}</code><a class="source-link" href="{E(s["url"])}">{E(t["sources"])}</a></details>'
    return out+f'<p>{E(t["common"])}</p></section>'

def static_main(d:dict,r:dict,root:str)->str:
    c=r['lang'];t=d['locales'][c]
    if r.get('prompt'):
        p=next(p for p in d['prompts'] if p['id']==r['prompt']);loc=text_for(p,c)
        body=f'<a class="back-link" href="{root}{c}/">{E(t["backLibrary"])}</a><section class="detail-hero"><h1>{E(loc["title"])}</h1><p>{E(loc["description"])}</p></section>'
        body+=f'<details class="usage-panel"><summary>{E(t["usageToggle"])} · {E(t[p["level"]])}</summary>{guide_html(d,c,p["level"])}</details>'
        body+=f'<p><a class="button" href="{root}prompts/{p["id"]}.{c if c in p["locales"] else p["sourceLanguage"]}.md" download>{E(t["download"])}</a></p><section class="reader"><div class="reader-content"><pre class="prompt">{E(loc["body"])}</pre></div></section>'
        if loc.get('starter'):body+=f'<h2>{E(t["starter"])}</h2><pre class="starter-body">{E(loc["starter"])}</pre>'
        if c not in p['locales']:body='<p class="fallback-notice">'+E(t['statusMissing'].replace('{language}',d['locales'][p['sourceLanguage']]['name']))+'</p>'+body
        return body+f'<p>{E(t["evaluationNote"])}</p><p>{E(status_text(d,p,c))}</p>'
    if r['view']=='guide':return f'<h1>{E(t["usageToggle"])}</h1><p>{E(t["scopeNote"])}</p><div class="guide-grid">'+''.join(guide_html(d,c,l['id']) for l in d['levels'])+'</div>'
    body=f'<section class="hero"><h1>{E(t["heroTitle"] if r["level"]=="all" else t[r["level"]])}</h1><p>{E(t["heroDesc"])}</p></section><div class="entries">'
    for p in d['prompts']:
        if r['level'] not in ('all',p['level']):continue
        loc=text_for(p,c)
        body+=f'<a class="entry" href="{root}{route_path(c,p["level"],p["id"])}"><img src="{root}assets/icons/{p["icon"]}.svg" width="48" height="48" alt=""><div><h2>{E(loc["title"])}</h2><p>{E(loc["description"])}</p></div></a>'
    return body+'</div>'

def rendered_html(d:dict,r:dict|None=None,output_path='index.html')->str:
    r=r or {'lang':'en','view':'library','level':'all','prompt':None}
    c=r['lang'];t=d['locales'][c]
    depth=len(Path(output_path).parts)-1;root='../'*depth or './'
    p=next((p for p in d['prompts'] if p['id']==r.get('prompt')),None)
    title=(text_for(p,c)['title']+' · '+d['site']['title']) if p else d['site']['title']+' — '+t['heroTitle']
    desc=text_for(p,c)['description'] if p else t['heroDesc']
    canonical=d['site']['url']+(output_path[:-10] if output_path.endswith('index.html') else '')
    if p and c not in p['locales']:canonical=link(d,p['sourceLanguage'],p['level'],p['id'])
    codes=list(p['locales']) if p else list(d['locales'])
    alternatives=''.join(f'<link rel="alternate" hreflang="{code}" href="{E(link(d,code,r["level"],r.get("prompt"),r["view"]))}">\n' for code in codes)
    alternatives+=f'<link rel="alternate" hreflang="x-default" href="{E(link(d,p["sourceLanguage"] if p else "en",r["level"],r.get("prompt"),r["view"]))}">'
    nav=f'<nav class="static-nav"><a href="{root}{c}/">{E(t["all"])}</a>' + ''.join(f'<a href="{root}{c}/{l["id"]}/">{E(t[l["id"]])}</a>' for l in d['levels'])+f'<a href="{root}{c}/guide/">{E(t["how"])}</a></nav>'
    def jsdata(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    page={'root':root,'route':r,'indexRoot':output_path=='index.html','notFound':output_path=='404.html'}
    tokens={'LANG_LABEL':E(t['language']),'PRIVACY':E(t['privacy']),'GUIDE_LABEL':E(t['usageToggle']),'LICENSE_LABEL':E(t['license']),'SITE_TITLE':E(d['site']['title']),'SITE_URL':E(d['site']['url']),'REPO_URL':E(d['site']['repository']),'PAGE_TITLE':E(title),'DESCRIPTION':E(desc),'CANONICAL':E(canonical),'ALTERNATES':alternatives,'LANG':c,'DIR':t['dir'],'BRAND_SUB':E(t['brandSub']),'ROOT':root,'HOME':root+c+'/','GUIDE':root+c+'/guide/','SKIP':E(t['skip']),'STATIC_NAV':nav,'STATIC_HOME':static_main(d,r,root),'NOJS':E(t['common'])+' <a href="'+E(d['site']['repository'])+'#readme">README</a>','CSS':(ROOT/'templates/styles.css').read_text(encoding='utf-8'),'SYMBOLS':sprite(),'DATA':jsdata(d),'PAGE_DATA':jsdata(page),'APP_JS':(ROOT/'templates/app.js').read_text(encoding='utf-8'),'LANG_OPTIONS':''.join(f'<option value="{c2}" lang="{c2}" dir="{loc["dir"]}" {"selected" if c==c2 else ""}>{E(loc["name"])}</option>' for c2,loc in d['locales'].items())}
    template=(ROOT/'templates/index.html').read_text(encoding='utf-8')
    # Substitute tokens once, preventing prompt text that resembles tokens from being interpreted.
    template=re.sub(r'@@([A-Z_]+)@@',lambda m:tokens[m[1]],template)
    return template

def readme(d:dict)->str:
    L=['<a name="languages"></a>','',f'<img src="assets/icons/handbook.svg" width="48" height="48" alt="{d["site"]["title"]}">','',f'# {d["site"]["title"]}','','**Useful prompts, within reach. / 常用的提示词，随手可用。**','',
    'A multilingual handbook for **personal preferences** and **project workflows**. Browse by scope, combine, and copy.  ', '按**用户级偏好**与**项目级工作流程**整理。选择条目，按需组合，直接复制。','',
    f'**[Open in English]({link(d,"en")}) · [打开中文手册]({link(d,"zh-CN")}) · [How to use / 使用指南]({link(d,"en",view="guide")})**','',
    f'**{len(d["prompts"])} prompts · {len(d["levels"])} scopes · {d["languageCount"]} languages / {len(d["locales"])} locale versions**','',
    '| Scope / 级别 | Entry / 条目 | Use / 用途 |','|---|---|---|']
    for p in d['prompts']:
        a=text_for(p,'en');b=text_for(p,'zh-CN');level=p['level']
        L.append(f'| {d["locales"]["en"][level]} / {d["locales"]["zh-CN"][level]} | [{a["title"]}]({link(d,"en",level,p["id"])}) / [{b["title"]}]({link(d,"zh-CN",level,p["id"])}) | {a["description"]} |')
    L+=['','Choose a language and expand an entry. Copy only its prompt code block; setup guidance and complete texts are available below.  ','选择语言，再展开条目。只复制提示词代码框；README 中保留全部正文和使用说明。','']
    locs=list(d['locales'].items())
    for i in range(0,len(locs),4):L+=[' · '.join(f'[{t["name"]}](#lang-{code.lower()})' for code,t in locs[i:i+4])+'  ']
    L+=['','> Scope describes intended usage, not API roles or elevated permissions. / 分类表示使用范围，不代表 API 角色或更高权限。','']
    for code,t in locs:
        L+=['---','',f'<a name="lang-{code.lower()}"></a>','','<details>',f'<summary><strong>{E(t["name"])}</strong> — {E(t["readmeGuide"])}</summary>','',f'## {t["heroTitle"]}','',f'[{t["library"]}]({link(d,code)})','',t['languageHelp'],'',t['quickText'],'']
        for p in d['prompts']:
            loc=text_for(p,code);level=p['level']
            L+=['<details>',f'<summary><strong>{E(t[level])} · {E(loc["title"])}</strong></summary>','',f'### {loc["title"]}','',loc['description'],'',f'[{t["open"]}]({link(d,code,level,p["id"])}) · `v{p["version"]}`','']
            if code not in p['locales']:L +=[t['statusMissing'].replace('{language}',d['locales'][p['sourceLanguage']]['name']),'']
            L +=[f'**{t["promptTitle"]}**','',fenced(loc['body']),'']
            for other in p.get('recommendedWith',[]):
                q=next(x for x in d['prompts'] if x['id']==other)
                L+=[f'[{t["include"].replace("{title}",text_for(q,code)["title"])}]({link(d,code,level,p["id"],with_ids=[other])})','']
            if loc.get('starter'):L +=[f'**{t["starter"]}**','',t['starterHelp'],'',fenced(loc['starter']),'']
            L +=[f'### {t["usageToggle"]}','',t['hint'] if level=='user' else t['projectNote'],'']
            for sid in d['guides'][level]:
                s=d['services'][sid];L +=[f'**{s["name"]}**','',t['routes'][sid],'',f'[{t["sources"]}]({s["url"]}) · {s["checked"]}','']
            L +=[f'**{t["commonTitle"]}**','',t['common'],'',f'**{t["reviewTitle"]}**','',f'{t["sourceLabel"]}: {d["locales"][p["sourceLanguage"]]["name"]} · {t["versionLabel"]}: {p["version"]} · {t["updatedLabel"]}: {p["updated"]}','',status_text(d,p,code),'',t['evaluationNote'],'','</details>','']
        L +=[t['notes'],'',t['lengthNote'],'',t['quality'],'',f'[{t["library"]} ↑](#languages)','','</details>','']
    L+=['---','','## Contribute / 参与维护','','[Contributing](CONTRIBUTING.md) · [中文维护指南](docs/MAINTAIN.zh-CN.md) · [Deployment / 部署](docs/PUBLISH.zh-CN.md) · [Testing](docs/TESTING.md) · [Evaluation protocol](docs/EVALUATION.md)','',
    'Content lives in `content/library.json` (site, UI, service guides) and `content/prompts/*.json` (one file per prompt). Names are localized; IDs remain stable. The generator creates this complete README, the offline-capable root page, Markdown exports, and indexable static routes.','',
    '```bash','python tools/build.py','python tools/build.py --check','python tools/test_unit.py','```','',
    'The supplied workflow validates and builds, runs browser regression checks, synchronizes generated repository files, then deploys `_site/`. Set GitHub Pages to **GitHub Actions**. Changes made through the GitHub editor can therefore update both the website and README after a successful run. See the deployment guide for permissions and protected-branch alternatives.','',
    'All translations are AI-assisted unless explicitly marked reviewed. No systematic model-effectiveness evaluation is claimed. The browser tests do not constitute native-language review or real-device certification.','',
    '## License / 许可','','MIT — see [LICENSE](LICENSE). The original copyright notice is preserved.','']
    return '\n'.join(L)

class References(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=set();self.canonical=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag in ('a','link','script','img','use'):
            for key in ('href','src'):
                if a.get(key):self.refs.append(a[key])
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a['href']

def site_outputs(d:dict)->dict[str,str|bytes]:
    output={}; routes=[('index.html',{'lang':'en','view':'library','level':'all','prompt':None})]
    for code in d['locales']:
        for level in ['all']+[x['id'] for x in d['levels']]:routes.append((route_path(code,level)+'index.html',{'lang':code,'view':'library','level':level,'prompt':None}))
        routes.append((route_path(code,view='guide')+'index.html',{'lang':code,'view':'guide','level':'all','prompt':None}))
        for p in d['prompts']:
            routes.append((route_path(code,p['level'],p['id'])+'index.html',{'lang':code,'view':'prompt','level':p['level'],'prompt':p['id']}))
    for path,r in routes:output[path]=rendered_html(d,r,path)
    output['404.html']=rendered_html(d,output_path='404.html').replace('<meta name="color-scheme"','<meta name="robots" content="noindex">\n<meta name="color-scheme"',1)
    for p in d['prompts']:
        for code,loc in p['locales'].items():output[f'prompts/{p["id"]}.{code}.md']=loc['body']+'\n'
    urls=[d['site']['url']+path.removesuffix('index.html') for path,r in routes if not r.get('prompt') or r['lang'] in next(p for p in d['prompts'] if p['id']==r['prompt'])['locales']]
    output['sitemap.xml']='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{E(u)}</loc></url>' for u in urls)+'</urlset>\n'
    # A robots.txt under a GitHub project path is not origin-wide. Use a sitemap link in the README/docs instead.
    output['.nojekyll']=''
    for path in ['LICENSE','favicon.svg','favicon.ico','apple-touch-icon.png']:
        output[path]=(ROOT/path).read_bytes()
    for path in (ROOT/'assets').rglob('*'):
        if path.is_file():output[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    return output

def validate_internal_links(d:dict,outputs:dict)->int:
    checks=0;site=d['site']['url'];asset_prefix=urlparse(site).path
    for path,body in outputs.items():
        if not path.endswith('.html'):continue
        parser=References();parser.feed(str(body));base=site+path
        for ref in parser.refs:
            if ref.startswith('#'):
                # Client routes and inlined SVG symbol references.
                if '=' in ref or ref in ('#main',):continue
                require(unquote(ref[1:]) in parser.ids,f'{path}: missing anchor {ref}');checks+=1;continue
            absolute=urljoin(base,ref)
            if not absolute.startswith(site):continue
            target=unquote(urlparse(absolute).path[len(asset_prefix):])
            if target.endswith('/') or not target:target+='index.html'
            require(target in outputs,f'{path}: broken local link {ref} -> {target}');checks+=1
    return checks

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('--repository',default='');args=ap.parse_args()
    try:
        d=load()
        if args.repository:require(d['site']['repository'].removeprefix('https://github.com/').lower()==args.repository.lower(),'Configured repository does not match --repository; edit content/library.json')
        generated={'index.html':rendered_html(d),'README.md':readme(d)}
        paper=next((p for p in d['prompts'] if p['id']=='paper-mentor'),None)
        generated['docs/PAPER-MENTOR.zh-CN.md']=(text_for(paper,'zh-CN')['body']+'\n') if paper else '# This entry is no longer in the library.\n'
        for rel,body in generated.items():
            if args.check:require((ROOT/rel).is_file() and (ROOT/rel).read_text(encoding='utf-8')==body,'Stale generated file: '+rel+'; run python tools/build.py')
            else:(ROOT/rel).write_text(body,encoding='utf-8',newline='\n')
        out=site_outputs(d);checks=validate_internal_links(d,out)
        if not args.check:
            site=ROOT/'_site'
            if site.exists():shutil.rmtree(site)
            for rel,body in out.items():
                f=site/rel;f.parent.mkdir(parents=True,exist_ok=True)
                f.write_bytes(body if isinstance(body,bytes) else body.encode('utf-8'))
        require('AI-direct-first/' not in generated['index.html']+generated['README.md'],'Legacy repository URL leaked into generated files')
        print(f'{"Verified" if args.check else "Built"}: {len(d["prompts"])} prompts, {len(d["locales"])} locales, {sum(k.endswith(".html") for k in out)} HTML pages; {checks} local links checked.')
        return 0
    except (OSError,ValueError,KeyError,TypeError,ET.ParseError) as e:print('Build failed: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
