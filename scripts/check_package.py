from pathlib import Path
import json
from xml.etree import ElementTree as ET
r=Path(__file__).resolve().parents[1]
cfg=json.loads((r/'config/projects.json').read_text())
assert type(cfg.get('count')) is int and 1 <= cfg['count'] <= 12
assert isinstance(cfg.get('exclude'),list)
readme=(r/'README.md').read_text()
for marker in ['<!-- PROJECTS:START','<!-- PROJECTS:END -->','<!-- FOLLOWUP:START','<!-- FOLLOWUP:END -->']:
 assert marker in readme, f'missing README marker {marker}'
for p in [r/'README.md',r/'.github/workflows/metrics.yml',r/'scripts/select_projects.py',r/'scripts/assemble.py',r/'assets/rem-re-zero.gif',r/'profile/metrics.notable.svg',r/'profile/metrics.shikimori.svg']:
 assert p.exists() and p.stat().st_size>50,p
for p in (r/'profile/summary').glob('*.svg'):
 svg=ET.parse(p).getroot(); assert svg.tag.endswith('svg') and p.stat().st_size>500,p
 assert not any(x in ' '.join(svg.itertext()).lower() for x in ('unexpected error','deployment_disabled','api rate limit exceeded')),p
print('README markers, config, workflow, Python helpers and checked SVG assets are present and valid.')
