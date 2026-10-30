# CleanYourWatch ⌚

> Safely debloat, optimize battery life, and benchmark resource consumption on Samsung Galaxy Watch and Wear OS devices over Wi-Fi ADB.

Inspired by [CleanYourTV](https://github.com/Gathin23/cleanyourtv), **CleanYourWatch** gives you control over your Samsung Galaxy Watch. It removes intrusive telemetry, eliminates background battery drains, cleans up unused apps and watch faces, and **measures exact before-and-after RAM, CPU, and background process reductions**.

---

## 🌟 Key Features

* **📊 Before & After Benchmarking:** Real-time RAM profiling (`dumpsys meminfo`), active background services count, process table monitoring, and storage recovery metrics.
* **🛡️ 100% Reversible & Safe:** Uses `pm disable-user --user 0`. No APKs are deleted, no root required, and no risk of bricking. One command restores everything back to factory state.
* **🤝 Tailored Interactive Wizard:** Asks you exactly what you want to keep:
  * **Payments:** Keep Samsung Pay, Google Wallet, both, or neither.
  * **Health & Fitness:** Keep Samsung Health (ECG/BP/workouts) or free up ~60MB RAM if you don't use it.
  * **Voice Assistants:** Turn off always-listening mic drain ("Hi Bixby") while keeping or swapping assistants.
  * **Ecosystem Apps:** Choose which Samsung apps to keep (Browser, SmartThings, Voice Recorder, Modes & Routines, etc.).
  * **Stock Watch Faces:** Disable Samsung's 35+ pre-installed watch faces if you use custom faces.
* **⚡ Zero Dependencies:** Built with pure Python 3 standard library. Runs out-of-the-box on macOS, Linux, and Windows.
* **🔒 Strict Safety Blacklist:** Hard-coded guard preventing accidental disablement of critical components (System UI, Bluetooth, Watch Face Runtime, Settings, Phone, Keyboard).

---

## 📱 Hardware Tested

* **Samsung Galaxy Watch 6 (SM-R940)**
* **OS:** Wear OS 5 / 6 (Android 16 / One UI 6 Watch)
* **Connectivity:** Local Wi-Fi ADB (`adb connect <ip>:<port>`)

---

## 🚀 Quick Start

### 1. Enable Wireless Debugging on your Watch

1. On your watch, navigate to **Settings > About watch > Software info**.
2. Tap **Software version** 7 times until Developer Mode is unlocked.
3. Go back to **Settings > Developer options**.
4. Enable **ADB debugging** and **Wireless debugging**.
5. Pair or connect from your computer:
   ```bash
   adb connect <watch_ip>:<port>
   ```

### 2. Run CleanYourWatch

Clone and start the interactive debloater:

```bash
git clone https://github.com/Gathin23/cleanyourwatch.git # or your local path
cd cleanyourwatch
chmod +x main.py run.sh restore.sh

# Run interactive debloater (measures before, asks choices, creates backup, measures after)
./run.sh
# or directly:
python3 main.py debloat
```

---

## 📖 CLI Commands

### 1. Check Connected Watch Info
```bash
python3 main.py device
```
Displays hardware model, Wear OS version, battery percentage and temperature, storage breakdown, and live memory metrics.

### 2. Measure Current Resource Usage (Benchmark)
```bash
python3 main.py measure
```
Captures a full system resource snapshot (RAM, PSS, RSS, ZRAM swap, running services, CPU load average, and top 10 memory-consuming apps) into `snapshots/`.

### 3. List Installed Packages & Recommendations
```bash
python3 main.py list
```
Scans all 260+ packages on the watch and groups them into clearly defined categories with RAM/battery impact indicators.

### 4. Interactive Debloater
```bash
python3 main.py debloat
```
Guides you through a friendly questionnaire asking which features you want to keep. Measures resources before and after, presenting a side-by-side comparison table.

### 5. Undo / Restore Packages
```bash
# Restore from latest backup
./restore.sh
# or:
python3 main.py restore

# Restore from a specific backup file
python3 main.py restore --file backups/backup_192_168_31_47_44713_20261030_125000.json
```

---

## 📊 Benchmark Example (Galaxy Watch 6)

```text
═══ BENCHMARK RESULTS: BEFORE vs AFTER ═════════════════════════════

  Metric                   Before           After            Change          
  ──────────────────────────────────────────────────────────────────────────
  RAM Used                 1351.5 MB        1124.2 MB        -227.3 MB       
  RAM Free                 655.8 MB         883.1 MB         +227.3 MB       
  ZRAM Swap Freed          -                -                +42.1 MB        
  Running Services         72               53               -19             
  Running Processes        76               59               -17             
  Packages Disabled        -                38               +38             
  Storage Used (/data)     3.03 GB          2.98 GB          -0.05 GB        
  ──────────────────────────────────────────────────────────────────────────

  Processes Unloaded from RAM:
    • com.sec.android.app.sbrowser (55.6 MB freed)
    • com.samsung.android.app.routines (52.4 MB freed)
    • com.samsung.android.watch.runestone.app (45.4 MB freed)
    • com.samsung.android.bixby.agent (39.2 MB freed)
    • com.samsung.android.wear.voicerecorder (36.1 MB freed)
    • com.samsung.android.wear.smartswitchassistant (33.9 MB freed)
```

---

## 🗂️ Package Categories

| Category | Typical Packages | Recommendation |
| :--- | :--- | :--- |
| **Telemetry & Analytics** | Samsung DiagMon, Samsung Global Goals (SREE), Retail Attract Loop, Rubin Customization | **Disable** (Zero functional impact) |
| **Voice Assistants** | Bixby Voice, Bixby Wakeup ("Hi Bixby"), Google Assistant | **User Choice** (Wakeup drains mic constantly) |
| **Payments** | Samsung Pay / Wallet, Google Wallet | **User Choice** (Keep preferred provider) |
| **Health Suite** | Samsung Health, Samsung Health Monitor (ECG/BP) | **User Choice** (Keep if tracking fitness) |
| **Samsung Ecosystem** | Samsung Internet, Voice Recorder, SmartThings, Modes & Routines, Smart Switch | **User Choice** (Keep what you use) |
| **Stock Watch Faces** | 35+ pre-installed Samsung watch faces | **Optional** (Free clutter if using custom face) |
| **Critical System** | System UI, Bluetooth, Settings, Framework, Honeyboard keyboard, Watchface Runtime | **BLACKLISTED** (Never touched) |

---

## 🛡️ Safety Guarantee

CleanYourWatch never deletes files from system storage. Suspended packages remain safely in ROM and can be re-enabled at any moment using `pm enable <package>` or `./restore.sh`.
