#!/usr/bin/env python3
"""Optional Chromium checks. Requires playwright and a Chromium executable.

Loads the self-contained HTML into an in-memory browser document. Clipboard API
and storage adapters are simulated: these tests do NOT validate OS clipboard,
real GitHub Pages deployment, network resource loading, or AI prompt effectiveness.

Example: python tools/test_browser.py --browser /usr/bin/chromium --report report.json
"""
from __future__ import annotations
import argparse,json,re,shutil,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'content/library.json').read_text(encoding='utf-8'))
HTML=(ROOT/'index.html').read_text(encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',default=shutil.which('chromium'))
    parser.add_argument('--report',type=Path,default=None)
    parser.add_argument('--locales',help='Comma-separated locale subset for a quick development check')
    args=parser.parse_args()
    selected=[code for code in D['locales'] if not args.locales or code in args.locales.split(',')]
    results={'mode':'in-memory HTML / Chromium','locales':len(selected),'prompts':len(D['prompts']),'viewport_checks':0,'copy_checks':0,'errors':[],
             'limitations':['No real GitHub rendering or Pages deployment tested','Clipboard and storage adapters are simulated','HTTP/file resource loading is not validated by in-memory tests','Prompt effectiveness and native-language translation review are outside these tests']}
    with sync_playwright() as pw:
        launch={'headless':True,'args':['--no-sandbox']}
        if args.browser:launch['executable_path']=args.browser
        browser=pw.chromium.launch(**launch)
        context=browser.new_context(viewport={'width':1440,'height':960},accept_downloads=True)
        def mount(route,storage=None):
            p=context.new_page();p.on('pageerror',lambda err:results['errors'].append(str(err)))
            p.goto('about:blank#'+route)
            if storage is not None:p.evaluate('''value => {window.__store=value;Object.defineProperty(window,'localStorage',{value:{getItem:k=>window.__store[k]||null,setItem:(k,v)=>{window.__store[k]=v}},configurable:true})}''',storage)
            p.set_content(HTML);p.wait_for_selector('#language');p.add_style_tag(content='html{scroll-behavior:auto!important}')
            return p
        def go(p,route,body=None):
            p.evaluate('h=>{location.hash=h}',route)
            if body is not None:p.wait_for_function('text=>document.getElementById("prompt-text")?.textContent===text',arg=body)
            else:p.wait_for_timeout(35)
        def overflow(p,label):
            for width in (1440,390,320):
                p.set_viewport_size({'width':width,'height':960})
                assert not p.evaluate('document.documentElement.scrollWidth > innerWidth+1'),f'Horizontal overflow: {label}, {width}px'
                ids=p.locator('[id]').evaluate_all('(els)=>els.map(e=>e.id)')
                assert len(ids)==len(set(ids)),f'Duplicate DOM IDs: {label}'
                results['viewport_checks']+=1
        def mock_clipboard(p):
            p.evaluate('''() => {window.__clipboard=null;Object.defineProperty(window,'isSecureContext',{value:true,configurable:true});Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.__clipboard=text}},configurable:true})}''')
        def copied(p,text,selector='#copy-prompt'):
            p.locator(selector).dispatch_event('click');p.wait_for_function('s=>window.__clipboard===s',arg=text);results['copy_checks']+=1
        for code,t in D['locales'].items():
            if args.locales and code not in args.locales.split(','):continue
            print('Checking',code,flush=True)
            p=mount('view=library&lang='+code)
            assert p.locator('.entry').count()==2,code
            assert p.locator('html').get_attribute('dir')==t['dir'],code
            overflow(p,code+'/library');mock_clipboard(p)
            for prompt in D['prompts']:
                loc=prompt['locales'][code]
                go(p,f'prompt={prompt["id"]}&lang={code}',loc['body'])
                assert p.locator('h1').inner_text()==loc['title']
                overflow(p,code+'/'+prompt['id']);copied(p,loc['body'])
                if prompt['level']=='project':
                    p.check('#combine');text=p.locator('#prompt-text').inner_text()
                    assert text.count(D['prompts'][0]['locales'][code]['body'])==1
                    assert text.count(loc['body'])==1
                    copied(p,text);copied(p,loc['starter'],'#copy-starter')
                    copied(p,D['site']['url']+f'#prompt=paper-mentor&with=direct-first&lang={code}','#share')
                    assert p.locator('#character-count').inner_text().endswith(t['characters'])
            go(p,'view=guide&lang='+code);p.wait_for_selector('.guide-grid');overflow(p,code+'/guide')
            assert p.locator('.guide-grid .service').count()==11
            p.close()
        # Search, scoped navigation, language preservation, and old links.
        print('Checking navigation',flush=True)
        p=mount('view=library&lang=zh-CN',{})
        p.fill('#search','unlikely_search_0');assert p.locator('.entry').count()==0
        p.click('#clear-search');assert p.locator('.entry').count()==2
        p.fill('#search','同义词');assert p.locator('.entry').count()==1
        p.click('#clear-search');p.locator('.scope-card').first.click()
        assert p.locator('.entry').count()==1 and p.locator('.categories').count()==0
        p.locator('.entry').first.click();assert p.locator('h1').inner_text()=='Direct First'
        p.evaluate('history.back()');p.wait_for_selector('.entry');assert p.locator('.entry').count()==1
        p.select_option('#language','az');assert p.locator('html').get_attribute('lang')=='az'
        assert p.evaluate('window.__store["prompt-handbook-language"]')=='az'
        p.close();results['navigation_search_persistence']='passed (storage adapter simulated)'
        for route,expected in [('lang=zh-CN','zh-CN'),('lang=en','en'),('lang=zh-HK','zh-TW')]:
            p=mount(route);assert p.locator('#prompt-text').inner_text()==D['prompts'][0]['locales'][expected]['body'];p.close()
        p=mount('',{'direct-first-language':'zh-CN'});assert p.locator('html').get_attribute('lang')=='zh-CN';assert p.locator('.entry').count()==2;p.close()
        p=mount('view=library&lang=en',{'prompt-handbook-language':'ar'});assert p.locator('html').get_attribute('lang')=='en';p.close()
        p=mount('prompt=unknown&lang=en');assert p.locator('.entry').count()==2;p.close();results['routing_legacy_links']='passed'
        print('Checking downloads',flush=True)
        # Check real browser-generated downloadable bytes (no mocked download function).
        for code,combine in [('en',False),('zh-CN',True)]:
            p=mount('prompt=paper-mentor&lang='+code+('&with=direct-first' if combine else ''))
            body=p.locator('#prompt-text').inner_text()
            with p.expect_download(timeout=5000) as download_info:p.click('#download')
            download=download_info.value
            assert Path(download.path()).read_text(encoding='utf-8')==body+'\n'
            assert download.suggested_filename.endswith('.'+code+'.md');p.close()
        results['markdown_downloads']='passed (browser-generated Blob downloads)'
        print('Checking denial and race',flush=True)
        # Clipboard denial selects a visible manual fallback with the actual full text.
        p=mount('prompt=direct-first&lang=en');mock_clipboard(p)
        p.evaluate("navigator.clipboard.writeText=async()=>{throw Error('denied')};document.execCommand=()=>false")
        p.click('#copy-prompt');p.wait_for_selector('.copy-fallback textarea')
        assert p.input_value('.copy-fallback textarea')==D['prompts'][0]['locales']['en']['body']
        p.close();results['clipboard_denial']='passed (simulated denial)'
        # A late permission result must not announce a different language as copied.
        p=mount('prompt=direct-first&lang=en');mock_clipboard(p)
        p.evaluate('() => {navigator.clipboard.writeText=text=>new Promise(resolve=>{window.__resolve=resolve});}')
        p.click('#copy-prompt');p.select_option('#language','zh-CN');p.evaluate('window.__resolve()')
        p.wait_for_timeout(30);assert p.locator('#toast').is_hidden();p.close();results['clipboard_race']='passed'
        print('Checking dark theme',flush=True)
        # Dark theme and RTL variants; both the page and native controls stay within viewport.
        dark=browser.new_context(color_scheme='dark',viewport={'width':390,'height':844})
        p=dark.new_page();p.goto('about:blank#prompt=paper-mentor&lang=ar');p.set_content(HTML)
        assert p.locator('html').get_attribute('dir')=='rtl'
        assert not p.evaluate('document.documentElement.scrollWidth > innerWidth+1')
        results['dark_rtl']='passed';dark.close()
        context.close();browser.close()
    assert not results['errors'],results['errors']
    for prompt in D['prompts']:
        for loc in prompt['locales'].values():assert (ROOT/'README.md').read_text(encoding='utf-8').count(loc['body'])==1
    results['readme_sync']='all 32 prompt bodies present exactly once'
    results['status']='passed'
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
