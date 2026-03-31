# Building Warframe Damage Calculator by TenZeroGG v1.0.0

This project includes the files needed to build a Windows executable with PyInstaller and a Windows installer with Inno Setup.

## Build the EXE

1. Open a normal Command Prompt or PowerShell window.
2. Change into the project folder.
3. Run:

```bat
build_exe.bat
```

The built app will be placed in `dist\WDC`.

## Build the installer

1. Install Inno Setup 6.
2. Make sure `dist\WDC\WDC.exe` exists.
3. Run:

```bat
build_installer.bat
```

The installer will be written to `installer_output`.

## Notes

- The PyInstaller spec includes the bundled source backup files so first-run setup can still fall back to packaged data.
- The existing `data\weapons.db` file is also included when present, which helps testing but is not required for first launch.
- WDC stores its working files in `%APPDATA%\WDC` at runtime.
- The project already includes `wdc.ico`, and both PyInstaller and Inno Setup are configured to use it.
