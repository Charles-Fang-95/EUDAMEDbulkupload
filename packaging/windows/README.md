# Windows EXE Build Guide

This folder prepares a Windows tester package for the local EUDAMED beta tool.

## Build Environment

- Build this on a Windows 10/11 machine.
- Install Python 3.11+ from python.org or Microsoft Store.
- PyInstaller cannot reliably cross-compile a Windows `.exe` from macOS, so the final `.exe` must be built on Windows or a Windows VM.

## Build Command

Open PowerShell in the project root and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\packaging\windows\build_windows_exe.ps1
```

The script creates:

- `dist\EUDAMED_Local_Beta\EUDAMED_Local_Beta.exe`
- `dist\EUDAMED_Local_Beta_Windows.zip`

Send the ZIP file to testers, not only the `.exe`, because the app needs bundled templates, XSD files, static assets and vendor libraries.

## Runtime Behavior

- The local website still runs at `http://127.0.0.1:8765`.
- User data is written next to the executable in `local_beta_data`.
- The bundled official docs, XSD files and template are read from the packaged resource folder.

## Notes for Testers

- If Windows Defender or SmartScreen warns about the executable, this is expected for unsigned internal beta builds.
- For broader distribution, use code signing. Unsigned `.exe` files are acceptable for small controlled tests only if the recipient explicitly trusts the sender.
