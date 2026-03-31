# Warframe Damage Calculator by TenZeroGG v1.0.0

Desktop Warframe damage calculator built around the calculator engine and packaged as a PyQt6 desktop app.

## Current Features

- PyQt6 dark mode UI
- SQLite database for weapons and mods
- Real mod selection with rank support
- Slot-order elemental combining
- Accurate HUD and final damage calculation flow with Warframe-style rounding
- Built-in FAQ dialog that explains the calculator logic
- Settings dialog for:
  - refreshing Warframe data from DE
  - rebuilding the SQLite database in-app
  - showing where the app stores its AppData-backed files
- App data stored in the user's AppData-backed calculator folder for easier packaging later
- Save and load build files as JSON

## App Data Layout

The app stores its working files in:

- Windows: `%APPDATA%\WDC`
- Fallback on non-Windows systems: `~/.local/share/WDC`

Inside that folder the app keeps:

- `data/weapons.db`
- `source/ExportWeapons_en_Cleaned.zip`
- `source/ExportKeys_en_Cleaned.zip`
- `source/Warframe-Damage-Calculator_v2.xlsx`
- `builds/*.json`
- `settings.json`

## Running

```bash
pip install -r requirements.txt
python main.py
```

If the app does not detect a ready database on startup, it prompts to build initial data from DE and falls back to bundled backup export files when needed.

## Rebuilding The Database Manually

```bash
python build_database.py
```

## Notes

- The updater now uses streamed downloads with file-size validation before it runs Python LZMA decoding on Warframe's manifest index.
- Truncated downloads are caught early with a clearer error message.
- 7-Zip is no longer required for normal refreshes.
- The current focus is the core damage path, not every secondary combat system in Warframe yet.


## Building A Windows EXE And Installer

This project includes:

- `WDC.spec` for PyInstaller
- `build_exe.bat` to build the app into `dist\WDC`
- `installer\WDC.iss` for Inno Setup
- `build_installer.bat` to compile the installer into `installer_output`
- `installer\BUILDING.md` with quick build steps

Typical build flow:

```bat
build_exe.bat
build_installer.bat
```
