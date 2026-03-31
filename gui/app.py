from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCompleter,
)

from modules.app_paths import ensure_app_dirs
from modules.calculator import DamageCalculator
from modules.constants import APP_TITLE, APP_VERSION, DAMAGE_TYPES, DISPLAY_NAMES, FACTION_MULTIPLIERS, MOD_SLOT_COUNT, MOD_STAT_ORDER, WINDOW_TITLE
from modules.database import ModRepository, WeaponRepository
from modules.importer import build_database
from modules.mod_engine import ModAggregator
from modules.models import CalculationInputs, EquippedMod, Mod, Weapon
from modules.updater import DataRefreshError, WarframeDataUpdater


DARK_STYLESHEET = """
QWidget {
    background-color: #11161f;
    color: #e6ecff;
    font-size: 12px;
}
QMainWindow, QScrollArea, QGroupBox, QFrame {
    background-color: #11161f;
}
QLineEdit, QComboBox, QSpinBox, QListWidget, QTableWidget, QTextEdit {
    background-color: #1a2230;
    color: #edf2ff;
    border: 1px solid #2b3850;
    border-radius: 8px;
    padding: 6px;
    selection-background-color: #2c6bed;
    selection-color: #ffffff;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView, QListWidget {
    background-color: #182131;
    alternate-background-color: #1d2738;
    color: #edf2ff;
    border: 1px solid #2b3850;
    selection-background-color: #2c6bed;
    selection-color: #ffffff;
}
QPushButton {
    background-color: #2c6bed;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #3d7af0;
}
QPushButton:pressed {
    background-color: #275dcb;
}
QGroupBox {
    border: 1px solid #283244;
    border-radius: 14px;
    margin-top: 14px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #9fb9ff;
}
QHeaderView::section {
    background-color: #20293a;
    color: #dce7ff;
    border: 0;
    border-right: 1px solid #33425d;
    padding: 6px;
}
QTableWidget {
    gridline-color: #2a3448;
    background-color: #182131;
    alternate-background-color: #1d2738;
    color: #edf2ff;
}
QTableWidget::item {
    padding: 6px;
    border: none;
    background: transparent;
}
QTableCornerButton::section {
    background-color: #20293a;
    border: 0;
}
QScrollBar:vertical {
    background-color: #141b27;
    width: 12px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #33425d;
    min-height: 24px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    border: none;
    height: 0;
}
QListWidget::item:selected {
    background-color: #2c6bed;
    border-radius: 6px;
}
"""

FAQ_TEXT = """
WDC FAQ - Warframe Damage Calculator by TenZeroGG
==============================

Why are there both HUD values and Final values?
-----------------------------------------------
The HUD / Mod Screen values show the damage buckets after the weapon, adversary bonus, and mod values have been built into each damage type. This view is useful for seeing what the build itself is doing before enemy modifiers are applied.

The Final values show the per-type damage buckets after faction resistances or weaknesses and armor are applied. This is the practical output against the selected target profile.

What is the valence input doing?
--------------------------------
The calculator works backward from the weapon's displayed bonus damage to recover the true adversary multiplier before the rest of the math runs.

True Valence = Valence Base / Base Weapon Damage

That recovered multiplier is then used to rebuild the weapon's actual total damage before mods and enemy calculations are applied.

Why is Quanta shown?
--------------------
WDC uses damage quanta to stay aligned with Warframe-style packet rounding.

Quanta = Weapon Total Damage / 16

That value is used in the HUD and final per-type rounding passes so the calculator stays aligned with in-game behavior.

Why can the HUD total and Final total be very different?
--------------------------------------------------------
Because enemy health type and armor matter a lot. The HUD side shows the built damage on the weapon. The Final side shows what survives after enemy modifiers are applied to each damage bucket.

How are elemental mods combined?
--------------------------------
Elemental effects are combined by slot order. Single elements are queued in slot order and paired into Blast, Radiation, Gas, Magnetic, Viral, or Corrosive when possible.

Why do faction mods show separately?
------------------------------------
Faction damage is tracked as its own multiplier so the calculator can show the pre-faction and post-faction totals separately.

How does WDC process the damage flow?
------------------------------------
WDC preserves the same layered logic used by the calculator engine:
- weapon lookup
- true valence reconstruction
- quanta-based rounding
- elemental combination by slot order
- HUD bucket calculation
- faction and armor application
- final total calculation

Why might adversary weapons still be slightly off?
--------------------------------------------------
Warframe does not expose enough decimal precision in every place needed to fully reconstruct the hidden values. The math is built to stay as close as possible to what the game shows, but there are still edge cases where the game's hidden precision wins.

Where is the database saved?
----------------------------
The SQLite database and source data live in WDC's AppData-backed folder so the app can be packaged later without relying on files sitting beside the executable.

How does the data updater work?
-------------------------------
WDC can download fresh public export data from DE and rebuild the SQLite database in one step. If the download cannot be completed, WDC can fall back to the bundled backup export files that ship with the app.
""".strip()


class SummaryCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("QFrame { background-color: #182131; border: 1px solid #2b3950; border-radius: 16px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        label = QLabel(title)
        label.setStyleSheet("color: #8ea9e6; font-size: 11px;")
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        layout.addWidget(label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class FAQDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_TITLE} FAQ")
        self.resize(880, 760)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(FAQ_TEXT)
        layout.addWidget(text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)




ENEMY_PRESETS = {
    "Custom": (None, None),
    "Grineer Heavy Armor": ("Grineer", 500),
    "Kuva Heavy Armor": ("Kuva", 600),
    "Corpus Tech": ("Corpus", 250),
    "Amalgam": ("Amalgam", 300),
    "Infested Heavy": ("Infested", 150),
    "Deimos Heavy": ("Deimos", 175),
    "Corrupted Heavy": ("Orokin", 400),
    "Sentient Durable": ("Sentient", 350),
    "Narmer Heavy": ("Narmer", 375),
    "Murmur Heavy": ("Murmur", 450),
    "Zariman Void": ("Zairman", 250),
}


class CompareBuildDialog(QDialog):
    def __init__(self, current_summary: list[tuple[str, str]], compare_summary: list[tuple[str, str]], compare_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Compare Builds")
        self.resize(760, 520)

        layout = QVBoxLayout(self)
        intro = QLabel(f"Current build is shown against: {compare_name}")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        table = QTableWidget(len(current_summary), 3)
        table.setHorizontalHeaderLabels(["Metric", "Current Build", "Compared Build"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        compare_map = {name: value for name, value in compare_summary}
        for row_index, (metric, current_value) in enumerate(current_summary):
            table.setItem(row_index, 0, QTableWidgetItem(metric))
            table.setItem(row_index, 1, QTableWidgetItem(current_value))
            table.setItem(row_index, 2, QTableWidgetItem(compare_map.get(metric, "-")))

        layout.addWidget(table, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class ModPickerDialog(QDialog):
    def __init__(self, mods: list[Mod], current_unique_name: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Mod")
        self.resize(760, 560)
        self.mods = mods
        self.selected_unique_name = current_unique_name

        layout = QVBoxLayout(self)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search mods...")
        self.list_widget = QListWidget()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(140)

        layout.addWidget(self.search_edit)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.detail_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.search_edit.textChanged.connect(self.refresh_list)
        self.list_widget.currentItemChanged.connect(self.on_current_changed)
        self.list_widget.itemDoubleClicked.connect(lambda *_: self.accept())

        self.refresh_list()

    def refresh_list(self) -> None:
        query = self.search_edit.text().strip().lower()
        self.list_widget.clear()
        selected_row = 0
        for mod in self.mods:
            haystack = f"{mod.name} {mod.effect_summary} {mod.description}".lower()
            if query and query not in haystack:
                continue
            label = mod.name
            if mod.effect_summary:
                label += f"  |  {mod.effect_summary[:72]}"
            if mod.polarity:
                label += f"  |  Polarity: {mod.polarity}"
            label += f"  |  Drain: {mod.base_drain}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, mod.unique_name)
            self.list_widget.addItem(item)
            if mod.unique_name == self.selected_unique_name:
                selected_row = self.list_widget.count() - 1

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(selected_row)

    def on_current_changed(self, current: QListWidgetItem | None) -> None:
        if current is None:
            self.detail_text.clear()
            return
        unique_name = current.data(Qt.ItemDataRole.UserRole)
        mod = next((entry for entry in self.mods if entry.unique_name == unique_name), None)
        if mod is None:
            self.detail_text.clear()
            return
        self.selected_unique_name = mod.unique_name
        lines = [mod.name]
        if mod.effect_summary:
            lines.append(mod.effect_summary)
        if mod.description and mod.description not in mod.effect_summary:
            lines.append(mod.description)
        lines.append(f"Polarity: {mod.polarity or 'None'}")
        lines.append(f"Base Drain: {mod.base_drain}")
        lines.append(f"Max Rank: {mod.fusion_limit}")
        lines.append(f"Compatibility: {mod.compat_name or mod.mod_type or 'General'}")
        self.detail_text.setPlainText("\n".join(lines))

    def chosen_unique_name(self) -> str | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)


class SettingsDialog(QDialog):
    def __init__(self, parent: "DamageCalculatorWindow") -> None:
        super().__init__(parent)
        self.window = parent
        self.paths = ensure_app_dirs()
        self.setWindowTitle(f"{APP_TITLE} Settings")
        self.resize(900, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        intro_box = QGroupBox("Updater and Storage")
        intro_layout = QVBoxLayout(intro_box)
        intro_layout.setContentsMargins(14, 18, 14, 14)
        intro_layout.setSpacing(10)

        intro_text = QLabel(
            "Use this panel to download the latest public export data, rebuild the SQLite database, "
            "and manage where WDC stores its working files. The updater uses Python LZMA recovery for "
            "DE's manifest index and can fall back to the bundled backup export files when fresh data "
            "cannot be reached."
        )
        intro_text.setWordWrap(True)
        intro_text.setStyleSheet("color: #dce7ff;")
        intro_layout.addWidget(intro_text)

        path_box = QGroupBox("App Paths")
        path_layout = QFormLayout(path_box)
        path_layout.setContentsMargins(12, 16, 12, 12)
        path_layout.setHorizontalSpacing(16)
        path_layout.setVerticalSpacing(10)

        self.root_path_label = QLabel(str(self.paths["root"]))
        self.db_path_label = QLabel(str(self.paths["db"]))
        self.source_path_label = QLabel(str(self.paths["source"]))
        for label in (self.root_path_label, self.db_path_label, self.source_path_label):
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setStyleSheet("color: #91a3c4;")

        path_layout.addRow("App Data Folder", self.root_path_label)
        path_layout.addRow("SQLite Database", self.db_path_label)
        path_layout.addRow("Source Folder", self.source_path_label)
        intro_layout.addWidget(path_box)
        layout.addWidget(intro_box)

        status_box = QGroupBox("Status")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(12, 16, 12, 12)
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(220)
        self.status.setPlaceholderText("Updater and rebuild messages will show up here.")
        status_layout.addWidget(self.status)
        layout.addWidget(status_box, 1)

        button_box = QGroupBox("Actions")
        button_layout = QGridLayout(button_box)
        button_layout.setContentsMargins(12, 16, 12, 12)
        button_layout.setHorizontalSpacing(10)
        button_layout.setVerticalSpacing(10)
        self.update_and_rebuild_button = QPushButton("Download Fresh Data + Rebuild Database")
        self.use_backup_button = QPushButton("Use Bundled Backup Data + Rebuild")
        self.open_folder_button = QPushButton("Open App Data Folder")
        self.close_button = QPushButton("Close")
        self.update_and_rebuild_button.setMinimumHeight(42)
        self.use_backup_button.setMinimumHeight(42)
        self.open_folder_button.setMinimumHeight(42)
        self.close_button.setMinimumHeight(42)
        button_layout.addWidget(self.update_and_rebuild_button, 0, 0, 1, 2)
        button_layout.addWidget(self.use_backup_button, 1, 0)
        button_layout.addWidget(self.open_folder_button, 1, 1)
        button_layout.addWidget(self.close_button, 2, 0, 1, 2)
        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)
        layout.addWidget(button_box)

        self.update_and_rebuild_button.clicked.connect(self.update_and_rebuild)
        self.use_backup_button.clicked.connect(self.rebuild_from_backup)
        self.open_folder_button.clicked.connect(self.open_appdata_folder)
        self.close_button.clicked.connect(self.accept)

    def set_status(self, message: str) -> None:
        self.status.append(message)
        QApplication.processEvents()

    def update_and_rebuild(self) -> None:
        try:
            self.set_status("Downloading fresh data from DE and rebuilding the SQLite database...")
            outputs = self.window.run_data_pipeline(prefer_online=True, log_callback=self.set_status)
            self.set_status(f"Database rebuilt at: {outputs['db_path']}")
            self.set_status(f"Data source: {outputs['source_mode']}")
            self.set_status(f"Manifest decode path: {outputs['lzma_method']}")
            if outputs.get("refresh_error"):
                self.set_status(f"Fresh download failed, so WDC used bundled backup data: {outputs['refresh_error']}")
            QMessageBox.information(self, "Update Complete", "WDC finished rebuilding the database.")
        except Exception as exc:
            self.set_status(f"Update failed: {exc}")
            QMessageBox.critical(self, "Update Failed", str(exc))

    def rebuild_from_backup(self) -> None:
        try:
            self.set_status("Rebuilding the database from bundled backup data...")
            outputs = self.window.run_data_pipeline(prefer_online=False, log_callback=self.set_status)
            self.set_status(f"Database rebuilt at: {outputs['db_path']}")
            self.set_status("WDC used bundled backup data for this rebuild.")
            QMessageBox.information(self, "Rebuild Complete", "The SQLite database was rebuilt from bundled backup data.")
        except Exception as exc:
            self.set_status(f"Rebuild failed: {exc}")
            QMessageBox.critical(self, "Rebuild Failed", str(exc))

    def open_appdata_folder(self) -> None:
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.paths["root"])))
        if not opened:
            QMessageBox.information(self, "App Data Folder", str(self.paths["root"]))


class ModSlotWidget(QGroupBox):
    def __init__(self, slot_number: int, parent: QWidget | None = None) -> None:
        super().__init__(f"Mod Slot {slot_number}", parent)
        self.current_mod: Mod | None = None
        self.mod_lookup: dict[str, Mod] = {}
        self.current_options: list[Mod] = []

        layout = QGridLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)

        self.mod_combo = QComboBox()
        self.mod_combo.setEditable(True)
        self.mod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mod_combo.setMaxVisibleItems(24)
        self.mod_combo.addItem("-- Empty --", None)
        self.mod_combo.setMinimumWidth(300)
        self.mod_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.mod_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.mod_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.mod_combo.view().setAlternatingRowColors(True)

        self.rank_spin = QSpinBox()
        self.rank_spin.setRange(0, 10)
        self.rank_spin.setValue(0)

        self.browse_button = QPushButton("Browse")
        self.clear_button = QPushButton("Clear")
        self.summary_label = QLabel("No mod selected")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #91a3c4;")

        layout.addWidget(QLabel("Mod"), 0, 0)
        layout.addWidget(self.mod_combo, 0, 1)
        layout.addWidget(self.browse_button, 0, 2)
        layout.addWidget(QLabel("Rank"), 0, 3)
        layout.addWidget(self.rank_spin, 0, 4)
        layout.addWidget(self.clear_button, 0, 5)
        layout.addWidget(self.summary_label, 1, 0, 1, 6)

        self.browse_button.clicked.connect(self.open_picker)

    def set_mod_options(self, mods: List[Mod]) -> None:
        current_unique = self.current_mod.unique_name if self.current_mod else None
        self.current_options = list(mods)
        self.mod_lookup = {mod.unique_name: mod for mod in mods}
        self.mod_combo.blockSignals(True)
        self.mod_combo.clear()
        self.mod_combo.addItem("-- Empty --", None)
        for mod in mods:
            summary = (mod.effect_summary or mod.description or "").strip()
            suffix = []
            if mod.rarity:
                suffix.append(mod.rarity.title())
            if mod.polarity:
                suffix.append(f"Polarity {mod.polarity}")
            suffix.append(f"Drain {mod.base_drain}")
            suffix.append(f"Max {mod.fusion_limit}")
            display_text = mod.name
            if summary:
                display_text += f"  |  {summary[:64]}"
            display_text += f"  |  {' / '.join(suffix)}"
            self.mod_combo.addItem(display_text, mod.unique_name)
            self.mod_combo.setItemData(self.mod_combo.count() - 1, summary or mod.description, Qt.ItemDataRole.ToolTipRole)
        self.mod_combo.blockSignals(False)

        if current_unique and current_unique in self.mod_lookup:
            index = self.mod_combo.findData(current_unique)
            if index >= 0:
                self.mod_combo.setCurrentIndex(index)
                self.current_mod = self.mod_lookup[current_unique]
                self.rank_spin.setMaximum(max(self.current_mod.fusion_limit, 0))
                self.rank_spin.setValue(min(self.rank_spin.value(), self.rank_spin.maximum()))
                self._refresh_summary()
                return

        self.clear_selection()

    def selected_unique_name(self) -> str | None:
        return self.mod_combo.currentData()

    def open_picker(self) -> None:
        if not self.current_options:
            return
        dialog = ModPickerDialog(self.current_options, self.selected_unique_name(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        unique_name = dialog.chosen_unique_name()
        if not unique_name:
            return
        index = self.mod_combo.findData(unique_name)
        if index >= 0:
            self.mod_combo.setCurrentIndex(index)

    def _refresh_summary(self) -> None:
        if self.current_mod is None:
            self.summary_label.setText("No mod selected")
            return
        parts = [self.current_mod.effect_summary or self.current_mod.description or "No supported effects found"]
        extra = []
        if self.current_mod.polarity:
            extra.append(f"Polarity: {self.current_mod.polarity}")
        extra.append(f"Drain: {self.current_mod.base_drain}")
        if extra:
            parts.append(" | ".join(extra))
        self.summary_label.setText("\n".join(parts))

    def clear_selection(self) -> None:
        self.current_mod = None
        self.mod_combo.setCurrentIndex(0)
        self.rank_spin.setMaximum(10)
        self.rank_spin.setValue(0)
        self.summary_label.setText("No mod selected")


class DamageCalculatorWindow(QMainWindow):
    def __init__(self, weapon_repository: WeaponRepository, mod_repository: ModRepository, project_root: Path) -> None:
        super().__init__()
        self.weapon_repository = weapon_repository
        self.mod_repository = mod_repository
        self.project_root = project_root
        self.paths = ensure_app_dirs()
        self.calculator = DamageCalculator()
        self.mod_aggregator = ModAggregator()
        self.selected_weapon: Weapon | None = None
        self.mod_slots: list[ModSlotWidget] = []
        self.available_mods: list[Mod] = []
        self.current_results = None

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1800, 1040)

        self._build_ui()
        self._connect_events()
        self.refresh_weapon_list()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([340, 1460])

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        title = QLabel(f"{APP_TITLE} v{APP_VERSION}")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search weapon name...")

        self.weapon_list = QListWidget()
        self.weapon_summary = QTextEdit()
        self.weapon_summary.setReadOnly(True)
        self.weapon_summary.setMinimumHeight(260)

        subtitle = QLabel("Search for a weapon, build a loadout, and compare the real damage output.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #91a3c4;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.weapon_list, 1)
        layout.addWidget(self.weapon_summary)

        bottom_buttons = QHBoxLayout()
        self.settings_button = QPushButton("Settings")
        self.faq_button = QPushButton("FAQ")
        bottom_buttons.addWidget(self.settings_button)
        bottom_buttons.addWidget(self.faq_button)
        layout.addLayout(bottom_buttons)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        layout.addWidget(self._build_inputs_group())
        layout.addWidget(self._build_summary_cards())
        layout.addWidget(self._build_mod_section())
        layout.addWidget(self._build_tables_section())
        layout.addStretch(1)

        return panel

    def _build_inputs_group(self) -> QWidget:
        box = QGroupBox("Enemy / Weapon Inputs")
        form = QFormLayout(box)
        form.setContentsMargins(14, 18, 14, 14)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)

        self.enemy_preset_combo = QComboBox()
        self.enemy_preset_combo.addItems(list(ENEMY_PRESETS.keys()))

        self.lich_combo = QComboBox()
        self.lich_combo.addItems([""] + DAMAGE_TYPES)
        self.valence_edit = QLineEdit("0")
        self.faction_combo = QComboBox()
        self.faction_combo.addItems(list(FACTION_MULTIPLIERS.keys()))
        self.armor_edit = QLineEdit("0")

        form.addRow("Enemy Preset", self.enemy_preset_combo)
        form.addRow("Adversary Element", self.lich_combo)
        form.addRow("Valence Base", self.valence_edit)
        form.addRow("Faction", self.faction_combo)
        form.addRow("Armor Value", self.armor_edit)
        return box

    def _build_summary_cards(self) -> QWidget:
        wrapper = QWidget()
        grid = QGridLayout(wrapper)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self.cards = {
            "base_damage": SummaryCard("Base Damage"),
            "weapon_total_damage": SummaryCard("Weapon Damage"),
            "quanta": SummaryCard("Quanta"),
            "valence_multiplier": SummaryCard("True Valence"),
            "hud_total": SummaryCard("HUD Total"),
            "hud_total_with_bane": SummaryCard("HUD + Bane"),
            "final_total": SummaryCard("Final Total"),
            "final_total_with_bane": SummaryCard("Final + Bane"),
        }
        order = list(self.cards.values())
        for index, card in enumerate(order):
            grid.addWidget(card, index // 4, index % 4)
        return wrapper

    def _build_mod_section(self) -> QWidget:
        box = QGroupBox("Mods")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 18, 14, 14)

        note = QLabel(
            "Pick real mods and ranks. WDC filters mods by the selected weapon family, supports a searchable slot picker, shows polarity and drain details, and combines elemental effects in slot order before sending the results through the calculator engine."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #91a3c4;")
        layout.addWidget(note)

        filter_row = QHBoxLayout()
        self.mod_search_edit = QLineEdit()
        self.mod_search_edit.setPlaceholderText("Filter mods by name or effect...")
        self.mod_category_combo = QComboBox()
        self.mod_category_combo.addItems([
            "All Mods",
            "Elemental",
            "Base Damage",
            "Physical",
            "Faction",
            "Other",
        ])
        filter_row.addWidget(QLabel("Filter"))
        filter_row.addWidget(self.mod_search_edit, 1)
        filter_row.addWidget(QLabel("Type"))
        filter_row.addWidget(self.mod_category_combo)
        layout.addLayout(filter_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for index in range(MOD_SLOT_COUNT):
            slot = ModSlotWidget(index + 1)
            self.mod_slots.append(slot)
            grid.addWidget(slot, index // 2, index % 2)
        layout.addLayout(grid)

        button_row = QHBoxLayout()
        self.save_build_button = QPushButton("Save Build")
        self.load_build_button = QPushButton("Load Build")
        self.compare_build_button = QPushButton("Compare Build")
        self.clear_mods_button = QPushButton("Clear All Mods")
        self.recalc_button = QPushButton("Recalculate")
        button_row.addWidget(self.save_build_button)
        button_row.addWidget(self.load_build_button)
        button_row.addWidget(self.compare_build_button)
        button_row.addStretch(1)
        button_row.addWidget(self.clear_mods_button)
        button_row.addWidget(self.recalc_button)
        layout.addLayout(button_row)
        return box

    def _build_tables_section(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.aggregated_table = self._create_table(["Stat", "Total Mod"])
        self.hud_table = self._create_table(["Damage Type", "HUD Value"])
        self.final_table = self._create_table(["Damage Type", "Final Value"])

        layout.addWidget(self._wrap_table("Aggregated Mod Totals", self.aggregated_table), 1)
        layout.addWidget(self._wrap_table("HUD / Mod Screen Damage", self.hud_table), 1)
        layout.addWidget(self._wrap_table("Final Damage", self.final_table), 1)
        return wrapper

    def _wrap_table(self, title: str, table: QTableWidget) -> QWidget:
        box = QGroupBox(title)
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        inner = QVBoxLayout(box)
        inner.setContentsMargins(10, 16, 10, 10)
        inner.setSpacing(0)
        inner.addWidget(table, 0, Qt.AlignmentFlag.AlignTop)
        return box

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.setWordWrap(False)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setMinimumHeight(220)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return table

    def _connect_events(self) -> None:
        self.search_edit.textChanged.connect(self.refresh_weapon_list)
        self.weapon_list.currentItemChanged.connect(self.on_weapon_selected)
        self.enemy_preset_combo.currentTextChanged.connect(self.apply_enemy_preset)
        self.faction_combo.currentTextChanged.connect(self.recalculate)
        self.lich_combo.currentTextChanged.connect(self.recalculate)
        self.valence_edit.textChanged.connect(self.recalculate)
        self.armor_edit.textChanged.connect(self.recalculate)
        self.recalc_button.clicked.connect(self.recalculate)
        self.clear_mods_button.clicked.connect(self.clear_all_mods)
        self.mod_search_edit.textChanged.connect(self.apply_mod_filters)
        self.mod_category_combo.currentTextChanged.connect(self.apply_mod_filters)
        self.settings_button.clicked.connect(self.open_settings)
        self.faq_button.clicked.connect(self.open_faq)
        self.save_build_button.clicked.connect(self.save_build)
        self.load_build_button.clicked.connect(self.load_build)
        self.compare_build_button.clicked.connect(self.compare_build)

        for slot in self.mod_slots:
            slot.mod_combo.currentIndexChanged.connect(self.on_mod_changed)
            slot.rank_spin.valueChanged.connect(self.recalculate)
            slot.clear_button.clicked.connect(self._make_clear_slot_callback(slot))

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def open_faq(self) -> None:
        FAQDialog(self).exec()

    def _make_clear_slot_callback(self, slot: ModSlotWidget):
        def callback() -> None:
            slot.clear_selection()
            self.recalculate()

        return callback

    def rebuild_database(self) -> None:
        build_database(
            db_path=self.paths["db"],
            cleaned_weapons_zip_path=self.paths["source"] / "ExportWeapons_en_Cleaned.zip",
            cleaned_upgrades_zip_path=self.paths["source"] / "ExportKeys_en_Cleaned.zip",
            spreadsheet_xlsx_path=(self.paths["source"] / "Warframe-Damage-Calculator_v2.xlsx"),
        )
        self.refresh_weapon_list()
        if self.selected_weapon is not None:
            refreshed = self.weapon_repository.get_weapon(self.selected_weapon.weapon)
            if refreshed is not None:
                self.selected_weapon = refreshed
                self._show_weapon_summary(refreshed)
                self._load_mod_options_for_weapon(refreshed)
                self.recalculate()

    def refresh_weapon_list(self) -> None:
        weapons = self.weapon_repository.search_weapons(self.search_edit.text())
        current_name = self.weapon_list.currentItem().text() if self.weapon_list.currentItem() else None

        self.weapon_list.blockSignals(True)
        self.weapon_list.clear()
        for weapon_name in weapons:
            self.weapon_list.addItem(weapon_name)
        self.weapon_list.blockSignals(False)

        if current_name:
            matches = self.weapon_list.findItems(current_name, Qt.MatchFlag.MatchExactly)
            if matches:
                self.weapon_list.setCurrentItem(matches[0])
        elif self.weapon_list.count() > 0:
            self.weapon_list.setCurrentRow(0)

    def on_weapon_selected(self, current: QListWidgetItem | None) -> None:
        if current is None:
            return

        weapon = self.weapon_repository.get_weapon(current.text())
        if weapon is None:
            return

        self.selected_weapon = weapon
        self._show_weapon_summary(weapon)
        self._load_mod_options_for_weapon(weapon)
        self.recalculate()

    def _show_weapon_summary(self, weapon: Weapon) -> None:
        lines = [
            weapon.weapon,
            f"Category: {weapon.product_category or weapon.slot_group}",
            f"Weapon Family: {weapon.slot_group}",
            f"Base Damage: {weapon.dmg:.6f}",
            f"Fire Rate: {weapon.firerate:.6f}",
            f"Multishot: {weapon.multi:.6f}",
            f"Crit Chance: {weapon.critchan:.6f}",
            f"Crit Multiplier: {weapon.critmult:.6f}",
            f"Status Chance: {weapon.statchan:.6f}",
            "",
            "Base Damage Types:",
        ]
        for damage_type in DAMAGE_TYPES:
            value = weapon.damage_for(damage_type)
            if value:
                lines.append(f"  {self.display_name(damage_type)}: {value:.6f}")
        self.weapon_summary.setPlainText("\n".join(lines))

    def _load_mod_options_for_weapon(self, weapon: Weapon) -> None:
        raw_mods = self.mod_repository.list_mods_for_slot(weapon.slot_group)
        deduped: dict[tuple[str, str], Mod] = {}
        for mod in raw_mods:
            key = (mod.name.strip().lower(), (mod.effect_summary or "").strip().lower())
            existing = deduped.get(key)
            if existing is None or mod.fusion_limit > existing.fusion_limit:
                deduped[key] = mod
        self.available_mods = sorted(deduped.values(), key=lambda mod: (mod.name.lower(), mod.fusion_limit))
        self.apply_mod_filters()

    def apply_mod_filters(self) -> None:
        if not self.available_mods:
            return

        search_text = self.mod_search_edit.text().strip().lower()
        category = self.mod_category_combo.currentText()
        filtered = []
        for mod in self.available_mods:
            haystack = " ".join([mod.name, mod.effect_summary, mod.description]).lower()
            if search_text and search_text not in haystack:
                continue
            if not self._mod_matches_category(mod, category):
                continue
            filtered.append(mod)

        for slot in self.mod_slots:
            slot.set_mod_options(filtered)

    def _mod_matches_category(self, mod: Mod, category: str) -> bool:
        summary = f"{mod.effect_summary} {mod.description}".lower()
        if category == "All Mods":
            return True
        if category == "Elemental":
            return any(term in summary for term in ("heat", "cold", "electric", "electricity", "toxin", "blast", "radiation", "gas", "magnetic", "viral", "corrosive"))
        if category == "Base Damage":
            return "damage" in summary and not any(term in summary for term in ("damage to grineer", "damage to corpus", "damage to infested", "damage to corrupted", "impact", "puncture", "slash"))
        if category == "Physical":
            return any(term in summary for term in ("impact", "puncture", "slash"))
        if category == "Faction":
            return any(term in summary for term in ("damage to grineer", "damage to corpus", "damage to infested", "damage to corrupted"))
        if category == "Other":
            return not self._mod_matches_category(mod, "Elemental") and not self._mod_matches_category(mod, "Base Damage") and not self._mod_matches_category(mod, "Physical") and not self._mod_matches_category(mod, "Faction")
        return True

    def on_mod_changed(self) -> None:
        for slot in self.mod_slots:
            unique_name = slot.selected_unique_name()
            if not unique_name:
                slot.current_mod = None
                slot.summary_label.setText("No mod selected")
                slot.rank_spin.setMaximum(10)
                continue

            mod = slot.mod_lookup.get(unique_name)
            if mod is None:
                mod = self.mod_repository.get_mod(unique_name)
            slot.current_mod = mod
            if mod is not None:
                slot.rank_spin.setMaximum(max(mod.fusion_limit, 0))
                if slot.rank_spin.value() > slot.rank_spin.maximum():
                    slot.rank_spin.setValue(slot.rank_spin.maximum())
                slot._refresh_summary()
        self.recalculate()

    def clear_all_mods(self) -> None:
        for slot in self.mod_slots:
            slot.clear_selection()
        self.recalculate()

    def recalculate(self) -> None:
        if self.selected_weapon is None:
            return

        try:
            equipped_mods = self._build_equipped_mods()
            aggregated_mods = self.mod_aggregator.aggregate(equipped_mods, self.faction_combo.currentText())
            inputs = CalculationInputs(
                weapon_name=self.selected_weapon.weapon,
                faction=self.faction_combo.currentText() or "Grineer",
                armor_value=self.safe_float(self.armor_edit.text()),
                lich_element=self.lich_combo.currentText(),
                valence_base=self.safe_float(self.valence_edit.text()),
                mods=aggregated_mods,
            )
            results = self.calculator.calculate(self.selected_weapon, inputs)
            self.current_results = results
            self._update_results(results)
        except Exception as exc:
            QMessageBox.critical(self, "Calculation error", str(exc))

    def _build_equipped_mods(self) -> list[EquippedMod]:
        equipped: list[EquippedMod] = []
        for slot in self.mod_slots:
            if slot.current_mod is None:
                equipped.append(EquippedMod())
                continue
            rank = slot.rank_spin.value()
            effects = self.mod_repository.fetch_ranked_effects(slot.current_mod.unique_name, rank)
            equipped.append(EquippedMod(mod=slot.current_mod, rank=rank, effects=effects))
        return equipped

    def _update_results(self, results) -> None:
        self.cards["base_damage"].set_value(f"{results.base_weapon_damage:.6f}")
        self.cards["weapon_total_damage"].set_value(f"{results.weapon_total_damage:.6f}")
        self.cards["quanta"].set_value(f"{results.quanta:.6f}")
        self.cards["valence_multiplier"].set_value(f"{results.valence_multiplier:.10f}")
        self.cards["hud_total"].set_value(f"{results.hud_total:.6f}")
        self.cards["hud_total_with_bane"].set_value(f"{results.hud_total_with_bane:.6f}")
        self.cards["final_total"].set_value(f"{results.final_total:.6f}")
        self.cards["final_total_with_bane"].set_value(f"{results.final_total_with_bane:.6f}")

        self.fill_table(self.aggregated_table, results.rows_for_mods(), label_column=True)
        self.fill_table(self.hud_table, results.rows_for_hud(), label_column=True)
        self.fill_table(self.final_table, results.rows_for_final(), label_column=True)

    def fill_table(self, table: QTableWidget, rows: list[tuple[str, float]], label_column: bool = False) -> None:
        table.setRowCount(len(rows))
        for row_index, (name, value) in enumerate(rows):
            display = self.display_name(name) if label_column else name
            item_name = QTableWidgetItem(display)
            item_value = QTableWidgetItem(f"{value:.6f}")
            item_value.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row_index, 0, item_name)
            table.setItem(row_index, 1, item_value)
        table.resizeRowsToContents()
        extra_height = table.horizontalHeader().height() + 8
        for row_index in range(table.rowCount()):
            extra_height += table.rowHeight(row_index)
        table.setFixedHeight(max(extra_height + 8, 220))

    def save_build(self) -> None:
        if self.selected_weapon is None:
            QMessageBox.information(self, "Save Build", "Pick a weapon first.")
            return
        default_path = self.paths["builds"] / f"{self.selected_weapon.weapon.replace('/', '-').replace(' ', '_')}.json"
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Build", str(default_path), "JSON Files (*.json)")
        if not file_name:
            return
        payload = {
            "weapon": self.selected_weapon.weapon,
            "inputs": {
                "lich_element": self.lich_combo.currentText(),
                "valence_base": self.valence_edit.text(),
                "faction": self.faction_combo.currentText(),
                "armor": self.armor_edit.text(),
            },
            "mods": [
                {
                    "unique_name": slot.current_mod.unique_name if slot.current_mod else None,
                    "rank": slot.rank_spin.value(),
                }
                for slot in self.mod_slots
            ],
        }
        Path(file_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Save Build", "Build saved.")

    def load_build(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Build", str(self.paths["builds"]), "JSON Files (*.json)")
        if not file_name:
            return
        payload = json.loads(Path(file_name).read_text(encoding="utf-8"))
        weapon_name = str(payload.get("weapon") or "")
        if not weapon_name:
            QMessageBox.warning(self, "Load Build", "That build file does not include a weapon name.")
            return

        self.search_edit.setText(weapon_name)
        matches = self.weapon_list.findItems(weapon_name, Qt.MatchFlag.MatchExactly)
        if matches:
            self.weapon_list.setCurrentItem(matches[0])
        else:
            self.refresh_weapon_list()
            matches = self.weapon_list.findItems(weapon_name, Qt.MatchFlag.MatchExactly)
            if matches:
                self.weapon_list.setCurrentItem(matches[0])

        inputs = payload.get("inputs") or {}
        self.lich_combo.setCurrentText(str(inputs.get("lich_element") or ""))
        self.valence_edit.setText(str(inputs.get("valence_base") or "0"))
        self.faction_combo.setCurrentText(str(inputs.get("faction") or self.faction_combo.currentText()))
        self.armor_edit.setText(str(inputs.get("armor") or "0"))

        mod_rows = payload.get("mods") or []
        for slot, row in zip(self.mod_slots, mod_rows):
            unique_name = row.get("unique_name")
            rank = int(row.get("rank") or 0)
            if not unique_name:
                slot.clear_selection()
                continue
            index = slot.mod_combo.findData(unique_name)
            if index >= 0:
                slot.mod_combo.setCurrentIndex(index)
                slot.rank_spin.setValue(rank)
        self.on_mod_changed()
        QMessageBox.information(self, "Load Build", "Build loaded.")

    def apply_enemy_preset(self) -> None:
        preset_name = self.enemy_preset_combo.currentText()
        faction, armor = ENEMY_PRESETS.get(preset_name, (None, None))
        if faction:
            self.faction_combo.setCurrentText(faction)
        if armor is not None:
            self.armor_edit.setText(str(armor))
        if preset_name == "Custom":
            self.recalculate()

    def run_data_pipeline(self, prefer_online: bool, log_callback: Callable[[str], None] | None = None) -> dict[str, str | Path]:
        updater = WarframeDataUpdater()
        if log_callback:
            if prefer_online:
                log_callback("Trying to download fresh data from DE. If that fails, WDC will fall back to bundled backup data.")
            else:
                log_callback("Using bundled backup export data that ships with WDC.")
        outputs = updater.update_and_build_database(
            db_path=self.paths["db"],
            cleaned_weapons_zip_path=self.paths["source"] / "ExportWeapons_en_Cleaned.zip",
            cleaned_upgrades_zip_path=self.paths["source"] / "ExportKeys_en_Cleaned.zip",
            spreadsheet_xlsx_path=(self.paths["source"] / "Warframe-Damage-Calculator_v2.xlsx"),
            allow_bundled_fallback=prefer_online,
        )
        self.refresh_weapon_list()
        if self.selected_weapon is not None:
            refreshed = self.weapon_repository.get_weapon(self.selected_weapon.weapon)
            if refreshed is not None:
                self.selected_weapon = refreshed
                self._show_weapon_summary(refreshed)
                self._load_mod_options_for_weapon(refreshed)
                self.recalculate()
        return outputs

    def compare_build(self) -> None:
        if self.selected_weapon is None or self.current_results is None:
            QMessageBox.information(self, "Compare Build", "Pick a weapon and calculate a build first.")
            return
        file_name, _ = QFileDialog.getOpenFileName(self, "Compare Build", str(self.paths["builds"]), "JSON Files (*.json)")
        if not file_name:
            return
        payload = json.loads(Path(file_name).read_text(encoding="utf-8"))
        weapon_name = str(payload.get("weapon") or "")
        weapon = self.weapon_repository.get_weapon(weapon_name)
        if weapon is None:
            QMessageBox.warning(self, "Compare Build", "The selected build references a weapon that is not in the database.")
            return

        inputs = payload.get("inputs") or {}
        equipped_mods: list[EquippedMod] = []
        for row in payload.get("mods") or []:
            unique_name = row.get("unique_name")
            rank = int(row.get("rank") or 0)
            if not unique_name:
                equipped_mods.append(EquippedMod())
                continue
            mod = self.mod_repository.get_mod(unique_name)
            if mod is None:
                equipped_mods.append(EquippedMod())
                continue
            effects = self.mod_repository.fetch_ranked_effects(unique_name, rank)
            equipped_mods.append(EquippedMod(mod=mod, rank=rank, effects=effects))

        aggregated_mods = self.mod_aggregator.aggregate(equipped_mods, str(inputs.get("faction") or "Grineer"))
        compare_inputs = CalculationInputs(
            weapon_name=weapon.weapon,
            faction=str(inputs.get("faction") or "Grineer"),
            armor_value=self.safe_float(str(inputs.get("armor") or "0")),
            lich_element=str(inputs.get("lich_element") or ""),
            valence_base=self.safe_float(str(inputs.get("valence_base") or "0")),
            mods=aggregated_mods,
        )
        compare_results = self.calculator.calculate(weapon, compare_inputs)

        current_summary = [
            ("Weapon", self.selected_weapon.weapon),
            ("Faction", self.faction_combo.currentText()),
            ("Armor", self.armor_edit.text()),
            ("HUD Total", f"{self.current_results.hud_total:.6f}"),
            ("HUD + Faction", f"{self.current_results.hud_total_with_bane:.6f}"),
            ("Final Total", f"{self.current_results.final_total:.6f}"),
            ("Final + Faction", f"{self.current_results.final_total_with_bane:.6f}"),
            ("Quanta", f"{self.current_results.quanta:.6f}"),
            ("True Valence", f"{self.current_results.valence_multiplier:.10f}"),
        ]
        compare_summary = [
            ("Weapon", weapon.weapon),
            ("Faction", compare_inputs.faction),
            ("Armor", str(compare_inputs.armor_value)),
            ("HUD Total", f"{compare_results.hud_total:.6f}"),
            ("HUD + Faction", f"{compare_results.hud_total_with_bane:.6f}"),
            ("Final Total", f"{compare_results.final_total:.6f}"),
            ("Final + Faction", f"{compare_results.final_total_with_bane:.6f}"),
            ("Quanta", f"{compare_results.quanta:.6f}"),
            ("True Valence", f"{compare_results.valence_multiplier:.10f}"),
        ]

        CompareBuildDialog(current_summary, compare_summary, Path(file_name).name, self).exec()

    def display_name(self, code: str) -> str:
        return DISPLAY_NAMES.get(code, code.title())

    def safe_float(self, value: str) -> float:
        try:
            return float(value.strip()) if value.strip() else 0.0
        except ValueError:
            return 0.0


def build_application(db_path) -> QApplication:
    app = QApplication.instance() or QApplication([])
    icon_path = Path(__file__).resolve().parents[1] / "wdc.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(DARK_STYLESHEET)
    return app
