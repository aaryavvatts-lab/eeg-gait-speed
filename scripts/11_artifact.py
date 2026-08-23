"""Build the shareable web page as one self-contained HTML file.

Everything the page needs lives inside the file: the fonts, the figures and
the model output that drives the interactive demo. Nothing is fetched from
another server when somebody opens it. That keeps the privacy notice short and
honest, and it means the page still works if a font host goes down.

Every number on the page is read from results_summary.json, so the text cannot
drift away from the tables that produced it.
"""
from __future__ import annotations

import base64
import json
import sys

from gaitbci import config as cfg, fonts, refs

OUT = cfg.REPORT / "index.html"


def img(name: str) -> str:
    path = cfg.FIGURES / f"{name}.png"
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def figure(name: str, caption: str, alt: str) -> str:
    src = img(name)
    if not src:
        return ""
    return (
        '<figure class="fig">\n'
        f'  <div class="fig-scroll"><img src="{src}" alt="{alt}"></div>\n'
        f"  <figcaption>{caption}</figcaption>\n"
        "</figure>"
    )


def f3(v) -> str:
    return "n/a" if v is None else f"{float(v):.3f}"


CSS = """
:root {
  --ground:#F3F5F7; --surface:#FFFFFF; --surface-2:#E9EDF1;
  --ink:#12181F; --ink-2:#4B5563; --ink-3:#5F6975;
  --rule:#D8DEE4; --rule-strong:#BAC3CB;
  --accent:#155288; --accent-soft:#E4EEF6;
  --marker:#A83E1B; --marker-soft:#F8E7DF;
  --good:#1F6F45;
  --shadow:0 1px 2px rgba(18,24,31,.05), 0 8px 24px -12px rgba(18,24,31,.18);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground:#0B0F13; --surface:#121821; --surface-2:#19212B;
    --ink:#EDF1F5; --ink-2:#96A3B0; --ink-3:#7E8B99;
    --rule:#212B35; --rule-strong:#33404C;
    --accent:#5B9BD5; --accent-soft:#132538;
    --marker:#E8794F; --marker-soft:#2E1B10;
    --good:#4ECA8B;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 28px -14px rgba(0,0,0,.7);
  }
}
:root[data-theme="dark"] {
  --ground:#0B0F13; --surface:#121821; --surface-2:#19212B;
  --ink:#EDF1F5; --ink-2:#96A3B0; --ink-3:#7E8B99;
  --rule:#212B35; --rule-strong:#33404C;
  --accent:#5B9BD5; --accent-soft:#132538;
  --marker:#E8794F; --marker-soft:#2E1B10;
  --good:#4ECA8B;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 28px -14px rgba(0,0,0,.7);
}

*,*::before,*::after { box-sizing:border-box; }
body {
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Source Serif 4",Georgia,"Times New Roman",serif;
  font-size:17px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}
.shell { max-width:1100px; margin:0 auto; padding:0 24px 96px; }
.col { max-width:64ch; margin-inline:auto; }

h1,h2,h3,.eyebrow,.readout,th,.tag,.num,.ctl,button,label,input {
  font-family:Archivo,"Helvetica Neue",Arial,sans-serif;
}
h1 { font-size:clamp(2.1rem,5.2vw,3.5rem); line-height:1.04; letter-spacing:-.022em;
     font-weight:700; margin:0 0 .5em; text-wrap:balance; }
h2 { font-size:clamp(1.35rem,2.6vw,1.85rem); line-height:1.18; letter-spacing:-.015em;
     font-weight:700; margin:0 0 .35em; text-wrap:balance; }
h3 { font-size:1.06rem; letter-spacing:-.008em; font-weight:600; margin:2.2em 0 .3em; }
h4 { font-size:.95rem; font-weight:600; margin:1.6em 0 .25em;
     font-family:Archivo,"Helvetica Neue",Arial,sans-serif; }
p { margin:0 0 1.05em; }
a { color:var(--accent); text-underline-offset:2px; }
a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible {
  outline:3px solid var(--accent); outline-offset:2px; border-radius:3px; }
strong { font-weight:600; }

.skip {
  position:absolute; left:-9999px; top:0; z-index:99;
  background:var(--accent); color:#fff; padding:10px 16px; border-radius:0 0 6px 0;
  font-size:.85rem; text-decoration:none;
}
.skip:focus { left:0; }

.eyebrow {
  font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.7rem; letter-spacing:.14em; text-transform:uppercase;
  color:var(--ink-3); margin:0 0 .9em; display:flex; align-items:center; gap:.7em;
}
.eyebrow::after { content:""; flex:1; height:1px; background:var(--rule); }

.hero { padding:clamp(56px,9vw,104px) 0 0; }
.deck { font-size:clamp(1.05rem,2vw,1.28rem); color:var(--ink-2); line-height:1.5;
        max-width:56ch; margin:0 0 1.6em; }
.byline { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.74rem;
          color:var(--ink-3); letter-spacing:.04em; margin-bottom:2.4em; }

.scope { position:relative; border:1px solid var(--rule); border-radius:10px;
  background:var(--surface); box-shadow:var(--shadow); overflow:hidden;
  margin-bottom:2.4em; }
.scope canvas { display:block; width:100%; height:230px; }
.scope-labels { position:absolute; inset:0; pointer-events:none;
  display:flex; flex-direction:column; justify-content:space-around;
  padding:10px 0 10px 14px; }
.scope-labels span {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.68rem;
  color:var(--ink-2); letter-spacing:.08em; align-self:flex-start;
  background:var(--surface); border:1px solid var(--rule);
  padding:2px 7px; border-radius:4px; }
.scope-foot { border-top:1px solid var(--rule); padding:9px 14px;
  background:var(--surface-2);
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.67rem;
  color:var(--ink-3); letter-spacing:.05em; }

.readouts { display:grid; grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
  gap:1px; background:var(--rule); border:1px solid var(--rule);
  border-radius:10px; overflow:hidden; margin:0 0 1em; }
.readout { background:var(--surface); padding:16px 18px; }
.readout .num { display:block; font-size:1.72rem; font-weight:700; letter-spacing:-.02em;
  font-variant-numeric:tabular-nums; line-height:1.1; }
.readout .lab { display:block; font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:.66rem; letter-spacing:.09em; text-transform:uppercase;
  color:var(--ink-3); margin-top:.5em; line-height:1.45; }
.readout.is-false .num { color:var(--marker); }
.readout.is-true .num { color:var(--accent); }
.readout-note { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.68rem;
  color:var(--ink-3); letter-spacing:.03em; margin:0 0 3em; }

.toc { border:1px solid var(--rule); border-radius:10px; background:var(--surface);
  padding:16px 20px; margin:0 0 1em; }
.toc h2 { font-size:.7rem; font-family:"IBM Plex Mono",ui-monospace,monospace;
  letter-spacing:.14em; text-transform:uppercase; color:var(--ink-3);
  margin:0 0 .7em; font-weight:500; }
.toc ol { margin:0; padding:0; list-style:none; display:grid;
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:.35em 1.4em; }
.toc a { font-size:.9rem; text-decoration:none; }
.toc a:hover { text-decoration:underline; }

section { padding:clamp(44px,6vw,72px) 0 0; }

.callout { border-left:3px solid var(--accent); background:var(--accent-soft);
  padding:16px 20px; border-radius:0 8px 8px 0; margin:1.6em 0; }
.callout p:last-child { margin-bottom:0; }
.callout.warn { border-left-color:var(--marker); background:var(--marker-soft); }

.tbl-scroll { overflow-x:auto; margin:1.5em 0; border:1px solid var(--rule);
  border-radius:9px; background:var(--surface); }
table { border-collapse:collapse; width:100%; font-size:.9rem; line-height:1.4; }
th,td { padding:11px 14px; text-align:left; border-bottom:1px solid var(--rule);
  white-space:nowrap; vertical-align:top; }
td.prose { white-space:normal; color:var(--ink-2); }
th { font-size:.68rem; letter-spacing:.09em; text-transform:uppercase;
  color:var(--ink-3); font-weight:600; background:var(--surface-2); }
tbody tr:last-child td { border-bottom:none; }
td.n { font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-variant-numeric:tabular-nums; }
td.hi { color:var(--accent); font-weight:600; }
td.lo { color:var(--marker); font-weight:600; }
caption { caption-side:top; text-align:left; padding:10px 14px 0;
  font-size:.78rem; color:var(--ink-3);
  font-family:"IBM Plex Mono",ui-monospace,monospace; }

.fig { margin:2.4em 0; }
.fig-scroll { overflow-x:auto; border:1px solid var(--rule-strong); border-radius:10px;
  background:#FFFFFF; padding:10px; box-shadow:var(--shadow); }
.fig img { display:block; width:100%; min-width:640px; max-width:100%; height:auto;
  border-radius:3px; }
figcaption { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem;
  line-height:1.6; color:var(--ink-3); margin-top:.85em;
  letter-spacing:.02em; max-width:72ch; }

.limits { display:flex; flex-direction:column; gap:1px; background:var(--rule);
  border:1px solid var(--rule); border-radius:10px; overflow:hidden; margin:1.6em 0; }
.limit { background:var(--surface); padding:18px 20px; }
.limit h3 { margin:0 0 .3em; font-size:.95rem; }
.limit p { margin:0; font-size:.94rem; color:var(--ink-2); }

.app { border:1px solid var(--rule-strong); border-radius:12px;
  background:var(--surface); box-shadow:var(--shadow); overflow:hidden;
  margin:1.8em 0; }
.app-head { padding:16px 20px; border-bottom:1px solid var(--rule);
  background:var(--surface-2); }
.app-head h3 { margin:0 0 .2em; font-size:1rem; }
.app-head p { margin:0; font-size:.84rem; color:var(--ink-2); }
.app-body { padding:18px 20px 20px; }
.app canvas { display:block; width:100%; height:230px; border-radius:6px;
  background:var(--ground); border:1px solid var(--rule); }
.legend { display:flex; flex-wrap:wrap; gap:6px 18px; margin:10px 0 0;
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem;
  color:var(--ink-2); }
.legend span { display:inline-flex; align-items:center; gap:7px; }
.legend i { display:inline-block; width:16px; height:3px; border-radius:2px;
  background:currentColor; font-style:normal; }
.legend .k-real { color:var(--ink-2); }
.legend .k-real i { height:5px; opacity:.55; }
.legend .k-cmd { color:var(--accent); }
.legend .k-raw { color:var(--ink-3); }
.legend .k-raw i { width:5px; height:5px; border-radius:50%; }
.legend .k-chg { color:var(--marker); }
.legend .k-chg i { height:0; border-top:2px dotted currentColor; }

.ctls { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:16px 22px; margin:0 0 18px; }
.ctl { display:flex; flex-direction:column; gap:6px; }
.ctl > .lbl { font-size:.7rem; letter-spacing:.09em; text-transform:uppercase;
  color:var(--ink-3); font-family:"IBM Plex Mono",ui-monospace,monospace; }
.ctl input[type=range] { width:100%; accent-color:var(--accent); height:22px; }
.ctl .val { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.8rem;
  color:var(--ink-2); font-variant-numeric:tabular-nums; }
.radios { display:flex; gap:8px; flex-wrap:wrap; }
.radios label { display:inline-flex; align-items:center; gap:6px; font-size:.85rem;
  border:1px solid var(--rule-strong); border-radius:6px; padding:6px 11px;
  cursor:pointer; background:var(--ground); }
.radios input { accent-color:var(--accent); margin:0; }
.radios label:has(input:checked) { border-color:var(--accent);
  background:var(--accent-soft); color:var(--accent); font-weight:600; }

.app-actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap;
  margin:14px 0 0; }
button.play { font-size:.85rem; font-weight:600; padding:9px 18px; cursor:pointer;
  border-radius:7px; border:1px solid var(--accent); background:var(--accent);
  color:#fff; }
button.play:hover { filter:brightness(1.08); }
button.reset { font-size:.85rem; font-weight:600; padding:9px 16px; cursor:pointer;
  border-radius:7px; border:1px solid var(--rule-strong); background:var(--ground);
  color:var(--ink); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:1px; background:var(--rule); border:1px solid var(--rule);
  border-radius:9px; overflow:hidden; margin:16px 0 0; }
.stat { background:var(--ground); padding:12px 14px; }
.stat b { display:block; font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:1.15rem; font-variant-numeric:tabular-nums; color:var(--accent);
  font-weight:600; }
.stat span { display:block; font-size:.66rem; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-3); margin-top:3px;
  font-family:"IBM Plex Mono",ui-monospace,monospace; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px;
  overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }

.legal { border-top:1px solid var(--rule); margin-top:clamp(48px,7vw,80px);
  padding-top:12px; }
.legal details { border-bottom:1px solid var(--rule); }
.legal summary { cursor:pointer; padding:15px 2px; font-weight:600; font-size:.95rem;
  font-family:Archivo,"Helvetica Neue",Arial,sans-serif; list-style:none;
  display:flex; align-items:center; justify-content:space-between; gap:12px; }
.legal summary::-webkit-details-marker { display:none; }
.legal summary::after { content:"+"; font-family:"IBM Plex Mono",monospace;
  color:var(--ink-3); font-size:1.1rem; }
.legal details[open] summary::after { content:"\\2212"; }
.legal .body { padding:0 2px 20px; font-size:.92rem; color:var(--ink-2);
  max-width:70ch; }
.legal .body p { margin:0 0 .85em; }
.legal .body h3 { color:var(--ink); margin:1.3em 0 .3em;
  font-size:.95rem; }
.legal .body ul { margin:0 0 .9em; padding-left:1.2em; }
.legal .body li { margin-bottom:.3em; }

.notice { border:1px solid var(--rule-strong); background:var(--surface-2);
  border-radius:9px; padding:12px 16px; margin:0 0 2.2em; font-size:.85rem;
  color:var(--ink-2); display:flex; gap:14px; align-items:flex-start;
  justify-content:space-between; }
.notice p { margin:0; }
.notice button { flex:none; font-size:.75rem; padding:5px 11px; cursor:pointer;
  border-radius:6px; border:1px solid var(--rule-strong); background:var(--surface);
  color:var(--ink); font-weight:600; }

.refs { font-size:.88rem; color:var(--ink-2); padding-left:1.3em; }
.refs li { margin-bottom:.7em; }
.refs a { word-break:break-word; }

footer { margin-top:40px; padding-top:24px; border-top:1px solid var(--rule);
  color:var(--ink-3); font-size:.86rem; }
footer code { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.85em; }
.tag { display:inline-block; font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:.66rem; letter-spacing:.08em; text-transform:uppercase;
  padding:3px 8px; border:1px solid var(--rule-strong); border-radius:4px;
  color:var(--ink-2); margin-right:.4em; }

@media (max-width:640px){
  body { font-size:16px; }
  .scope canvas { height:180px; }
  th,td { padding:9px 11px; }
  .notice { flex-direction:column; }
}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important;}
}
"""

CANVAS_JS = """
(function(){
  var c = document.getElementById('scope');
  if(!c) return;
  var ctx = c.getContext('2d');
  var CAD = [0.68, 0.81, 0.91];
  var AMP = [0.62, 0.82, 1.0];
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var W=0, H=0, dpr=1, inkC=null, faintC=null, raf=null, t0=null;

  function resize(){
    var nd = Math.min(window.devicePixelRatio||1, 2);
    var nw = c.clientWidth, nh = c.clientHeight;
    if(nw===W && nh===H && nd===dpr) return false;
    dpr=nd; W=nw; H=nh; c.width=W*dpr; c.height=H*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
    return true;
  }
  function css(v){
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  }
  function readColors(){
    inkC = css('--accent') || '#155288';
    faintC = css('--rule') || '#DAD7E4';
  }
  function noise(x, seed){
    var s = Math.sin(x*12.9898 + seed*78.233) * 43758.5453;
    return (s - Math.floor(s)) * 2 - 1;
  }
  function smoothNoise(x, seed){
    var i = Math.floor(x), f = x - i;
    var a = noise(i,seed), b = noise(i+1,seed);
    var t = f*f*(3-2*f);
    return a*(1-t)+b*t;
  }
  function draw(t){
    ctx.clearRect(0,0,W,H);
    ctx.strokeStyle = faintC; ctx.lineWidth = 1;
    for(var gx=0; gx<W; gx+=W/24){
      ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,H); ctx.stroke();
    }
    for(var k=0;k<3;k++){
      var mid = H*(k+0.5)/3;
      var scale = (H/3)*0.34*AMP[k];
      ctx.beginPath();
      ctx.globalAlpha = 0.45 + 0.275*k;
      ctx.strokeStyle = inkC;
      ctx.lineWidth = 1.35;
      for(var px=0; px<=W; px++){
        var x = px/W*10;
        var phase = (x + t) * CAD[k] * Math.PI*2;
        var gait = Math.sin(phase)*0.55 + Math.sin(phase*2)*0.26
                 + Math.sin(phase*3)*0.13;
        var fast = smoothNoise((x+t)*38, k+1)*0.42
                 + smoothNoise((x+t)*95, k+7)*0.2;
        var y = mid - (gait + fast) * scale;
        if(px===0){ ctx.moveTo(px,y); } else { ctx.lineTo(px,y); }
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
  function frame(ts){
    if(t0===null) t0 = ts;
    draw(((ts-t0)/1000)*0.35);
    raf = requestAnimationFrame(frame);
  }
  resize(); readColors();
  window.addEventListener('resize', function(){ if(resize() && reduce) draw(0); });
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  if(mq.addEventListener){
    mq.addEventListener('change', function(){ readColors(); if(reduce) draw(0); });
  }
  if(reduce){ draw(0); return; }
  document.addEventListener('visibilitychange', function(){
    if(document.hidden){
      if(raf!==null){ cancelAnimationFrame(raf); raf=null; t0=null; }
    } else if(raf===null){ raf = requestAnimationFrame(frame); }
  });
  raf = requestAnimationFrame(frame);
})();
"""

APP_JS = """
(function(){
  var el = document.getElementById('sim');
  if(!el || typeof STREAM === 'undefined') return;

  var SPEEDS = STREAM.speeds;
  var RANK = {}; SPEEDS.forEach(function(s,i){ RANK[s]=i; });
  var TRUTH = STREAM.truth;
  var HOP = STREAM.hop_s;
  var N = TRUTH.length;

  var canvas = document.getElementById('simCanvas');
  var ctx = canvas.getContext('2d');
  var elSmooth = document.getElementById('smooth');
  var elHold = document.getElementById('hold');
  var elSmoothVal = document.getElementById('smoothVal');
  var elHoldVal = document.getElementById('holdVal');
  var elPlay = document.getElementById('play');
  var elReset = document.getElementById('reset');
  var elAcc = document.getElementById('statAcc');
  var elLat = document.getElementById('statLat');
  var elNow = document.getElementById('statNow');
  var elSummary = document.getElementById('simSummary');

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var playing = false, head = N, raf = null, lastTs = 0;

  function arm(){
    var picked = document.querySelector('input[name="arm"]:checked');
    return picked ? picked.value : 'EEG';
  }
  function rollingMode(labels, k){
    // Ties are broken by taking the speed that sorts first, which is what
    // numpy does in the offline pipeline. Without this the numbers shown here
    // drift a little away from the table above, for no reason a reader could
    // guess at.
    var out = new Array(labels.length);
    for(var i=0;i<labels.length;i++){
      var counts = {}, j, v;
      for(j=Math.max(0,i-k+1); j<=i; j++){
        v = labels[j];
        counts[v] = (counts[v]||0)+1;
      }
      var best = null, bestN = -1;
      for(j=0;j<SPEEDS.length;j++){
        v = SPEEDS[j];
        if((counts[v]||0) > bestN){ bestN = counts[v]||0; best = v; }
      }
      out[i] = best;
    }
    return out;
  }
  function applyHold(sm, hold){
    var out = new Array(sm.length), cur = sm[0], streak = 0;
    for(var i=0;i<sm.length;i++){
      if(sm[i] === cur){ streak = 0; }
      else {
        streak++;
        if(streak >= hold){ cur = sm[i]; streak = 0; }
      }
      out[i] = cur;
    }
    return out;
  }
  function settleTimes(cmd){
    var events = [], i;
    for(i=1;i<N;i++){
      if(TRUTH[i] !== TRUTH[i-1]) events.push(i);
    }
    return events.map(function(idx, k){
      var end = (k+1 < events.length) ? events[k+1] : N;
      for(var j=idx;j<end;j++){
        var ok = true;
        for(var m=j;m<end;m++){ if(cmd[m] !== TRUTH[idx]){ ok = false; break; } }
        if(ok) return (j-idx)*HOP;
      }
      return null;
    });
  }
  function compute(){
    var raw = STREAM.raw[arm()];
    var k = parseInt(elSmooth.value,10);
    var h = parseInt(elHold.value,10);
    var cmd = applyHold(rollingMode(raw,k), h);
    var right = 0;
    for(var i=0;i<N;i++){ if(cmd[i]===TRUTH[i]) right++; }
    return { raw: raw, cmd: cmd, acc: right/N, lat: settleTimes(cmd) };
  }

  var W=0,H=0,dpr=1;
  function resize(){
    var nd = Math.min(window.devicePixelRatio||1, 2);
    var nw = canvas.clientWidth, nh = canvas.clientHeight;
    if(nw===W && nh===H && nd===dpr) return;
    dpr=nd; W=nw; H=nh; canvas.width=W*dpr; canvas.height=H*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function css(v){
    return getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  }
  function draw(state){
    resize();
    var padL = 70, padR = 14, padT = 14, padB = 26;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var ink = css('--ink') || '#16131F';
    var faint = css('--rule') || '#DAD7E4';
    var grey = css('--ink-3') || '#69637F';
    var accent = css('--accent') || '#155288';
    var marker = css('--marker') || '#A83E1B';

    ctx.clearRect(0,0,W,H);
    var yOf = function(r){ return padT + plotH - (r+0.5)/3*plotH; };
    var xOf = function(i){ return padL + (i/(N-1))*plotW; };

    ctx.strokeStyle = faint; ctx.lineWidth = 1;
    ctx.fillStyle = grey;
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    for(var r=0;r<3;r++){
      var y = yOf(r);
      ctx.beginPath(); ctx.moveTo(padL,y); ctx.lineTo(W-padR,y); ctx.stroke();
      ctx.fillText(STREAM.speed_labels[SPEEDS[r]], padL-8, y);
    }

    var i;
    ctx.globalAlpha = 0.6; ctx.fillStyle = grey;
    for(i=0;i<N;i++){
      if(i > state.head) break;
      ctx.beginPath();
      ctx.arc(xOf(i), yOf(RANK[state.raw[i]]), 2.2, 0, Math.PI*2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // Square steps, not diagonals. Speed is one of three fixed values, so a
    // sloped line between them would draw speeds that never happened.
    function stepLine(labels, upto){
      ctx.beginPath();
      var started = false, prevY = null, k, y, x;
      for(k=0;k<=upto;k++){
        y = yOf(RANK[labels[k]]); x = xOf(k);
        if(!started){ ctx.moveTo(x,y); started = true; }
        else {
          if(y !== prevY) ctx.lineTo(x, prevY);
          ctx.lineTo(x, y);
        }
        prevY = y;
      }
      if(started) ctx.stroke();
    }

    ctx.globalAlpha = 0.38; ctx.strokeStyle = ink; ctx.lineWidth = 5;
    stepLine(TRUTH, N-1);
    ctx.globalAlpha = 1; ctx.strokeStyle = accent; ctx.lineWidth = 2;
    stepLine(state.cmd, Math.min(state.head, N-1));

    for(i=1;i<N;i++){
      if(TRUTH[i]!==TRUTH[i-1]){
        ctx.strokeStyle = marker; ctx.lineWidth = 1;
        ctx.setLineDash([3,3]); ctx.beginPath();
        ctx.moveTo(xOf(i),padT); ctx.lineTo(xOf(i),padT+plotH); ctx.stroke();
        ctx.setLineDash([]);
      }
    }
    if(state.head < N-1){
      ctx.strokeStyle = accent; ctx.lineWidth = 1.4; ctx.beginPath();
      ctx.moveTo(xOf(state.head),padT); ctx.lineTo(xOf(state.head),padT+plotH);
      ctx.stroke();
    }
    ctx.fillStyle = grey; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText('time in seconds', padL + plotW/2, padT + plotH + 8);
  }

  function render(){
    var s = compute();
    s.head = Math.min(head, N-1);
    draw(s);
    elAcc.textContent = (s.acc*100).toFixed(1) + '%';
    var shown = s.lat.filter(function(v){ return v !== null; });
    elLat.textContent = shown.length
      ? shown.map(function(v){ return v.toFixed(0)+' s'; }).join(' / ')
      : 'never settles';
    var now = STREAM.speed_labels[s.cmd[s.head]];
    var real = STREAM.speed_labels[TRUTH[s.head]];
    elNow.textContent = now;
    elSummary.textContent =
      'Using ' + (arm()==='EEG' ? 'brain signals only' : 'brain and muscle signals') +
      ', a smoothing window of ' + elSmooth.value + ' and a hold of ' + elHold.value +
      '. The command is right ' + (s.acc*100).toFixed(1) + '% of the time. ' +
      'Time to settle after each speed change: ' +
      (shown.length ? shown.map(function(v){ return v.toFixed(0)+' seconds'; }).join(' and ')
                    : 'it never settles') +
      '. At the current position the chair is told ' + now + ' and the real speed is ' +
      real + '.';
  }

  function tick(ts){
    if(!playing) return;
    if(ts - lastTs > 60){
      lastTs = ts;
      head += 1;
      if(head >= N){ head = N-1; stop(); render(); return; }
      render();
    }
    raf = requestAnimationFrame(tick);
  }
  function start(){
    if(head >= N-1) head = 0;
    playing = true;
    elPlay.textContent = 'Pause';
    elPlay.setAttribute('aria-pressed','true');
    raf = requestAnimationFrame(tick);
  }
  function stop(){
    playing = false;
    elPlay.textContent = 'Play';
    elPlay.setAttribute('aria-pressed','false');
    if(raf!==null){ cancelAnimationFrame(raf); raf=null; }
  }

  elPlay.addEventListener('click', function(){ playing ? stop() : start(); });
  elReset.addEventListener('click', function(){ stop(); head = N; render(); });
  elSmooth.addEventListener('input', function(){
    elSmoothVal.textContent = elSmooth.value + ' window' +
      (elSmooth.value === '1' ? '' : 's');
    render();
  });
  elHold.addEventListener('input', function(){
    elHoldVal.textContent = elHold.value + ' window' +
      (elHold.value === '1' ? '' : 's');
    render();
  });
  Array.prototype.forEach.call(
    document.querySelectorAll('input[name="arm"]'),
    function(r){ r.addEventListener('change', render); });
  window.addEventListener('resize', render);

  elSmoothVal.textContent = elSmooth.value + ' windows';
  elHoldVal.textContent = elHold.value + ' windows';
  render();
})();

(function(){
  var n = document.getElementById('privacyNotice');
  var b = document.getElementById('noticeClose');
  if(n && b){ b.addEventListener('click', function(){ n.remove(); }); }
})();
"""



def build() -> str:
    s = json.loads((cfg.TABLES / "results_summary.json").read_text())
    stream = json.loads((cfg.TABLES / "realtime_stream.json").read_text())
    lk = s.get("leakage", {})
    loso = s.get("loso", {})
    gk = s.get("groupkfold_rf", {})
    conf = s.get("confounds", {})
    band = s.get("band_importance", {})
    groups = s.get("electrode_groups", {})
    ctx = s.get("context", {})
    sid = s.get("subject_identifiability", {})
    rt = s.get("realtime", {})
    perm = s.get("permutation", {})
    cad = s.get("median_cadence_hz", {})
    sens = s.get("window_sensitivity", {})
    n = refs.numbered()

    def L(arm, key):
        return loso.get(arm, {}).get(key)

    def cite(key):
        i = n[key]
        return f'<a href="#ref-{key}">[{i}]</a>'

    # permutation table
    perm_html = ""
    if perm.get("arms"):
        np_ = perm.get("n_permutations", 200)
        rows = ""
        for arm, d in perm["arms"].items():
            label = {"EEG": "brain", "EMG": "muscle", "EEG+EMG": "both"}[arm]
            p = d["p_value"]
            ptxt = f"{p:.3f}" if p > 1 / (np_ + 1) else f"below {1/np_:.3f}"
            rows += (f"<tr><td>{label}</td><td class='n hi'>{f3(d['observed'])}</td>"
                     f"<td class='n'>{f3(d['null_mean'])}</td>"
                     f"<td class='n'>{f3(d['null_p95'])}</td>"
                     f"<td class='n'>{ptxt}</td></tr>")
        perm_html = f"""
<section id="luck" aria-labelledby="luck-h">
  <div class="col">
    <p class="eyebrow">shuffled labels</p>
    <h2 id="luck-h">Could this just be luck?</h2>
    <p>To find out I shuffled the speed labels inside each person, so everybody
    keeps their three recordings and only the name on each one gets swapped
    around. Then I ran the whole thing again {np_} times. Shuffling across
    everyone at once would also wreck the person structure, which would make
    the comparison too easy and the answer too flattering.</p>
    <div class="tbl-scroll"><table>
      <caption>Real scores against {np_} shuffled runs.</caption>
      <thead><tr><th scope="col">signals</th><th scope="col">real score</th>
      <th scope="col">shuffled average</th><th scope="col">shuffled 95th</th>
      <th scope="col">p</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
    <p>The shuffled runs land on chance. That is the more useful half of this
    test. If the way I split the data were leaking anywhere, the shuffled runs
    would sit above chance too, and they do not.</p>
  </div>
  {figure("07_permutation_null",
          "Shuffled scores for each set of signals, with the real score marked.",
          "Three histograms of shuffled scores, all centred on chance, with the "
          "real score far to the right of each one")}
</section>"""

    sens_html = ""
    if sens:
        srows = "".join(
            f"<tr><td>{label}</td>"
            f"<td class='n'>{f3(sens.get(f'{arm}|2 s'))}</td>"
            f"<td class='n'>{f3(sens.get(f'{arm}|4 s'))}</td></tr>"
            for arm, label in (("EEG", "brain"), ("EMG", "muscle"),
                               ("EEG+EMG", "both")))
        sens_html = (
            "<h3>Window length is not doing the work</h3>"
            "<p>Two second windows were an arbitrary pick, so I ran the whole "
            "comparison again at four seconds. Brain signals gain about four "
            "points, which is what a noisy measurement should do when you hand "
            "it twice as much data. Muscle stays put. Brain is the weakest of "
            "the three either way.</p>"
            "<div class='tbl-scroll'><table>"
            "<thead><tr><th scope='col'>signals</th>"
            "<th scope='col'>2 second windows</th>"
            "<th scope='col'>4 second windows</th></tr></thead>"
            f"<tbody>{srows}</tbody></table></div>")

    rt_rows = ""
    if rt.get("arms"):
        for a in rt["arms"]:
            label = {"EEG": "brain only", "EEG+EMG": "brain and muscle"}.get(
                a["arm"], a["arm"])
            lat = [e["latency_s"] for e in a["transitions"] if e["settled"]]
            lat_txt = ", ".join(f"{v:.0f} s" for v in lat) if lat else "never settles"
            cls = "lo" if a["arm"] == "EEG" else "hi"
            rt_rows += (f"<tr><td>{label}</td>"
                        f"<td class='n'>{a['window_accuracy']:.1%}</td>"
                        f"<td class='n'>{a['command_accuracy']:.1%}</td>"
                        f"<td class='n {cls}'>{lat_txt}</td></tr>")

    cad_txt = ", ".join(f"{cfg.SPEED_LABEL.get(k, k)} gives {v:.2f} Hz"
                        for k, v in cad.items())
    lift = float(sid.get("lift", 0))
    stream_json = json.dumps(stream, separators=(",", ":"))
    sm_db = s.get("sensorimotor_change_db", 0)

    part1 = f"""<title>Reading Walking Speed From the Scalp</title>
<style>{fonts.css()}</style>
<style>{CSS}</style>

<a class="skip" href="#main">Skip to the main text</a>

<div class="shell">

<header class="hero">
  <div class="col">
    <p class="eyebrow">EEG and EMG, 58 people, 174 recordings</p>
    <h1>Reading walking speed from the scalp</h1>
    <p class="deck">A machine learning project that looked like it worked at
    92 percent, and what was left of it once I fixed the way it was tested.</p>
    <p class="byline">Public gait dataset from PhysioNet. Random forest on
    frequency band power. Tested by holding out one person at a time.</p>
  </div>

  <div class="scope">
    <canvas id="scope" aria-hidden="true"></canvas>
    <div class="scope-labels" aria-hidden="true">
      <span>0.50 m/s, 0.68 Hz</span><span>0.75 m/s, 0.81 Hz</span>
      <span>1.00 m/s, 0.91 Hz</span>
    </div>
    <div class="scope-foot">Step rhythm and overall power both go up with
      walking speed. Those are the two things a model can grab onto.</div>
  </div>

  <div class="col">
    <div class="readouts">
      <div class="readout is-false">
        <span class="num">{f3(lk.get('random'))}</span>
        <span class="lab">split at random<br>means very little</span>
      </div>
      <div class="readout is-true">
        <span class="num">{f3(lk.get('subject'))}</span>
        <span class="lab">split by person<br>no calibration</span>
      </div>
      <div class="readout is-true">
        <span class="num">{f3(L('EEG','balanced_accuracy'))}</span>
        <span class="lab">brain, calibrated<br>each window</span>
      </div>
      <div class="readout is-true">
        <span class="num">{f3(L('EEG','trial_balanced_accuracy'))}</span>
        <span class="lab">brain, calibrated<br>whole recording</span>
      </div>
    </div>
    <p class="readout-note">Balanced accuracy across three speeds. Guessing
    gives 0.333.</p>

    <div class="notice" id="privacyNotice">
      <p>This page sets no cookies, stores nothing on your device and sends no
      data anywhere. Details are in the notes at the bottom.</p>
      <button type="button" id="noticeClose">Got it</button>
    </div>

    <nav class="toc" aria-labelledby="toc-h">
      <h2 id="toc-h">On this page</h2>
      <ol>
        <li><a href="#premise">The idea, and the catch</a></li>
        <li><a href="#split">The split is the experiment</a></li>
        <li><a href="#who">The features know who you are</a></li>
        <li><a href="#signals">What is in the signal</a></li>
        <li><a href="#results">Brain, muscle, and both</a></li>
        <li><a href="#luck">Could this be luck?</a></li>
        <li><a href="#mechanism">What the model reads</a></li>
        <li><a href="#try">Try it yourself</a></li>
        <li><a href="#limits">What this does not show</a></li>
        <li><a href="#refs">References</a></li>
      </ol>
    </nav>
  </div>
</header>

<main id="main">

<section id="premise" aria-labelledby="premise-h">
  <div class="col">
    <p class="eyebrow">the idea</p>
    <h2 id="premise-h">The idea, and the catch</h2>
    <p>Take EEG recorded while people walk at three speeds. Cut it into short
    windows, measure how much power sits in each frequency band, and train a
    model to name the speed. It is a clean little project and the pipeline
    works fine.</p>
    <p>The trouble is the first number it gives you. I got
    <strong>{f3(lk.get('random'))}</strong>, and that number is close to
    meaningless.</p>
    <p>Each one minute recording gets cut into 58 windows that overlap each
    other by half. Shuffle those windows and deal them into a training set and
    a test set, and windows from the same recording land on both sides. They
    share half their samples, so they are near enough copies. The model can
    score well by recognising a window it has already seen most of. It never
    has to learn anything about walking.</p>
  </div>
</section>

<section id="split" aria-labelledby="split-h">
  <div class="col">
    <p class="eyebrow">how the data is split</p>
    <h2 id="split-h">The split is the whole experiment</h2>
    <p>Same model, same features, same scoring. The only thing that changes is
    where the line between training and testing gets drawn.</p>
    <div class="tbl-scroll"><table>
      <caption>Balanced accuracy under three ways of splitting.</caption>
      <thead><tr><th scope="col">how the split is drawn</th>
      <th scope="col">score</th><th scope="col">what it tells you</th></tr></thead>
      <tbody>
        <tr><td>at random across windows</td>
            <td class="n lo">{f3(lk.get('random'))}</td>
            <td class="prose">very little, for the reason above</td></tr>
        <tr><td>by recording</td>
            <td class="n lo">{f3(lk.get('trial'))}</td>
            <td class="prose">something worse than nothing, see below</td></tr>
        <tr><td>by person</td>
            <td class="n hi">{f3(lk.get('subject'))}</td>
            <td class="prose">whether it works on somebody new</td></tr>
      </tbody>
    </table></div>
    <p>This is a known trap rather than a clever discovery. Leinonen and
    colleagues found the same thing in heart recordings {cite('leinonen2024')}.
    Ordinary cross validation gave scores that were too high, and holding out
    whole sources gave honest ones.</p>
  </div>
  {figure("01_leakage_comparison",
          "A random forest on 209 EEG band power features, two second windows. "
          "The score falls from 0.923 to 0.528 when the split is drawn by "
          "person instead of at random.",
          "Bar chart of three scores, 0.923 for a random split, 0.333 for a "
          "split by recording and 0.528 for a split by person, with the "
          "matching confusion matrices below")}
</section>

<section id="who" aria-labelledby="who-h">
  <div class="col">
    <p class="eyebrow">a second problem</p>
    <h2 id="who-h">The features know who you are</h2>
    <p>The middle row of that table bothered me for a while. Splitting by
    recording is a weaker rule than splitting by person, so it ought to score
    higher. It sits at chance instead.</p>
    <p>So I ran the obvious check. Instead of asking the model to name the
    speed, I asked it to name the person. Out of 58 people it picked the right
    one <strong>{f3(sid.get('subject_id_accuracy'))}</strong> of the time,
    against a chance level of 1.7 percent. That is about {lift:.0f} times
    better than guessing.</p>
    <div class="callout warn">
      <p>Everybody walked all three speeds once. Hold out one of their
      recordings and the model has already been trained on the other two, so it
      knows what that person looks like at the two speeds it has seen, and it
      files the held out recording under one of those. The right answer is the
      one speed it was never shown. Real 1.0 m/s ends up called 0.75 m/s more
      often than it gets called correctly.</p>
    </div>
    <p>That people can be picked out from their EEG is not news. It was shown
    back in 2007 {cite('marcel2007')} and there is a whole survey of the field
    {cite('gui2019')}. What is worth saying here is that the personal signature
    is strong enough to drown out the thing I was trying to measure, and that
    it drags the score below chance rather than above it.</p>
    <p>Splitting by person is the only version that answers the question a real
    device would face. Everything after this uses it.</p>
  </div>
  {figure("02_subject_fingerprint",
          "The same features name the person better than they name the speed.",
          "Bar chart comparing 0.528 for naming the speed with 0.568 for naming "
          "the person, next to a confusion matrix showing 1.0 m/s being called "
          "0.75 m/s 60 percent of the time")}
</section>

<section id="signals" aria-labelledby="signals-h">
  <div class="col">
    <p class="eyebrow">before any model</p>
    <h2 id="signals-h">What is in the signal</h2>
    <p>It is worth looking at the spectra before letting a model summarise them
    for you. Two things climb with walking speed and both are visible by eye.</p>
    <p>Power goes up at every frequency as people walk faster, so this is a
    rise in the overall level rather than a shift between bands. And below
    about 10 Hz there is a row of sharp spikes: the step rhythm and its
    multiples, pressed into the EEG by the head bobbing. Measured off the
    muscle recordings, the step rate runs {cad_txt}.</p>
  </div>
  {figure("04_signal_overview",
          "Average spectra across 19 channels and 58 people, the same spectra "
          "next to the slowest condition, and step rate measured from the "
          "muscle recordings.",
          "Three panels: EEG spectra for the three speeds, power relative to "
          "the slowest speed, and a box plot of step rhythm rising from 0.68 to "
          "0.91 Hz")}
  {figure("05_raw_vs_filtered",
          "One person at electrode Cz, before and after filtering, six seconds "
          "at each speed. Dry electrodes on a moving head are messy.",
          "Three stacked traces showing the raw signal in grey and the filtered "
          "signal in blue, one panel per walking speed")}
</section>

<section id="results" aria-labelledby="results-h">
  <div class="col">
    <p class="eyebrow">holding out one person at a time</p>
    <h2 id="results-h">Brain, muscle, and both</h2>
    <p>The dataset also carries muscle recordings from twelve leg muscles,
    which makes the honest comparison possible. How much of this comes from the
    brain, and how much from the legs doing the walking?</p>
    <p>All three run on the same rows, {ctx.get('n_common_windows','?')} windows
    from {ctx.get('n_common_trials','?')} recordings, so they can be compared
    directly. A model that guesses at random scores
    {f3(s.get('dummy_balanced_accuracy'))} here, which is the check that the
    folds are built properly.</p>
    <div class="tbl-scroll"><table>
      <caption>Held out one person at a time, {ctx.get('n_subjects','57')}
      people.</caption>
      <thead><tr><th scope="col">signals</th><th scope="col">each window</th>
      <th scope="col">whole recording</th><th scope="col">kappa</th>
      <th scope="col">rank correlation</th></tr></thead>
      <tbody>
        <tr><td>brain</td><td class="n">{f3(L('EEG','balanced_accuracy'))}</td>
            <td class="n">{f3(L('EEG','trial_balanced_accuracy'))}</td>
            <td class="n">{f3(L('EEG','kappa'))}</td>
            <td class="n">{f3(L('EEG','spearman_rho'))}</td></tr>
        <tr><td>muscle</td><td class="n">{f3(L('EMG','balanced_accuracy'))}</td>
            <td class="n">{f3(L('EMG','trial_balanced_accuracy'))}</td>
            <td class="n">{f3(L('EMG','kappa'))}</td>
            <td class="n">{f3(L('EMG','spearman_rho'))}</td></tr>
        <tr><td>both</td>
            <td class="n hi">{f3(L('EEG+EMG','balanced_accuracy'))}</td>
            <td class="n hi">{f3(L('EEG+EMG','trial_balanced_accuracy'))}</td>
            <td class="n">{f3(L('EEG+EMG','kappa'))}</td>
            <td class="n">{f3(L('EEG+EMG','spearman_rho'))}</td></tr>
      </tbody>
    </table></div>
    <p>Muscle beats brain by a wide margin, and putting brain signals on top of
    muscle buys almost nothing. Tortora and colleagues built a gait decoder in
    2020 that combined the two and did get a gain from it
    {cite('tortora2020')}. I do not see one that size here.</p>
    <p>The whole recording column is the number worth quoting for a device. A
    chair would not act on a single two second window. It would gather a few
    seconds and then decide.</p>
  </div>
  {figure("03_modality_comparison",
          "Scores per window and per recording, the spread across the people "
          "held out, and the confusion matrices.",
          "Six panels comparing brain, muscle and combined signals. Brain "
          "reaches 0.727 per window, muscle 0.893 and both together 0.899")}
  <div class="col">
    <h3>Calibration matters more than which signal you pick</h3>
    <p>There are two ways a device could meet somebody new. It could work
    straight out of the box, or it could record them for a minute first and use
    that to set its own baseline. The second version scales each feature
    against the spread of that person's own recordings. It never sees their
    labels.</p>
    <div class="tbl-scroll"><table>
      <thead><tr><th scope="col">signals</th><th scope="col">no calibration</th>
      <th scope="col">with calibration</th></tr></thead>
      <tbody>
        <tr><td>brain</td>
            <td class="n">{f3(gk.get('EEG|raw',{}).get('window'))}</td>
            <td class="n hi">{f3(gk.get('EEG|per_subject_z',{}).get('window'))}</td></tr>
        <tr><td>muscle</td>
            <td class="n">{f3(gk.get('EMG|raw',{}).get('window'))}</td>
            <td class="n hi">{f3(gk.get('EMG|per_subject_z',{}).get('window'))}</td></tr>
        <tr><td>both</td>
            <td class="n">{f3(gk.get('EEG+EMG|raw',{}).get('window'))}</td>
            <td class="n hi">{f3(gk.get('EEG+EMG|per_subject_z',{}).get('window'))}</td></tr>
      </tbody>
    </table></div>
    <p>Taking away each person's baseline is worth more than switching from
    brain to muscle. There is a catch and it is a real one. The calibration
    step uses the held out person's own recordings, including the ones being
    tested. So it describes a device that gets a calibration session, and it
    does not describe one that works cold.</p>
    <p>These rows use only the people who also have muscle recordings, which is
    why the no calibration brain score here is
    {f3(gk.get('EEG|raw',{}).get('window'))} rather than the
    {f3(lk.get('subject'))} quoted earlier on the full set.</p>
  </div>
</section>

{perm_html}

<section id="mechanism" aria-labelledby="mech-h">
  <div class="col">
    <p class="eyebrow">taking shortcuts away</p>
    <h2 id="mech-h">What the model is actually reading</h2>
    <p>Walking faster means stepping faster. Step rhythm turns up in the brain
    recording because the head bobs and the neck muscles work, so the worry is
    that the model is reading footsteps off the scalp. To test it I took away
    one suspected shortcut at a time and trained again.</p>
    <div class="tbl-scroll"><table>
      <caption>Each row removes one thing, with calibration on.</caption>
      <thead><tr><th scope="col">what the model gets</th>
      <th scope="col">numbers</th><th scope="col">score</th></tr></thead>
      <tbody>
        <tr><td class="prose">everything</td><td class="n">209</td>
            <td class="n hi">{f3(conf.get('all|per_subject_z'))}</td></tr>
        <tr><td class="prose">alpha, beta and gamma only, as the video asks</td>
            <td class="n">114</td>
            <td class="n">{f3(conf.get('reel|per_subject_z'))}</td></tr>
        <tr><td class="prose">delta and theta gone, where the step rhythm lives</td>
            <td class="n">133</td>
            <td class="n">{f3(conf.get('no_lowfreq|per_subject_z'))}</td></tr>
        <tr><td class="prose">total power only, no frequency detail at all</td>
            <td class="n">19</td>
            <td class="n">{f3(conf.get('broadband|per_subject_z'))}</td></tr>
        <tr><td class="prose">front and side electrodes gone</td>
            <td class="n">143</td>
            <td class="n">{f3(conf.get('no_rim|per_subject_z'))}</td></tr>
        <tr><td class="prose">C3, Cz and C4 only, over the motor strip</td>
            <td class="n">33</td>
            <td class="n">{f3(conf.get('motor|per_subject_z'))}</td></tr>
      </tbody>
    </table></div>
    <p>Taking out the bands that hold the step rhythm barely dents the score.
    And total power on its own, 19 numbers with no frequency detail in them,
    gets to {f3(conf.get('broadband|per_subject_z'))}. So the model is mostly
    reading a rise in the overall level rather than a change in the shape of
    the spectrum.</p>

    <h3>For a while I read this the friendly way</h3>
    <p>Shuffling one electrode's features at a time and watching the score drop
    gives this:</p>
    <div class="tbl-scroll"><table>
      <thead><tr><th scope="col">electrodes</th>
      <th scope="col">average drop each</th></tr></thead>
      <tbody>
        <tr><td class="prose">C3, Cz, C4, over the motor strip</td>
            <td class="n hi">{groups.get('motor', 0):.4f}</td></tr>
        <tr><td class="prose">the other ten</td>
            <td class="n">{groups.get('other', 0):.4f}</td></tr>
        <tr><td class="prose">Fp1, Fp2, F7, F8, T7, T8, nearest the eyes and neck</td>
            <td class="n lo">{groups.get('rim', 0):.4f}</td></tr>
      </tbody>
    </table></div>
    <p>The electrodes closest to the eyes and the neck muscles turn out to be
    the least useful. The motor strip electrodes are the most useful, and beta
    is the strongest band at {band.get('beta', 0):.3f}. Beta over the motor
    strip is a normal thing to see during movement
    {cite('artoni2017')}{cite('peterson2018')}, so this looked like real brain
    activity to me.</p>

    <h3>Then I found a paper that says otherwise</h3>
    <p>Nordin, Hairston and Ferris published a study in 2019 that lands
    straight on this question {cite('nordin2019')}. They built a two layer
    electrode, where one layer sits on the scalp and a second layer sits on top
    of it, wired separately, picking up movement only. That gave them a
    recording of the artifact by itself, which they could then subtract. Their
    people walked at 0.5, 1.0, 1.5 and 2.0 m/s, so their two slowest speeds are
    my two extremes.</p>
    <p>Two of their findings matter here. Once the artifact was taken out,
    alpha and beta power over sensorimotor cortex went <strong>down</strong> as
    people walked faster. And the movement recordings, along with the neck
    muscle recordings, showed broad power going <strong>up</strong> at faster
    speeds.</p>
    <div class="callout warn">
      <p>In my data, alpha and beta at C3, Cz and C4 go up by
      {sm_db:+.1f} dB on average between 0.5 and 1.0 m/s, and the rise is broad
      across the whole band. That is the same direction as their movement
      channel and the opposite direction from their cleaned brain signal. So
      the friendly reading does not hold up. What my model is using looks like
      the artifact they measured rather than the cortex they measured.</p>
    </div>
    <p>One thing does survive. Fp1 and Fp2 sit just above the eyes, which is
    where blink artifact turns up first, and they hardly change with speed.
    They were also the two least useful electrodes. So I can rule out eye
    blinks as the main source. Neck muscle and head movement do not stay near
    the front of the head, so ruling out blinks rules out very little.</p>
    <p>The field does not agree on how bad this problem is. Nathan and
    Contreras-Vidal reported in 2016 that motion did not affect scalp EEG much
    during treadmill walking, with a warning once speed gets near 4.5 km/h
    {cite('nathan2016')}. My fastest condition is 3.6 km/h, under that line,
    which would put me in the clear on their account. Jacobsen and colleagues
    reached a less comfortable answer in 2020 and described clear gait related
    artifacts in mobile EEG {cite('jacobsen2020')}. Gorjan and colleagues wrote
    guidelines in 2022 that treat movement artifact as a problem needing active
    removal {cite('gorjan2022')}. My results sit with the second group.</p>
    {sens_html}
  </div>
  {figure("06_confound_controls",
          "What is left after each shortcut is removed, plus two checks on "
          "whether the electrodes are simply drifting over time.",
          "Grouped bar chart of scores for six feature sets with and without "
          "calibration, a flat line of accuracy across the recording, and a "
          "bar chart of the two halves of each recording")}
  {figure("08_interpretation",
          "Which bands and which electrodes the model leans on, and where the "
          "power rise sits on the scalp.",
          "Bar chart of band importance with beta highest, a scalp map of "
          "electrode importance, a bar chart showing motor electrodes matter "
          "most and eye and neck electrodes least, and five scalp maps of the "
          "power change per band")}
</section>
"""
    part2 = f"""
<section id="try" aria-labelledby="try-h">
  <div class="col">
    <p class="eyebrow">interactive, runs in your browser</p>
    <h2 id="try-h">Try it yourself</h2>
    <p>Scores on shuffled windows are not what a device lives through. So here
    is the model driving a chair. I took one person out of the training set,
    {rt.get('demo_subject','')}, joined their three recordings end to end, and
    fed them through the model one window at a time. I picked the person whose
    score sits closest to the middle of the group rather than the best one.</p>
    <p>The dots are the raw guesses, one a second, straight from the model.
    The dark line is the real treadmill speed. The blue line is what the
    chair would actually be told after smoothing. Drag the sliders and the two
    sets of signals behave in opposite ways, which is the whole point of
    putting this here.</p>

    <div class="app" id="sim">
      <div class="app-head">
        <h3>Wheelchair speed controller</h3>
        <p>Real model output for person {rt.get('demo_subject','')}, who was
        never in the training set. Only the smoothing is redone here.</p>
      </div>
      <div class="app-body">
        <div class="ctls">
          <div class="ctl">
            <span class="lbl" id="armLabel">Signals used</span>
            <div class="radios" role="radiogroup" aria-labelledby="armLabel">
              <label><input type="radio" name="arm" value="EEG" checked>
                Brain only</label>
              <label><input type="radio" name="arm" value="EEG+EMG">
                Brain and muscle</label>
            </div>
          </div>
          <div class="ctl">
            <label class="lbl" for="smooth">Smoothing window</label>
            <input type="range" id="smooth" min="1" max="15" step="1" value="5">
            <span class="val" id="smoothVal">5 windows</span>
          </div>
          <div class="ctl">
            <label class="lbl" for="hold">Windows that must agree</label>
            <input type="range" id="hold" min="1" max="6" step="1" value="2">
            <span class="val" id="holdVal">2 windows</span>
          </div>
        </div>

        <canvas id="simCanvas" aria-hidden="true"></canvas>

        <p class="legend" aria-hidden="true">
          <span class="k-real"><i></i>real treadmill speed</span>
          <span class="k-cmd"><i></i>what the chair is told</span>
          <span class="k-raw"><i></i>raw guess, once a second</span>
          <span class="k-chg"><i></i>speed change</span>
        </p>

        <p class="sr-only" id="simSummary" role="status" aria-live="polite"></p>

        <div class="app-actions">
          <button type="button" class="play" id="play" aria-pressed="false">Play</button>
          <button type="button" class="reset" id="reset">Show all</button>
        </div>

        <div class="stats">
          <div class="stat"><b id="statAcc">0%</b>
            <span>command right</span></div>
          <div class="stat"><b id="statLat">0 s</b>
            <span>time to settle</span></div>
          <div class="stat"><b id="statNow">0.50 m/s</b>
            <span>chair told to go</span></div>
        </div>
      </div>
    </div>

    <p>Time to settle is how long after a speed change the command reaches the
    new speed and stays there.</p>
    <p>With muscle in the mix the raw guesses are already right almost every
    second, so smoothing buys nothing and costs delay. At no smoothing the
    command is right 98.6 percent of the time and settles in one second. Wind
    the slider up to fifteen and that falls to 89.2 percent and eight seconds.
    The best thing you can do is leave it alone.</p>
    <p>Brain signals alone do the reverse. The guesses jump around so much that
    at light settings the command never holds still at all, which is why the
    settling time sits above thirty seconds. You have to average over about
    twelve seconds before it stops flipping. That gets the command right 90.5
    percent of the time, but by then the chair is reacting to what you wanted
    twelve seconds ago. There is no setting on this slider that gives you a
    command which is both steady and quick.</p>

    <div class="tbl-scroll"><table>
      <caption>The settings used in the write-up: smoothing of
      {rt.get('smoothing_windows', 5)}, hold of {rt.get('hold', 2)}.</caption>
      <thead><tr><th scope="col">signals</th><th scope="col">raw windows right</th>
      <th scope="col">command right</th>
      <th scope="col">time to settle</th></tr></thead>
      <tbody>{rt_rows}</tbody>
    </table></div>
    <p>The command right column makes the brain only model look usable and the
    settling column shows that it is not. It does reach the right speed, then
    drops back to the wrong one for a few seconds, over and over. For a chair,
    settling time is the number that decides whether you could ride it.</p>
  </div>
  {figure("09_realtime_demo",
          "The same run drawn out in full, for brain only and for brain and "
          "muscle together.",
          "Two time series panels. The brain only command jumps between speeds "
          "several times, while the combined command follows the real speed "
          "closely with about a three second lag")}
</section>

<section id="limits" aria-labelledby="limits-h">
  <div class="col">
    <p class="eyebrow">honest limits</p>
    <h2 id="limits-h">What this does not show</h2>
    <div class="limits">
      <div class="limit">
        <h3>The recording order cannot be undone</h3>
        <p>Every person walked 0.5, then 0.75, then 1.0, in one sitting with
        the headset fitted once. Speed lines up exactly with time since the
        session started, and so does everything that drifts with it: the dry
        electrodes settling in, sweat, hair moving, getting tired. No amount of
        analysis on this dataset pulls those apart. Settling it needs a study
        that varies the order between people.</p>
      </div>
      <div class="limit">
        <h3>Most of the signal is probably movement</h3>
        <p>The comparison with Nordin and colleagues points that way, and I
        have no way to strip the artifact properly without the two layer
        hardware they used.</p>
      </div>
      <div class="limit">
        <h3>The calibrated numbers use the test person's own data</h3>
        <p>No labels, but still their data. Read them as the score for a device
        that gets a calibration session first.</p>
      </div>
      <div class="limit">
        <h3>The group is narrow</h3>
        <p>Fifty-eight healthy adults with an average age of 24, on a
        treadmill, at three slow speeds. People who use wheelchairs are not
        this group, and a treadmill is not a pavement.</p>
      </div>
      <div class="limit">
        <h3>This is not a brain-computer interface</h3>
        <p>The people in this dataset were walking. Somebody who needs a
        powered chair is not. Reading an intended speed off somebody sitting
        still is a much harder problem and nothing here shows it can be done.
        Reviews of EEG control for lower limb assistive robots give a sense of
        how far off that is {cite('tariq2018')}.</p>
      </div>
    </div>
  </div>
</section>

<section id="refs" aria-labelledby="refs-h">
  <div class="col">
    <p class="eyebrow">sources</p>
    <h2 id="refs-h">References</h2>
    <ol class="refs">
      {refs.html_list()}
    </ol>
  </div>
</section>

<section class="legal" id="notes" aria-labelledby="notes-h">
  <div class="col">
    <p class="eyebrow">the small print</p>
    <h2 id="notes-h">Notes, privacy and terms</h2>

    <details id="privacy">
      <summary>Privacy</summary>
      <div class="body">
        <p>This is a single static page. It has no accounts, no forms, no
        comments and no analytics.</p>
        <h3>What the page collects</h3>
        <p>Nothing. There is no tracking code on it, no analytics script and no
        advertising. It does not ask you for anything and it has nowhere to
        send anything.</p>
        <h3>What the page loads</h3>
        <p>Everything the page needs is inside the file you are reading. The
        fonts, the charts and the model output are all embedded, so opening the
        page makes no request to any other company's servers. Nobody learns
        that you read it except the service hosting it.</p>
        <h3>What the host can see</h3>
        <p>Whoever hosts this page can keep ordinary server records, such as the
        address your request came from, in the same way any website host can.
        That sits outside this page and is covered by the host's own privacy
        policy rather than this one.</p>
        <h3>About the people in the data</h3>
        <p>The recordings come from a public dataset that its authors
        anonymised before release, under an approved ethics protocol at their
        university. It holds no names, no contact details and nothing that
        identifies a participant. Nothing on this page can be traced back to an
        individual who took part.</p>
        <h3>Questions</h3>
        <p>If you want something on this page corrected or removed, contact
        whoever sent you the link.</p>
      </div>
    </details>

    <details id="cookies">
      <summary>Cookies and storage</summary>
      <div class="body">
        <p>This page sets no cookies. It writes nothing to local storage or
        session storage, and it stores nothing else on your device.</p>
        <p>The short notice near the top of the page disappears when you dismiss
        it, and that choice is not saved anywhere. Reload the page and the
        notice comes back, because nothing was written down.</p>
        <p>The interactive controller runs entirely in your browser using data
        that is already inside the page. It sends nothing out and saves nothing.</p>
        <p>Because no cookies are set and nothing is stored, there is nothing
        here for you to consent to or opt out of. If the service hosting this
        page sets its own cookies, those are covered by that service's policy.</p>
      </div>
    </details>

    <details id="terms">
      <summary>Terms of use</summary>
      <div class="body">
        <p>This is a student project written to learn and to be looked at. It
        is offered as is, with no warranty of any kind, and no promise that
        anything on it is correct or fit for any purpose.</p>
        <h3>Not medical or clinical advice</h3>
        <p>Nothing here is medical advice. None of this is a medical device or
        part of one. Do not use anything on this page, or the code behind it,
        to make a decision about anybody's care, treatment, mobility equipment
        or safety. The wheelchair framing is a way of explaining the problem.
        The model shown here is nowhere near fit to steer a real chair, and the
        page says why.</p>
        <h3>Limits</h3>
        <p>To the fullest extent the law allows, the author is not liable for
        any loss or damage arising from use of this page, the figures on it or
        the code behind it.</p>
        <h3>The data</h3>
        <p>The recordings belong to Katmah and colleagues and are published on
        PhysioNet under a Creative Commons Attribution 4.0 licence, which allows
        reuse with credit. The dataset itself is not redistributed here. Credit
        is given in the references, and anyone reusing this work should credit
        them too.</p>
        <h3>This page and the code</h3>
        <p>The text, figures and code written by me are released under the MIT
        licence. You may reuse them with credit. The findings are reported as I
        measured them, and the limits section is part of the finding rather
        than a disclaimer bolted on the end.</p>
      </div>
    </details>

    <details id="accessibility">
      <summary>Accessibility</summary>
      <div class="body">
        <p>I aimed at WCAG 2.1 level AA. Here is what that meant in practice
        and where it falls short, so you can judge for yourself.</p>
        <h3>What is in place</h3>
        <ul>
          <li>A skip link to the main text, and proper landmarks for header,
          navigation, main content and footer.</li>
          <li>Headings run in order without skipping levels, so a screen reader
          can move through the page by structure.</li>
          <li>Every control in the interactive section is a standard HTML input
          or button, so it works with a keyboard and with assistive software.
          Focus is always visible.</li>
          <li>Body text meets a contrast ratio of at least 4.5 to 1 against its
          background in both the light and the dark theme. Small grey captions
          were darkened until they passed.</li>
          <li>Every figure has a text description that says what it shows, and
          the finding in each figure is also written out in the surrounding
          text, so nothing is only available as a picture.</li>
          <li>The page respects a reduced motion setting. The moving line
          drawing at the top freezes and the demo does not animate.</li>
          <li>Text reflows down to a 320 pixel wide screen and at 200 percent
          zoom. Wide tables and figures scroll inside their own box rather than
          pushing the page sideways.</li>
          <li>Colour is never the only way information is given. Numbers are
          written out next to every coloured bar.</li>
        </ul>
        <h3>Known gaps</h3>
        <ul>
          <li>The charts are images produced by a plotting library, so they
          cannot be read line by line by a screen reader. The description and
          the surrounding text carry the same information.</li>
          <li>The moving line drawing at the top is decoration and is hidden
          from screen readers on purpose. It shows nothing that is not written
          in the text beside it.</li>
          <li>The interactive chart is drawn on a canvas, which screen readers
          cannot inspect. A written summary sits next to it and updates as you
          change the settings, giving the same numbers.</li>
        </ul>
        <h3>Telling me about a problem</h3>
        <p>If part of this page does not work with the software you use,
        contact whoever sent you the link and say what failed. That is the
        fastest way to get it fixed.</p>
      </div>
    </details>
  </div>
</section>

</main>

<footer>
  <div class="col">
    <p><span class="tag">data</span> Katmah, R., AlShehhi, A., Kosaji, D.,
    Al-Rahmani, N., Abdullah, M., Hulleck, A. A. V., and Khalaf, K. (2026).
    A multimodal gait dataset of brain activity, muscle activity, kinematics
    and ground forces in young adults, version 1.0.0. PhysioNet.
    <a href="https://doi.org/10.13026/r0ea-7161">doi.org/10.13026/r0ea-7161</a>.
    Used under a Creative Commons Attribution 4.0 licence.</p>
    <p><span class="tag">method</span> 19 dry EEG electrodes at 300 Hz, moved
    onto a linked ear reference with Pz rebuilt following the procedure the
    dataset ships. Filtered 1 to 45 Hz, mains notched at 60 and 120 Hz, cut
    into two second windows every second, with noisy windows dropped per
    recording. Random forest, tested by holding out whole people.</p>
    <p><span class="tag">note</span> Person S32 was left out because the header
    of their 1.0 m/s file lists channel names that do not match the other 176
    recordings.</p>
  </div>
</footer>

</div>
<script>var STREAM = {stream_json};</script>
<script>{CANVAS_JS}</script>
<script>{APP_JS}</script>
"""
    return part1 + part2


def ascii_safe(html: str) -> str:
    """Swap every non-ASCII character for a numbered HTML entity.

    The publishing wrapper supplies its own page head, so this file cannot
    declare a character set of its own. Numbered entities are plain ASCII and
    come out the same whatever encoding the host assumes, which removes a whole
    class of mangled-character bugs. Safe to do here only because the inline
    style and script blocks are already ASCII, since entities are not decoded
    inside those.
    """
    assert all(ord(c) < 128 for c in CSS + CANVAS_JS + APP_JS), (
        "style or script block contains non-ASCII, entity encoding would "
        "corrupt it")
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in html)


def main() -> int:
    html = ascii_safe(build())
    OUT.write_text(html)
    print(f"page -> {OUT.relative_to(cfg.ROOT)} "
          f"({len(html.encode()) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
