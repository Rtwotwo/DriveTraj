"""Replace the static prelude; preserve all subsequent demo packets verbatim."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

p=argparse.ArgumentParser()
p.add_argument('--repo',required=True);p.add_argument('--master',required=True)
p.add_argument('--logo',required=True);p.add_argument('--teaser',required=True)
p.add_argument('--work',required=True);a=p.parse_args()
repo=Path(a.repo);work=Path(a.work);work.mkdir(parents=True,exist_ok=True)
W,H,FPS=2560,1440,30
logo=Image.open(a.logo).convert('RGBA')
teaser=Image.open(a.teaser).convert('RGB')
overview=Image.open(repo/'docs/assets/images/overview.png').convert('RGB')
def ease(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)
def frame():return Image.new('RGB',(W,H),'white')
def fitted(src,width,height):
 s=min(width/src.width,height/src.height)
 return src.resize((round(src.width*s),round(src.height*s)),Image.Resampling.LANCZOS)
T=fitted(teaser,2420,1350);O=fitted(overview,2460,1340)
tx,ty=(W-T.width)//2,(H-T.height)//2
ox,oy=(W-O.width)//2,(H-O.height)//2
def logo_frame(t):
 im=frame();scale=.96+.04*ease(t/.65)
 lg=fitted(logo,1900*scale,650)
 x,y=(W-lg.width)//2,(H-lg.height)//2
 im.paste(lg,(x,y),lg)
 # A restrained dot follows the existing coral underline.
 if .4<t<1.9:
  u=ease((t-.4)/1.5); sx=lg.width/1020;sy=lg.height/270
  px=x+(755+179*u)*sx;py=y+(221-16*u*u)*sy
  d=ImageDraw.Draw(im);r=6*scale;d.ellipse((px-r,py-r,px+r,py+r),fill='#df7060')
 return im
def teaser_frame(t):
 im=frame();im.paste(T,(tx,ty));d=ImageDraw.Draw(im,'RGBA')
 # Reveal existing panels in reading order, then emphasize our panel.
 boxes=[(0,0,.5,.49),(.5,0,1,.49),(0,.49,.5,.965),(.5,.49,1,.965)]
 for i,(x0,y0,x1,y1) in enumerate(boxes):
  alpha=round(230*(1-ease((t-i*.5)/.55)))
  d.rectangle((tx+x0*T.width,ty+y0*T.height,tx+x1*T.width,ty+y1*T.height),fill=(255,255,255,alpha))
 if t>2:
  alpha=round(150*math.sin(math.pi*min(1,(t-2)/1.6)))
  d.rounded_rectangle((tx+.51*T.width,ty+.50*T.height,tx+.988*T.width,ty+.96*T.height),radius=18,outline=(23,109,96,alpha),width=4)
 return im
def xy(x,y):return (ox+x*O.width/1820,oy+y*O.height/958)
def overview_frame(t):
 im=frame();im.paste(O,(ox,oy));d=ImageDraw.Draw(im,'RGBA')
 # Reveal input, archive and planning regions without relocating any module.
 regions=[((0,0,1200,460),0),((1220,0,1820,470),.45),((0,460,1200,958),.8),((1220,470,1820,958),1.25)]
 for (x0,y0,x1,y1),start in regions:
  alpha=round(200*(1-ease((t-start)/.65)))
  d.rectangle((*xy(x0,y0),*xy(x1,y1)),fill=(255,255,255,alpha))
 # Follow only the actual AR -> DiT -> scorer -> selected-plan connections.
 for points,start,end in [([(340,659),(475,659)],1.5,2.1),([(615,708),(615,807)],2.1,2.7),([(755,845),(835,845)],2.7,3.3)]:
  if start<=t<=end:
   u=(t-start)/(end-start);(x0,y0),(x1,y1)=points
   x,y=xy(x0+u*(x1-x0),y0+u*(y1-y0));r=7
   d.ellipse((x-r,y-r,x+r,y+r),fill=(23,109,96,235),outline='white',width=2)
 return im
def run(cmd):
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-5000:])
 return r.stdout
def duration(f):return float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(f)]))
def concat(files,out):
 listing=work/(out.stem+'.txt');listing.write_text(''.join("file '"+str(x)+"'\n" for x in files))
 run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(out)])
# This edit replaces the original 16-second opening exactly once.
assert abs(duration(Path(a.master))-327.4)<.05, 'Expected original 327.4-second master'
original_edit=json.loads((repo/'docs/assets/data/demo-edit.json').read_text(encoding='utf-8'))
assert original_edit['chapters'][2]['title']=='NAVSIM' and abs(original_edit['chapters'][2]['start']-16)<.05
intro=work/'intro.mp4'
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-threads','4','-video_track_timescale','15360',str(intro)],stdin=subprocess.PIPE)
for name,seconds,fn in [('Logo',2.4,logo_frame),('Teaser',3.6,teaser_frame),('Overview',4.4,overview_frame)]:
 for i in range(round(seconds*FPS)):
  im=fn(i/FPS)
  if name=='Logo' and i==0:im.save(work/'demo-poster.jpg',quality=96)
  if i in [0,round(seconds*FPS/2),round(seconds*FPS)-1]:im.resize((1280,720)).save(work/f'{name.lower()}_{i}.jpg',quality=92)
  proc.stdin.write(im.tobytes())
 print('animated '+name,flush=True)
proc.stdin.close()
if proc.wait()!=0:raise RuntimeError('intro encode failed')
def hashes(path,start):
 data=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_packets','-show_data_hash','sha256','-show_entries','packet=pts_time,data_hash','-of','json',str(path)]))
 return [x['data_hash'] for x in data['packets'] if float(x['pts_time'])>=start-.0001]
for kind,source in [('master',Path(a.master))]:
 tail=work/(kind+'_tail.mp4');dest=work/('drivetraj-demo-'+kind+'.mp4')
 run(['ffmpeg','-y','-v','error','-ss','16','-i',str(source),'-map','0:v:0','-an','-c','copy',str(tail)])
 concat([intro,tail],dest)
 assert abs(duration(dest)-321.8)<.05,(kind,duration(dest))
 assert hashes(source,16)==hashes(dest,10.4),kind+' demo packets changed'
 run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'])
 print(json.dumps(dict(kind=kind,duration=duration(dest),bytes=dest.stat().st_size,tail_packets='identical',sha256=hashlib.sha256(dest.read_bytes()).hexdigest())),flush=True)
# Re-encode the verified master so the web rendition has clean segment boundaries.
web=work/'drivetraj-demo-web.mp4'
run(['ffmpeg','-y','-v','error','-i',str(work/'drivetraj-demo-master.mp4'),'-an','-c:v','libx264','-preset','fast','-b:v','2100k','-maxrate','2600k','-bufsize','5200k','-pix_fmt','yuv420p','-threads','8','-movflags','+faststart',str(web)])
assert abs(duration(web)-321.8)<.05
run(['ffmpeg','-v','error','-i',str(web),'-f','null','-'])
print(json.dumps(dict(kind='web',duration=duration(web),bytes=web.stat().st_size,source='verified master',sha256=hashlib.sha256(web.read_bytes()).hexdigest())),flush=True)
edit=json.loads((repo/'docs/assets/data/demo-edit.json').read_text())
edit['duration_s']=321.8
edit['chapters']=[dict(title='DriveTraj',start=0,duration=2.4),dict(title='Teaser',start=2.4,duration=3.6),dict(title='Overview',start=6,duration=4.4)]+[dict(c,start=round(c['start']-5.6,3)) for c in edit['chapters'][2:]]
edit['opening']='2.4 s logo, 3.6 s panel reveal, 4.4 s overview reveal with existing-link highlights; no narration or added explanations'
edit['demo_tail_verification']='Master demo packet hashes after the opening match the previous version; web rendition is encoded from the verified master.'
(work/'demo-edit.json').write_text(json.dumps(edit,indent=2))
def stamp(t):
 n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02}.{n%1000:03}'
(work/'demo-chapters.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(stamp(c['start'])+' --> '+stamp(c['start']+c['duration'])+'\n'+c['title'] for c in edit['chapters'])+'\n')
print('COMPLETE',flush=True)
