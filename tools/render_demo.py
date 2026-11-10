"""Render the DriveTraj project film from existing evaluation videos. CPU only.

Schematic method animation is labelled; recorded rollouts retain their original
timing. The montage uses excerpts; the gallery exports complete selected episodes.
"""
from pathlib import Path
import argparse, json, math, subprocess
from PIL import Image, ImageDraw, ImageFont

P = argparse.ArgumentParser()
P.add_argument('--out', required=True)
P.add_argument('--work', required=True)
P.add_argument('--selection', required=True)
P.add_argument('--nav', required=True)
P.add_argument('--overview', required=True)
A = P.parse_args()
OUT, WORK = Path(A.out), Path(A.work)
for p in [OUT/'videos/hugsim', OUT/'images/posters', WORK]: p.mkdir(parents=True, exist_ok=True)
W,H=2560,1440
BG='#f7f8f4'; INK='#203632'; MUTED='#63746e'; GREEN='#176d60'; CORAL='#df7060'; LINE='#dce3dc'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def txt(d,xy,s,size=38,fill=INK,b=False): d.text(xy,s,font=font(size,b),fill=fill)
def base(section):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 # A branching road: the same symbol appears in the SVG project logo.
 d.rounded_rectangle((95,68,165,138),radius=18,fill=INK)
 d.line([(130,124),(130,105),(116,84)],fill='#ffffff',width=5)
 d.line([(130,106),(145,83)],fill=CORAL,width=5)
 d.line([(130,105),(130,83)],fill='#83b6a3',width=4)
 txt(d,(185,73),'DriveTraj',47,b=True)
 txt(d,(W-720,87),section.upper(),22,fill=MUTED)
 d.line((96,H-95,W-96,H-95),fill=LINE,width=2)
 txt(d,(96,H-68),'Beyond a single human demonstration',23,fill=MUTED)
 txt(d,(W-630,H-68),'rtwotwo.github.io/DriveTraj',23,fill=GREEN)
 return im
def fit(im,box,source):
 src=Image.open(source).convert('RGB');src.thumbnail((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
 im.paste(src,(box[0]+(box[2]-box[0]-src.width)//2,box[1]+(box[3]-box[1]-src.height)//2))
def run(args): subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def encode_still(im,name,duration):
 png=WORK/(name+'.png');im.save(png)
 v=WORK/(name+'.mp4')
 run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(png),'-t',str(duration),'-vf','fps=30','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-threads','4',str(v)])
 return v
def arrow(d,x,y,x2,y2,c=GREEN):
 d.line((x,y,x2,y2),fill=c,width=5)
 d.polygon([(x2,y2),(x2-18,y2-10),(x2-18,y2+10)],fill=c)
def schematic(t):
 im=base('method / schematic');d=ImageDraw.Draw(im)
 phase=min(2,int(t/6));progress=(t%6)/6
 titles=['One record. Several useful alternatives.','Match high-quality targets to distinct proposals.','Refine locally. Score the resulting plans.']
 txt(d,(100,210),titles[phase],65,b=True)
 sub=['Search smooth path deformations and evaluate their tracked execution.',
      'Dense targets teach generation; replay teaches the scorer what to accept and reject.',
      'Observed-video features guide the refiner and scorer through separate adapters.']
 txt(d,(100,310),sub[phase],31,fill=MUTED)
 if phase==0:
  d.rounded_rectangle((100,425,1520,1185),radius=30,fill='#edf2eb')
  # Conceptual road and candidate curves. This is not measured scene geometry.
  d.polygon([(510,1150),(970,1150),(1260,465),(780,465)],fill='#dfe6df')
  for j in range(13):
   endx=600+j*54; pts=[]
   for k in range(101):
    u=k/100; warp=6*u**5-15*u**4+10*u**3
    pts.append((740+190*u+(endx-930)*warp,1100-550*u))
   n=max(2,min(101,int(progress*160)))
   d.line(pts[:n],fill=GREEN if 4<=j<=8 else '#b6c6bf',width=5 if 4<=j<=8 else 2)
  d.rounded_rectangle((710,1070,770,1180),radius=8,fill=CORAL)
  txt(d,(1580,460),'Track and score',43,b=True)
  txt(d,(1580,540),'Driving validity',34)
  txt(d,(1580,600),'Trackability',34)
  txt(d,(1580,660),'Geometric separation',34)
  txt(d,(1580,825),'2.61M',94,fill=GREEN,b=True)
  txt(d,(1580,945),'screened targets',36)
  txt(d,(1580,1005),'from 103.3k real scenes',30,fill=MUTED)
 elif phase==1:
  labels=[('Dense targets',100),('AR proposals',960),('Scorer',1820)]
  for label,x in labels:
   d.rounded_rectangle((x,450,x+640,1130),radius=30,fill='white',outline=LINE,width=2)
   txt(d,(x+36,490),label,43,b=True)
  for i in range(5):
   y=650+i*74;d.line([(155,y+35),(320,y+25),(600,y-30+i*8)],fill=GREEN,width=6)
   if progress>i*.12:
    arrow(d,750,y+10,940,y+10)
   d.line([(1010,y+36),(1190,y+30),(1515,y-26+i*8)],fill=CORAL,width=6)
  arrow(d,1610,810,1800,810)
  for i in range(6):
   x=1880+i*80;top=930-[120,280,190,235,105,320][i]
   d.rounded_rectangle((x,top,x+50,930),radius=8,fill=GREEN if i==5 else '#a6c5b9')
  txt(d,(1865,1010),'Native + replay labels',25,fill=MUTED)
  txt(d,(110,1200),'Stage 1  /  Expert anchoring + dense matching + score calibration',36,fill=GREEN)
 else:
  xs=[100,960,1820]
  for x,title in zip(xs,['64 parents','Residual refinement','Score + select']):
   d.rounded_rectangle((x,650,x+640,1050),radius=30,fill='white',outline=LINE,width=2)
   txt(d,(x+32,695),title,40,b=True)
  for i in range(4):
   y=840+i*40;d.line([(160,y),(330,y-8),(650,y-50+i*15)],fill='#9db2a8',width=4)
   d.line([(1020,y),(1200,y-8),(1510,y-60+i*18)],fill=CORAL if i==1 else '#bdb7ca',width=6 if i==1 else 3)
  arrow(d,750,850,940,850);arrow(d,1610,850,1800,850)
  txt(d,(1870,855),'Fresh evaluator labels',27)
  txt(d,(1870,920),'One selected trajectory',27,fill=GREEN)
  d.rounded_rectangle((960,430,2460,565),radius=24,fill='#e8e4ee')
  txt(d,(1010,470),'JEPA: observed video + motion history',40,b=True)
  for x in (1280,2140):
   d.line((x,570,x,635),fill='#9383a2',width=4)
   d.polygon([(x,646),(x-9,628),(x+9,628)],fill='#9383a2')
  txt(d,(110,1140),'Up to four local targets; denoising and path losses share one winner.',34)
  txt(d,(110,1200),'Video adaptation updates JEPA. Planning gradients stop at its features.',31,fill=GREEN)
 return im

segments=[];chapters=[];clock=0
def add(v,title,duration):
 global clock
 actual=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(v)],text=True).strip())
 segments.append(v);chapters.append({'start':round(clock,3),'duration':actual,'title':title});clock+=actual

im=base('project introduction');d=ImageDraw.Draw(im)
txt(d,(100,235),'DriveTraj',126,b=True)
txt(d,(108,420),'Beyond a Single',82,b=True)
txt(d,(108,530),'Human Demonstration',82,b=True)
txt(d,(110,730),'Learning from scored trajectory alternatives',43,fill=MUTED)
txt(d,(110,795),'for end-to-end driving',43,fill=MUTED)
for i in range(9):
 pts=[]
 for k in range(101):
  u=k/100;pts.append((1900+210*u+(i-4)*50*u*u,1160-650*u))
 d.line(pts,fill=GREEN if i%2 else '#a9bfb5',width=5)
d.rounded_rectangle((1860,1110,1940,1240),radius=12,fill=CORAL)
txt(d,(110,1110),'Construct  /  Learn  /  Refine  /  Select',34,fill=GREEN,b=True)
im.save(OUT/'images/demo-poster.jpg',quality=95)
add(encode_still(im,'00_intro',5),'From one demonstration to many plans',5)
v=WORK/'01_method.mp4'
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','10','-i','-','-vf','fps=30','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-threads','4',str(v)],stdin=subprocess.PIPE)
for i in range(180):proc.stdin.write(schematic(i/10).tobytes())
proc.stdin.close()
if proc.wait()!=0:raise RuntimeError('Method encoder failed')
add(v,'Construct, supervise, and refine',18)
im=base('model overview');d=ImageDraw.Draw(im)
txt(d,(100,180),'One model. Two training stages.',61,b=True)
fit(im,(100,310,2460,1250),A.overview)
add(encode_still(im,'02_overview',6),'Model overview',6)

def clip(source,name,section,title,note,detail,duration,start=0,crop=None):
 im=base(section);d=ImageDraw.Draw(im)
 txt(d,(100,220),title,65,b=True)
 txt(d,(100,320),note,31,fill=MUTED)
 # Media is centered at native aspect ratio in a wide area.
 txt(d,(100,1130),detail,32,fill=GREEN)
 txt(d,(100,1200),'DriveTraj-Scale  /  Stage 2  /  NAVTEST PDMS 95.55',26,fill=MUTED)
 png=WORK/(name+'.png');im.save(png);v=WORK/(name+'.mp4')
 filt=(crop+',' if crop else '')+'scale=2360:680:force_original_aspect_ratio=decrease,setsar=1,fps=30'
 run(['ffmpeg','-y','-loglevel','error','-framerate','30','-loop','1','-i',str(png),'-ss',str(start),'-i',str(source),'-filter_complex',f'[1:v]{filt}[v];[0:v][v]overlay=x=(W-w)/2:y=430+(680-h)/2:shortest=1,fps=30,format=yuv420p[out]','-map','[out]','-t',str(duration),'-r','30','-an','-c:v','libx264','-preset','fast','-crf','21','-threads','4',str(v)])
 return v
for i,token in enumerate(['10909749099354e6','7cead15dfaab593e','6f8c03f8038757cc']):
 v=clip(Path(A.nav)/(token+'.mp4'),'03_nav_'+str(i),'NAVTEST / selected comparisons','Compare plans in the same scene.',
        'Front view + DriveTraj + FPD-Drive + Chainflow + DrivoR',
        'Fixed-start predictions; vehicle footprints and evaluator events shown over time.',5.1)
 add(v,'NAVTEST: '+token,5.1)

selection=json.loads(Path(A.selection).read_text());public=[]
for i,item in enumerate(selection):
 r=item['row'];source=Path(r['output'])/'video.mp4';slug=r['dataset']+'-'+r['scene']+'-'+r['mode']
 dest=OUT/'videos/hugsim'/(slug+'.mp4');poster=OUT/'images/posters'/(slug+'.jpg')
 # All source videos have a three-view front row at y=0..450.
 # The full episode timing is retained; rear-camera/empty lower row is excluded.
 run(['ffmpeg','-y','-loglevel','error','-i',str(source),'-vf','crop=2400:450:0:0,scale=1920:360','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-threads','4',str(dest)])
 run(['ffmpeg','-y','-loglevel','error','-ss','3','-i',str(dest),'-frames:v','1','-q:v','2',str(poster)])
 hd=float(r['hdscore'])*100;rc=float(r['rc'])*100
 start=5 if r['dataset']=='kitti360' else 0
 v=clip(source,'04_hug_'+str(i),'HUGSIM / selected closed-loop episode',
        {'kitti360':'KITTI-360','nuscenes':'nuScenes','pandaset':'PandaSet','waymo':'Waymo'}[r['dataset']],
        'The planner observes, replans, and controls the simulated vehicle.',
        f'Selected episode  /  Route completion {rc:.2f}  /  HD-Score {hd:.2f}',10,start,'crop=2400:450:0:0')
 add(v,'HUGSIM: '+r['dataset'],10)
 public.append(dict(dataset=r['dataset'],scene=r['scene'],mode=r['mode'],difficulty=r['difficulty'],rc=rc,hd_score=hd,
       duration_s=float(item['video']['format']['duration']),video='assets/videos/hugsim/'+dest.name,poster='assets/images/posters/'+poster.name,
       selection='Highest HD-Score in this data source; first listed episode breaks ties',crop='Top three camera views; full episode timing'))

im=base('full evaluation');d=ImageDraw.Draw(im)
txt(d,(100,230),'Scored alternatives. Better decisions.',73,b=True)
txt(d,(100,350),'DriveTraj-Scale / Stage 2',40,fill=MUTED)
for x,value,label,scope in [(100,'95.55','NAVTEST PDMS','12.1k scenarios'),(940,'56.09','HUGSIM route completion','345 closed-loop scenarios'),(1780,'46.69','HUGSIM HD-Score','Same 345 scenarios')]:
 txt(d,(x,580),value,112,fill=GREEN,b=True);txt(d,(x,755),label,30,b=True);txt(d,(x,820),scope,26,fill=MUTED)
txt(d,(100,1030),'Explore the method and all 41 selected NAVTEST animations.',37)
txt(d,(100,1135),'github.com/Rtwotwo/DriveTraj',48,fill=GREEN,b=True)
add(encode_still(im,'05_end',6),'Full evaluation results',6)
listing=WORK/'concat.txt';listing.write_text(''.join("file '"+str(p)+"'\n" for p in segments))
run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(OUT/'videos/drivetraj-demo.mp4')])
def stamp(t):
 ms=int(round(t*1000));return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
(OUT/'videos/demo-chapters.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(stamp(x['start'])+' --> '+stamp(x['start']+x['duration'])+'\n'+x['title'] for x in chapters)+'\n')
(OUT/'hugsim-selection.json').write_text(json.dumps(public,indent=2))
(WORK/'render_report.json').write_text(json.dumps(dict(duration_s=clock,resolution=[W,H],fps=30,chapters=chapters),indent=2))
# Extract every original comparison's poster without modifying any source video.
for p in sorted(Path(A.nav).glob('*.mp4')):
 run(['ffmpeg','-y','-loglevel','error','-ss','1.5','-i',str(p),'-frames:v','1','-vf','scale=1600:-2','-q:v','3',str(OUT/'images/posters'/(p.stem+'.jpg'))])
print(json.dumps({'state':'complete','duration':clock,'hugsim':len(public),'navtest_posters':len(list(Path(A.nav).glob('*.mp4')))}),flush=True)
