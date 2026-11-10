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
  const tabs=$('#hugsim-tabs');
  function show(index){
    const item=data[index];
    tabs.querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
    setVideo($('#hug-video'),item.video,item.poster);
    $('#hug-dataset').textContent=names[item.dataset];
    $('#hug-scene').textContent=`${item.scene} · ${item.mode}`;
    $('#hug-meta').textContent=`${item.duration_s.toFixed(2)} s · Full selected episode · Stage 2 Scale`;
    $('#hug-rc').textContent=item.rc.toFixed(2);$('#hug-hd').textContent=item.hd_score.toFixed(2);
    $('#hug-download').href=item.video;
  }
  data.forEach((item,index)=>{const b=document.createElement('button');b.textContent=names[item.dataset];b.type='button';b.addEventListener('click',()=>show(index));tabs.append(b);});
  show(0);
}).catch(e=>reportError($('#hugsim'),e));
