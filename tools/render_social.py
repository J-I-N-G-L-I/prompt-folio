#!/usr/bin/env python3
"""Optional refresh of editorial preview assets: pip install cairosvg.
Fonts are resolved from the local system; no font files are redistributed.
"""
from pathlib import Path
import html,json,re
ROOT=Path(__file__).resolve().parents[1]
def main():
 import cairosvg
 d=json.loads((ROOT/'content/library.json').read_text(encoding='utf-8'));title=html.escape(d['site']['title']);url=html.escape(d['site']['url'].removeprefix('https://'))
 def icon(name,x,y,size):
  s=(ROOT/'assets/icons'/f'{name}.svg').read_text(encoding='utf-8');inner=re.sub(r'^.*?<svg[^>]*>','',s,flags=re.S);inner=re.sub(r'</svg>\s*$','',inner)
  return f'<g fill="none" transform="translate({x} {y}) scale({size/64})">{inner}</g>'
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">
 <rect width="1280" height="640" fill="#f6f5f0"/>
 <g font-family="DejaVu Sans,Arial,sans-serif" fill="#243b30">
 {icon('handbook',72,62,60)}<text x="150" y="104" font-size="34" font-weight="700">{title}</text>
 <path d="M72 158H1208" stroke="#dce2d9"/>
 <text x="72" y="256" font-size="51" font-weight="600">Useful prompts,</text><text x="72" y="324" font-size="51" font-weight="600">within reach.</text>
 <text x="74" y="383" font-size="22" fill="#647169">Personal preferences. Focused project workflows.</text>
 <rect x="72" y="437" width="334" height="90" rx="17" fill="#fffefb" stroke="#dce2d9"/>
 {icon('user',92,452,59)}<text x="172" y="492" font-size="23">User-level</text>
 <rect x="428" y="437" width="334" height="90" rx="17" fill="#fffefb" stroke="#dce2d9"/>
 {icon('project',448,452,59)}<text x="527" y="492" font-size="23">Project-level</text>
 <text x="74" y="589" font-size="17" fill="#647169">{url}</text>
 <text x="1208" y="589" text-anchor="end" font-size="18" fill="#647169">{len({c.split('-')[0] for c in d['locales']})} languages · Ready to copy</text>
 </g></svg>'''
 (ROOT/'assets/social-preview.svg').write_text(svg,encoding='utf-8',newline='\n')
 cairosvg.svg2png(bytestring=svg.encode(),write_to=str(ROOT/'assets/social-preview.png'))
 labels=[('handbook','Prompt Folio'),('user','User-level'),('project','Project-level'),('direct-first','Direct First'),('paper-mentor','Paper Mentor')]
 board='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="370"><rect width="1200" height="370" fill="#f6f5f0"/><g font-family="DejaVu Sans,Arial,sans-serif" fill="#243b30"><text x="45" y="65" font-size="27" font-weight="600">Prompt Folio · Icon system</text>'
 for i,(name,label) in enumerate(labels):
  x=53+i*230;board+=icon(name,x+53,116,92)+f'<text x="{x+99}" y="250" text-anchor="middle" font-size="18">{label}</text>'
 board+='<text x="45" y="321" font-size="15" fill="#647169">Rounded geometry · Consistent strokes · One quiet palette</text></g></svg>'
 (ROOT/'docs/icon-system.svg').write_text(board,encoding='utf-8',newline='\n');cairosvg.svg2png(bytestring=board.encode(),write_to=str(ROOT/'docs/icon-system.png'))
 print('Updated social and icon reference assets.')
if __name__=='__main__':main()
