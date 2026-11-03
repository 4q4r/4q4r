#!/usr/bin/env python3
"""Accept only non-error SVGs. Failed renders never replace last-known-good assets."""
from pathlib import Path
from xml.etree import ElementTree as ET
import os, re, shutil, sys
root=Path(__file__).resolve().parents[1]

def valid(src):
 p=Path(src)
 if not p.is_file() or p.stat().st_size<500: return False
 try:
  tree=ET.parse(p); svg=tree.getroot()
  if not svg.tag.endswith('svg'): return False
  text=' '.join(svg.itertext()).lower()
  bad=('unexpected error','an error occurred','error while','api rate limit exceeded','deployment_disabled')
  return not any(marker in text for marker in bad)
 except Exception: return False

def adopt(src,dst):
 if valid(src):
  out=root/dst; out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,out); print(f'Accepted {dst}'); return True
 print(f'Rejected failed/missing SVG: {src}',file=sys.stderr); return False
# GitHub profile summary cards are output to a deterministic Tokyo Night directory.
summary={
 '0-profile-details.svg':'profile/summary/profile-details.svg',
 '3-stats.svg':'profile/summary/stats.svg',
 '2-most-commit-language.svg':'profile/summary/languages.svg'}
base=Path('profile-summary-card-output/tokyonight')
for src,dst in summary.items():
 candidate=base/src
 if not candidate.exists() or not valid(candidate):
  print(f'Using bundled last-known-good Summary Card for {src}.')
 if candidate.exists() and valid(candidate): adopt(candidate,dst)
 if not valid(root/dst): raise SystemExit(f'No valid current or last-known-good Summary Card {src}; abort without publication.')
# lowlighter/metrics output_action:none is explicitly copied out of its runner volume.
metrics=Path('/metrics_renders')
if not metrics.exists(): metrics=Path('metrics_renders')
if os.environ.get('METRICS_OK')=='true':
 if not adopt(metrics/'metrics.notable.svg','profile/metrics.notable.svg'):
  print('Keeping prior known-good notable SVG.')
else: print('Metrics generation failed/skipped; preserving bundled last-known-good notable card.')
follow=(metrics/'metrics.followup.svg')
if os.environ.get('FOLLOWUP_OK')=='true' and valid(follow):
 adopt(follow,'profile/metrics.followup.svg')
 p=root/'README.md'; text=p.read_text(); block='\n\n## ✦ Repository follow-up\n\n<div align="center"><img width="720" src="./profile/metrics.followup.svg" alt="Open and closed issues and pull requests"></div>\n'
 start='<!-- FOLLOWUP:START — workflow inserts this section only after a valid render. -->'; end='<!-- FOLLOWUP:END -->'
 text=text.replace(start+'\n'+end,start+block+end); p.write_text(text); print('Added valid follow-up card.')
else: print('Follow-up unavailable/invalid; no placeholder/error graphic inserted.')
