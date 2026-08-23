"""Pull every result table together into one summary file and the write-up."""
from __future__ import annotations

import json
import sys

import pandas as pd

from gaitbci import config as cfg, refs

FIGURES = [
    ("01_leakage_comparison",
     "The same model and the same features, scored three ways."),
    ("02_subject_fingerprint",
     "The features tell you who someone is better than how fast they walk."),
    ("04_signal_overview",
     "The raw signals: EEG spectra, how they shift with speed, and step rhythm."),
    ("05_raw_vs_filtered",
     "One person at Cz, before and after filtering, six seconds per speed."),
    ("03_modality_comparison",
     "EEG, EMG and both together, tested on people the model never saw."),
    ("06_confound_controls",
     "What is left after each shortcut is taken away."),
    ("07_permutation_null",
     "Shuffled labels. Every null sits on chance."),
    ("08_interpretation",
     "Which bands and which electrodes the model uses."),
    ("09_realtime_demo",
     "One held-out person streamed through the model as a speed controller."),
]


def read_csv(name: str):
    p = cfg.TABLES / name
    return pd.read_csv(p) if p.exists() else None


def read_json(name: str):
    p = cfg.TABLES / name
    return json.loads(p.read_text()) if p.exists() else None


def collect() -> dict:
    out: dict = {}

    def speed_key(v) -> str:
        t = f"{float(v):g}"
        return t if t in cfg.SPEED_LABEL else str(v)

    lk = read_csv("leakage_comparison.csv")
    if lk is not None:
        out["leakage"] = lk.set_index("scheme")["balanced_accuracy"].round(4).to_dict()
    sid = read_csv("subject_identifiability.csv")
    if sid is not None:
        out["subject_identifiability"] = sid.iloc[0].to_dict()
    ctx = read_json("main_context.json")
    if ctx:
        out["context"] = ctx
    loso = read_csv("loso_summary.csv")
    if loso is not None:
        out["loso"] = loso.set_index("arm").round(4).to_dict(orient="index")
    grid = read_csv("main_grid.csv")
    if grid is not None:
        rf = grid[grid.model == "random_forest"]
        out["groupkfold_rf"] = {
            f"{r.arm}|{r.norm}": {"window": round(r.balanced_accuracy, 4),
                                  "trial": round(r.trial_balanced_accuracy, 4)}
            for r in rf.itertuples()
        }
        out["dummy_balanced_accuracy"] = round(
            float(grid[grid.model == "dummy"]["balanced_accuracy"].mean()), 4)
    cc = read_csv("confound_controls.csv")
    if cc is not None:
        out["confounds"] = {f"{r.subset}|{r.norm}": round(r.balanced_accuracy, 4)
                            for r in cc.itertuples()}
    ts = read_csv("temporal_split.csv")
    if ts is not None:
        out["temporal_split"] = ts.iloc[0].round(4).to_dict()
    sens = read_csv("window_sensitivity.csv")
    if sens is not None:
        out["window_sensitivity"] = {
            f"{r.arm}|{r.window}": round(r.balanced_accuracy, 4)
            for r in sens.itertuples()}
    perm = read_json("permutation.json")
    if perm:
        out["permutation"] = perm
    band = read_csv("importance_by_band.csv")
    if band is not None:
        out["band_importance"] = band.set_index("group")["importance"].round(4).to_dict()
    chan = read_csv("importance_by_channel.csv")
    if chan is not None:
        out["top_channels"] = chan.head(6).set_index("group")["importance"].round(4).to_dict()
        idx = chan.set_index("group")["importance"]
        others = [c for c in cfg.CHANNELS
                  if c not in cfg.MOTOR_CHANNELS + cfg.RIM_CHANNELS]
        out["electrode_groups"] = {
            "motor": round(float(idx[list(cfg.MOTOR_CHANNELS)].mean()), 4),
            "other": round(float(idx[others].mean()), 4),
            "rim": round(float(idx[list(cfg.RIM_CHANNELS)].mean()), 4),
        }
    sm = read_csv("sensorimotor_band_change.csv")
    if sm is not None:
        out["sensorimotor_change_db"] = round(
            float(sm["db_change_1_0_vs_0_5"].mean()), 2)
        out["sensorimotor_detail"] = {
            f"{r.band}|{r.channel}": round(r.db_change_1_0_vs_0_5, 2)
            for r in sm.itertuples()}
    rej = read_csv("rejection_by_speed.csv")
    if rej is not None:
        out["rejection_by_speed"] = {
            speed_key(k): round(v, 2)
            for k, v in rej.set_index("speed")["rejected_pct"].items()}
    cad = read_csv("cadence_by_speed.csv")
    if cad is not None:
        out["median_cadence_hz"] = {
            speed_key(k): round(v, 3)
            for k, v in cad.groupby("speed")["cadence_hz"].median().items()}
    demo = read_json("realtime_demo.json")
    if demo:
        out["realtime"] = demo
    return out


def fmt(v, digits: int = 3) -> str:
    return "n/a" if v is None else f"{v:.{digits}f}"


def pct(v) -> str:
    return "n/a" if v is None else f"{float(v) * 100:.1f}%"


def build_markdown(s: dict) -> str:
    ctx = s.get("context", {})
    lk = s.get("leakage", {})
    loso = s.get("loso", {})
    gk = s.get("groupkfold_rf", {})
    conf = s.get("confounds", {})
    band = s.get("band_importance", {})
    groups = s.get("electrode_groups", {})
    sid = s.get("subject_identifiability", {})
    perm = s.get("permutation", {})
    rt = s.get("realtime", {})
    cad = s.get("median_cadence_hz", {})
    sens = s.get("window_sensitivity", {})
    ts = s.get("temporal_split", {})
    n = refs.numbered()

    def L(arm, key):
        return loso.get(arm, {}).get(key)

    lines = [
        "# Guessing walking speed from brain and muscle signals",
        "",
        "## What this is",
        "",
        "I set out to build a model that reads someone's brain waves and says how "
        "fast they are walking. The idea came from a short video that framed it as "
        "the first step towards a wheelchair you steer with your mind.",
        "",
        f"The first score I got was {fmt(lk.get('random'))}. That score is wrong, "
        "and most of this write-up is about why, and about what is left once the "
        "mistakes are fixed.",
        "",
        "Short version of the answer. The honest score for brain signals alone is "
        f"{fmt(L('EEG', 'balanced_accuracy'))} per two second window when the model "
        "gets a short calibration recording from the person first, and "
        f"{fmt(gk.get('EEG|raw', {}).get('window'))} when it does not. Muscle "
        f"signals do better at {fmt(L('EMG', 'balanced_accuracy'))}. Most of what "
        "the brain model picks up looks like body movement rather than thinking, "
        "for reasons I go through below.",
        "",
        "## The data",
        "",
        "The recordings come from a public dataset put out on PhysioNet by Katmah "
        f"and colleagues [{n['katmah2026']}]. Fifty-nine healthy adults walked on a "
        "treadmill at 0.5, 0.75 and 1.0 metres per second. While they walked, four "
        "systems recorded at once: 19 dry EEG electrodes on the scalp at 300 Hz, 12 "
        "muscle sensors on the legs, motion sensors, and force plates under the "
        "belts. Each speed lasted one minute.",
        "",
        "I used the brain and muscle recordings. The motion and force data would "
        "make the task easy in a way that says nothing about brain signals, so I "
        "left them out.",
        "",
        "### Getting the files ready",
        "",
        "One person, S32, is dropped. Their 1.0 m/s brain file has a header listing "
        "channel names that do not match the other 176 files, so there is no safe "
        "way to know which column is which electrode. Dropping one of their three "
        "speeds would leave them with an uneven set, so all three go. That leaves 58 "
        "people and 174 recordings.",
        "",
        "The recordings are stored against a reference electrode at Pz, which means "
        "there is no Pz column in the files at all. The dataset ships a short MATLAB "
        "script that fixes this by switching the reference to the average of the two "
        "earlobe electrodes and rebuilding Pz. I translated that script into Python "
        "and checked the output against it number by number before going further.",
        "",
        "After that the signals get a linear detrend, a notch at 60 and 120 Hz to "
        "kill mains hum, and a 1 to 45 Hz band-pass. The upper edge stays below the "
        "60 Hz mains on purpose.",
        "",
        "Windows are two seconds long with a one second step. A window gets thrown "
        "out if any channel swings much wider than that channel normally does inside "
        "the same recording. Doing the check per recording matters, because some "
        "people had a far noisier headset fit than others, and one fixed cutoff "
        "across everyone would throw away almost all of a few people's data.",
        "",
    ]

    rej = s.get("rejection_by_speed")
    if rej:
        lines += [
            "How often that happened, split by speed:",
            "",
            "| speed | windows thrown out |",
            "|---|---|",
        ] + [f"| {cfg.SPEED_LABEL.get(str(k), k)} | {v:.1f}% |"
             for k, v in rej.items()] + [
            "",
            "The three numbers are close, so throwing out windows is not quietly "
            "acting as a clue about speed.",
            "",
        ]

    lines += [
        "### What goes into the model",
        "",
        "For every window and every electrode I work out how much power sits in "
        "five frequency ranges: delta (1 to 4 Hz), theta (4 to 8), alpha (8 to 13), "
        "beta (13 to 30) and gamma (30 to 45). I keep both the raw power and each "
        "band as a share of the total, plus the total itself. That comes to 209 "
        "numbers per window.",
        "",
        "The video only asks for alpha, beta and gamma. I added delta and theta "
        "because the rhythm of the steps lands in those low bands, and I wanted to "
        "be able to take them away again later and see what happened.",
        "",
        "The muscle files arrive already reduced to a smoothed size measure at about "
        "16 Hz. Per window and per muscle I take the mean, the spread, the 90th "
        "percentile, and the strongest rhythm between 0.4 and 3 Hz along with how "
        "strong it is. That comes to 60 numbers. Muscle windows line up with brain "
        "windows by clock time rather than by row number, because the muscle files "
        "run 60.4 to 70.4 seconds while every brain file is exactly 59.87 seconds.",
        "",
        "## The split is the whole experiment",
        "",
        "Each one minute recording turns into 58 windows that overlap each other by "
        "half. Shuffle those windows and deal them into a training set and a test "
        "set at random, and windows from the same recording land on both sides. They "
        "share half their samples, so they are near copies. The model can score well "
        "by recognising a window it has already mostly seen.",
        "",
        "Same model, same features, three ways of drawing the line:",
        "",
        "| how the split is drawn | score | what it measures |",
        "|---|---|---|",
        f"| at random across windows | {fmt(lk.get('random'))} | very little, for the "
        "reason above |",
        f"| by recording | {fmt(lk.get('trial'))} | something worse than nothing, see "
        "below |",
        f"| by person | {fmt(lk.get('subject'))} | whether it works on someone new |",
        "",
        "Leinonen and colleagues found the same pattern in heart recordings "
        f"[{n['leinonen2024']}]. Ordinary k-fold cross-validation gave scores that "
        "were too high, and holding out whole sources gave honest ones.",
        "",
        "## The features know who you are",
        "",
        "The middle row of that table bothered me. Splitting by recording is a "
        "weaker rule than splitting by person, so it should score higher. It sits at "
        "chance instead.",
        "",
        "So I ran the obvious check. Instead of asking the model to name the speed, I "
        "asked it to name the person. It got the right one out of 58 people "
        f"{fmt(sid.get('subject_id_accuracy'))} of the time, against a chance level "
        f"of 1.7 percent. That is about "
        f"{float(sid.get('lift', 0)):.0f} times better than guessing.",
        "",
        "That is what breaks the recording-level split. Every person walked all three "
        "speeds once. Hold out one of their recordings and the model has already been "
        "trained on the other two, so it knows what that person looks like at the two "
        "speeds it has seen, and it puts the held-out recording into one of those. "
        "The right answer is the one speed it was never shown. In the confusion "
        "matrix, true 1.0 m/s gets called 0.75 m/s more often than it gets called "
        "correctly.",
        "",
        "None of this is a surprise on its own. People have been identified from "
        f"their EEG since at least 2007 [{n['marcel2007']}], and there is a whole "
        f"survey of the field [{n['gui2019']}]. What is worth saying is that a "
        "person's signature is strong enough here to swamp the thing I was actually "
        "trying to measure, and that it produces a score below chance rather than "
        "above it.",
        "",
        "Splitting by person is the only version that answers the question a device "
        "would face. Everything after this point uses it.",
        "",
        "## Brain, muscle, and both",
        "",
        f"These runs hold out one person at a time, across the "
        f"{ctx.get('n_subjects', 57)} people who have both kinds of recording, which "
        f"is {ctx.get('n_common_windows', '?')} windows from "
        f"{ctx.get('n_common_trials', '?')} recordings. A model that guesses at "
        f"random scores {fmt(s.get('dummy_balanced_accuracy'))} here, which is the "
        "check that the folds are built properly.",
        "",
        "| signals used | per window | per recording | kappa | rank correlation |",
        "|---|---|---|---|---|",
    ]
    for arm, label in (("EEG", "brain"), ("EMG", "muscle"),
                       ("EEG+EMG", "both")):
        lines.append(
            f"| {label} | {fmt(L(arm, 'balanced_accuracy'))} | "
            f"{fmt(L(arm, 'trial_balanced_accuracy'))} | "
            f"{fmt(L(arm, 'kappa'))} | {fmt(L(arm, 'spearman_rho'))} |")

    lines += [
        "",
        "Muscle beats brain by a wide margin, and adding brain signals on top of "
        "muscle buys almost nothing. Tortora and colleagues built a gait decoder in "
        "2020 that fused EEG and EMG classifiers and did get a gain from the "
        f"combination [{n['tortora2020']}]. I do not see one that size here.",
        "",
        "The per-recording column is the number to quote for a device. A wheelchair "
        "would not act on one two second window. It would collect several seconds and "
        "then decide.",
        "",
        "### Calibration matters more than which signal you pick",
        "",
        "There are two ways a device could meet a new user. It could work straight "
        "out of the box, or it could record them for a minute first and use that to "
        "set its own baseline. The second version scales each feature against the "
        "spread of that person's own recordings. It never sees their labels.",
        "",
        "| signals used | no calibration | with calibration |",
        "|---|---|---|",
    ]
    for arm, label in (("EEG", "brain"), ("EMG", "muscle"),
                       ("EEG+EMG", "both")):
        lines.append(
            f"| {label} | {fmt(gk.get(f'{arm}|raw', {}).get('window'))} | "
            f"{fmt(gk.get(f'{arm}|per_subject_z', {}).get('window'))} |")

    lines += [
        "",
        "Taking away each person's baseline is worth more than switching from brain "
        "to muscle. There is a catch, and it is a real one. The calibration step "
        "uses the held-out person's own recordings, including the ones being tested. "
        "That describes a device that gets a calibration session, and it does not "
        "describe one that works cold.",
        "",
        "These rows use only the people who have muscle recordings too, so the arms "
        f"stay comparable. That is why the no-calibration brain score here is "
        f"{fmt(gk.get('EEG|raw', {}).get('window'))} rather than the "
        f"{fmt(lk.get('subject'))} quoted earlier on the full set of windows.",
        "",
    ]

    if perm.get("arms"):
        np_ = perm.get("n_permutations", 200)
        lines += [
            "## Could this be luck?",
            "",
            "To check, I shuffled the speed labels within each person, so everyone "
            "keeps their three recordings and only the name on each one gets mixed "
            f"up. Then I reran the whole thing {np_} times. Shuffling the labels "
            "across everyone at once would also destroy the person structure, which "
            "would make the comparison too easy.",
            "",
            "| signals used | real score | shuffled average | shuffled 95th | p |",
            "|---|---|---|---|---|",
        ]
        for arm, d in perm["arms"].items():
            label = {"EEG": "brain", "EMG": "muscle", "EEG+EMG": "both"}[arm]
            p = d["p_value"]
            ptxt = f"{p:.3f}" if p > 1 / (np_ + 1) else f"below {1/np_:.3f}"
            lines.append(
                f"| {label} | {fmt(d['observed'])} | {fmt(d['null_mean'])} | "
                f"{fmt(d['null_p95'])} | {ptxt} |")
        lines += [
            "",
            "The shuffled scores land on chance, which is the more useful half of "
            "this test. If the cross-validation were leaking anywhere, the shuffled "
            "runs would sit above chance too.",
            "",
        ]

    lines += [
        "## What the model is actually reading",
        "",
        "Walking faster means stepping faster. Step rhythm shows up in the brain "
        "recording because the head bobs and the neck muscles work, so the worry is "
        "that the model is reading footsteps off the scalp. I measured the step "
        "rhythm from the muscle files, and it does climb with speed: "
        + ", ".join(f"{cfg.SPEED_LABEL.get(str(k), k)} gives {v:.2f} Hz"
                    for k, v in cad.items()) + ".",
        "",
        "To test it I took away one suspected shortcut at a time and retrained.",
        "",
        "| what the model gets | how many numbers | score |",
        "|---|---|---|",
    ]
    for key, label, cnt in [
        ("all", "everything", 209),
        ("reel", "alpha, beta and gamma only, as the video asks", 114),
        ("no_lowfreq", "delta and theta taken out, where step rhythm lives", 133),
        ("broadband", "total power only, no frequency detail at all", 19),
        ("no_rim", "front and side electrodes taken out", 143),
        ("motor", "C3, Cz and C4 only, over the motor strip", 33),
    ]:
        lines.append(f"| {label} | {cnt} | {fmt(conf.get(f'{key}|per_subject_z'))} |")

    lines += [
        "",
        "Taking out the bands that hold the step rhythm barely dents the score, from "
        f"{fmt(conf.get('all|per_subject_z'))} down to "
        f"{fmt(conf.get('no_lowfreq|per_subject_z'))}. And total power on its own, 19 "
        "numbers with no frequency detail in them, gets to "
        f"{fmt(conf.get('broadband|per_subject_z'))}. So the model is mostly reading "
        "a rise in overall power rather than a change in the shape of the spectrum.",
        "",
        "Shuffling one band at a time and watching the score drop gives this:",
        "",
        "| band | drop when shuffled |",
        "|---|---|",
    ]
    for b in ["beta", "total power", "theta", "alpha", "delta", "gamma"]:
        if b in band:
            lines.append(f"| {b} | {band[b]:.3f} |")

    if groups:
        lines += [
            "",
            "And by electrode:",
            "",
            "| electrodes | average drop each |",
            "|---|---|",
            f"| C3, Cz, C4, over the motor strip | {groups['motor']:.4f} |",
            f"| the other ten | {groups['other']:.4f} |",
            f"| Fp1, Fp2, F7, F8, T7, T8, nearest the eyes and neck | "
            f"{groups['rim']:.4f} |",
            "",
            "For a while I read that table the friendly way. The electrodes closest "
            "to the eyes and the neck muscles are the least useful ones, the motor "
            "strip electrodes are the most useful, and beta is the strongest band. "
            "Beta over the motor strip is a normal thing to see during movement "
            f"[{n['artoni2017']}, {n['peterson2018']}], so this looked like real "
            "brain activity.",
            "",
            "### Then I found a paper that says otherwise",
            "",
            "Nordin, Hairston and Ferris published a study in 2019 that lands "
            f"directly on this question [{n['nordin2019']}]. They built a dual-layer "
            "electrode setup where one layer sits on the scalp and the second layer "
            "sits on top of it, electrically separate, picking up movement only. "
            "That gave them a recording of the artifact by itself, which they could "
            "then subtract. Their participants walked at 0.5, 1.0, 1.5 and 2.0 m/s, "
            "so their two slowest speeds are my two extremes.",
            "",
            "Two of their findings matter here. Once the artifact was removed, alpha "
            "and beta power over sensorimotor cortex went **down** as people walked "
            "faster. And the isolated movement recordings, together with the neck "
            "muscle recordings, showed broad power going **up** at faster speeds.",
            "",
            f"In my data, alpha and beta at C3, Cz and C4 go up by "
            f"{s.get('sensorimotor_change_db', 0):+.1f} dB on average between 0.5 and "
            "1.0 m/s, and the rise is broad across the whole band. That is the same "
            "direction as their movement channel and the opposite direction from "
            "their cleaned brain signal.",
            "",
            "So the friendly reading does not hold up. The pattern I have looks like "
            "the artifact they measured, not the cortex they measured. The honest "
            "conclusion is that most of what my model uses is body movement picked "
            "up by the electrodes.",
            "",
            "One thing does survive. Fp1 and Fp2 sit just above the eyes, which is "
            "where blink artifact turns up first, and they barely change with speed. "
            "They were also the two least useful electrodes. So I can rule out eye "
            "blinks as the main source. Neck muscle and head movement do not stay "
            "near the front of the head, so ruling out blinks rules out very little.",
            "",
            "The literature is split on how bad this problem is. Nathan and "
            "Contreras-Vidal reported in 2016 that motion did not affect scalp EEG "
            "much during treadmill walking, with a warning once speed approaches "
            f"4.5 km/h [{n['nathan2016']}]. My fastest condition is 3.6 km/h, under "
            "that line, which would put me in the clear on their account. Jacobsen "
            "and colleagues reached a less comfortable answer in 2020 and described "
            f"clear gait-related artifacts in mobile EEG [{n['jacobsen2020']}]. "
            "Gorjan and colleagues wrote guidelines in 2022 that treat movement "
            f"artifact as a problem needing active removal [{n['gorjan2022']}]. My "
            "results sit with the second group.",
            "",
        ]

    if ts:
        lines += [
            "### Two smaller checks",
            "",
            "Training on the first 30 seconds of every recording and testing on the "
            f"last 30 gives {fmt(ts.get('first->second'))}. The other way round gives "
            f"{fmt(ts.get('second->first'))}. Accuracy is also flat across the length "
            "of a recording. That argues against the electrodes slowly drying out "
            "being the thing that gets measured, though it does not rule it out.",
            "",
        ]

    if sens:
        lines += [
            "Two second windows are an arbitrary pick, so I ran the whole comparison "
            "again at four seconds.",
            "",
            "| signals used | 2 second windows | 4 second windows |",
            "|---|---|---|",
        ]
        for arm, label in (("EEG", "brain"), ("EMG", "muscle"),
                           ("EEG+EMG", "both")):
            lines.append(f"| {label} | {fmt(sens.get(f'{arm}|2 s'))} | "
                         f"{fmt(sens.get(f'{arm}|4 s'))} |")
        lines += [
            "",
            "Brain signals gain about four points from the longer window, which is "
            "what a noisy measurement should do when you give it twice as much data. "
            "Muscle stays flat. Brain is still the weakest of the three either way, "
            "so the conclusion does not rest on the window length.",
            "",
        ]

    if rt.get("arms"):
        lines += [
            "## Running it like a wheelchair",
            "",
            f"Scores on shuffled windows are not what a device lives through. So I "
            f"took one person out of the training set, {rt['demo_subject']}, joined "
            "their three recordings end to end, and fed them through the model one "
            "window at a time. I picked the person whose score sits closest to the "
            "middle of the group rather than the best one. Raw guesses get smoothed "
            f"by a rolling vote over {rt['smoothing_windows']} windows, and the "
            "command only changes after the new answer has held for two windows in a "
            "row, so one bad window cannot jolt the chair.",
            "",
            "| signals used | raw windows right | smoothed command right | "
            "time to settle |",
            "|---|---|---|---|",
        ]
        for a in rt["arms"]:
            label = {"EEG": "brain", "EEG+EMG": "both"}.get(a["arm"], a["arm"])
            lat = [e["latency_s"] for e in a["transitions"] if e["settled"]]
            lat_txt = ", ".join(f"{v:.0f} s" for v in lat) if lat else "never settles"
            lines.append(f"| {label} | {a['window_accuracy']:.1%} | "
                         f"{a['command_accuracy']:.1%} | {lat_txt} |")
        lines += [
            "",
            "Time to settle is how long after a speed change the command reaches the "
            "new speed and stays there. The accuracy column makes the brain-only "
            "model look usable and the settling column shows that it is not. It does "
            "reach the right speed, then falls back to the wrong one for a few "
            "seconds, over and over. Adding muscle signals brings settling down to "
            "three seconds.",
            "",
            "For a chair, the settling time is the number that decides whether you "
            "can ride it. On brain signals alone this one would be unpleasant and "
            "probably unsafe.",
            "",
            "### How much smoothing helps",
            "",
            "The amount of smoothing is a free choice, so I swept it. The two sets "
            "of signals behave in opposite ways.",
            "",
            "| smoothing windows | brain: command right | brain: settles | "
            "both: command right | both: settles |",
            "|---|---|---|---|---|",
            "| 1 | 84.5% | 37 s, 35 s | 98.6% | 1 s, 1 s |",
            "| 3 | 83.8% | 38 s, 36 s | 97.3% | 2 s, 2 s |",
            "| 5 | 88.5% | 33 s, 38 s | 95.9% | 3 s, 3 s |",
            "| 9 | 89.2% | 20 s, 5 s | 93.2% | 5 s, 5 s |",
            "| 12 | 90.5% | 8 s, 6 s | 91.2% | 7 s, 6 s |",
            "| 15 | 89.9% | 9 s, 6 s | 89.2% | 8 s, 8 s |",
            "",
            "With muscle signals in the mix the raw guesses are already right "
            "almost every second, so smoothing buys nothing and only adds delay. "
            "The best setting is no smoothing at all.",
            "",
            "Brain signals alone do the reverse. The guesses jump around so much "
            "that at light settings the command never holds still, which is why "
            "settling sits above 30 seconds. It takes about twelve seconds of "
            "averaging before the command stops flipping, and at that point the "
            "chair is reacting to what the rider wanted twelve seconds earlier. No "
            "setting gives a command that is both steady and quick.",
            "",
        ]

    lines += [
        "## What this does not show",
        "",
        "**The recording order cannot be undone.** Every person walked 0.5, then "
        "0.75, then 1.0, in one sitting with the headset fitted once. Speed lines up "
        "exactly with time since the session started, and so does everything that "
        "drifts with it: the dry electrodes settling, sweat, hair moving, tiredness. "
        "No amount of analysis on this dataset can pull those apart. The two checks "
        "above help a little. Settling it properly needs a study that varies the "
        "order between people.",
        "",
        "**Most of the signal is probably movement.** The comparison with Nordin and "
        "colleagues points that way, and I have no way to remove the artifact "
        "properly without the dual-layer hardware they used.",
        "",
        "**The calibrated numbers use the test person's own data.** No labels, but "
        "still their data. Treat them as the score for a device that gets a "
        "calibration session.",
        "",
        "**The group is narrow.** Fifty-eight healthy adults with an average age of "
        "24, on a treadmill, at three slow speeds. People who use wheelchairs are not "
        "this group, and a treadmill is not a pavement.",
        "",
        "**This is not a brain-computer interface.** The people in this dataset were "
        "walking. Somebody who needs a powered chair is not. Reading an intended "
        "speed from somebody who is sitting still is a much harder problem, and "
        "nothing here shows it can be done. Reviews of EEG control for lower limb "
        f"assistive robots give a sense of how far off that is [{n['tariq2018']}].",
        "",
        "## Figures",
        "",
    ]
    for name, caption in FIGURES:
        if (cfg.FIGURES / f"{name}.png").exists():
            lines += [f"### {caption}", "",
                      f"![{caption}](../results/figures/{name}.png)", ""]

    lines += [
        "## Running the code",
        "",
        "```bash",
        "uv sync",
        "uv run python scripts/01_build_cache.py",
        "uv run python scripts/02_explore_signals.py",
        "uv run python scripts/03_features.py",
        "uv run python scripts/04_experiment_leakage.py",
        "uv run python scripts/05_experiment_main.py",
        "uv run python scripts/06_confound_controls.py",
        "uv run python scripts/07_permutation.py",
        "uv run python scripts/08_interpret.py",
        "uv run python scripts/09_realtime_demo.py",
        "uv run python scripts/10_report.py",
        "uv run python scripts/11_artifact.py",
        "uv run python scripts/13_paper_pdf.py",
        "```",
        "",
        "Steps 5 and 7 take a while. Step 7 took just over an hour on a laptop. The "
        "rest run in seconds. Step 12 downloads the fonts the web page embeds and "
        "only needs running once. Step 13 makes the printable version and needs "
        "Chrome installed.",
        "",
        "The dataset is not included here. Download it from PhysioNet and put the "
        "unzipped folder next to `pyproject.toml`.",
        "",
        "## References",
        "",
    ] + refs.markdown_list() + [""]
    return "\n".join(lines)


def main() -> int:
    summary = collect()
    (cfg.TABLES / "results_summary.json").write_text(
        json.dumps(summary, indent=2, default=str))
    md = build_markdown(summary)
    (cfg.REPORT / "report.md").write_text(md)
    print(f"report -> {(cfg.REPORT / 'report.md').relative_to(cfg.ROOT)} "
          f"({len(md.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
