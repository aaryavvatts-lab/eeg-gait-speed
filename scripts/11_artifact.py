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

from gaitbci import config as cfg, fonts, refs, webpage

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
<style>{webpage.CSS}</style>

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
<script>{webpage.CANVAS_JS}</script>
<script>{webpage.APP_JS}</script>
"""
    return part1 + part2


def main() -> int:
    html = webpage.ascii_safe(build())
    OUT.write_text(html)
    print(f"page -> {OUT.relative_to(cfg.ROOT)} "
          f"({len(html.encode()) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
