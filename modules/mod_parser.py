from __future__ import annotations

import re
from typing import List

from .models import ModEffect

TOKEN_PATTERN = re.compile(r'([+-]?\d+(?:\.\d+)?%|x\d+(?:\.\d+)?)', re.IGNORECASE)
TAG_PATTERN = re.compile(r'<[^>]+>')
WHITESPACE_PATTERN = re.compile(r'\s+')

PHRASE_MAP = {
    "impact": "IMPACT",
    "puncture": "PUNC",
    "slash": "SLASH",
    "heat": "HEAT",
    "cold": "COLD",
    "electricity": "ELEC",
    "electric": "ELEC",
    "toxin": "TOXIN",
    "blast": "BLAST",
    "radiation": "RAD",
    "gas": "GAS",
    "magnetic": "MAG",
    "viral": "VIRAL",
    "corrosive": "CORR",
    "void": "VOID",
}

IGNORE_TERMS = {
    "status chance",
    "critical chance",
    "critical damage",
    "reload speed",
    "fire rate",
    "attack speed",
    "magazine capacity",
    "ammo maximum",
    "recoil",
    "zoom",
    "punch through",
    "combo count chance",
    "finisher damage",
    "slam attack",
    "heavy attack",
    "status duration",
    "projectile speed",
    "flight speed",
    "accuracy",
    "holster rate",
    "initial combo",
    "combo duration",
    "chance to gain",
    "ammo mutation",
    "maximum ammo",
    "beam length",
    "weapon recoil",
    "spread",
}


def parse_effects(stat_line: str) -> List[ModEffect]:
    cleaned_line = clean_stat_line(stat_line)
    matches = list(TOKEN_PATTERN.finditer(cleaned_line))
    effects: List[ModEffect] = []

    for index, match in enumerate(matches, start=1):
        raw_value = match.group(1).strip().lower()
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(cleaned_line)
        label = cleaned_line[start:end].strip().lower()
        code = map_label_to_code(label)
        if not code:
            continue

        if raw_value.startswith('x'):
            value = float(raw_value[1:])
        else:
            value = float(raw_value.rstrip('%')) / 100.0

        text = f"{raw_value.upper() if raw_value.startswith('x') else raw_value} {label}".strip()
        effects.append(ModEffect(code=code, value=value, text=text, position=index))

    return effects


def clean_stat_line(stat_line: str) -> str:
    cleaned = TAG_PATTERN.sub('', stat_line or '')
    cleaned = cleaned.replace('×', 'x')
    cleaned = WHITESPACE_PATTERN.sub(' ', cleaned).strip()
    return cleaned


def map_label_to_code(label: str) -> str | None:
    normalized = WHITESPACE_PATTERN.sub(' ', label.strip().lower())

    if any(term == normalized or term in normalized for term in IGNORE_TERMS):
        return None

    if 'damage to grineer' in normalized:
        return 'BANE_GRINEER'
    if 'damage to corpus' in normalized:
        return 'BANE_CORPUS'
    if 'damage to infested' in normalized:
        return 'BANE_INFESTED'
    if 'damage to corrupted' in normalized:
        return 'BANE_CORRUPTED'

    normalized = normalized.removesuffix(' damage').strip()

    for phrase, code in PHRASE_MAP.items():
        if normalized == phrase or normalized.endswith(f' {phrase}') or normalized.startswith(f'{phrase} '):
            return code

    if normalized == 'damage':
        return 'TRUE'

    return None
