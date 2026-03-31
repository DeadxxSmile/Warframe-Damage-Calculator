from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .constants import DAMAGE_TYPES, MOD_STAT_ORDER


@dataclass(slots=True)
class Weapon:
    weapon: str
    unique_name: str
    product_category: str
    slot_group: str
    dmg: float
    critchan: float
    critmult: float
    statchan: float
    firerate: float
    multi: float
    damage: Dict[str, float] = field(default_factory=dict)

    def damage_for(self, damage_type: str) -> float:
        return float(self.damage.get(damage_type, 0.0))


@dataclass(slots=True)
class ModEffect:
    code: str
    value: float
    text: str
    position: int = 0


@dataclass(slots=True)
class Mod:
    unique_name: str
    name: str
    mod_type: str
    compat_name: str
    polarity: str
    rarity: str
    fusion_limit: int
    base_drain: int
    description: str
    effect_summary: str
    supported: bool


@dataclass(slots=True)
class EquippedMod:
    mod: Mod | None = None
    rank: int = 0
    effects: List[ModEffect] = field(default_factory=list)


@dataclass(slots=True)
class CalculationInputs:
    weapon_name: str
    faction: str
    armor_value: float
    lich_element: str = ""
    valence_base: float = 0.0
    mods: Dict[str, float] = field(default_factory=dict)

    def mod_for(self, damage_type: str) -> float:
        return float(self.mods.get(damage_type, 0.0))


@dataclass(slots=True)
class CalculationResults:
    base_weapon_damage: float
    quanta: float
    valence_multiplier: float
    weapon_total_damage: float
    lich_damage: Dict[str, float]
    faction_modifiers: Dict[str, float]
    armor_modifiers: Dict[str, float]
    hud_damage_by_type: Dict[str, float]
    final_damage_by_type: Dict[str, float]
    aggregated_mods: Dict[str, float]
    hud_total: float
    hud_total_with_bane: float
    final_total: float
    final_total_with_bane: float

    def rows_for_hud(self) -> List[tuple[str, float]]:
        return [(damage_type, self.hud_damage_by_type[damage_type]) for damage_type in DAMAGE_TYPES]

    def rows_for_final(self) -> List[tuple[str, float]]:
        return [(damage_type, self.final_damage_by_type[damage_type]) for damage_type in DAMAGE_TYPES]

    def rows_for_mods(self) -> List[tuple[str, float]]:
        return [(code, self.aggregated_mods.get(code, 0.0)) for code in MOD_STAT_ORDER]
