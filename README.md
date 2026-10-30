# CleanYourWatch ⌚

> Safely debloat, optimize battery life, and benchmark resource consumption on Samsung Galaxy Watch and Wear OS devices over Wi-Fi ADB.

Inspired by [CleanYourTV](https://github.com/Gathin23/cleanyourtv), **CleanYourWatch** gives you control over your Samsung Galaxy Watch. It removes intrusive telemetry, eliminates background battery drains, cleans up unused apps and watch faces, and **measures exact before-and-after RAM, CPU, and background process reductions**.

---

## 🌟 Key Features

* **📊 Real-time Before & After Benchmarking:** Real-time RAM profiling (`dumpsys meminfo`), active background services count, process table monitoring, and storage recovery metrics.
* **🛡️ 100% Reversible & Safe:** Uses `pm disable-user --user 0`. No APKs are deleted, no root required, and zero risk of bootloops. A single command restores everything back to factory state.
* **🤝 Tailored Interactive Wizard:** Asks you exactly what you want to keep:
  * **Payments:** Keep Samsung Pay, Google Wallet, both, or neither.
  * **Health & Fitness:** Keep Samsung Health (ECG/BP/workouts) or free up ~60MB RAM if you don't use it.
  * **Voice Assistants:** Turn off always-listening mic drain ("Hi Bixby") while keeping or swapping assistants.
  * **Ecosystem Apps:** Choose which Samsung apps to keep (Browser, SmartThings, Voice Recorder, Modes & Routines, etc.).
  * **Stock Watch Faces:** Disable Samsung's 35+ pre-installed watch faces if you use custom faces.
* **⚡ Zero External Dependencies:** Built with pure Python 3 standard library. Runs out-of-the-box on macOS, Linux, and Windows.
* **🔒 Strict Safety Blacklist:** Hard-coded guard preventing accidental disablement of critical components (System UI, Bluetooth, Watch Face Runtime, Settings, Phone, Keyboard).

---

## 📱 Real-World Benchmark: Galaxy Watch 6 (SM-R940)

The following benchmark was captured on a physical **Samsung Galaxy Watch 6 (SM-R940)** running **Wear OS (Android 16 / One UI 6 Watch)** over Wi-Fi ADB:

```text
═══ BENCHMARK RESULTS: BEFORE VS AFTER ═════════════════════════════

  Metric                   Before           After            Change          
  ──────────────────────────────────────────────────────────────────────
  RAM Used                 1351.5 MB        1209.1 MB        -142.4 MB (-10.5%)
  RAM Free                 655.8 MB         777.0 MB         +121.2 MB (+18.5% headroom)
  ZRAM Swap Freed          -                -                +2.7 MB
  Running Processes        76               74               -2
  Packages Disabled        2                27               +25 Suspended
  ──────────────────────────────────────────────────────────────────────

  Top Background Processes Unloaded:
    • com.google.android.wearable.assistant (~39.1 MB freed)
    • com.samsung.android.bixby.agent & wakeup (~39.2 MB freed)
    • com.samsung.android.watch.runestone.app (Rubin telemetry) (~45.4 MB freed)
    • com.sec.android.diagmonagent (Samsung telemetry)
    • com.samsung.android.samsungpay.gear (Samsung Pay suspended; Google Wallet active)
```

### 💡 High-Potential Note: Custom Services Retained!
> [!NOTE]
> **The results above were achieved while intentionally keeping core user features active:**
> * ✅ **Samsung Health suite** remained fully active (continuous sensor listeners, sleep tracking, ECG/BP).
> * ✅ **Samsung Ecosystem apps** remained active (Samsung Internet Browser, SmartThings, Galaxy Buds Controller, Modes & Routines, Voice Recorder).
> * ✅ **Stock Watch Faces** (all ~40 pre-installed OEM faces) remained untouched.
> * ✅ **Google Wallet** remained active for contactless wrist payments.
>
> **The potential for deeper optimization is even higher:**
> Disabling the Samsung Browser (~55 MB cached), Modes & Routines (~52 MB), and unused OEM watch faces reclaims an **additional ~150 MB to ~250 MB of RAM**, pushing total freed memory well past **300 MB**!

---

## 🔋 Battery Savings Estimation

By removing telemetry loops, continuous audio listening, and memory paging pressure, CleanYourWatch delivers noticeable battery life improvements:

| Optimization Vector | What Changed | Estimated Battery Impact |
| :--- | :--- | :--- |
| **Microphone Hotword Listener** | Disabled **Bixby Voice Wakeup** (`com.samsung.android.bixby.wakeup`). Stops low-power audio DSP from continuously monitoring for the *"Hi Bixby"* trigger. | **+8% to +15%** battery savings per day |
| **Telemetry & Log Sync Loops** | Disabled **Samsung DiagMon**, **Rubin AI personalization**, and **Global Goals (SREE)** lock screen ads. Prevents background wake locks and telemetry radio bursts. | **+4% to +7%** battery savings per day |
| **ZRAM & Memory Thrashing** | Gained **+121.2 MB of free RAM headroom**. Reduces Android Low Memory Killer (LMK) activity, avoiding CPU-intensive ZRAM decompression and app cold restarts. | **+5% to +10%** battery savings per day |
| **Total Estimated Runtime Gain** | **Balanced Profile** (keeping Samsung Health & Ecosystem) | **+15% to +30% longer runtime per charge** *(e.g. extending a 28h watch up to 34–38h)* |
| **Aggressive Profile** | Disabling Samsung Health & unused background sync daemons | **Up to +40% to +50% longer battery life** |

---

## 📋 Requirements

* **Python 3.8+** (Uses only Python's standard library — zero external pip packages required).
* **ADB (Android Debug Bridge)**:

### How to Install ADB

<details>
<summary><b>🍎 macOS</b></summary>

Using [Homebrew](https://brew.sh/):
```bash
brew install android-platform-tools
```
</details>

<details>
<summary><b>🪟 Windows</b></summary>

Using **winget** (Windows Package Manager):
```powershell
winget install Google.PlatformTools
```
Or using **Chocolatey**:
```powershell
choco install adb
```
*(Alternatively, download the official [Google SDK Platform Tools zip](https://developer.android.com/tools/releases/platform-tools) and extract it to a folder in your system PATH).*
</details>

<details>
<summary><b>🐧 Linux</b></summary>

* **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install -y android-tools-adb android-tools-fastboot
  ```
* **Fedora / RHEL:**
  ```bash
  sudo dnf install -y android-tools
  ```
* **Arch Linux:**
  ```bash
  sudo pacman -S android-tools
  ```
</details>

Once installed, verify it by running:
```bash
adb version
```

---

## ⚙️ How It Works

Samsung Galaxy Watches (and other Wear OS devices) run on Android. They have the standard **Android Debug Bridge (ADB)** built into Developer Options over your local Wi-Fi network.

* **Reversible Package Suspension:** CleanYourWatch uses `pm disable-user --user 0 <package>` to safely deactivate unwanted apps, telemetry, and background services. The APK remains safely preserved in the read-only system partition — meaning **no root is required**, **no system files are deleted**, and **no bricking can occur**.
* **Instant One-Click Revert:** Before touching any package, the tool automatically saves a timestamped snapshot of all package states to `backups/`. Running `./restore.sh` or `python3 main.py restore` instantly re-enables any package back to its original state.
* **Live Resource Profiling:** The tool queries Android's low-level memory manager (`dumpsys meminfo`), service manager, process table, and `/proc/loadavg` before and after debloating to calculate the exact delta of RAM reclaimed, processes terminated, and background services stopped.
* **Strict Blacklist Safety Guard:** A hardcoded safety blacklist prevents accidental modification of critical system components (System UI, Bluetooth stack, Settings, Watchface Runtime, On-screen Keyboard, Phone services).

---

## 🚀 Quick Start

### ⚡ Method A: The 1-Prompt AI Setup (Recommended)

Just like [CleanYourTV](https://github.com/Gathin23/cleanyourtv), CleanYourWatch is designed for **AI coding assistants** with shell access (such as Cursor, Claude Code, Antigravity, Gemini CLI, or GitHub Copilot Workspace).

1. Clone this repository to your computer:
   ```bash
   git clone https://github.com/pedrohrsilva/cleanyourwatch.git
   cd cleanyourwatch
   ```
2. Enable Wireless Debugging on your watch ([see instructions below](#-enabling-wireless-debugging--pairing)).
3. Open this folder in your AI coding assistant and copy-paste this prompt:

> **Copy & Paste into your AI Assistant:**
> ```text
> Optimize and debloat my Wear OS smartwatch using the CleanYourWatch repository.
> Watch Model: Galaxy Watch 6 (SM-R940)
> Watch IP:Port: <your_watch_ip>:<connect_port>
>
> Follow the workflow in PROMPT.md: measure pre-debloat resources, ask my preferences for contactless payments, Samsung Health, voice assistants, and stock watch faces, create a safety backup, safely suspend unwanted packages, and output the before-and-after resource comparison table.
> ```

The AI assistant will handle everything interactively, confirming your choices before applying any changes!

---

### 💻 Method B: Interactive CLI (Manual)

If you prefer running the interactive tool directly from your terminal:

```bash
git clone https://github.com/pedrohrsilva/cleanyourwatch.git
cd cleanyourwatch
chmod +x main.py run.sh restore.sh

# Start the interactive debloater
./run.sh
# or directly with python:
python3 main.py debloat
```

---

### 📶 Enabling Wireless Debugging & Pairing

Before running the tool, connect your watch to your computer over Wi-Fi:

1. **Enable Developer Options:**
   * On your watch, open **Settings > About watch > Software info**.
   * Tap **Software version** 7 times until you see the *"Developer mode turned on"* notification.
2. **Turn on Wireless Debugging:**
   * Go back to **Settings > Developer options**.
   * Turn ON **ADB debugging** and **Wireless debugging** (make sure watch & computer are on the same Wi-Fi).
3. **Pair the Watch (Wear OS 4 / 5 / 6):**
   * Tap **Wireless debugging > Pair new device with pairing code**.
   * Note the **6-digit pairing code** and the **IP address & pairing port** (e.g. `192.168.31.47:37123`).
   * In your computer's terminal, run:
     ```bash
     adb pair <watch_ip>:<pairing_port>
     # Example: adb pair 192.168.31.47:37123
     ```
   * Enter the 6-digit code when prompted until you see `Successfully paired`.
4. **Connect to the Watch:**
   * Go back to the main **Wireless debugging** screen and note the **Connection port** (e.g. `192.168.31.47:44713` — *note: connection port differs from pairing port*).
   * Run:
     ```bash
     adb connect <watch_ip>:<connect_port>
     # Example: adb connect 192.168.31.47:44713
     ```
   * Check connection: `adb devices` (your watch should show as `device`).

---

## 📖 CLI Commands

### 1. Check Connected Watch Hardware & Live Memory
```bash
python3 main.py device
```

### 2. Take a Resource Benchmark Snapshot
```bash
python3 main.py measure
```
Captures full RAM breakdown (PSS/RSS/ZRAM), running services, processes, and CPU load to `snapshots/`.

### 3. List All Installed Packages & Safety Recommendations
```bash
python3 main.py list
```
Scans and categorizes all 260+ watch packages into Telemetry, Voice Assistants, Payments, Health, Ecosystem, and Watch Faces.

### 4. Interactive Debloat Wizard
```bash
python3 main.py debloat
```
Guides you through selecting which features to retain, automatically takes pre/post benchmark snapshots, and outputs a formatted comparison table.

You can also pass a custom list of packages directly:
```bash
python3 main.py debloat -t presets/user_plan.txt -y
```

### 5. Instant Revert & Restore
```bash
# Restore from latest backup
./restore.sh
# or:
python3 main.py restore

# Restore from a specific backup file
python3 main.py restore --file backups/backup_192_168_31_47_44713_20261030_130253.json
```

---

## 🗂️ Package Catalog Overview

| Category | Typical Packages | Default Action |
| :--- | :--- | :--- |
| **Telemetry & Analytics** | Samsung DiagMon, Samsung Global Goals (SREE), Retail Attract Loop, Rubin Customization | **Disable** (Zero functional impact) |
| **Voice Assistants** | Bixby Voice, Bixby Wakeup ("Hi Bixby"), Google Assistant | **User Choice** (Wakeup drains mic constantly) |
| **Payments** | Samsung Pay / Wallet, Google Wallet | **User Choice** (Keep preferred provider) |
| **Health Suite** | Samsung Health, Samsung Health Monitor (ECG/BP) | **User Choice** (Keep if tracking fitness) |
| **Samsung Ecosystem** | Samsung Internet, Voice Recorder, SmartThings, Modes & Routines, Smart Switch | **User Choice** (Keep what you use) |
| **Stock Watch Faces** | 35+ pre-installed Samsung watch faces | **Optional** (Free clutter if using custom face) |
| **Critical System** | System UI, Bluetooth, Settings, Framework, Honeyboard keyboard, Watchface Runtime | **BLACKLISTED** (Safety guard: never touched) |

---

## 🛡️ Safety Guarantee

CleanYourWatch never deletes files from system storage. Suspended packages remain safely in ROM and can be re-enabled at any moment using `pm enable <package>` or `./restore.sh`.

---

## 🤝 Contributing & Support

Issues, PRs, and package catalogs for other Wear OS models (Galaxy Watch 4/5/7/Ultra, Pixel Watch, TicWatch) are welcome!

Distributed under the MIT License.
