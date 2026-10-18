"""Build a small standalone page meant for real hosting (Vercel, GitHub Pages).

Unlike report/index.html, this page does not embed the fonts or the matplotlib
figures, so it stays under 100 KB instead of 2.3 MB. That matters because this
file gets deployed by handing its exact bytes to a hosting API in one request,
and a multi-megabyte file is not something that can be moved that way
reliably.

The trade is that this page links out to the full report instead of
containing everything itself. It carries the same interactive wheelchair demo
as the full page, using the same shared CSS and JavaScript, so what people can
click and try is identical.
"""
from __future__ import annotations

import json
import sys

from gaitbci import config as cfg, refs, webpage

OUT = cfg.ROOT / "report" / "landing-generated.html"  # site/index.html is hand-authored since the October 2026 redesign; this script no longer overwrites it

FULL_REPORT_URL = "https://claude.ai/code/artifact/1f300dea-4ad8-4849-b8d5-0ad01f862670"
GITHUB_URL = "https://github.com/aaryavvatts-lab/eeg-gait-speed"

EXTRA_CSS = """
.links { display:flex; flex-wrap:wrap; gap:12px; margin:1.6em 0 0; }
.links a { display:inline-flex; align-items:center; gap:8px; font-size:.92rem;
  font-weight:600; padding:10px 18px; border-radius:8px; text-decoration:none;
  font-family:Archivo,"Helvetica Neue",Arial,sans-serif; }
.links a.primary { background:var(--accent); color:#fff; }
.links a.primary:hover { filter:brightness(1.08); }
.links a.secondary { border:1px solid var(--rule-strong); color:var(--ink);
  background:var(--surface); }
.links a.secondary:hover { border-color:var(--accent); color:var(--accent); }
"""


def f3(v) -> str:
    return "n/a" if v is None else f"{float(v):.3f}"


def build() -> str:
    s = json.loads((cfg.TABLES / "results_summary.json").read_text())
    stream = json.loads((cfg.TABLES / "realtime_stream.json").read_text())
    lk = s.get("leakage", {})
    loso = s.get("loso", {})
    sid = s.get("subject_identifiability", {})
    rt = s.get("realtime", {})

    def L(arm, key):
        return loso.get(arm, {}).get(key)

    stream_json = json.dumps(stream, separators=(",", ":"))
    lift = float(sid.get("lift", 0))

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

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reading Walking Speed From the Scalp</title>
<meta name="description" content="A machine learning project that looked
like it worked at 92 percent, and what was left of it once the test was
fixed. Brain and muscle sensor data, a real interactive demo.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{webpage.CSS}</style>
<style>{EXTRA_CSS}</style>
</head>
<body>

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
    <div class="links">
      <a class="primary" href="{FULL_REPORT_URL}">Read the full write-up</a>
      <a class="secondary" href="{GITHUB_URL}">View the code on GitHub</a>
    </div>
  </div>
</header>

<main id="main">

<section id="premise" aria-labelledby="premise-h">
  <div class="col">
    <p class="eyebrow">the idea, and the catch</p>
    <h2 id="premise-h">Why the first number was wrong</h2>
    <p>Take EEG recorded while people walk at three speeds. Cut it into short
    windows, measure how much power sits in each frequency band, and train a
    model to name the speed. That gave me <strong>{f3(lk.get('random'))}</strong>
    balanced accuracy, which sounds great and is close to meaningless.</p>
    <p>Each one minute recording gets cut into 58 windows that overlap by
    half. Split those windows at random and near copies land on both sides of
    the training and test sets, so the model scores well by recognising a
    window it has already mostly seen.</p>
    <p>There is a second problem underneath that one. The same features can
    name <em>which of 58 people</em> a window came from
    <strong>{f3(sid.get('subject_id_accuracy'))}</strong> of the time, against
    a chance level of 1.7 percent, about {lift:.0f} times better than
    guessing. That personal signature is strong enough to swamp the thing I
    was actually trying to measure. Splitting the data by person instead of
    by window is the only version that answers the question a real device
    would face, and that drops the score to
    <strong>{f3(lk.get('subject'))}</strong>.</p>
  </div>
</section>

<section id="results" aria-labelledby="results-h">
  <div class="col">
    <p class="eyebrow">holding out one person at a time</p>
    <h2 id="results-h">Brain, muscle, and both</h2>
    <p>The dataset also carries muscle sensor recordings from the legs, which
    makes the honest comparison possible. Letting the model calibrate on a
    short recording from each person first:</p>
    <div class="tbl-scroll"><table>
      <thead><tr><th scope="col">signals</th><th scope="col">each window</th>
      <th scope="col">whole recording</th></tr></thead>
      <tbody>
        <tr><td>brain</td><td class="n">{f3(L('EEG','balanced_accuracy'))}</td>
            <td class="n">{f3(L('EEG','trial_balanced_accuracy'))}</td></tr>
        <tr><td>muscle</td><td class="n">{f3(L('EMG','balanced_accuracy'))}</td>
            <td class="n">{f3(L('EMG','trial_balanced_accuracy'))}</td></tr>
        <tr><td>both</td>
            <td class="n hi">{f3(L('EEG+EMG','balanced_accuracy'))}</td>
            <td class="n hi">{f3(L('EEG+EMG','trial_balanced_accuracy'))}</td></tr>
      </tbody>
    </table></div>
    <p>Muscle beats brain by a wide margin. I also compared my results
    against a <a href="https://doi.org/10.1109/tbme.2019.2921766">2019
    study</a> that used a two layer electrode to record movement artifact on
    its own, separately from brain activity, and found that most of what my
    brain model reads looks like body movement rather than the brain. The
    full write-up goes through exactly how I checked that.</p>
  </div>
</section>

<section id="try" aria-labelledby="try-h">
  <div class="col">
    <p class="eyebrow">interactive, runs in your browser</p>
    <h2 id="try-h">Try it yourself</h2>
    <p>Scores on shuffled windows are not what a device lives through, so here
    is the model actually driving a chair. Person {rt.get('demo_subject','')}
    was held out of training, their three recordings were joined end to end,
    and pushed through the model one window at a time. The dark line is the
    real treadmill speed. The blue line is what the chair would be told after
    smoothing.</p>

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

    <div class="tbl-scroll"><table>
      <thead><tr><th scope="col">signals</th><th scope="col">raw windows</th>
      <th scope="col">command right</th><th scope="col">time to settle</th></tr></thead>
      <tbody>{rt_rows}</tbody>
    </table></div>
    <p>With muscle in the mix the raw guesses are already right almost every
    second, so smoothing only adds delay, best left at zero. Brain signals
    alone are so jittery that the command needs about twelve seconds of
    averaging before it stops flipping between speeds, and by then it is
    reacting to what the rider wanted twelve seconds ago. For a chair, that
    settling time is the number that decides whether you could ride it.</p>
  </div>
</section>

<section id="limits" aria-labelledby="limits-h">
  <div class="col">
    <p class="eyebrow">honest limits</p>
    <h2 id="limits-h">What this does not show</h2>
    <p>Every person walked the three speeds in the same fixed order in one
    sitting, so speed is tangled up with anything that drifts over the course
    of a session, such as the electrodes settling in. That cannot be undone
    with this dataset. The calibrated numbers use the held out person's own
    recordings, so they describe a device with a short calibration step, not
    one that works cold. The group tested is 58 healthy adults on a treadmill
    at slow, fixed speeds, which is not the same as a wheelchair user walking
    at their own pace outdoors. And the people in this dataset were walking,
    so this says nothing about reading an intended speed from somebody who is
    sitting still, which is what an actual brain-computer interface for a
    wheelchair would need to do.</p>
    <div class="links">
      <a class="primary" href="{FULL_REPORT_URL}">Read the full write-up</a>
      <a class="secondary" href="{GITHUB_URL}">View the code on GitHub</a>
    </div>
  </div>
</section>

<section class="legal" id="notes" aria-labelledby="notes-h">
  <div class="col">
    <p class="eyebrow">the small print</p>
    <h2 id="notes-h">Notes, privacy and terms</h2>

    <details id="privacy">
      <summary>Privacy</summary>
      <div class="body">
        <p>This is a single static page with no accounts, no forms, no
        comments and no analytics.</p>
        <h3>What the page collects</h3>
        <p>Nothing. There is no tracking code and no advertising on it. It
        does not ask you for anything.</p>
        <h3>The one outside request this page makes</h3>
        <p>The page loads its typefaces from Google Fonts
        (fonts.googleapis.com and fonts.gstatic.com). That is the only request
        this page sends to anyone else's server. Google Fonts does not set
        cookies for this kind of request, but it can see ordinary request
        information such as your IP address when your browser fetches the
        font files, the same as any font or image loaded from a website. See
        <a href="https://policies.google.com/privacy">Google's privacy
        policy</a> for what they do with that.</p>
        <h3>What the host can see</h3>
        <p>Whoever hosts this page, currently Vercel, can keep ordinary server
        records such as the address your request came from, the same as any
        website host. That sits outside this page and is covered by the
        host's own privacy policy.</p>
        <h3>About the people in the data</h3>
        <p>The recordings come from a public dataset that its authors
        anonymised before release, under an approved ethics protocol at their
        university. It holds no names or contact details, and nothing on this
        page can be traced back to an individual who took part.</p>
      </div>
    </details>

    <details id="cookies">
      <summary>Cookies and storage</summary>
      <div class="body">
        <p>This page sets no cookies of its own and writes nothing to local
        storage or session storage.</p>
        <p>The interactive controller above runs entirely in your browser
        using data that is already inside the page. It sends nothing out and
        saves nothing.</p>
        <p>Loading the fonts from Google, described in the privacy section
        above, does not involve cookies for this kind of request. If the
        service hosting this page sets its own cookies, those are covered by
        that service's policy rather than this one.</p>
      </div>
    </details>

    <details id="terms">
      <summary>Terms of use</summary>
      <div class="body">
        <p>This is a student project written to learn and to be looked at. It
        is offered as is, with no warranty of any kind, and no promise that
        anything on it is correct or fit for any purpose.</p>
        <h3>Not medical or clinical advice</h3>
        <p>Nothing here is medical advice, and none of this is a medical
        device or part of one. Do not use anything on this page, or the code
        behind it, to make a decision about anybody's care, treatment,
        mobility equipment or safety. The wheelchair framing is a way of
        explaining the problem. The model shown here is nowhere near fit to
        steer a real chair, and the page says why.</p>
        <h3>Limits</h3>
        <p>To the fullest extent the law allows, the author is not liable for
        any loss or damage arising from use of this page or the code behind
        it.</p>
        <h3>The data</h3>
        <p>The recordings belong to Katmah and colleagues and are published on
        PhysioNet under a Creative Commons Attribution 4.0 licence, which
        allows reuse with credit. The dataset itself is not redistributed
        here.</p>
        <h3>This page and the code</h3>
        <p>The text, figures and code written for this project are released
        under the MIT licence, on the GitHub repository linked above. You may
        reuse them with credit.</p>
      </div>
    </details>

    <details id="accessibility">
      <summary>Accessibility</summary>
      <div class="body">
        <p>This page aims at WCAG 2.1 level AA.</p>
        <ul>
          <li>A skip link to the main text, and proper landmarks for header,
          main content and the interactive demo.</li>
          <li>Every control is a standard HTML input or button, so it works
          with a keyboard and with assistive software, with focus always
          visible.</li>
          <li>Body text holds at least a 4.5 to 1 contrast ratio against its
          background in both the light and dark theme.</li>
          <li>The page respects a reduced motion setting. The moving line
          drawing at the top freezes and the demo does not animate on its
          own.</li>
          <li>Text reflows down to a 320 pixel wide screen. Wide tables scroll
          inside their own box rather than pushing the page sideways.</li>
        </ul>
        <p>The interactive chart is drawn on a canvas, which a screen reader
        cannot read directly. A written summary next to it updates as the
        settings change, giving the same numbers in text. The moving line
        drawing at the top is decoration and is hidden from screen readers on
        purpose.</p>
        <p>If something on this page does not work with the software you use,
        the GitHub repository linked above is the place to raise it.</p>
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
    <p><span class="tag">more</span> The
    <a href="{FULL_REPORT_URL}">full write-up</a> has all nine figures, every
    ablation, the permutation test and the complete list of references. The
    <a href="{GITHUB_URL}">source code</a> has the full pipeline, from raw
    files to this page.</p>
  </div>
</footer>

</div>
<script>var STREAM = {stream_json};</script>
<script>{webpage.CANVAS_JS}</script>
<script>{webpage.APP_JS}</script>
</body>
</html>
"""


def main() -> int:
    OUT.parent.mkdir(exist_ok=True)
    html = webpage.ascii_safe(build())
    OUT.write_text(html)
    print(f"landing page -> {OUT.relative_to(cfg.ROOT)} "
          f"({len(html.encode()) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
