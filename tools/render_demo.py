"""Demo-only montage. Real-time footage; no explanatory or score overlays.

Uses the original 41 comparison videos and high-HD HUGSIM episodes. Each
difficulty has three independent, continuous episode lanes. Only the last
episode in a lane may be cut at the 60-second chapter boundary.
"""
import argparse, concurrent.futures, csv, json, subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--repo',required=True)
p.add_argument('--csv',required=True)
p.add_argument('--teaser',required=True)
p.add_argument('--work',required=True)
a=p.parse_args()
repo=Path(a.repo); work=Path(a.work); work.mkdir(parents=True,exist_ok=True)
out=work/'output'; out.mkdir(exist_ok=True)
def run(cmd):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if r.returncode: raise RuntimeError(r.stderr[-5000:])
    return r.stdout
def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
def duration(path):return float(probe(path)['format']['duration'])
def encode(inputs,filters,dest,seconds=None):
    cmd=['ffmpeg','-y','-loglevel','error','-filter_complex_threads','1']+inputs
    cmd+=['-filter_complex',filters,'-map','[out]','-an']
    if seconds is not None:cmd+=['-t',str(seconds)]
    cmd+=['-r','30','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-threads','2','-video_track_timescale','15360',str(dest)]
    run(cmd)
def concat(paths,dest):
    listing=dest.with_suffix('.txt'); listing.write_text(''.join("file '"+str(x)+"'\n" for x in paths))
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(dest)])

rows=list(csv.DictReader(open(a.csv)))
plans=[]
for diff in ['easy','medium','hard','extreme']:
    candidates=sorted([r for r in rows if r['difficulty']==diff and float(r['hdscore'])>=.8],key=lambda r:(-float(r['hdscore']),-float(r['rc']),r['dataset'],r['scene'],r['mode']))
    lanes=[[],[],[]]; lengths=[0.,0.,0.]; seen=set()
    for row in candidates:
        # One episode per physical scene in each difficulty.
        key=(row['dataset'],row['scene'])
        if key in seen:continue
        source=Path(row['output'])/'video.mp4'
        info=probe(source); video=next(s for s in info['streams'] if s['codec_type']=='video')
        if (video['width'],video['height'])!=(2400,900):raise ValueError((str(source),video['width'],video['height']))
        d=float(info['format']['duration'])
        lane=min(range(3),key=lambda j:lengths[j])
        lanes[lane].append(dict(row=row,source=str(source),duration=d,start=lengths[lane]))
        lengths[lane]+=d; seen.add(key)
        if min(lengths)>=60:break
    if min(lengths)<60:raise ValueError((diff,'Not enough distinct high-score footage',lengths))
    plans.append(dict(difficulty=diff,lanes=lanes,lengths=lengths))
(work/'selection_private.json').write_text(json.dumps(plans,indent=2))
print(json.dumps({'phase':'selected','chapters':[{k:v for k,v in x.items() if k!='lanes'} for x in plans]}),flush=True)

jobs=[]; segments=[]; chapter_names=[]
for name,src in [('Teaser',Path(a.teaser)),('Overview',repo/'docs/assets/images/overview.png')]:
    dest=work/(name.lower()+'.mp4');segments.append(dest);chapter_names.append(name)
    jobs.append((['-loop','1','-framerate','30','-i',str(src)],'[0:v]scale=2520:1400:force_original_aspect_ratio=decrease,pad=2560:1440:(ow-iw)/2:(oh-ih)/2:white,setsar=1,fps=30,format=yuv420p[out]',dest,8))
cases=json.loads((repo/'docs/assets/data/navtest-cases.json').read_text())['cases']
for i in range(0,len(cases),3):
    group=cases[i:i+3]; inputs=[]; filt=[]
    for j,c in enumerate(group):
        inputs+=['-i',str(repo/'docs'/c['video'])]
        filt.append(f'[{j}:v]scale=2560:480:force_original_aspect_ratio=decrease,pad=2560:480:(ow-iw)/2:(oh-ih)/2:white,setsar=1,fps=30[v{j}]')
    filt.append(''.join(f'[v{j}]' for j in range(len(group)))+f'vstack=inputs={len(group)}:shortest=1,pad=2560:1440:0:(oh-ih)/2:white,format=yuv420p[out]')
    dest=work/f'nav_{i//3:02}.mp4';segments.append(dest);chapter_names.append('NAVSIM')
    jobs.append((inputs,';'.join(filt),dest,None))

for plan in plans:
    for l,lane in enumerate(plan['lanes']):
        for j,item in enumerate(lane):
            dest=work/f"hug_{plan['difficulty']}_{l}_{j}.mp4";item['render']=str(dest)
            use=min(item['duration'],60-item['start'])
            jobs.append((['-i',item['source']],'[0:v]crop=2400:450:0:0,scale=2560:480,setsar=1,fps=30,format=yuv420p[out]',dest,use))

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(encode,*job) for job in jobs]
    for i,f in enumerate(concurrent.futures.as_completed(futures),1):
        f.result();print(f'encoded {i}/{len(jobs)}',flush=True)
for plan in plans:
    inputs=[]
    for l,lane in enumerate(plan['lanes']):
        dest=work/f"lane_{plan['difficulty']}_{l}.mp4"
        concat([Path(x['render']) for x in lane],dest);inputs+=['-i',str(dest)]
    # Single discreet difficulty label; no scores or explanatory text.
    label='HUGSIM · '+plan['difficulty'].capitalize()
    dest=work/f"chapter_{plan['difficulty']}.mp4"
    encode(inputs,f"[0:v][1:v][2:v]vstack=inputs=3:shortest=1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{label}':fontsize=30:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=8:x=20:y=20,format=yuv420p[out]",dest,60)
    segments.append(dest);chapter_names.append(label)
    print('finished '+label,flush=True)
movie=out/'drivetraj-demo.mp4';concat(segments,movie)
def stamp(t):
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02}.{n%1000:03}'
t=0;chapters=[]
for f,name in zip(segments,chapter_names):
    d=duration(f)
    if chapters and name=='NAVSIM' and chapters[-1]['title']=='NAVSIM':chapters[-1]['duration']+=d
    else:chapters.append(dict(title=name,start=t,duration=d))
    t+=d
(out/'demo-chapters.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(stamp(c['start'])+' --> '+stamp(c['start']+c['duration'])+'\n'+c['title'] for c in chapters)+'\n')
public=[]
for plan in plans:
    for l,lane in enumerate(plan['lanes']):
        for it in lane:
            r=it['row'];public.append(dict(dataset=r['dataset'],scene=r['scene'],mode=r['mode'],difficulty=r['difficulty'],hd_score=100*float(r['hdscore']),rc=100*float(r['rc']),lane=l,chapter_offset_s=it['start'],used_s=min(it['duration'],60-it['start'])))
report=dict(duration_s=duration(movie),resolution=[2560,1440],fps=30,navtest_cases=41,hugsim_episodes=len(public),chapters=chapters,hugsim_selection=public,selection_rule='HD >= 80; descending HD then RC; unique physical scene within each difficulty; balance three lanes until 60 seconds each; trim only the last episode per lane',timing='Original real time; repeated frames only to encode 30 fps',overlays='Difficulty label only on HUGSIM; original NAVSIM annotations retained')
assert report['duration_s']>300
(out/'demo-edit.json').write_text(json.dumps(report,indent=2))
run(['ffmpeg','-y','-loglevel','error','-ss','20','-i',str(movie),'-frames:v','1','-q:v','2',str(out/'demo-poster.jpg')])
run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'])
print(json.dumps({'state':'complete','duration':report['duration_s'],'bytes':movie.stat().st_size}),flush=True)
