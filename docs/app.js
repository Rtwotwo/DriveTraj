'use strict';
const $ = (s) => document.querySelector(s);
// A single active player avoids silent parallel downloads and overlapping sound.
document.querySelectorAll('video').forEach(v => v.addEventListener('play', () => {
  document.querySelectorAll('video').forEach(other => { if (other !== v) other.pause(); });
}));
async function getJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json();
}
function setVideo(video, source, poster) {
  video.pause(); video.src = source; video.poster = poster; video.load();
}
function reportError(parent, error) {
  const p = document.createElement('p');p.className='error';
  p.textContent='The video index could not load. Please refresh or download the MP4 files from GitHub.';
  parent.append(p); console.error(error);
}
getJSON('assets/data/links.json').then(links=>{
  document.querySelectorAll('[data-resource]').forEach(a=>{
    const url=links[a.dataset.resource];
    if(typeof url==='string' && /^https:\/\//.test(url)) {
      a.href=url;a.removeAttribute('aria-disabled');a.title=a.textContent.trim();
    }
  });
}).catch(e=>console.error(e));
getJSON('assets/data/navtest-cases.json').then(data => {
  let cases = data.cases, current = 0;
  const select = $('#case-select'), filter = $('#case-filter'), video = $('#nav-video');
  function show(index) {
    current = (index + cases.length) % cases.length;
    const item = cases[current];select.value=item.token;
    setVideo(video,item.video,item.poster);
    $('#case-count').textContent=`${current+1} / ${cases.length}`;
    $('#case-caption').textContent=`Front view | ${item.token} · Four-method comparison`;
    $('#case-download').href=item.video;
  }
  function populate() {
    cases=data.cases.filter(c=>filter.value!=='zero'||c.zero_baselines===3);
    select.replaceChildren(...cases.map(c=>{const o=document.createElement('option');o.value=c.token;o.textContent=c.token;return o;}));
    show(0);
  }
  select.addEventListener('change',()=>show(cases.findIndex(c=>c.token===select.value)));
  filter.addEventListener('change',populate);
  $('#prev-case').addEventListener('click',()=>show(current-1));
  $('#next-case').addEventListener('click',()=>show(current+1));
  populate();
}).catch(e=>reportError($('#navtest .container'),e));
getJSON('assets/hugsim-selection.json').then(data=>{
  const names={kitti360:'KITTI-360',nuscenes:'nuScenes',pandaset:'PandaSet',waymo:'Waymo'};
  const difficulties=['easy','medium','hard','extreme'];
  const tabs=$('#hugsim-tabs'),source=$('#hug-source'),select=$('#hug-select');
  let difficulty='easy',items=[],current=0;
  function show(index){
    if(!items.length)return;
    current=(index+items.length)%items.length;
    const item=items[current];select.value=String(current);
    setVideo($('#hug-video'),item.video,item.poster);
    $('#hug-dataset').textContent=names[item.dataset];
    $('#hug-scene').textContent=`${item.scene} \u00b7 ${item.mode}`;
    $('#hug-meta').textContent=`${item.duration_s.toFixed(2)} s \u00b7 DriveTraj-Scale Stage 2`;
    $('#hug-rc').textContent=item.rc.toFixed(2);$('#hug-hd').textContent=item.hd_score.toFixed(2);
    $('#hug-download').href=item.video;$('#hug-count').textContent=`${current+1} / ${items.length}`;
    const grid=$('#hug-thumbs');grid.replaceChildren();
    const offset=Math.floor(current/6)*6;
    items.slice(offset,offset+6).forEach((x,j)=>{
      const b=document.createElement('button');b.type='button';b.className='episode-card';
      b.setAttribute('aria-pressed',String(offset+j===current));
      const img=document.createElement('img');img.src=x.poster;img.alt=`${names[x.dataset]} ${x.scene}`;img.loading='lazy';
      const label=document.createElement('span');label.textContent=`${names[x.dataset]} \u00b7 ${x.scene}`;
      b.append(img,label);b.addEventListener('click',()=>show(offset+j));grid.append(b);
    });
  }
  function populate(){
    source.querySelectorAll('option').forEach(o=>{o.disabled=o.value!=='all'&&!data.some(x=>x.difficulty===difficulty&&x.dataset===o.value)});
    if(source.selectedOptions[0].disabled)source.value='all';
    items=data.filter(x=>x.difficulty===difficulty&&(source.value==='all'||x.dataset===source.value));
    tabs.querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-pressed',String(difficulties[i]===difficulty)));
    select.replaceChildren(...items.map((x,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=`${names[x.dataset]} \u00b7 ${x.scene} \u00b7 ${x.mode}`;return o;}));
    show(0);
  }
  difficulties.forEach(d=>{const b=document.createElement('button');b.type='button';b.textContent=`${d[0].toUpperCase()+d.slice(1)} (${data.filter(x=>x.difficulty===d).length})`;b.addEventListener('click',()=>{difficulty=d;populate()});tabs.append(b)});
  source.addEventListener('change',populate);select.addEventListener('change',()=>show(Number(select.value)));
  $('#hug-prev').addEventListener('click',()=>show(current-1));$('#hug-next').addEventListener('click',()=>show(current+1));
  populate();
}).catch(e=>reportError($('#hugsim'),e));
