from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .constants import BASE_ELEMENT_TYPES, BANE_CODE_MAP, ELEMENT_COMBINATIONS, MOD_STAT_ORDER
from .models import EquippedMod


class ModAggregator:
    def aggregate(self, equipped_mods: Iterable[EquippedMod], faction: str) -> Dict[str, float]:
        totals = defaultdict(float)
        pending_element: tuple[str, float] | None = None

        bane_codes = BANE_CODE_MAP.get(faction, set())

        for equipped in equipped_mods:
            if equipped.mod is None:
                continue

            for effect in equipped.effects:
                code = effect.code
                if code in bane_codes:
                    totals["BANE"] += effect.value
                    continue

                if code in BASE_ELEMENT_TYPES:
                    if pending_element is None:
                        pending_element = (code, effect.value)
                        continue

                    prior_code, prior_value = pending_element
                    if prior_code != code:
                        combo_code = ELEMENT_COMBINATIONS.get(frozenset((prior_code, code)))
                        if combo_code:
                            totals[combo_code] += prior_value + effect.value
                            pending_element = None
                            continue

                    totals[prior_code] += prior_value
                    pending_element = (code, effect.value)
                    continue

                totals[code] += effect.value

        if pending_element is not None:
            totals[pending_element[0]] += pending_element[1]

        return {code: float(totals.get(code, 0.0)) for code in MOD_STAT_ORDER}
