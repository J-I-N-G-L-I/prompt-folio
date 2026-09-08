#!/usr/bin/env python3
"""Build the deployable HTML and multilingual README from one content source.

Python 3.10+, standard library only. Run from any working directory:
    python tools/build.py
    python tools/build.py --check
No build process is required on GitHub Pages; commit the generated files.
"""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
MINI = {
'grid':'<rect x="4" y="4" width="6" height="6" rx="1.5"/><rect x="14" y="4" width="6" height="6" rx="1.5"/><rect x="4" y="14" width="6" height="6" rx="1.5"/><rect x="14" y="14" width="6" height="6" rx="1.5"/>',
'user':'<path d="M4 7h16M4 17h16"/><rect x="8" y="4" width="4" height="6" rx="2" fill="var(--bg)"/><rect x="14" y="14" width="4" height="6" rx="2" fill="var(--bg)"/>',
'project':'<path d="M3 8V6a2 2 0 0 1 2-2h5l3 3h6a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8ZM3 10h18"/>',
'book':'<path d="M3 5c3-1 6-1 9 1 3-2 6-2 9-1v14c-3-1-6-1-9 1-3-2-6-2-9-1ZM12 6v14"/>',
'copy':'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h3"/>',
'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 16v4h16v-4"/>',
'link':'<path d="m9 15 6-6M8 17l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 7l1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 0) scale(.91 1)"/>',
'external':'<path d="M7 17 18 6M8 6h10v10"/>',
'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
'back':'<path d="M20 12H4m6-6-6 6 6 6"/>',
'search':'<circle cx="10" cy="10" r="6.5"/><path d="m15 15 6 6"/>',
'close':'<path d="m6 6 12 12M6 18 18 6"/>',
'github':'<path d="M8 21v-3c-4 1-4-2-5-2M16 21v-4c0-1-.4-1.6-1-2 3-.3 5-1.5 5-5 0-1.4-.5-2.4-1.5-3.3.1-.8.1-1.6-.3-2.7-1.4 0-2.6.7-3.3 1.3-2-.6-4-.6-6 0C8.2 4.7 7 4 5.6 4c-.4 1.1-.4 1.9-.3 2.7C4.5 7.6 4 8.6 4 10c0 3.5 2 4.7 5 5-.6.4-1 1-1 2"/>'
}

def load() -> dict:
    try:
        data = json.loads((ROOT/'content/library.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Cannot read content/library.json: {exc}') from exc
    if data.get('schemaVersion') != 1:
        raise ValueError('Unsupported schemaVersion')
    locales = data.get('locales', {})
    if not locales or 'en' not in locales or 'zh-CN' not in locales:
        raise ValueError('English and Simplified Chinese source locales are required')
    keys = set(locales['en'])
    for code, loc in locales.items():
        if not re.fullmatch(r'[a-z]{2}(?:-[A-Za-z]{2,4})?',code):
            raise ValueError(f'Invalid locale code: {code}')
        if set(loc) != keys:
            raise ValueError(f'{code}: inconsistent UI keys: {set(loc)^keys}')
        if loc['dir'] not in ('ltr','rtl'):
            raise ValueError(f'{code}: invalid direction')
        for key, value in loc.items():
            if not value or not isinstance(value,(str,list)):
                raise ValueError(f'{code}.{key}: empty or invalid value')
        for level in ('user','project'):
            if len(loc[level+'Routes'])!=len(data['guides'][level]):
                raise ValueError(f'{code}.{level}: guide count mismatch')
    levels = {v['id'] for v in data['levels']}
    ids = set()
    for prompt in data['prompts']:
        if not re.fullmatch('[a-z0-9-]+',prompt['id']) or prompt['id'] in ids:
            raise ValueError(f'Invalid or duplicate prompt id: {prompt["id"]}')
        ids.add(prompt['id'])
        if prompt['level'] not in levels or set(prompt['locales'])!=set(locales):
            raise ValueError(f'{prompt["id"]}: missing level or translations')
        for code, loc in prompt['locales'].items():
            if not {'title','description','body'} <= set(loc) or set(loc)-{'title','description','body','starter','starterTitle'} or any(not isinstance(x,str) or not x.strip() for x in loc.values()):
                raise ValueError(f'{prompt["id"]}/{code}: invalid text')
            if '```' in loc['body']:
                raise ValueError('Prompt bodies currently use plain text. Escape Markdown fences before adding fenced examples.')
        if not (ROOT/'assets/icons'/f'{prompt["icon"]}.svg').is_file():
            raise ValueError(f'{prompt["id"]}: missing SVG')
    if 'direct-first' not in ids:
        raise ValueError('direct-first is required by the optional project composer and legacy links')
    for url in [data['site']['url'],data['site']['repository']]+[s['url'] for guides in data['guides'].values() for s in guides]:
        if urlparse(url).scheme!='https':
            raise ValueError(f'Expected an HTTPS URL: {url}')
    if not data['site']['url'].endswith('/'):
        raise ValueError('site.url must end with /')
    return data

def sprite() -> str:
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true" focusable="false"><defs>']
    for file in sorted((ROOT/'assets/icons').glob('*.svg')):
        inner=re.sub(r'^.*?<svg\b[^>]*>','',file.read_text(encoding='utf-8'),count=1,flags=re.S)
        inner=re.sub(r'</svg>\s*$','',inner)
        pieces.append(f'<symbol id="tile-{file.stem}" viewBox="0 0 64 64" fill="none">{inner}</symbol>')
    for name,inner in MINI.items():
        pieces.append(f'<symbol id="i-{name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{inner}</symbol>')
    return ''.join(pieces)+'</defs></svg>'

def rendered_html(data:dict) -> str:
    template=(ROOT/'templates/index.html').read_text(encoding='utf-8')
    # Escape '<' so editable prompt text cannot terminate this JSON script element.
    embedded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    options=''.join(f'<option value="{html.escape(code)}" lang="{html.escape(code)}" dir="{loc["dir"]}">{html.escape(loc["name"])}</option>' for code,loc in data['locales'].items())
    static=f'<section class="hero"><p class="eyebrow">{html.escape(data["site"]["title"])}</p><h1>Useful prompts, within reach.</h1><p>A multilingual handbook of user-level preferences and project-level workflows.</p></section>'
    for prompt in data['prompts']:
        static+=f'<h2>{html.escape(prompt["locales"]["en"]["title"])}</h2><p>{html.escape(prompt["locales"]["en"]["description"])}</p>'
    static+=f'<p><a href="{html.escape(data["site"]["repository"])}#readme">Read the full handbook / 阅读完整手册</a></p>'
    substitutions={'@@SITE_TITLE@@':html.escape(data['site']['title'],quote=True),'@@SITE_URL@@':html.escape(data['site']['url'],quote=True),'@@REPO_URL@@':html.escape(data['site']['repository'],quote=True),'@@SYMBOLS@@':sprite(),'@@LANG_OPTIONS@@':options,'@@STATIC_HOME@@':static,'@@DATA@@':embedded,'@@APP_JS@@':(ROOT/'templates/app.js').read_text(encoding='utf-8')}
    for token,value in substitutions.items():template=template.replace(token,value)
    if re.search(r'@@[A-Z_]+@@',template):raise ValueError('Unresolved template placeholder')
    return template

def site_link(data:dict,code:str,**kwargs) -> str:
    return data['site']['url']+'#'+urlencode({**kwargs,'lang':code})

def scope_entries(data:dict,level:str) -> str:
    return ' · '.join(f'[{p["locales"]["zh-CN"]["title"]}]({site_link(data,"zh-CN",prompt=p["id"])})' for p in data['prompts'] if p['level']==level)

def readme(data:dict) -> str:
    lines=['<a name="languages"></a>','', '<img src="assets/icons/handbook.svg" width="56" height="56" alt="Prompt Handbook">','', f'# {data["site"]["title"]}', '', '**Useful prompts, within reach. / 常用的提示词，随手可用。**','',
        'A multilingual handbook of **user-level preferences** and **project-level workflows**. Direct First is now the first entry in this collection.  ',
        '按**用户级**与**项目级**整理的多语言 Prompt 手册。Direct First 作为第一条用户级提示词保留。','',
        f'**[Open the handbook / 打开交互手册]({data["site"]["url"]}#view=library)** · [中文部署与维护](docs/PUBLISH.zh-CN.md) · [Content & UI source](content/library.json)','',
        f'**{len(data["prompts"])} prompts · {len(data["levels"])} scopes · 15 languages / 16 locale versions**  ',
        f'**当前 {len(data["prompts"])} 条提示词均提供完整的 {len(data["locales"])} 个语言版本。** 复制一种语言即可；Paper Mentor 跟随用户明确指定的回复语言，未指定时跟随对话。','',
        '| Scope / 级别 | Intended use / 用途 | Entry / 条目 |','|---|---|---|',
        f'| <img src="assets/icons/user.svg" width="28" alt=""> User-level / 用户级 | Personal defaults across conversations / 长期沟通偏好 | {scope_entries(data,"user")} |',
        f'| <img src="assets/icons/project.svg" width="28" alt=""> Project-level / 项目级 | A focused topic or workflow / 专用主题与流程 | {scope_entries(data,"project")} |','',
        'Choose your language, expand its section, and then open an entry. Copy **only the prompt code block**. Full prompts and setup guidance are available here without visiting the website.  ',
        '点击下方语言，展开该语言，再选择条目。只复制提示词代码框中的内容；无需进入网页也能取得完整提示词与使用说明。','']
    all_locales=list(data['locales'].items())
    for i in range(0,len(all_locales),4):lines.append(' · '.join(f'[{loc["name"]}](#lang-{code.lower()})' for code,loc in all_locales[i:i+4])+'  ')
    lines+=['','> Scope labels describe intended usage, not API message roles. Projects may require preferences to be included explicitly; see official guides below.  ','> 分类表示使用范围，不等同于 API 系统角色。项目中需要保留的用户偏好可明确附加；网页支持可选组合复制。','', '---','']
    for code,t in all_locales:
        lines += [f'<a name="lang-{code.lower()}"></a>', '', '<details>',f'<summary><strong>{t["name"]}</strong> — {html.escape(t["readmeGuide"])}</summary>','',f'## {t["heroTitle"]}', '',t['heroDesc'],'',f'[{t["library"]} ↗]({site_link(data,code,view="library")})','',t['quickText'],'',t['scopeNote'],'']
        for prompt in data['prompts']:
            loc=prompt['locales'][code];level=prompt['level']
            lines+=['<details>',f'<summary><strong>{html.escape(t[level])} · {html.escape(loc["title"])}</strong></summary>','',f'### {loc["title"]}','',loc['description'],'',f'[{t["open"]} ↗]({site_link(data,code,prompt=prompt["id"])}) · `v{prompt["version"]}`','',f'**{t["promptTitle"]}**','','```text',loc['body'],'```','']
            if level=='project':
                lines += [t['projectNote'],'',f'[{t["attach"]} ↗]({site_link(data,code,prompt=prompt["id"],**{"with":"direct-first"})})','']
                if loc.get('starter'):
                    lines += [f'**{loc.get("starterTitle",t["commonTitle"])}**','','```text',loc['starter'],'```','']
            else:lines += [t['hint'],'']
            lines += [f'### {t["how"]}','',t['intro'] if level=='user' else t['projectDesc'],'']
            for i,source in enumerate(data['guides'][level]):
                lines += [f'**{source["name"]}**', '', t[level+'Routes'][i], '', f'[{t["sources"]}]({source["url"]})','']
            lines += [f'**{t["commonTitle"]}**','',t['common'],'','Grok · DeepSeek · Qwen · Kimi · Doubao','', '</details>', '']
        lines += [f'### {t["notesTitle"]}','',t['notes'],'',t['lengthNote'],'',t['quality'],'',t['checked'],'',f'[{t["library"]} ↑](#languages)','', '</details>', '', '---','']
    lines += ['## Maintainers / 维护者', '',
        'The website and this README are generated from **one content source**: `content/library.json`. The deployable `index.html` is self-contained; it does not fetch JSON or load third-party scripts at runtime. All translations are AI-assisted and have not been independently reviewed by native speakers. Browser checks validate the site, not prompt effectiveness.', '',
        '网站与 README 从同一个内容源生成，避免不同入口的提示词版本不一致。直接上传已经生成的文件即可部署。编辑内容后运行：','',
        '```bash','python tools/build.py','python tools/build.py --check','```','',
        'See [deployment and migration](docs/PUBLISH.zh-CN.md), [content maintenance](docs/MAINTAIN.zh-CN.md), [design system](docs/DESIGN.md), and [verification scope](docs/TESTING.md).','',
        'Legacy `#lang=zh-CN` links open Direct First. New library links explicitly use `#view=library&lang=zh-CN`. The existing repository name and GitHub Pages URL can remain unchanged.','',
        '## License / 许可','', 'MIT — see [LICENSE](LICENSE). The original copyright notice has been preserved.','']
    return '\n'.join(lines)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Validate source and fail if generated files are stale; write nothing')
    args=parser.parse_args()
    try:
        data=load()
        paper=next(p for p in data['prompts'] if p['id']=='paper-mentor')
        outputs={ROOT/'index.html':rendered_html(data),ROOT/'README.md':readme(data),ROOT/'docs/PAPER-MENTOR.zh-CN.md':paper['locales']['zh-CN']['body']+'\n'}
        stale=[]
        for path,text in outputs.items():
            if args.check:
                if not path.is_file() or path.read_text(encoding='utf-8')!=text:stale.append(str(path.relative_to(ROOT)))
            else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
        if stale:print('Generated files are stale: '+', '.join(stale),file=sys.stderr);return 1
        print(f'{"Verified" if args.check else "Built"}: {len(data["prompts"])} prompts × {len(data["locales"])} locales; HTML, README, Chinese prompt export.')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(f'Build failed: {exc}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
