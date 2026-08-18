# Desktop Packaging & Installer Guide

**Goal:** Produce a normal Windows program you can put on a flash drive, double-click to install (Next → Next → Finish), then open and test.

---

## What you will get

| Artifact | What it is | How the user uses it |
|----------|------------|----------------------|
| `PrintRecovery.exe` (folder) | Standalone program (no Python needed) | Double-click the `.exe` |
| `PrintRecovery-Setup-0.1.0.exe` | Real Windows installer | Double-click → Next → Next → Finish |
| Portable folder | Copy-paste ready folder | Copy whole folder to flash drive / desktop |

---

## One-time preparation on a Windows PC

You only need to do this once (or when you want a new version).

### 1. Install the two free tools

1. **Python 3.11 or 3.12**  
   https://www.python.org/downloads/  
   During install tick **“Add python.exe to PATH”**.

2. **Inno Setup 6** (for the nice installer)  
   https://jrsoftware.org/isinfo.php  
   Install with default options.

### 2. Get the project

```powershell
git clone https://github.com/akameredon/print-recovery-mvp.git
cd print-recovery-mvp
```

(Or just download the ZIP from GitHub and extract it.)

### 3. Build the standalone executable

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build-exe.ps1
```

When it finishes you will have:

```
dist\PrintRecovery\
    PrintRecovery.exe
    ... (all supporting files)
```

You can already double-click `PrintRecovery.exe` to test.

### 4. Create the real installer (Next → Next → Finish)

1. Open **Inno Setup Compiler**.
2. Open the file:  
   `packaging\windows\PrintRecovery.iss`
3. Click **Compile** (or press Ctrl+F9).
4. The finished installer appears here:

```
dist\installer\PrintRecovery-Setup-0.1.0.exe
```

This is the single file you put on a flash drive.

---

## How an office user installs it

1. Copy `PrintRecovery-Setup-0.1.0.exe` to the desktop (or run from flash drive).
2. Double-click it.
3. Click **Next → Next → Install → Finish**.
4. Start **Print Recovery** from the Start Menu or Desktop shortcut.
5. Browser opens at `http://127.0.0.1:5173` (or open it yourself).

Data is stored under the install folder (or ProgramData if you later change the script). Uninstalling does **not** delete job data unless you choose to.

---

## Quick portable option (no installer)

If you only want a folder you can copy:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\create-portable.ps1
```

Result:

```
dist\PrintRecovery-Portable\
```

Copy the whole folder to a flash drive. On the target PC double-click `Run-PrintRecovery.bat` (or `PrintRecovery.exe` if you built it first).

---

## Using Antigravity / other builders

All the important files are already in the repository:

| File | Purpose |
|------|---------|
| `packaging/windows/print-recovery.spec` | PyInstaller recipe |
| `packaging/windows/build-exe.ps1` | One-command build of the `.exe` folder |
| `packaging/windows/PrintRecovery.iss` | Inno Setup script → real installer |
| `packaging/windows/create-portable.ps1` | Makes a flash-drive ready folder |
| `packaging/windows/Run-PrintRecovery.bat` | Simple double-click launcher |

You (or Antigravity) can point any packaging tool at these files.

---

## Important limits (still true after packaging)

- The software is **assisted recovery only**.
- It does **not** control the printer or RIP.
- It does **not** measure physical media position.
- Real RIP observation still needs a validated adapter (future work).

You can fully test job capture, checkpoints, interruption recording, continuation image generation, reports, multi-user features, etc. on the desktop today.

---

## Checklist before you go to the office

- [ ] Built `dist\PrintRecovery\` with `build-exe.ps1`
- [ ] Compiled `PrintRecovery-Setup-0.1.0.exe` with Inno Setup
- [ ] Copied the Setup.exe (or the whole portable folder) to flash drive
- [ ] On the office PC: install → open → create a test job with an image → record a checkpoint → mark interruption → generate continuation

That is the complete path from source to a normal Windows program.
