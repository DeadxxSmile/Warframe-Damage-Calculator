from __future__ import annotations

APP_NAME = "WDC"
APP_TITLE = "Warframe Damage Calculator by TenZeroGG"
APP_VERSION = "1.0.1"
WINDOW_TITLE = f"{APP_TITLE} v{APP_VERSION}"

DAMAGE_TYPES = [
    "IMPACT",
    "PUNC",
    "SLASH",
    "HEAT",
    "COLD",
    "ELEC",
    "TOXIN",
    "BLAST",
    "RAD",
    "GAS",
    "MAG",
    "VIRAL",
    "CORR",
    "VOID",
]

PHYSICAL_DAMAGE_TYPES = {"IMPACT", "PUNC", "SLASH"}
BASE_ELEMENT_TYPES = {"HEAT", "COLD", "ELEC", "TOXIN"}
COMBINED_ELEMENT_TYPES = {"BLAST", "RAD", "GAS", "MAG", "VIRAL", "CORR"}

DISPLAY_NAMES = {
    "PUNC": "Puncture",
    "RAD": "Radiation",
    "MAG": "Magnetic",
    "CORR": "Corrosive",
    "ELEC": "Electric",
    "TRUE": "Base Damage",
    "BANE": "Faction Damage",
}

MOD_STAT_ORDER = [*DAMAGE_TYPES, "TRUE", "BANE"]

HUD_ROUNDING_PRECISION = {
    "MAG": 3,
}

DEFAULT_HUD_DECIMALS = 4
FINAL_DAMAGE_DECIMALS = 3

FACTION_MULTIPLIERS = {
    "Grineer": {"IMPACT": 1.5, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 1, "VIRAL": 1, "CORR": 1.5, "VOID": 1, "TRUE": 1},
    "Kuva": {"IMPACT": 1.5, "PUNC": 1, "SLASH": 1, "HEAT": 0.5, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 1, "VIRAL": 1, "CORR": 1.5, "VOID": 1, "TRUE": 1},
    "Corpus": {"IMPACT": 1, "PUNC": 1.5, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 1.5, "VIRAL": 1, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Amalgam": {"IMPACT": 1, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1.5, "TOXIN": 1, "BLAST": 0.5, "RAD": 1, "GAS": 1, "MAG": 1.5, "VIRAL": 1, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Infested": {"IMPACT": 1, "PUNC": 1, "SLASH": 1.5, "HEAT": 1.5, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 1, "VIRAL": 1, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Deimos": {"IMPACT": 1, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1.5, "RAD": 1, "GAS": 1.5, "MAG": 1, "VIRAL": 0.5, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Orokin": {"IMPACT": 1, "PUNC": 1.5, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 0.5, "GAS": 1, "MAG": 1, "VIRAL": 1.5, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Sentient": {"IMPACT": 1, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1.5, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1.5, "GAS": 1, "MAG": 1, "VIRAL": 1, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Narmer": {"IMPACT": 1, "PUNC": 1, "SLASH": 1.5, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1.5, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 0.5, "VIRAL": 1, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Murmur": {"IMPACT": 1, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1.5, "TOXIN": 1, "BLAST": 1, "RAD": 1.5, "GAS": 1, "MAG": 1, "VIRAL": 0.5, "CORR": 1, "VOID": 1, "TRUE": 1},
    "Zairman": {"IMPACT": 1, "PUNC": 1, "SLASH": 1, "HEAT": 1, "COLD": 1, "ELEC": 1, "TOXIN": 1, "BLAST": 1, "RAD": 1, "GAS": 1, "MAG": 1, "VIRAL": 1, "CORR": 1, "VOID": 1.5, "TRUE": 1},
}

JSON_DAMAGE_INDEX_MAP = {
    "IMPACT": 0,
    "PUNC": 1,
    "SLASH": 2,
    "COLD": 3,
    "ELEC": 4,
    "HEAT": 5,
    "TOXIN": 6,
    "BLAST": 7,
    "RAD": 8,
    "GAS": 9,
    "MAG": 10,
    "VIRAL": 11,
    "CORR": 12,
}

BANE_CODE_MAP = {
    "Grineer": {"BANE_GRINEER"},
    "Kuva": {"BANE_GRINEER"},
    "Corpus": {"BANE_CORPUS"},
    "Amalgam": {"BANE_CORPUS"},
    "Infested": {"BANE_INFESTED"},
    "Deimos": {"BANE_INFESTED"},
    "Orokin": {"BANE_CORRUPTED"},
    "Sentient": set(),
    "Narmer": {"BANE_GRINEER", "BANE_CORPUS"},
    "Murmur": set(),
    "Zairman": set(),
}

ELEMENT_COMBINATIONS = {
    frozenset(("HEAT", "COLD")): "BLAST",
    frozenset(("HEAT", "ELEC")): "RAD",
    frozenset(("HEAT", "TOXIN")): "GAS",
    frozenset(("COLD", "ELEC")): "MAG",
    frozenset(("COLD", "TOXIN")): "VIRAL",
    frozenset(("ELEC", "TOXIN")): "CORR",
}

WEAPON_SLOT_MAP = {
    "LongGuns": "PRIMARY",
    "Pistols": "SECONDARY",
    "Melee": "MELEE",
    "Shotgun": "PRIMARY",
}

SEARCH_LIMIT = 250
MOD_SLOT_COUNT = 8
