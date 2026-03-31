from __future__ import annotations

from pathlib import Path

from modules.app_paths import ensure_app_dirs, seed_source_files
from modules.importer import build_database


def main() -> None:
    project_root = Path(__file__).resolve().parent
    seed_source_files(project_root)
    paths = ensure_app_dirs()

    cleaned_weapons_zip = paths["source"] / "ExportWeapons_en_Cleaned.zip"
    cleaned_upgrades_zip = paths["source"] / "ExportKeys_en_Cleaned.zip"
    spreadsheet_xlsx = paths["source"] / "Warframe-Damage-Calculator_v2.xlsx"

    build_database(
        db_path=paths["db"],
        cleaned_weapons_zip_path=cleaned_weapons_zip,
        cleaned_upgrades_zip_path=cleaned_upgrades_zip,
        spreadsheet_xlsx_path=spreadsheet_xlsx if spreadsheet_xlsx.exists() else None,
    )
    print(f"Built database at: {paths['db']}")


if __name__ == "__main__":
    main()
