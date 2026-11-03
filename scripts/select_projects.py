#!/usr/bin/env python3
"""Choose a fresh random set of public owner repositories; never expose private data."""
import fnmatch, json, os, random, sys, time, urllib.error, urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'config/projects.json').read_text())
owner=os.environ.get('PROFILE_OWNER','4q4r')
token=os.environ.get('GITHUB_TOKEN','')
url=f'https://api.github.com/users/{owner}/repos?type=owner&per_page=100&sort=full_name&page=1'
fixture=os.environ.get('REPOSITORIES_JSON')
if fixture:
 data=json.loads(Path(fixture).read_text())
else:
 headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'profile-readme-refresh'}
 if token: headers['Authorization']=f'Bearer {token}'
 next_url=url; data=[]; pages=0
 while next_url:
  req=urllib.request.Request(next_url,headers=headers)
  for attempt in range(3):
   try:
    with urllib.request.urlopen(req,timeout=25) as r:
     page=json.load(r); link=r.headers.get('Link','')
     if r.status!=200: raise RuntimeError(f'GitHub API HTTP {r.status}')
    if not isinstance(page,list): raise RuntimeError('GitHub API returned a non-list repository page')
    data.extend(page); pages+=1
    if pages>100: raise RuntimeError('GitHub API pagination exceeded 100 pages; preserving existing files')
    match=__import__('re').search(r'<([^>]+)>;\s*rel="next"',link)
    next_url=match.group(1) if match else None
    break
   except Exception:
    if attempt==2: raise
    time.sleep(2**attempt)
if not isinstance(data,list): raise SystemExit('GitHub API did not return a repository list; keeping existing README assets.')
patterns=[str(x).strip().lower() for x in cfg.get('exclude',[]) if str(x).strip()]
def eligible(r):
 if r.get('private') or r.get('owner',{}).get('login','').lower()!=owner.lower(): return False
 if r.get('fork') and not cfg.get('include_forks',False): return False
 if r.get('archived') and not cfg.get('include_archived',False): return False
 names=[r.get('name','').lower(),r.get('full_name','').lower()]
 return not any(fnmatch.fnmatchcase(n,p) for n in names for p in patterns)
pool=[r for r in data if eligible(r)]
if not pool: raise SystemExit('No eligible public repositories; current files are left untouched.')
n=cfg.get('count',4)
if type(n) is not int or not 1<=n<=12: raise SystemExit('config/projects.json count must be an integer from 1 to 12')
n=min(n,len(pool))
rng=random.SystemRandom(); chosen=rng.sample(pool,n)
# Avoid an identical consecutive set only where there is a real alternative.
state=root/'profile/projects-state.json'
if cfg.get('avoid_repeating_exact_set',True) and len(pool)>n and state.exists():
 try: previous=set(json.loads(state.read_text()).get('names',[]))
 except Exception: previous=set()
 if {x['full_name'] for x in chosen}==previous:
  chosen[-1]=rng.choice([x for x in pool if x['full_name'] not in previous])

def esc(s): return (str(s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'",'&#39;'))
def card(r):
 title=esc(r['name']); desc=esc(r.get('description') or 'A public repository by 4q4r.')
 lang=esc(r.get('language') or '—'); stars=int(r.get('stargazers_count') or 0); forks=int(r.get('forks_count') or 0)
 return f'''<td width="50%" valign="top"><a href="{esc(r['html_url'])}"><b>⌘ {title}</b></a><br><sub>{desc[:180]}</sub><br><sub>◉ {lang}　★ {stars}　⑂ {forks}</sub></td>'''
rows=[]
for i in range(0,len(chosen),2):
 pair=chosen[i:i+2]; cells=''.join(card(r) for r in pair)
 if len(pair)==1: cells+='<td width="50%"></td>'
 rows.append('<tr>'+cells+'</tr>')
block='''<table width="100%" border="0" cellpadding="14" cellspacing="8">\n'''+ '\n'.join(rows)+'''\n</table>\n\n<sub>Randomly refreshed from the current public repository list · excludes are editable in <code>config/projects.json</code>.</sub>'''
readme=(root/'README.md').read_text()
start='<!-- PROJECTS:START — generated from all current public repositories; edit config/projects.json, not this block. -->'
end='<!-- PROJECTS:END -->'
a=readme.index(start)+len(start); b=readme.index(end,a)
(root/'README.md').write_text(readme[:a]+'\n\n'+block+'\n'+readme[b:])
state.write_text(json.dumps({'names':[x['full_name'] for x in chosen]},indent=2)+'\n')
print('Selected '+', '.join(x['full_name'] for x in chosen)+f' from {len(pool)} eligible public repositories.')
