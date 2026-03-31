from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from modules.constants import APP_NAME

DB_NAME = "weapons.db"
SETTINGS_NAME = "settings.json"
SOURCE_FILES = [
    "ExportWeapons_en_Cleaned.zip",
    "ExportKeys_en_Cleaned.zip",
    "Warframe-Damage-Calculator_v2.xlsx",
]


def get_appdata_root() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def ensure_app_dirs() -> dict[str, Path]:
    root = get_appdata_root()
    data = root / "data"
    source = root / "source"
    temp = root / "temp"
    builds = root / "builds"
    for folder in (root, data, source, temp, builds):
        folder.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "data": data,
        "source": source,
        "temp": temp,
        "builds": builds,
        "db": data / DB_NAME,
        "settings": root / SETTINGS_NAME,
    }


def seed_source_files(project_root: Path) -> None:
    paths = ensure_app_dirs()
    bundled_source = project_root / "source"
    for file_name in SOURCE_FILES:
        source_file = bundled_source / file_name
        target_file = paths["source"] / file_name
        if source_file.exists() and not target_file.exists():
            shutil.copy2(source_file, target_file)


def default_settings() -> dict[str, str]:
    return {}


def load_settings() -> dict[str, str]:
    paths = ensure_app_dirs()
    settings_path = paths["settings"]
    settings = default_settings()
    if settings_path.exists():
        try:
            saved = json.loads(settings_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                settings.update({k: str(v) for k, v in saved.items()})
        except Exception:
            pass
    return settings


def save_settings(settings: dict[str, str]) -> None:
    paths = ensure_app_dirs()
    paths["settings"].write_text(json.dumps(settings, indent=2), encoding="utf-8")
