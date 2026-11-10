"""Check the static website and its declared media without third-party packages."""
from pathlib import Path
from html.parser import HTMLParser
import csv,json,re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'docs'
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:
   assert a['id'] not in self.ids,'duplicate id '+a['id']
   self.ids.add(a['id'])
  self.refs += [a[k] for k in ['src','href','poster'] if k in a]
p=Parser();p.feed((SITE/'index.html').read_text(encoding='utf-8'))
for r in p.refs:
 if r.startswith(('http:','https:','mailto:','data:')):continue
 if r.startswith('#'):
  if len(r)>1:assert r[1:] in p.ids,r
 else:assert (SITE/r.split('#')[0]).is_file(),r
nav=json.loads((SITE/'assets/data/navtest-cases.json').read_text())
assert nav['count']==41==len(nav['cases'])
assert len({x['token'] for x in nav['cases']})==41
for x in nav['cases']:
 assert x['scores']['DriveTraj']>=95
 assert all(v<80 for k,v in x['scores'].items() if k!='DriveTraj')
hug=json.loads((SITE/'assets/hugsim-selection.json').read_text())
assert len(hug)==4 and len({x['dataset'] for x in hug})==4
for x in nav['cases']+hug:
 for k in ['video','poster']:assert (SITE/x[k]).is_file(),x[k]
for name,count in [('navtest-scores.csv',12146),('hugsim-scores.csv',345)]:
 with (SITE/'assets/data'/name).open(newline='') as f:rows=list(csv.DictReader(f))
 assert len(rows)==count,(name,len(rows))
 assert 'output' not in rows[0]
for f in SITE.rglob('*'):
 if not f.is_file():continue
 assert f.stat().st_size<100*1024*1024,('GitHub file limit',f)
 if f.suffix in ['.html','.js','.css','.json','.svg','.vtt','.csv']:
  t=f.read_text(encoding='utf-8')
  assert not re.search(r'/data/xinyao/|C:\\Users\\|8\.130\.174\.55|\.aris/',t),('internal path',f)
assert len(list((SITE/'assets/videos/navtest').glob('*.mp4')))==41
print('PASS: anchors, local references, 41 NAVTEST videos, 4 HUGSIM videos, score counts, file sizes, public-path checks.')
