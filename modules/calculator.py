from __future__ import annotations

import math
from typing import Dict

from .constants import (
    DAMAGE_TYPES,
    DEFAULT_HUD_DECIMALS,
    FACTION_MULTIPLIERS,
    FINAL_DAMAGE_DECIMALS,
    HUD_ROUNDING_PRECISION,
    PHYSICAL_DAMAGE_TYPES,
)
from .models import CalculationInputs, CalculationResults, Weapon
from .rounding import excel_round


class DamageCalculator:
    def calculate(self, weapon: Weapon, inputs: CalculationInputs) -> CalculationResults:
        base_weapon_damage = float(weapon.dmg)
        valence_multiplier = (float(inputs.valence_base) / base_weapon_damage) if base_weapon_damage else 0.0
        weapon_total_damage = base_weapon_damage + (base_weapon_damage * valence_multiplier)
        quanta = weapon_total_damage / 16 if weapon_total_damage else 0.0

        lich_damage = self._build_lich_damage(weapon, inputs, base_weapon_damage, valence_multiplier)
        faction_modifiers = self._build_faction_modifiers(inputs.faction)
        armor_modifiers = self._build_armor_modifiers(inputs.armor_value, faction_modifiers)

        hud_damage_by_type: Dict[str, float] = {}
        final_damage_by_type: Dict[str, float] = {}

        true_mod = inputs.mod_for("TRUE")
        bane_mod = inputs.mod_for("BANE")

        for damage_type in DAMAGE_TYPES:
            hud_damage_by_type[damage_type] = self._calculate_hud_damage_for_type(
                weapon=weapon,
                damage_type=damage_type,
                quanta=quanta,
                weapon_total_damage=weapon_total_damage,
                lich_damage=lich_damage,
                mod_value=inputs.mod_for(damage_type),
                true_mod=true_mod,
            )
            final_damage_by_type[damage_type] = self._calculate_final_damage_for_type(
                weapon=weapon,
                damage_type=damage_type,
                quanta=quanta,
                weapon_total_damage=weapon_total_damage,
                lich_damage=lich_damage,
                mod_value=inputs.mod_for(damage_type),
                armor_modifier=armor_modifiers[damage_type],
                true_mod=true_mod,
            )

        hud_total = sum(hud_damage_by_type.values()) * weapon.multi
        hud_total_with_bane = (hud_total * bane_mod) if bane_mod > 0 else hud_total

        final_total = excel_round(sum(final_damage_by_type.values()), 0)
        final_total_with_bane = excel_round(final_total * bane_mod, 0) if bane_mod > 0 else final_total

        return CalculationResults(
            base_weapon_damage=base_weapon_damage,
            quanta=quanta,
            valence_multiplier=valence_multiplier,
            weapon_total_damage=weapon_total_damage,
            lich_damage=lich_damage,
            faction_modifiers=faction_modifiers,
            armor_modifiers=armor_modifiers,
            hud_damage_by_type=hud_damage_by_type,
            final_damage_by_type=final_damage_by_type,
            aggregated_mods=dict(inputs.mods),
            hud_total=hud_total,
            hud_total_with_bane=hud_total_with_bane,
            final_total=final_total,
            final_total_with_bane=final_total_with_bane,
        )

    def _build_faction_modifiers(self, faction: str) -> Dict[str, float]:
        return {damage_type: float(FACTION_MULTIPLIERS[faction][damage_type]) for damage_type in DAMAGE_TYPES}

    def _build_armor_modifiers(self, armor_value: float, faction_modifiers: Dict[str, float]) -> Dict[str, float]:
        armor_term = (1 - (0.9 * math.sqrt(max(armor_value, 0.0) / 2700.0))) if armor_value > 0 else 1.0
        return {damage_type: armor_term * faction_modifiers[damage_type] for damage_type in DAMAGE_TYPES}

    def _build_lich_damage(
        self,
        weapon: Weapon,
        inputs: CalculationInputs,
        base_weapon_damage: float,
        valence_multiplier: float,
    ) -> Dict[str, float]:
        lich_element = (inputs.lich_element or "").strip().upper()
        if not lich_element or valence_multiplier <= 0:
            return {damage_type: 0.0 for damage_type in DAMAGE_TYPES}

        lich_damage = {damage_type: 0.0 for damage_type in DAMAGE_TYPES}
        bonus_value = base_weapon_damage * valence_multiplier

        if lich_element in PHYSICAL_DAMAGE_TYPES:
            lich_damage[lich_element] = bonus_value
            return lich_damage

        mod_heat = inputs.mod_for("HEAT") > 0
        mod_cold = inputs.mod_for("COLD") > 0
        mod_elec = inputs.mod_for("ELEC") > 0
        mod_toxin = inputs.mod_for("TOXIN") > 0
        mod_blast = inputs.mod_for("BLAST") > 0
        mod_rad = inputs.mod_for("RAD") > 0
        mod_gas = inputs.mod_for("GAS") > 0
        mod_mag = inputs.mod_for("MAG") > 0
        mod_viral = inputs.mod_for("VIRAL") > 0
        mod_corr = inputs.mod_for("CORR") > 0

        base_blast = weapon.damage_for("BLAST") > 0
        base_rad = weapon.damage_for("RAD") > 0
        base_gas = weapon.damage_for("GAS") > 0
        base_mag = weapon.damage_for("MAG") > 0
        base_viral = weapon.damage_for("VIRAL") > 0
        base_corr = weapon.damage_for("CORR") > 0

        if lich_element == "BLAST" or (lich_element in {"HEAT", "COLD"} and (base_blast or (mod_heat and mod_cold) or mod_blast)):
            lich_damage["BLAST"] = bonus_value
        if lich_element == "RAD" or (lich_element in {"HEAT", "ELEC"} and (base_rad or (mod_heat and mod_elec) or mod_rad)):
            lich_damage["RAD"] = bonus_value
        if lich_element == "GAS" or (lich_element in {"HEAT", "TOXIN"} and (base_gas or (mod_heat and mod_toxin) or mod_gas)):
            lich_damage["GAS"] = bonus_value
        if lich_element == "MAG" or (lich_element in {"COLD", "ELEC"} and (base_mag or (mod_cold and mod_elec) or mod_mag)):
            lich_damage["MAG"] = bonus_value
        if lich_element == "VIRAL" or (lich_element in {"COLD", "TOXIN"} and (base_viral or (mod_cold and mod_toxin) or mod_viral)):
            lich_damage["VIRAL"] = bonus_value
        if lich_element == "CORR" or (lich_element in {"ELEC", "TOXIN"} and (base_corr or (mod_elec and mod_toxin) or mod_corr)):
            lich_damage["CORR"] = bonus_value

        if lich_element == "HEAT":
            blocked = base_blast or base_rad or base_gas or (mod_heat and mod_cold) or (mod_heat and mod_toxin) or (mod_heat and mod_elec) or lich_damage["BLAST"] > 0 or lich_damage["RAD"] > 0 or lich_damage["GAS"] > 0
            if not blocked:
                lich_damage["HEAT"] = bonus_value
        if lich_element == "COLD":
            blocked = base_blast or base_mag or base_viral or (mod_heat and mod_cold) or (mod_cold and mod_elec) or (mod_cold and mod_toxin) or mod_blast or mod_mag or mod_viral
            if not blocked:
                lich_damage["COLD"] = bonus_value
        if lich_element == "ELEC":
            blocked = base_rad or base_mag or base_corr or (mod_heat and mod_elec) or (mod_cold and mod_elec) or (mod_elec and mod_toxin) or mod_rad or mod_mag or mod_corr
            if not blocked:
                lich_damage["ELEC"] = bonus_value
        if lich_element == "TOXIN":
            blocked = base_gas or base_viral or base_corr or (mod_heat and mod_toxin) or (mod_cold and mod_toxin) or (mod_elec and mod_toxin) or mod_gas or mod_viral or mod_corr
            if not blocked:
                lich_damage["TOXIN"] = bonus_value
        if lich_element == "VOID":
            lich_damage["VOID"] = bonus_value

        return lich_damage

    def _calculate_hud_damage_for_type(
        self,
        weapon: Weapon,
        damage_type: str,
        quanta: float,
        weapon_total_damage: float,
        lich_damage: Dict[str, float],
        mod_value: float,
        true_mod: float,
    ) -> float:
        if quanta <= 0:
            return 0.0

        base_value = weapon.damage_for(damage_type) + lich_damage[damage_type]
        if damage_type in PHYSICAL_DAMAGE_TYPES:
            raw = base_value * (1 + mod_value)
        else:
            raw = base_value + (weapon_total_damage * mod_value)

        rounding_digits = HUD_ROUNDING_PRECISION.get(damage_type, DEFAULT_HUD_DECIMALS)
        mod_screen = excel_round(raw / quanta, rounding_digits) * quanta
        return mod_screen + (mod_screen * true_mod)

    def _calculate_final_damage_for_type(
        self,
        weapon: Weapon,
        damage_type: str,
        quanta: float,
        weapon_total_damage: float,
        lich_damage: Dict[str, float],
        mod_value: float,
        armor_modifier: float,
        true_mod: float,
    ) -> float:
        if quanta <= 0:
            return 0.0

        base_value = weapon.damage_for(damage_type) + lich_damage[damage_type]
        if damage_type in PHYSICAL_DAMAGE_TYPES:
            raw = base_value * (1 + mod_value)
        else:
            raw = base_value + (weapon_total_damage * mod_value)

        quantized = excel_round(raw / quanta, 0) * quanta
        rounded = excel_round(quantized, FINAL_DAMAGE_DECIMALS)
        scaled = rounded * armor_modifier
        return scaled + (scaled * true_mod)
