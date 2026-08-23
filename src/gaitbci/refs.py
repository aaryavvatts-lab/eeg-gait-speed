"""Papers cited in the write-up.

Every entry was looked up through a live literature search and the DOI checked
against the record, so nothing here is from memory.
"""
from __future__ import annotations

REFS: dict[str, dict] = {
    "katmah2026": {
        "authors": "Katmah, R., AlShehhi, A., Kosaji, D., Al-Rahmani, N., "
                   "Abdullah, M., Hulleck, A. A. V., and Khalaf, K.",
        "year": 2026,
        "title": "A multimodal gait dataset of brain activity, muscle activity, "
                 "kinematics and ground forces in young adults (version 1.0.0)",
        "venue": "PhysioNet",
        "doi": "10.13026/r0ea-7161",
    },
    "nordin2019": {
        "authors": "Nordin, A. D., Hairston, W. D., and Ferris, D. P.",
        "year": 2019,
        "title": "Faster gait speeds reduce alpha and beta EEG spectral power "
                 "from human sensorimotor cortex",
        "venue": "IEEE Transactions on Biomedical Engineering",
        "doi": "10.1109/tbme.2019.2921766",
    },
    "nathan2016": {
        "authors": "Nathan, K., and Contreras-Vidal, J. L.",
        "year": 2016,
        "title": "Negligible motion artifacts in scalp electroencephalography "
                 "(EEG) during treadmill walking",
        "venue": "Frontiers in Human Neuroscience",
        "doi": "10.3389/fnhum.2015.00708",
    },
    "jacobsen2020": {
        "authors": "Jacobsen, N. S. J., Blum, S., Witt, K., and Debener, S.",
        "year": 2020,
        "title": "A walk in the park? Characterizing gait-related artifacts in "
                 "mobile EEG recordings",
        "venue": "European Journal of Neuroscience",
        "doi": "10.1111/ejn.14965",
    },
    "gorjan2022": {
        "authors": "Gorjan, D., Gramann, K., De Pauw, K., and Marusic, U.",
        "year": 2022,
        "title": "Removal of movement-induced EEG artifacts: current state of "
                 "the art and guidelines",
        "venue": "Journal of Neural Engineering",
        "doi": "10.1088/1741-2552/ac542c",
    },
    "tortora2020": {
        "authors": "Tortora, S., Tonin, L., Chisari, C., Micera, S., "
                   "Menegatti, E., and Artoni, F.",
        "year": 2020,
        "title": "Hybrid human-machine interface for gait decoding through "
                 "Bayesian fusion of EEG and EMG classifiers",
        "venue": "Frontiers in Neurorobotics",
        "doi": "10.3389/fnbot.2020.582728",
    },
    "artoni2017": {
        "authors": "Artoni, F., Fanciullacci, C., Bertolucci, F., Panarese, A., "
                   "Makeig, S., Micera, S., and Chisari, C.",
        "year": 2017,
        "title": "Unidirectional brain to muscle connectivity reveals motor "
                 "cortex control of leg muscles during stereotyped walking",
        "venue": "NeuroImage",
        "doi": "10.1016/j.neuroimage.2017.07.013",
    },
    "tariq2018": {
        "authors": "Tariq, M., Trivailo, P. M., and Simic, M.",
        "year": 2018,
        "title": "EEG-based BCI control schemes for lower-limb assistive-robots",
        "venue": "Frontiers in Human Neuroscience",
        "doi": "10.3389/fnhum.2018.00312",
    },
    "marcel2007": {
        "authors": "Marcel, S., and Millan, J. del R.",
        "year": 2007,
        "title": "Person authentication using brainwaves (EEG) and maximum a "
                 "posteriori model adaptation",
        "venue": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
        "doi": "10.1109/tpami.2007.1012",
    },
    "gui2019": {
        "authors": "Gui, Q., Ruiz-Blondet, M. V., Laszlo, S., and Jin, Z.",
        "year": 2019,
        "title": "A survey on brain biometrics",
        "venue": "ACM Computing Surveys",
        "doi": "10.1145/3230632",
    },
    "leinonen2024": {
        "authors": "Leinonen, T., Wong, D., Vasankari, A., Wahab, A., "
                   "Nadarajah, R., Kaisti, M., and Airola, A.",
        "year": 2024,
        "title": "Empirical investigation of multi-source cross-validation in "
                 "clinical ECG classification",
        "venue": "Computers in Biology and Medicine",
        "doi": "10.1016/j.compbiomed.2024.109271",
    },
    "peterson2018": {
        "authors": "Peterson, S. M., and Ferris, D. P.",
        "year": 2018,
        "title": "Differentiation in theta and beta electrocortical activity "
                 "between visual and physical perturbations to walking and "
                 "standing balance",
        "venue": "eNeuro",
        "doi": "10.1523/eneuro.0207-18.2018",
    },
}

ORDER = [
    "katmah2026", "nordin2019", "nathan2016", "jacobsen2020", "gorjan2022",
    "tortora2020", "artoni2017", "tariq2018", "marcel2007", "gui2019",
    "leinonen2024", "peterson2018",
]


def numbered() -> dict[str, int]:
    """Map each key to its number in the reference list."""
    return {k: i + 1 for i, k in enumerate(ORDER)}


def markdown_list() -> list[str]:
    """The reference list, numbered, as markdown lines."""
    out = []
    for i, key in enumerate(ORDER, start=1):
        r = REFS[key]
        out.append(
            f"{i}. {r['authors']} ({r['year']}). {r['title']}. "
            f"*{r['venue']}*. https://doi.org/{r['doi']}"
        )
    return out


def html_list() -> str:
    """The reference list as HTML list items."""
    rows = []
    for key in ORDER:
        r = REFS[key]
        rows.append(
            f"<li id=\"ref-{key}\">{r['authors']} ({r['year']}). {r['title']}. "
            f"<em>{r['venue']}</em>. "
            f"<a href=\"https://doi.org/{r['doi']}\">doi.org/{r['doi']}</a></li>"
        )
    return "\n".join(rows)
