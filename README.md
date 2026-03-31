# MAJOR NOTE!!

## A Note on Development: This app's UI and structure were generated entirely using ChatGPT, but the underlying math is the result of countless hours of manual testing and coding.

Ages ago, I started the TenZero.GG project to make a better site to create and share Warframe builds. While I handled the bulk of the overarching project, my collaborator Xadreus and I teamed up heavily on the incredibly complex damage calculations and the underlying math. Together, we worked our tails off to accurately recreate the game's systems, matching not just the HUD stats, but the real-world values you actually see when using weapons in a mission. We honestly had the most accurate calculations of any model we could find online.

Unfortunately, life loves to get in the way of passion projects. Between college for Xadreus and it being over a decade and a half since I last touched webdev, the site itself suffered. But our math and our testing spreadsheets were rock solid.

Instead of letting all the work Xadreus and I put into those accurate damage calculations go to waste, I figured: why not throw our spreadsheet at ChatGPT and see if I could vibe code out a Python app? I wanted to give something back to the amazing Warframe community so our work actually means something, even if the original site never gets built. I absolutely plan to get my hands dirty in the code later to add features and make it look better, but with real life pulling me away, using AI was the best way to get this tool into your hands now. I hope you understand, and I hope you enjoy it!

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
# License

Distributed under the GNU GPL-3.0 license; please check the `LICENSE` file in the GitHub repository for more information.

---

# Disclaimer

The following is the disclaimer that applies to all scripts, functions, one-liners, etc. This disclaimer supersedes any disclaimer included in any script, function, one-liner, etc.

You running this script/function means you will not blame the author(s) if this breaks your stuff. This script/function is provided **AS IS** without warranty of any kind. Author(s) disclaim all implied warranties including, without limitation, any implied warranties of merchantability or of fitness for a particular purpose.

The entire risk arising out of the use or performance of the sample scripts and documentation remains with you.

In no event shall author(s) be held liable for any damages whatsoever (including, without limitation, damages for loss of business profits, business interruption, loss of business information, or other pecuniary loss) arising out of the use of or inability to use the script or documentation.

Neither this script/function, nor any part of it other than those parts that are explicitly copied from others, may be republished without author(s) express written permission.

The author(s) retain the right to alter this disclaimer at any time.

For the most up to date version of the disclaimer, see:  
https://ucunleashed.com/code-disclaimer
