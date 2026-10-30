# AGENTS.md - System Architecture & Safety Rules

This repository provides an automated, reversible, zero-root debloater and resource profiling engine for Samsung Galaxy Watch Wear OS devices (tested and tailored for Galaxy Watch 6 SM-R940).

## Core Architecture
- **`main.py`**: Entrypoint CLI handling `device`, `measure`, `list`, `debloat`, `compare`, `restore`.
- **`core/adb.py`**: ADB transport layer with multi-device detection, timeout guards, and safe `pm disable-user --user 0` execution.
- **`core/benchmark.py`**: Parses `dumpsys meminfo`, `dumpsys activity services`, `ps -A`, `cat /proc/loadavg`, `df -k /data`, and calculates deltas between pre/post snapshots.
- **`core/debloater.py`**: Evaluates package safety, enforces critical blacklists, captures timestamped backups, and runs the interactive customization questionnaire.
- **`packages/galaxy_watch6.json`**: Hardware-specific package catalog with descriptions, memory impact ratings, and default actions.

## Safety Directives for Agents
1. **Never Permanently Uninstall System APKs**: Never use `pm uninstall` without backups. Always use `pm disable-user --user 0 <pkg>`. This stops background processes and memory allocation while keeping the APK safe in system partition for instantaneous restoration.
2. **Never Touch Blacklisted Packages**: Never disable `android`, `com.samsung.android.wearable.sysui`, `com.google.android.apps.wearable.settings`, `com.google.android.apps.wearable.systemui`, `com.google.android.gms`, `com.android.bluetooth`, `com.samsung.android.honeyboard`, or `com.samsung.wear.watchface.runtime`.
3. **Always Benchmark Before & After**: Ensure resource metrics are captured prior to modifying package states and verified after disabling services.
4. **Always Back Up**: The system must persist state snapshots in `backups/` before altering any package.
