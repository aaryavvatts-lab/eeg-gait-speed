# Guessing walking speed from brain and muscle signals

I set out to build a model that reads someone's brain waves and says how fast
they are walking. The idea came from a short video that framed it as the first
step towards a wheelchair you steer with your mind.

The first score I got was **0.923**. That score is wrong, and most of this
project is about why, and about what is left once the mistakes are fixed.

Full write-up: [`report/report.md`](report/report.md).
Shareable web page with an interactive demo: [`report/index.html`](report/index.html).

## What went wrong, and what is left

Each one minute recording gets cut into 58 windows that overlap by half. Split
those windows at random and near copies land on both sides, so the model scores
well by recognising windows it has already seen. Splitting by person instead
drops the score to **0.528**.

There is a second problem underneath that one. The same features name *which of
58 people* a window came from **0.568** of the time, against a chance level of
1.7 percent. That personal signature is strong enough to swamp the thing I was
trying to measure.

Holding out one person at a time, and letting the model calibrate on a short
recording from that person first:

| signals | each window | whole recording |
|---|---|---|
| brain | 0.727 | 0.915 |
| muscle | 0.893 | 0.963 |
| both | 0.899 | 0.976 |

Muscle beats brain, and adding brain on top of muscle buys almost nothing.

Most of what the brain model uses turns out to be a rise in overall power
rather than a change in the shape of the spectrum. Nordin, Hairston and Ferris
measured this properly in 2019 using a two layer electrode that records the
movement artifact on its own. After they removed it, alpha and beta over
sensorimotor cortex went **down** with speed, while their movement channel went
**up**. My data goes up. So what my model reads looks more like body movement
than brain activity. The write-up goes through this in full.

## Layout

```
src/gaitbci/      settings, loading, filtering, features, models, scoring, plots
scripts/          numbered steps, each one runs on its own
results/          figures and tables, every number in the write-up comes from here
report/           the write-up and the web page
```

## Running it

Needs [uv](https://docs.astral.sh/uv/). The recordings are not included here.
Download them from PhysioNet and put the unzipped folder next to
`pyproject.toml`.

```bash
uv sync
uv run python scripts/01_build_cache.py
uv run python scripts/02_explore_signals.py
uv run python scripts/03_features.py
uv run python scripts/04_experiment_leakage.py
uv run python scripts/05_experiment_main.py
uv run python scripts/06_confound_controls.py
uv run python scripts/07_permutation.py
uv run python scripts/08_interpret.py
uv run python scripts/09_realtime_demo.py
uv run python scripts/10_report.py
uv run python scripts/11_artifact.py
uv run python scripts/13_paper_pdf.py
```

Step 5 takes about fifteen minutes and step 7 took just over an hour on a
laptop. The rest run in seconds. `scripts/12_fetch_fonts.py` downloads the
fonts the web page embeds and only needs running once. Step 13 makes a
printable PDF of the write-up and needs Chrome installed.

Three things come out at the end: [`report/report.md`](report/report.md) to
read, [`report/index.html`](report/index.html) to share, and
`report/walking-speed-from-eeg.pdf` to print or hand in.

## Things worth knowing about the data

- **Person S32 is left out.** The header of their 1.0 m/s file lists channel
  names that do not match the other 176 recordings, so there is no safe way to
  tell which column is which electrode. That leaves 58 people and 174
  recordings.
- **The reference electrode is rebuilt.** The files are recorded against Pz, so
  there is no Pz column in them. The dataset ships a MATLAB script that moves
  everything onto a linked ear reference and rebuilds Pz. I translated it into
  Python and checked the output against it number by number.
- **Muscle files line up by clock time,** not by row number. They run 60.4 to
  70.4 seconds while every brain file is exactly 59.87 seconds, so matching row
  numbers would drift by up to ten seconds by the end.

## Licence

Code and write-up are MIT. See [`LICENSE`](LICENSE). The recordings belong to
their authors and are CC BY 4.0.
