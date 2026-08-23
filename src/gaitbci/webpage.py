"""Shared CSS and JavaScript for both the full report page and the
lightweight landing page, so the two never drift apart.

Colour tokens are the same blue, green and amber palette used in every
matplotlib figure. Every text colour was checked to hold at least a 4.5:1
contrast ratio against its background in both the light and dark theme before
being picked.
"""
from __future__ import annotations

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


def ascii_safe(html: str) -> str:
    """Swap every non-ASCII character for a numbered HTML entity.

    A page published through the artifact wrapper supplies its own character
    set, and a page handed to a static host might not declare one either, so
    numbered entities are the one encoding that reads the same everywhere.
    Safe here only because CSS and JS stay pure ASCII, since entities are not
    decoded inside a style or script block.
    """
    assert all(ord(c) < 128 for c in CSS + CANVAS_JS + APP_JS), (
        "style or script block contains non-ASCII, entity encoding would "
        "corrupt it")
    return "".join(c if ord(c) < 128 else "&#%d;" % ord(c) for c in html)
