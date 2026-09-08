#!/usr/bin/env python3
"""Stamp translations AFTER updating them. This tool does not translate or review text.
Example: python tools/translation.py paper-mentor --locales en,fr
Human review: add --status reviewed --reviewer 'Public name' --date YYYY-MM-DD
"""
import argparse,hashlib,json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('prompt');p.add_argument('--locales',required=True);p.add_argument('--status',choices=['ai-assisted','reviewed'],default='ai-assisted');p.add_argument('--reviewer');p.add_argument('--date',default=datetime.date.today().isoformat());a=p.parse_args()
 f=ROOT/'content/prompts'/f'{a.prompt}.json'
 if f.resolve().parent!=(ROOT/'content/prompts').resolve():p.error('Invalid prompt ID')
 data=json.loads(f.read_text(encoding='utf-8'));source=data['sourceLanguage'];codes=a.locales.split(',')
 if any(c not in data['locales'] for c in codes):p.error('Add the actual translated text before stamping it')
 if a.status=='reviewed' and not a.reviewer:p.error('--reviewer is required; only use after actual human review')
 datetime.date.fromisoformat(a.date)
 digest=hashlib.sha256(data['locales'][source]['body'].encode()).hexdigest()
 data['sourceHash']=digest;data['updated']=a.date
 for c in [source]+codes:
  meta={'status':'source' if c==source else a.status,'sourceVersion':data['version'],'sourceHash':digest}
  if c!=source and a.status=='reviewed':meta.update(reviewer=a.reviewer,reviewedAt=a.date)
  data['locales'][c]['translation']=meta
 f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Stamped: '+', '.join(codes)+'. This records your revision declaration; it does not independently verify translation quality.')
if __name__=='__main__':main()
