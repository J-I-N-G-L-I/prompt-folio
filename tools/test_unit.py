#!/usr/bin/env python3
"""Content, generator and extension regression checks. Standard library only."""
import copy,hashlib,json,re,tempfile,unittest,shutil
from pathlib import Path
import build
D=build.load()
class ContentTests(unittest.TestCase):
    def test_brand_and_addresses(self):
        self.assertEqual(D['site']['title'],'Prompt Folio')
        if build.urlparse(D['site']['url']).hostname.endswith('.github.io'):
            self.assertEqual(D['site']['repository'].split('/')[-1],build.urlparse(D['site']['url']).path.strip('/'))
        self.assertNotIn('AI-direct-first/',build.readme(D)+build.rendered_html(D))
    def test_all_prompt_texts_survive(self):
        readme=build.readme(D);exports=build.site_outputs(D)
        for p in D['prompts']:
            for code,l in p['locales'].items():
                if len(l['body'])<=build.README_INLINE_LIMIT:self.assertIn(build.fenced(l['body']),readme)
                else:self.assertIn(f'/prompts/{p["id"]}.{code}.md',readme)
                self.assertEqual(exports[f'prompts/{p["id"]}.{code}.md'],l['body']+'\n')
                self.assertIn(build.E(l['body']),build.static_main(D,{'lang':code,'view':'prompt','level':p['level'],'prompt':p['id']},'./'))
    def test_translations_tied_to_source(self):
        for p in D['prompts']:
            for code,l in p['locales'].items():
                meta=l['translation']
                if code==p['sourceLanguage']:self.assertEqual(meta['effectiveStatus'],'source')
                elif meta['sourceHash']!=p['sourceHash'] or meta['sourceVersion']!=p['version']:self.assertEqual(meta['effectiveStatus'],'stale')
                else:self.assertIn(meta['effectiveStatus'],('ai-assisted','reviewed'))
    def test_source_edit_marks_old_translation_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shutil.copytree(build.ROOT/'content',root/'content')
            shutil.copytree(build.ROOT/'assets/icons',root/'assets/icons')
            p=root/'content/prompts/paper-mentor.json';src=json.loads(p.read_text(encoding='utf-8'))
            src['locales'][src['sourceLanguage']]['body']+='\nA real source change.'
            p.write_text(json.dumps(src,ensure_ascii=False),encoding='utf-8')
            changed=next(x for x in build.load(root)['prompts'] if x['id']==src['id'])
            self.assertEqual(changed['locales']['en']['translation']['effectiveStatus'],'stale')
            self.assertEqual(changed['locales'][src['sourceLanguage']]['translation']['effectiveStatus'],'source')
    def test_localized_names(self):
        p=next(p for p in D['prompts'] if p['id']=='direct-first')
        self.assertEqual(p['locales']['zh-CN']['title'],'先说重点')
        self.assertEqual(p['locales']['zh-TW']['title'],'先說重點')
        for c,l in p['locales'].items():
            if c!='en':self.assertNotEqual(l['title'],'Direct First')
    def test_partial_third_entry(self):
        d=copy.deepcopy(D);p=copy.deepcopy(d['prompts'][0]);p.update(id='third-example',recommendedWith=[])
        p['locales']={p['sourceLanguage']:p['locales'][p['sourceLanguage']]};d['prompts'].append(p)
        out=build.site_outputs(d)
        self.assertIn('en/user/third-example/index.html',out)
        page=out['en/user/third-example/index.html']
        self.assertIn(d['locales']['en']['statusMissing'].split(';')[0],build.html.unescape(page))
        build.validate_internal_links(d,out)
        self.assertIn(f'{len(d["prompts"])} prompts',build.readme(d))
    def test_chat_scope_routes_and_usage(self):
        p=next(p for p in D['prompts'] if p['id']=='dnd-dungeon-master')
        self.assertEqual(p['level'],'chat')
        out=build.site_outputs(D)
        for code,t in D['locales'].items():
            self.assertIn(f'{code}/chat/index.html',out)
            self.assertIn(f'{code}/chat/{p["id"]}/index.html',out)
            guide=build.guide_html(D,code,'chat')
            self.assertIn(build.E(t['chatUse']),guide)
            self.assertNotIn('Project settings',guide)
            self.assertNotIn(t['projectNote'],guide)
    def test_missing_translation_uses_source_language(self):
        d=copy.deepcopy(D)
        p=next(p for p in d['prompts'] if p['id']=='dnd-dungeon-master')
        p['locales']={p['sourceLanguage']:p['locales'][p['sourceLanguage']]}
        route={'lang':'ar','view':'prompt','level':'chat','prompt':p['id']}
        doc=build.rendered_html(d,route,f'ar/chat/{p["id"]}/index.html')
        parser=build.References();parser.feed(doc)
        self.assertEqual(parser.canonical,build.link(d,'zh-CN','chat',p['id']))
        self.assertIn('class="prompt" lang="zh-CN" dir="ltr"',doc)
        self.assertIn(f'prompts/{p["id"]}.zh-CN.md',doc)
        self.assertIn(build.E(build.status_text(d,p,'ar')),doc)
        readme=build.readme(d)
        self.assertIn(f'/prompts/{p["id"]}.zh-CN.md',readme)
        self.assertNotIn(f'/prompts/{p["id"]}.ar.md',readme)
        self.assertIn(f'(#prompt-{p["id"]}-zh-cn)',readme)
    def test_custom_domain_at_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shutil.copytree(build.ROOT/'content',root/'content')
            shutil.copytree(build.ROOT/'assets/icons',root/'assets/icons')
            f=root/'content/library.json';src=json.loads(f.read_text(encoding='utf-8'))
            src['site']['url']='https://prompts.example.com/'
            f.write_text(json.dumps(src,ensure_ascii=False),encoding='utf-8')
            d=build.load(root)
            out=build.site_outputs(d)
            build.validate_internal_links(d,out)
            parser=build.References();parser.feed(out['zh-CN/chat/dnd-dungeon-master/index.html'])
            self.assertEqual(parser.canonical,'https://prompts.example.com/zh-CN/chat/dnd-dungeon-master/')
            self.assertIn('https://prompts.example.com/zh-CN/',build.readme(d))
    def test_service_order_independent(self):
        d=copy.deepcopy(D);d['guides']['user'].reverse()
        html=build.guide_html(d,'zh-CN','user')
        for sid in d['guides']['user']:self.assertIn(build.E(d['locales']['zh-CN']['routes'][sid]),html)
    def test_json_script_safe(self):
        d=copy.deepcopy(D);d['prompts'][0]['locales']['en']['body']='</script><script>alert(1)</script> @@SITE_TITLE@@'
        doc=build.rendered_html(d);embedded=re.search(r'<script id="library-data" type="application/json">(.*?)</script>',doc,re.S)[1]
        self.assertEqual(json.loads(embedded)['prompts'][0]['locales']['en']['body'],d['prompts'][0]['locales']['en']['body'])
        self.assertNotIn('</script>',embedded)
    def test_fences(self):
        self.assertTrue(build.fenced('example ``` code').startswith('````text'))
    def test_root_relative_assets(self):
        p=D['prompts'][0];code='zh-CN';r={'lang':code,'view':'prompt','level':p['level'],'prompt':p['id']}
        doc=build.rendered_html(D,r,build.route_path(code,p['level'],p['id'])+'index.html')
        self.assertIn('href="../../../favicon.svg',doc)
        self.assertIn(f'{code}/{p["level"]}/{p["id"]}/',doc)
    def test_dnd_complete_locale_coverage(self):
        p=next(p for p in D['prompts'] if p['id']=='dnd-dungeon-master')
        self.assertEqual(set(p['locales']),set(D['locales']))
        self.assertEqual(hashlib.sha256(p['locales']['zh-CN']['body'].encode()).hexdigest(),'b1a42f89dd0c81fb0b1b4aae5dbe52320c8d28bf30fa27462fb1fa297e0fd76f')
        for code,loc in p['locales'].items():
            body=loc['body']
            self.assertEqual(re.findall(r'^## (\d+)\.',body,re.M),[str(i) for i in range(11)],code)
            self.assertNotIn('\ufffd',body,code)
            for key in ('schema_version','campaign_id','save_id','state_version','last_event_id','last_roll_id','config','world','scene','characters','inventory','quests','knowledge','npcs_and_relationships','combat','pending_resolution','recent_log','rulings','recovery_limits'):
                self.assertIn(key,body.replace('\\_','_'),code)
            if code!='zh-CN':
                self.assertNotEqual(body,p['locales']['zh-CN']['body'],code)
                self.assertEqual(loc['translation']['effectiveStatus'],'ai-assisted',code)
    def test_readme_within_github_limit(self):self.assertLess(len(build.readme(D).encode()),500*1024)
    def test_current_links(self):self.assertGreater(build.validate_internal_links(D,build.site_outputs(D)),100)
if __name__=='__main__':unittest.main(verbosity=2)
