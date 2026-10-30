import os
import json
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Tuple

from core.adb import AdbDevice
from core.models import PackageSafety, Category
from core.ui import (
    print_section,
    print_info,
    print_success,
    print_warning,
    print_error,
    prompt_choice,
    prompt_confirm,
    Colors
)

class DebloatEngine:
    def __init__(self, adb: AdbDevice, db_path: Optional[str] = None):
        self.adb = adb
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "packages", "galaxy_watch6.json")
        self.db_path = db_path
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @property
    def blacklist(self) -> Set[str]:
        return set(self.catalog.get("critical_blacklist", []))

    def create_backup(self, backup_dir: str = "backups") -> str:
        """Saves current state of all packages before changes."""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_serial = self.adb.serial.replace(":", "_").replace(".", "_")
        filename = f"backup_{safe_serial}_{timestamp}.json"
        filepath = os.path.join(backup_dir, filename)

        enabled = list(self.adb.get_enabled_packages())
        disabled = list(self.adb.get_disabled_packages())

        data = {
            "timestamp": datetime.now().isoformat(),
            "device": self.adb.model,
            "serial": self.adb.serial,
            "android_version": self.adb.android_version,
            "enabled_packages": enabled,
            "disabled_packages": disabled
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return filepath

    def scan_device(self) -> Dict[str, Any]:
        """Scans device and categorizes every installed package."""
        installed = self.adb.get_installed_packages()
        disabled = self.adb.get_disabled_packages()

        results = {
            "total_installed": len(installed),
            "total_disabled": len(disabled),
            "categories": {}
        }

        # Build reverse map for fast lookup
        pkg_cat_map = {}
        for cat_id, cat_info in self.catalog.get("categories", {}).items():
            for p in cat_info.get("packages", []):
                pkg_cat_map[p["package_name"]] = (cat_id, p)

        for cat_id, cat_info in self.catalog.get("categories", {}).items():
            results["categories"][cat_id] = {
                "title": cat_info["title"],
                "packages": []
            }

        unclassified = []

        for pkg_name, apk_path in installed.items():
            is_disabled = pkg_name in disabled
            is_blacklisted = pkg_name in self.blacklist

            if pkg_name in pkg_cat_map:
                cat_id, meta = pkg_cat_map[pkg_name]
                entry = dict(meta)
                entry["is_disabled"] = is_disabled
                entry["apk_path"] = apk_path
                results["categories"][cat_id]["packages"].append(entry)
            elif is_blacklisted:
                continue
            else:
                unclassified.append({
                    "package_name": pkg_name,
                    "is_disabled": is_disabled,
                    "apk_path": apk_path
                })

        results["unclassified"] = unclassified
        return results

    def interactive_wizard(self) -> List[str]:
        """Interactive questions asking the user what to keep and what to disable."""
        print_section("Customization Wizard: Select What To Keep")
        packages_to_disable: Set[str] = set()

        installed = self.adb.get_installed_packages()
        disabled = self.adb.get_disabled_packages()

        # Helper to filter installed packages from a category
        def get_installed_in_cat(cat_name: str) -> List[Dict[str, Any]]:
            pkgs = self.catalog.get("categories", {}).get(cat_name, {}).get("packages", [])
            return [p for p in pkgs if p["package_name"] in installed]

        # 1. Telemetry and Bloatware
        telemetry_pkgs = get_installed_in_cat("telemetry_and_bloat")
        if telemetry_pkgs:
            print(f"{Colors.BOLD}[1/6] Telemetry, Background Tracking & Demo Bloat{Colors.RESET}")
            print("  Includes: Samsung Diagnostic Monitor, Samsung Global Goals ads, retail demos, Rubin personalization.")
            choice = prompt_choice(
                "How would you like to handle telemetry and manufacturer bloat?",
                [
                    "Disable all telemetry and bloatware (Recommended - saves RAM & battery)",
                    "Keep telemetry active"
                ],
                default_idx=0
            )
            if choice == 0:
                for p in telemetry_pkgs:
                    packages_to_disable.add(p["package_name"])

        # 2. Contactless Payments
        payment_pkgs = get_installed_in_cat("payments")
        samsung_pay = "com.samsung.android.samsungpay.gear"
        google_pay = "com.google.android.apps.walletnfcrel"
        has_spay = samsung_pay in installed
        has_gpay = google_pay in installed

        if has_spay or has_gpay:
            print(f"\n{Colors.BOLD}[2/6] Contactless Payments & Wallets{Colors.RESET}")
            opts = []
            opt_actions = []
            
            if has_spay:
                opts.append("Keep Samsung Pay ONLY (Disable Google Wallet)")
                opt_actions.append(lambda: packages_to_disable.add(google_pay) if has_gpay else None)
            
            if has_gpay:
                opts.append("Keep Google Wallet ONLY (Disable Samsung Pay)")
                opt_actions.append(lambda: packages_to_disable.add(samsung_pay) if has_spay else None)

            if has_spay and has_gpay:
                opts.append("Keep BOTH Samsung Pay & Google Wallet")
                opt_actions.append(lambda: None)

            opts.append("Disable ALL contactless payment services (saves background NFC/RAM)")
            opt_actions.append(lambda: [packages_to_disable.add(p) for p in [samsung_pay, google_pay] if p in installed])

            choice = prompt_choice("Which payment service do you want to keep on your watch?", opts, default_idx=0)
            opt_actions[choice]()

        # 3. Samsung Health & Fitness Suite
        health_pkgs = get_installed_in_cat("samsung_health")
        if health_pkgs:
            print(f"\n{Colors.BOLD}[3/6] Samsung Health & Fitness Suite{Colors.RESET}")
            print("  Samsung Health uses ~60MB RAM and runs continuous background sensor listeners.")
            choice = prompt_choice(
                "Do you want to keep Samsung Health (step tracking, workouts, heart rate, ECG)?",
                [
                    "Keep Samsung Health active (Recommended if you track fitness on watch)",
                    "Disable Samsung Health suite (Maximum battery & RAM savings)"
                ],
                default_idx=0
            )
            if choice == 1:
                for p in health_pkgs:
                    packages_to_disable.add(p["package_name"])

        # 4. Voice Assistants
        voice_pkgs = get_installed_in_cat("voice_assistants")
        if voice_pkgs:
            bixby_wake = "com.samsung.android.bixby.wakeup"
            bixby_agent = "com.samsung.android.bixby.agent"
            goog_assist = "com.google.android.wearable.assistant"

            print(f"\n{Colors.BOLD}[4/6] Voice Assistants (Bixby & Google Assistant){Colors.RESET}")
            print("  Voice wakeup ('Hi Bixby') keeps microphone listening constantly, impacting battery life.")
            choice = prompt_choice(
                "Which voice assistant setup do you prefer?",
                [
                    "Disable ALL voice assistants & voice wake-up (Recommended for battery & privacy)",
                    "Keep Bixby app, but disable always-listening voice wakeup (Good balance)",
                    "Keep Google Assistant only (Disable Bixby)",
                    "Keep Bixby only",
                    "Keep everything enabled"
                ],
                default_idx=0
            )
            if choice == 0:
                for p in voice_pkgs:
                    packages_to_disable.add(p["package_name"])
            elif choice == 1:
                if bixby_wake in installed:
                    packages_to_disable.add(bixby_wake)
            elif choice == 2:
                if bixby_agent in installed:
                    packages_to_disable.add(bixby_agent)
                if bixby_wake in installed:
                    packages_to_disable.add(bixby_wake)
            elif choice == 3:
                if goog_assist in installed:
                    packages_to_disable.add(goog_assist)

        # 5. Samsung Ecosystem & Built-in Apps
        eco_pkgs = get_installed_in_cat("samsung_ecosystem")
        if eco_pkgs:
            print(f"\n{Colors.BOLD}[5/6] Samsung Ecosystem & Accessory Apps{Colors.RESET}")
            print("  Includes: Samsung Internet Browser (~55MB RAM), Voice Recorder, SmartThings, Modes & Routines, Smart Switch.")
            choice = prompt_choice(
                "How would you like to handle Samsung ecosystem apps?",
                [
                    "Disable non-essential Samsung apps (Browser, Smart Switch, Voice Recorder, SmartThings)",
                    "Custom selection (ask app-by-app)",
                    "Keep all Samsung ecosystem apps"
                ],
                default_idx=0
            )
            if choice == 0:
                common_removals = [
                    "com.sec.android.app.sbrowser",
                    "com.samsung.android.wear.smartswitchassistant",
                    "com.sec.android.easyMover",
                    "com.samsung.android.wear.voicerecorder",
                    "com.samsung.android.oneconnect",
                    "com.samsung.android.wear.musictransfer",
                    "com.samsung.android.gallery.watch"
                ]
                for p in common_removals:
                    if p in installed:
                        packages_to_disable.add(p)
            elif choice == 1:
                for p in eco_pkgs:
                    p_name = p["package_name"]
                    p_desc = p.get("description", "")
                    mem_impact = p.get("memory_impact", "low")
                    ans = prompt_choice(
                        f"App: {Colors.BOLD}{p['display_name']}{Colors.RESET} ({p_name})\n  Impact: {mem_impact} RAM | {p_desc}",
                        ["Keep this app", "Disable this app"],
                        default_idx=0
                    )
                    if ans == 1:
                        packages_to_disable.add(p_name)

        # 6. Samsung Pre-installed Stock Watch Faces
        watchface_pkgs = get_installed_in_cat("samsung_stock_watchfaces")
        if watchface_pkgs:
            print(f"\n{Colors.BOLD}[6/6] Samsung Stock Watch Faces{Colors.RESET}")
            print(f"  There are {len(watchface_pkgs)} Samsung pre-installed watchfaces on this watch.")
            print("  Disabling unused stock faces cleans up the watch face picker and saves background memory.")
            choice = prompt_choice(
                "Do you want to disable unused Samsung stock watch faces?",
                [
                    "Disable Samsung stock watchfaces (Recommended if using a third-party/custom face)",
                    "Keep all stock watch faces"
                ],
                default_idx=0
            )
            if choice == 0:
                for p in watchface_pkgs:
                    packages_to_disable.add(p["package_name"])

        # Filter out anything in blacklist or already disabled
        final_list = [
            pkg for pkg in packages_to_disable
            if pkg not in self.blacklist and pkg in installed and pkg not in disabled
        ]

        return final_list

    def apply_debloat(self, package_names: List[str]) -> Tuple[List[str], List[str]]:
        """Safely disables the given list of packages."""
        successes = []
        failures = []

        for pkg in package_names:
            if pkg in self.blacklist:
                print_warning(f"Skipping {pkg} (Safety protection: Critical system package)")
                continue

            try:
                ok = self.adb.disable_package(pkg)
                if ok:
                    successes.append(pkg)
                else:
                    failures.append(pkg)
            except Exception as e:
                failures.append(pkg)

        return successes, failures

    def restore_backup(self, backup_file: str) -> Tuple[List[str], List[str]]:
        """Restores packages to the state saved in backup_file."""
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        enabled_in_backup = set(data.get("enabled_packages", []))
        currently_disabled = self.adb.get_disabled_packages()

        # Packages that were enabled in backup, but are currently disabled
        to_restore = [p for p in currently_disabled if p in enabled_in_backup]

        restored = []
        failed = []
        for pkg in to_restore:
            try:
                ok = self.adb.enable_package(pkg)
                if ok:
                    restored.append(pkg)
                else:
                    failed.append(pkg)
            except Exception:
                failed.append(pkg)

        return restored, failed

    def restore_all_known(self) -> Tuple[List[str], List[str]]:
        """Re-enables all currently disabled packages that belong to known catalog."""
        currently_disabled = self.adb.get_disabled_packages()
        restored = []
        failed = []

        for pkg in currently_disabled:
            try:
                ok = self.adb.enable_package(pkg)
                if ok:
                    restored.append(pkg)
                else:
                    failed.append(pkg)
            except Exception:
                failed.append(pkg)

        return restored, failed
