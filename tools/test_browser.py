#!/usr/bin/env python3
"""Data-driven browser tests. Default: real local HTTP server. --memory: restricted sandboxes.
Clipboard checks use a deterministic mock plus denial/race tests. In HTTP mode,
a separate real Clipboard API round-trip is also tested in a permission-granted
headless browser. This is not a real-device or hosted Pages certification.
"""
from __future__ import annotations
import argparse,json,re,shutil,threading,sys
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright
import build
ROOT=build.ROOT;D=build.load()
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--memory',action='store_true');ap.add_argument('--browser');ap.add_argument('--report',type=Path,default=ROOT/'.test-output/browser.json');ap.add_argument('--screenshots',type=Path);args=ap.parse_args()
    report={'mode':'in-memory Chromium' if args.memory else 'local HTTP Chromium','locales':len(D['locales']),'prompts':len(D['prompts']),'viewport_checks':0,'copy_checks':0,'download_checks':0,'nojs_checks':0,'checks':[],'errors':[],
        'limitations':['Hosted GitHub Pages and GitHub README rendering are not tested','Physical devices and screen readers are not certified','Translations have not received independent native-speaker review','AI prompt effectiveness is not measured']}
    if args.memory:report['limitations']+=['Local HTTP navigation is blocked by this environment; in-memory mode used','OS clipboard and storage adapters are simulated']
    class Handler(Quiet):
        # Serve under the SAME project-prefix layout as Pages, rather than testing only /.
        def translate_path(self,path):
            path=unquote(urlparse(path).path);prefix=urlparse(D['site']['url']).path
            if path.startswith(prefix):path=path[len(prefix):]
            p=(ROOT/'_site'/path.lstrip('/')).resolve()
            if not p.is_relative_to((ROOT/'_site').resolve()):return str(ROOT/'_site/404.html')
            return str(p)
    server=None
    if not args.memory:
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        origin=f'http://127.0.0.1:{server.server_port}';base=origin+urlparse(D['site']['url']).path
    else:base=D['site']['url']
    try:
      with sync_playwright() as pw:
        launch={'headless':True,'args':['--no-sandbox']}
        if args.browser:launch['executable_path']=args.browser
        browser=pw.chromium.launch(**launch);context=browser.new_context(viewport={'width':1440,'height':960},accept_downloads=True)
        def mount(code='en',p=None,level='all',view='library',hash_route=None):
            r={'lang':code,'level':p['level'] if p else level,'view':'prompt' if p else view,'prompt':p['id'] if p else None}
            path=build.route_path(code,r['level'],r['prompt'],r['view'])+'index.html'
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            if args.memory:
                page.goto('about:blank'+('#'+hash_route if hash_route else ''))
                page.evaluate("() => {window.__store={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>window.__store[k]||null,setItem:(k,v)=>window.__store[k]=v},configurable:true})}")
                page.set_content((ROOT/'_site'/path).read_text(encoding='utf-8'),wait_until='domcontentloaded',timeout=15000)
            else:
                response=page.goto(base+(('#'+hash_route) if hash_route else path.removesuffix('index.html')));assert response.status==200
            page.wait_for_selector('#language');page.add_style_tag(content='html{scroll-behavior:auto!important}')
            return page
        def layouts(page,label):
            for w in (1440,820,390,320):
                page.set_viewport_size({'width':w,'height':960})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'Overflow {label} @ {w}'
                ids=page.locator('[id]').evaluate_all('(es)=>es.map(e=>e.id)');assert len(ids)==len(set(ids)),label
                report['viewport_checks']+=1
        def mock(page):page.evaluate("() => {window.__clipboard=null;Object.defineProperty(window,'isSecureContext',{value:true,configurable:true});Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.__clipboard=text}},configurable:true})}")
        def copy(page,text,selector):
            page.locator(selector).dispatch_event('click');page.wait_for_function('s=>window.__clipboard===s',arg=text);report['copy_checks']+=1
        for code,tr in D['locales'].items():
            print('Checking',code,flush=True)
            for level in ['all']+[l['id'] for l in D['levels']]:
                page=mount(code,level=level);assert page.locator('.entry').count()==sum(level in ('all',p['level']) for p in D['prompts']);layouts(page,code+'/'+level);page.close()
            for p in D['prompts']:
                page=mount(code,p);loc=build.text_for(p,code)
                assert page.locator('h1').inner_text()==loc['title'];assert page.locator('#prompt-text').text_content()==loc['body']
                content_lang=code if code in p['locales'] else p['sourceLanguage']
                assert page.locator('#prompt-text').get_attribute('lang')==content_lang
                assert page.locator('#prompt-text').get_attribute('dir')==D['locales'][content_lang]['dir']
                if code not in p['locales']:
                    assert page.locator('.fallback-notice').is_visible()
                    assert page.locator('#canonical').get_attribute('href')==build.link(D,content_lang,p['level'],p['id'])
                else:
                    assert page.locator('.fallback-notice').count()==0
                    assert page.locator('#canonical').get_attribute('href')==build.link(D,code,p['level'],p['id'])
                layouts(page,code+'/'+p['id']);mock(page);copy(page,loc['body'],'#copy-prompt')
                page.locator('#usage-panel>summary').click();assert page.locator('.usage-grid').is_visible()
                if loc.get('starter'):copy(page,loc['starter'],'#copy-starter')
                for qid in p.get('recommendedWith',[]):page.locator(f'.combine-toggle[value="{qid}"]').check()
                if p.get('recommendedWith'):
                    actual=page.locator('#prompt-text').text_content();assert actual.endswith(loc['body']);
                    for qid in p['recommendedWith']:
                        q=next(x for x in D['prompts'] if x['id']==qid);assert build.text_for(q,code)['body'] in actual
                    copy(page,actual,'#copy-prompt')
                with page.expect_download(timeout=10000) as di:page.locator('#download').click()
                down=di.value;assert Path(down.path()).read_text(encoding='utf-8')==page.locator('#prompt-text').text_content()+'\n'
                assert down.suggested_filename.endswith('.'+content_lang+'.md');report['download_checks']+=1
                page.locator('#share').dispatch_event('click');page.wait_for_timeout(20);shared=page.evaluate('window.__clipboard')
                assert p['id'] in shared and code in shared and 'AI-direct-first/' not in shared
                if not args.memory:assert urlparse(shared).netloc==urlparse(base).netloc
                page.close()
            page=mount(code,view='guide');layouts(page,code+'/guide');assert page.locator('.service').count()==sum(len(v) for v in D['guides'].values())+len(D['levels']);page.close()
        report['checks']+=['all available titles and bodies','all scopes','composition and localized names','browser-generated Markdown bytes','configured offline share URLs' if args.memory else 'same-origin share URLs','no horizontal overflow at four widths']
        print('Checking search, routes and clipboard edge cases',flush=True)
        # Cross-language search, history, clear-on-language-change, and label-only legacy links.
        page=mount('zh-CN');page.fill('#search','Paper Mentor');assert page.locator('.entry').count()==1
        page.fill('#search','文献');assert page.locator('.entry').count()==1
        page.fill('#search','unlikely-search-no-match');assert page.locator('.entry').count()==0
        page.select_option('#language','en');assert page.locator('#search').input_value()=='';assert page.locator('.entry').count()==len(D['prompts'])
        page.fill('#search','paper mentor');page.locator('.entry').first.click();page.wait_for_selector('#prompt-text');page.locator('.back-link').click();page.wait_for_selector('.entry');assert page.locator('.entry').count()==len(D['prompts']);page.close()
        page=mount('zh-CN');page.fill('#search','DND');assert page.locator('.entry').count()==1
        page.locator('.entry').click();page.wait_for_selector('#prompt-text')
        assert page.locator('#prompt-text').text_content()==next(p for p in D['prompts'] if p['id']=='dnd-dungeon-master')['locales']['zh-CN']['body']
        page.locator('#sidebar .nav-link').filter(has_text=D['locales']['zh-CN']['chat']).click()
        assert page.locator('.entry').count()==1;assert page.locator('h1').inner_text()==D['locales']['zh-CN']['chat'];page.close()
        dnd=next(p for p in D['prompts'] if p['id']=='dnd-dungeon-master')
        page=mount('zh-CN',dnd)
        for code in D['locales']:
            page.select_option('#language',code)
            assert page.locator('#prompt-text').text_content()==dnd['locales'][code]['body']
            assert page.locator('#prompt-text').get_attribute('lang')==code
            assert page.locator('.fallback-notice').count()==0
            assert page.locator('#canonical').get_attribute('href')==build.link(D,code,'chat',dnd['id'])
        page.close()
        report['checks']+=['DND search and chat-scope navigation','DND language switching across all 16 full translations','localized content, canonical URLs and download filenames']
        for code in ('en','zh-CN','ar'):
            page=mount(hash_route='lang='+code);assert page.locator('html').get_attribute('lang')==code;assert page.locator('.entry').count()==len(D['prompts']);page.close()
        page=mount('en',hash_route='prompt=paper-mentor&lang=zh-CN&with=direct-first');assert page.locator('.combine-toggle').first.is_checked();page.close()
        report['checks']+=['cross-language aliases','clear search on language change','back returns full handbook','legacy hash prompt links and language-only home links']
        # Denied clipboard produces exact, selected, visible fallback.
        p=D['prompts'][0];page=mount('en',p);mock(page);page.evaluate("() => { navigator.clipboard.writeText=async()=>{throw Error('denied')};document.execCommand=()=>false; }")
        page.locator('#copy-prompt').click();page.wait_for_selector('.copy-fallback textarea');assert page.locator('.copy-fallback textarea').input_value()==build.text_for(p,'en')['body'];page.close()
        page=mount('en',p);mock(page);page.evaluate('() => { navigator.clipboard.writeText=()=>new Promise(r=>window.__resolve=r); }');page.locator('#copy-prompt').click();page.select_option('#language','zh-CN');page.evaluate('window.__resolve()');page.wait_for_timeout(30);assert page.locator('#toast').is_hidden();page.close()
        report['checks']+=['clipboard denial fallback','asynchronous clipboard race']
        if not args.memory:
            context.grant_permissions(['clipboard-read','clipboard-write'],origin=origin)
            page=mount('en',D['prompts'][0]);page.locator('#copy-prompt').click();page.wait_for_timeout(100)
            # Windows exposes native CRLF line endings through the Clipboard API.
            copied=page.evaluate('navigator.clipboard.readText()').replace('\r\n','\n')
            assert copied==build.text_for(D['prompts'][0],'en')['body'];page.close()
            report['checks']+=['actual Clipboard API round-trip in headless Chromium (native CRLF normalized)']
            page=mount('zh-CN',D['prompts'][1]);page.reload();page.wait_for_selector('#prompt-text');assert page.locator('h1').inner_text()==build.text_for(D['prompts'][1],'zh-CN')['title'];page.close()
            report['checks']+=['real static deep-link HTTP reload']
        print('Checking dark mode and keyboard navigation',flush=True)
        # Generated HTML remains useful without JavaScript; no copy/composer claims.
        nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
        for code in D['locales']:
            for prompt in D['prompts'] if code in ('en','zh-CN','ar') else [dnd]:
                print('No-JS',code,prompt['id'],flush=True)
                pg=nojs.new_page();rp=build.route_path(code,prompt['level'],prompt['id'])+'index.html'
                if args.memory:pg.set_content((ROOT/'_site'/rp).read_text(encoding='utf-8'),wait_until='domcontentloaded',timeout=15000)
                else:assert pg.goto(base+rp.removesuffix('index.html')).status==200
                assert pg.locator('h1').inner_text()==build.text_for(prompt,code)['title']
                assert pg.locator('pre.prompt').text_content()==build.text_for(prompt,code)['body']
                content_lang=code if code in prompt['locales'] else prompt['sourceLanguage']
                assert pg.locator('pre.prompt').get_attribute('lang')==content_lang
                assert pg.locator('pre.prompt').get_attribute('dir')==D['locales'][content_lang]['dir']
                assert pg.locator('a[download]').get_attribute('href').endswith(f'{prompt["id"]}.{content_lang}.md')
                report['nojs_checks']+=1
                layouts(pg,'no-JS/'+code+'/'+prompt['id']);pg.close()
        nojs.close();report['checks']+=[f'{report["nojs_checks"]} JavaScript-disabled static documents']
        print('Checking final dark-mode and skip-link cases',flush=True)
        # Dark mode and keyboard-only access.
        page=mount('ar',D['prompts'][1]);page.emulate_media(color_scheme='dark');layouts(page,'dark-ar');page.close()
        page=mount('en');page.keyboard.press('Tab');assert page.locator('#skip').evaluate('(e)=>e===document.activeElement');page.keyboard.press('Enter');assert page.locator('#main').evaluate('(e)=>e===document.activeElement');page.close()
        report['checks']+=['dark RTL','keyboard skip link']
        if args.screenshots:
            args.screenshots.mkdir(parents=True,exist_ok=True)
            dnd=next(p for p in D['prompts'] if p['id']=='dnd-dungeon-master')
            for name,code,p,width in [('home-zh-desktop','zh-CN',None,1440),('home-zh-tablet','zh-CN',None,1024),('home-zh-mobile','zh-CN',None,390),('home-en-mobile','en',None,390),('paper-zh-desktop','zh-CN',D['prompts'][1],1440),('paper-zh-mobile','zh-CN',D['prompts'][1],390),('direct-zh-mobile','zh-CN',D['prompts'][0],390),('dnd-zh-desktop','zh-CN',dnd,1440),('dnd-zh-mobile','zh-CN',dnd,390),('dnd-ar-mobile','ar',dnd,390),('dnd-en-mobile','en',dnd,390),('dnd-ja-mobile','ja',dnd,390),('dnd-hi-mobile','hi',dnd,390)]:
                pg=mount(code,p);pg.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});pg.screenshot(path=str(args.screenshots/(name+'.png')));pg.close()
        browser.close()
      assert not report['errors'],report['errors'];report['status']='passed'
    except Exception as e:
        report['status']='failed';report['errors'].append(str(e));raise
    finally:
        if server:server.shutdown()
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
