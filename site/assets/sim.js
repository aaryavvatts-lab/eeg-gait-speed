/* The wheelchair speed controller, ported from the generated page without changing the maths.
   STREAM is the real model output for person S44 (held out of training), embedded as JSON in the page. */
(function () {
  var el = document.getElementById('sim');
  var dataEl = document.getElementById('stream-data');
  if (!el || !dataEl) return;
  var STREAM = JSON.parse(dataEl.textContent);
  var SPEEDS = STREAM.speeds;
  var RANK = {}; SPEEDS.forEach(function (s, i) { RANK[s] = i; });
  var TRUTH = STREAM.truth, HOP = STREAM.hop_s, N = TRUTH.length;

  var canvas = document.getElementById('simCanvas'), ctx = canvas.getContext('2d');
  var elSmooth = document.getElementById('smooth'), elHold = document.getElementById('hold');
  var elSmoothVal = document.getElementById('smoothVal'), elHoldVal = document.getElementById('holdVal');
  var elPlay = document.getElementById('play'), elReset = document.getElementById('reset');
  var elAcc = document.getElementById('statAcc'), elLat = document.getElementById('statLat'), elNow = document.getElementById('statNow');
  var elSummary = document.getElementById('simSummary');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var playing = false, head = N, raf = null, lastTs = 0;

  function arm() { var p = document.querySelector('input[name="arm"]:checked'); return p ? p.value : 'EEG'; }
  function rollingMode(labels, k) {
    var out = new Array(labels.length);
    for (var i = 0; i < labels.length; i++) {
      var counts = {}, j, v;
      for (j = Math.max(0, i - k + 1); j <= i; j++) { v = labels[j]; counts[v] = (counts[v] || 0) + 1; }
      var best = null, bestN = -1;
      for (j = 0; j < SPEEDS.length; j++) { v = SPEEDS[j]; if ((counts[v] || 0) > bestN) { bestN = counts[v] || 0; best = v; } }
      out[i] = best;
    }
    return out;
  }
  function applyHold(sm, hold) {
    var out = new Array(sm.length), cur = sm[0], streak = 0;
    for (var i = 0; i < sm.length; i++) { if (sm[i] === cur) { streak = 0; } else { streak++; if (streak >= hold) { cur = sm[i]; streak = 0; } } out[i] = cur; }
    return out;
  }
  function settleTimes(cmd) {
    var events = [], i;
    for (i = 1; i < N; i++) if (TRUTH[i] !== TRUTH[i - 1]) events.push(i);
    return events.map(function (idx, k) {
      var end = (k + 1 < events.length) ? events[k + 1] : N;
      for (var j = idx; j < end; j++) { var ok = true; for (var m = j; m < end; m++) { if (cmd[m] !== TRUTH[idx]) { ok = false; break; } } if (ok) return (j - idx) * HOP; }
      return null;
    });
  }
  function compute() {
    var raw = STREAM.raw[arm()], k = parseInt(elSmooth.value, 10), h = parseInt(elHold.value, 10);
    var cmd = applyHold(rollingMode(raw, k), h), right = 0;
    for (var i = 0; i < N; i++) if (cmd[i] === TRUTH[i]) right++;
    return { raw: raw, cmd: cmd, acc: right / N, lat: settleTimes(cmd) };
  }
  var W = 0, H = 0, dpr = 1;
  function resize() {
    var nd = Math.min(window.devicePixelRatio || 1, 2), nw = canvas.clientWidth, nh = canvas.clientHeight;
    if (nw === W && nh === H && nd === dpr) return;
    dpr = nd; W = nw; H = nh; canvas.width = W * dpr; canvas.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  function draw(state) {
    resize();
    var padL = 72, padR = 14, padT = 14, padB = 28, plotW = W - padL - padR, plotH = H - padT - padB;
    var ink = css('--ink'), surface = css('--surface'), grey = css('--muted'), accent = css('--accent'), marker = css('--bad');
    ctx.clearRect(0, 0, W, H);
    var yOf = function (r) { return padT + plotH - (r + 0.5) / 3 * plotH; };
    var xOf = function (i) { return padL + (i / (N - 1)) * plotW; };
    ctx.strokeStyle = surface; ctx.lineWidth = 1; ctx.fillStyle = grey;
    ctx.font = '12px Erode, Georgia, serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    for (var r = 0; r < 3; r++) { var y = yOf(r); ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke(); ctx.fillText(STREAM.speed_labels[SPEEDS[r]], padL - 8, y); }
    var i;
    ctx.globalAlpha = 0.6; ctx.fillStyle = grey;
    for (i = 0; i < N; i++) { if (i > state.head) break; ctx.beginPath(); ctx.arc(xOf(i), yOf(RANK[state.raw[i]]), 2.4, 0, Math.PI * 2); ctx.fill(); }
    ctx.globalAlpha = 1;
    function stepLine(labels, upto) {
      ctx.beginPath(); var started = false, prevY = null, k, y, x;
      for (k = 0; k <= upto; k++) { y = yOf(RANK[labels[k]]); x = xOf(k); if (!started) { ctx.moveTo(x, y); started = true; } else { if (y !== prevY) ctx.lineTo(x, prevY); ctx.lineTo(x, y); } prevY = y; }
      if (started) ctx.stroke();
    }
    ctx.globalAlpha = 0.38; ctx.strokeStyle = ink; ctx.lineWidth = 5; stepLine(TRUTH, N - 1);
    ctx.globalAlpha = 1; ctx.strokeStyle = accent; ctx.lineWidth = 2.5; stepLine(state.cmd, Math.min(state.head, N - 1));
    for (i = 1; i < N; i++) { if (TRUTH[i] !== TRUTH[i - 1]) { ctx.strokeStyle = marker; ctx.lineWidth = 1; ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(xOf(i), padT); ctx.lineTo(xOf(i), padT + plotH); ctx.stroke(); ctx.setLineDash([]); } }
    if (state.head < N - 1) { ctx.strokeStyle = accent; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(xOf(state.head), padT); ctx.lineTo(xOf(state.head), padT + plotH); ctx.stroke(); }
    ctx.fillStyle = grey; ctx.textAlign = 'center'; ctx.textBaseline = 'top'; ctx.fillText('time in seconds', padL + plotW / 2, padT + plotH + 8);
  }
  function render() {
    var s = compute(); s.head = Math.min(head, N - 1); draw(s);
    elAcc.textContent = (s.acc * 100).toFixed(1) + '%';
    var shown = s.lat.filter(function (v) { return v !== null; });
    elLat.textContent = shown.length ? shown.map(function (v) { return v.toFixed(0) + ' s'; }).join(' and ') : 'never settles';
    var now = STREAM.speed_labels[s.cmd[s.head]], real = STREAM.speed_labels[TRUTH[s.head]];
    elNow.textContent = now;
    elSummary.textContent = 'Using ' + (arm() === 'EEG' ? 'brain signals only' : 'brain and muscle signals') + ', a smoothing window of ' + elSmooth.value + ' and a hold of ' + elHold.value +
      '. The command is right ' + (s.acc * 100).toFixed(1) + '% of the time. Time to settle after each speed change: ' +
      (shown.length ? shown.map(function (v) { return v.toFixed(0) + ' seconds'; }).join(' and ') : 'it never settles') +
      '. At the current position the chair is told ' + now + ' and the real speed is ' + real + '.';
  }
  function tick(ts) { if (!playing) return; if (ts - lastTs > 60) { lastTs = ts; head += 1; if (head >= N) { head = N - 1; stop(); render(); return; } render(); } raf = requestAnimationFrame(tick); }
  function start() { if (head >= N - 1) head = 0; playing = true; elPlay.textContent = 'Pause'; elPlay.setAttribute('aria-pressed', 'true'); raf = requestAnimationFrame(tick); }
  function stop() { playing = false; elPlay.textContent = 'Play'; elPlay.setAttribute('aria-pressed', 'false'); if (raf !== null) { cancelAnimationFrame(raf); raf = null; } }
  elPlay.addEventListener('click', function () { playing ? stop() : start(); });
  elReset.addEventListener('click', function () { stop(); head = N; render(); });
  elSmooth.addEventListener('input', function () { elSmoothVal.textContent = elSmooth.value + ' window' + (elSmooth.value === '1' ? '' : 's'); render(); });
  elHold.addEventListener('input', function () { elHoldVal.textContent = elHold.value + ' window' + (elHold.value === '1' ? '' : 's'); render(); });
  Array.prototype.forEach.call(document.querySelectorAll('input[name="arm"]'), function (r) { r.addEventListener('change', render); });
  window.addEventListener('resize', render);
  document.addEventListener('themechange', render);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', render);
  elSmoothVal.textContent = elSmooth.value + ' windows'; elHoldVal.textContent = elHold.value + ' windows';
  render();
})();
