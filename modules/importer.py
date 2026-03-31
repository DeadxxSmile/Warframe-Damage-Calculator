from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path
from typing import Dict, List

import openpyxl

from .constants import DAMAGE_TYPES, JSON_DAMAGE_INDEX_MAP, WEAPON_SLOT_MAP
from .mod_parser import parse_effects


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS weapons (
            weapon TEXT PRIMARY KEY,
            unique_name TEXT,
            product_category TEXT,
            slot_group TEXT,
            dmg REAL NOT NULL,
            impact REAL NOT NULL DEFAULT 0,
            punc REAL NOT NULL DEFAULT 0,
            slash REAL NOT NULL DEFAULT 0,
            heat REAL NOT NULL DEFAULT 0,
            cold REAL NOT NULL DEFAULT 0,
            elec REAL NOT NULL DEFAULT 0,
            toxin REAL NOT NULL DEFAULT 0,
            blast REAL NOT NULL DEFAULT 0,
            rad REAL NOT NULL DEFAULT 0,
            gas REAL NOT NULL DEFAULT 0,
            mag REAL NOT NULL DEFAULT 0,
            viral REAL NOT NULL DEFAULT 0,
            corr REAL NOT NULL DEFAULT 0,
            void REAL NOT NULL DEFAULT 0,
            critchan REAL NOT NULL DEFAULT 0,
            critmult REAL NOT NULL DEFAULT 0,
            statchan REAL NOT NULL DEFAULT 0,
            firerate REAL NOT NULL DEFAULT 0,
            multi REAL NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(weapon COLLATE NOCASE);

        CREATE TABLE IF NOT EXISTS mods (
            unique_name TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mod_type TEXT,
            compat_name TEXT,
            slot_group TEXT,
            polarity TEXT,
            rarity TEXT,
            fusion_limit INTEGER NOT NULL DEFAULT 0,
            base_drain INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            effect_summary TEXT,
            supported INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_mods_name ON mods(name COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_mods_slot_group ON mods(slot_group);

        CREATE TABLE IF NOT EXISTS mod_effects (
            unique_name TEXT NOT NULL,
            rank INTEGER NOT NULL,
            position INTEGER NOT NULL,
            effect_code TEXT NOT NULL,
            effect_value REAL NOT NULL,
            effect_text TEXT NOT NULL,
            PRIMARY KEY (unique_name, rank, position)
        );
        CREATE INDEX IF NOT EXISTS idx_mod_effects_unique_rank ON mod_effects(unique_name, rank);
        """
    )


def upsert_weapon_rows(connection: sqlite3.Connection, rows: List[Dict[str, float | str]]) -> None:
    sql = """
        INSERT INTO weapons (
            weapon, unique_name, product_category, slot_group, dmg, impact, punc, slash, heat, cold, elec, toxin, blast,
            rad, gas, mag, viral, corr, void, critchan, critmult, statchan, firerate, multi
        ) VALUES (
            :weapon, :unique_name, :product_category, :slot_group, :dmg, :impact, :punc, :slash, :heat, :cold, :elec, :toxin, :blast,
            :rad, :gas, :mag, :viral, :corr, :void, :critchan, :critmult, :statchan, :firerate, :multi
        )
        ON CONFLICT(weapon) DO UPDATE SET
            unique_name = excluded.unique_name,
            product_category = excluded.product_category,
            slot_group = excluded.slot_group,
            dmg = excluded.dmg,
            impact = excluded.impact,
            punc = excluded.punc,
            slash = excluded.slash,
            heat = excluded.heat,
            cold = excluded.cold,
            elec = excluded.elec,
            toxin = excluded.toxin,
            blast = excluded.blast,
            rad = excluded.rad,
            gas = excluded.gas,
            mag = excluded.mag,
            viral = excluded.viral,
            corr = excluded.corr,
            void = excluded.void,
            critchan = excluded.critchan,
            critmult = excluded.critmult,
            statchan = excluded.statchan,
            firerate = excluded.firerate,
            multi = excluded.multi
    """
    connection.executemany(sql, rows)


def replace_mod_rows(connection: sqlite3.Connection, mod_rows: List[Dict[str, object]], effect_rows: List[Dict[str, object]]) -> None:
    connection.execute("DELETE FROM mods")
    connection.execute("DELETE FROM mod_effects")
    connection.executemany(
        """
        INSERT INTO mods (
            unique_name, name, mod_type, compat_name, slot_group, polarity, rarity, fusion_limit,
            base_drain, description, effect_summary, supported
        ) VALUES (
            :unique_name, :name, :mod_type, :compat_name, :slot_group, :polarity, :rarity, :fusion_limit,
            :base_drain, :description, :effect_summary, :supported
        )
        """,
        mod_rows,
    )
    connection.executemany(
        """
        INSERT INTO mod_effects (
            unique_name, rank, position, effect_code, effect_value, effect_text
        ) VALUES (
            :unique_name, :rank, :position, :effect_code, :effect_value, :effect_text
        )
        """,
        effect_rows,
    )


def _empty_damage_row() -> Dict[str, float]:
    return {damage_type.lower(): 0.0 for damage_type in DAMAGE_TYPES}


def rows_from_spreadsheet(xlsx_path: str | Path) -> List[Dict[str, float | str]]:
    workbook = openpyxl.load_workbook(xlsx_path, data_only=True)
    sheet = workbook["Weapon-Data"]
    output: List[Dict[str, float | str]] = []

    for row in sheet.iter_rows(min_row=3, values_only=True):
        if not row or not row[0]:
            continue
        payload = _empty_damage_row()
        payload.update(
            {
                "weapon": str(row[0]),
                "unique_name": "",
                "product_category": "",
                "slot_group": _slot_group_from_category(""),
                "dmg": float(row[1] or 0),
                "critchan": float(row[16] or 0),
                "critmult": float(row[17] or 0),
                "statchan": float(row[18] or 0),
                "firerate": float(row[19] or 0),
                "multi": float(row[20] or 0),
            }
        )
        for idx, damage_type in enumerate(DAMAGE_TYPES, start=2):
            payload[damage_type.lower()] = float(row[idx] or 0)
        output.append(payload)

    return output


def rows_from_cleaned_json(zip_path: str | Path) -> List[Dict[str, float | str]]:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        json_name = next(name for name in names if name.lower().endswith(".json"))
        payload = json.loads(archive.read(json_name))

    weapons = payload.get("ExportWeapons", [])
    output: List[Dict[str, float | str]] = []
    for item in weapons:
        name = item.get("name")
        if not name:
            continue

        category = str(item.get("productCategory") or "")
        damage_per_shot = item.get("damagePerShot") or []
        row = _empty_damage_row()
        row.update(
            {
                "weapon": str(name),
                "unique_name": str(item.get("uniqueName") or ""),
                "product_category": category,
                "slot_group": _slot_group_from_category(category),
                "dmg": float(item.get("totalDamage") or 0),
                "critchan": float(item.get("criticalChance") or 0),
                "critmult": float(item.get("criticalMultiplier") or 0),
                "statchan": float(item.get("procChance") or 0),
                "firerate": float(item.get("fireRate") or 0),
                "multi": float(item.get("multishot") or 0),
            }
        )

        for damage_type, index in JSON_DAMAGE_INDEX_MAP.items():
            if index < len(damage_per_shot):
                row[damage_type.lower()] = float(damage_per_shot[index] or 0)

        output.append(row)

    return output


def mods_from_cleaned_json(zip_path: str | Path) -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    with zipfile.ZipFile(zip_path) as archive:
        payload = json.loads(archive.read("ExportUpgrades_en_Cleaned.json"))

    upgrades = payload.get("ExportUpgrades", [])
    mod_rows: List[Dict[str, object]] = []
    effect_rows: List[Dict[str, object]] = []

    for item in upgrades:
        unique_name = str(item.get("uniqueName") or "")
        name = str(item.get("name") or "")
        if not unique_name or not name:
            continue

        slot_group = _slot_group_from_mod(item)
        rank_entries = item.get("levelStats") or []
        supported = False
        summary_bits: list[str] = []

        for rank, entry in enumerate(rank_entries):
            stat_lines = entry.get("stats") or []
            next_position = 1
            for stat_line in stat_lines:
                effects = parse_effects(str(stat_line))
                if effects:
                    supported = True
                    summary_bits.extend(effect.text for effect in effects if effect.text not in summary_bits)
                for effect in effects:
                    effect_rows.append(
                        {
                            "unique_name": unique_name,
                            "rank": rank,
                            "position": next_position,
                            "effect_code": effect.code,
                            "effect_value": effect.value,
                            "effect_text": effect.text,
                        }
                    )
                    next_position += 1

        description = " ".join(item.get("description") or [])
        mod_rows.append(
            {
                "unique_name": unique_name,
                "name": name,
                "mod_type": str(item.get("type") or ""),
                "compat_name": str(item.get("compatName") or ""),
                "slot_group": slot_group,
                "polarity": str(item.get("polarity") or ""),
                "rarity": str(item.get("rarity") or ""),
                "fusion_limit": int(item.get("fusionLimit") or 0),
                "base_drain": int(item.get("baseDrain") or 0),
                "description": description,
                "effect_summary": ", ".join(summary_bits),
                "supported": 1 if supported and slot_group in {"PRIMARY", "SECONDARY", "MELEE", "ANY"} else 0,
            }
        )

    return mod_rows, effect_rows


def _slot_group_from_category(category: str) -> str:
    return WEAPON_SLOT_MAP.get(category, "PRIMARY")


def _slot_group_from_mod(item: dict) -> str:
    mod_type = str(item.get("type") or "").upper()
    compat = str(item.get("compatName") or "").upper()

    if mod_type == "PRIMARY":
        return "PRIMARY"
    if mod_type == "SECONDARY":
        return "SECONDARY"
    if mod_type == "MELEE":
        return "MELEE"

    if compat in {"RIFLE", "SHOTGUN", "BOW", "SNIPER", "ASSAULT RIFLE", "PRIMARY", "TOME"}:
        return "PRIMARY"
    if compat in {"PISTOL", "SECONDARY"}:
        return "SECONDARY"
    if compat in {"MELEE", "CLAWS", "DAGGERS", "POLEARMS", "SWORDS", "THROWN MELEE", "ARCHMELEE"}:
        return "MELEE"
    if compat in {"ANY", ""}:
        return "ANY"

    return "OTHER"


def build_database(
    db_path: str | Path,
    cleaned_weapons_zip_path: str | Path,
    cleaned_upgrades_zip_path: str | Path,
    spreadsheet_xlsx_path: str | Path | None = None,
) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        create_schema(connection)

        if spreadsheet_xlsx_path and Path(spreadsheet_xlsx_path).exists():
            upsert_weapon_rows(connection, rows_from_spreadsheet(spreadsheet_xlsx_path))

        upsert_weapon_rows(connection, rows_from_cleaned_json(cleaned_weapons_zip_path))
        mod_rows, effect_rows = mods_from_cleaned_json(cleaned_upgrades_zip_path)
        replace_mod_rows(connection, mod_rows, effect_rows)
        connection.commit()
