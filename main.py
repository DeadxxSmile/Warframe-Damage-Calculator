from __future__ import annotations

import sqlite3
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

from gui.app import DamageCalculatorWindow, build_application
from modules.app_paths import ensure_app_dirs, seed_source_files
from modules.database import ModRepository, WeaponRepository


def database_is_ready(db_path: Path) -> bool:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    try:
        with sqlite3.connect(db_path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='weapons'").fetchone()
            if not row or int(row[0]) == 0:
                return False
            count_row = connection.execute("SELECT COUNT(*) FROM weapons").fetchone()
            return bool(count_row and int(count_row[0]) > 0)
    except Exception:
        return False


def maybe_bootstrap_database(window: DamageCalculatorWindow) -> None:
    if database_is_ready(window.paths["db"]):
        return

    message = QMessageBox(window)
    message.setWindowTitle("Build Initial Data")
    message.setIcon(QMessageBox.Icon.Question)
    message.setText(
        "WDC needs its initial data before weapon calculations can be used. "
        "Build it now using fresh DE data when available, with bundled backup data as a fallback?"
    )
    message.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    message.setDefaultButton(QMessageBox.StandardButton.Yes)

    if message.exec() != QMessageBox.StandardButton.Yes:
        return

    try:
        outputs = window.run_data_pipeline(prefer_online=True)
        details = [
            f"Data source: {outputs['source_mode']}",
            f"Manifest decode path: {outputs['lzma_method']}",
            f"Database: {outputs['db_path']}",
        ]
        if outputs.get("refresh_error"):
            details.append(f"Fresh download failed, so WDC used bundled backup data: {outputs['refresh_error']}")
        QMessageBox.information(window, "Initial Data Ready", "\n".join(details))
    except Exception as exc:
        QMessageBox.critical(
            window,
            "Initial Data Failed",
            "WDC could not build its initial data. Open Settings later to retry with fresh or bundled backup data.\n\n" + str(exc),
        )


def main() -> None:
    project_root = Path(__file__).resolve().parent
    seed_source_files(project_root)
    paths = ensure_app_dirs()

    app = build_application(paths["db"])
    weapon_repository = WeaponRepository(paths["db"])
    mod_repository = ModRepository(paths["db"])

    window = DamageCalculatorWindow(weapon_repository, mod_repository, project_root=project_root)
    window.show()
    maybe_bootstrap_database(window)
    app.exec()


if __name__ == "__main__":
    main()
