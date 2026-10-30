#!/usr/bin/env python3
import sys
import os
import argparse
import json
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.adb import AdbDevice, AdbError
from core.benchmark import BenchmarkEngine
from core.debloater import DebloatEngine
from core.models import BenchmarkSnapshot
from core.ui import (
    print_banner,
    print_section,
    print_device_card,
    print_comparison_table,
    print_info,
    print_success,
    print_warning,
    print_error,
    prompt_confirm,
    Colors
)

DEFAULT_WATCH_DEVICE = "192.168.31.47:44713"

def get_adb(serial_arg: str = None) -> AdbDevice:
    try:
        # Check if specified serial or default is in connected devices
        connected = AdbDevice.get_connected_devices()
        target = serial_arg
        if not target:
            if DEFAULT_WATCH_DEVICE in connected:
                target = DEFAULT_WATCH_DEVICE
            elif len(connected) > 0:
                # pick the first one matching IP:port or watch
                target = connected[0]
        
        adb = AdbDevice(target)
        return adb
    except AdbError as e:
        print_error(f"ADB Connection Error: {e}")
        print_info(f"Make sure wireless debugging is enabled on your watch and run:\n  adb connect {DEFAULT_WATCH_DEVICE}")
        sys.exit(1)

def cmd_device(args):
    print_banner()
    adb = get_adb(args.device)
    bench = BenchmarkEngine(adb)
    print_section("Connected Watch Information")
    snap = bench.capture_snapshot()
    print_device_card({
        "model": snap.device_model,
        "brand": adb.brand,
        "serial": snap.device_serial,
        "android_version": snap.android_version,
        "build_id": snap.build_id,
        "battery": snap.battery,
        "storage": snap.storage,
        "ram": snap.ram
    })
    print(f"\n  {Colors.BOLD}Background Services:{Colors.RESET} {snap.running_services_count}")
    print(f"  {Colors.BOLD}Active Processes:{Colors.RESET}    {snap.running_processes_count}")
    print(f"  {Colors.BOLD}CPU Load Average:{Colors.RESET}    {snap.cpu_load_1m} (1m), {snap.cpu_load_5m} (5m), {snap.cpu_load_15m} (15m)")
    print(f"  {Colors.BOLD}Packages:{Colors.RESET}            {snap.enabled_packages_count} enabled / {snap.disabled_packages_count} disabled")

def cmd_measure(args):
    print_banner()
    adb = get_adb(args.device)
    bench = BenchmarkEngine(adb)
    print_info("Measuring watch resources (RAM, CPU, storage, running processes)...")
    snap = bench.capture_snapshot()
    
    os.makedirs("snapshots", exist_ok=True)
    out_file = args.output
    if not out_file:
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_file = f"snapshots/snapshot_{ts}.json"
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snap.to_dict(), f, indent=2)

    print_section(f"Resource Benchmark Snapshot: {snap.device_model}")
    print_device_card({
        "model": snap.device_model,
        "brand": adb.brand,
        "serial": snap.device_serial,
        "android_version": snap.android_version,
        "build_id": snap.build_id,
        "battery": snap.battery,
        "storage": snap.storage,
        "ram": snap.ram
    })

    print(f"\n  {Colors.BOLD}Total RAM:{Colors.RESET}          {snap.ram.total_mb} MB")
    print(f"  {Colors.BOLD}Used RAM:{Colors.RESET}           {snap.ram.used_mb} MB ({snap.ram.used_percent}%)")
    print(f"  {Colors.BOLD}Free RAM:{Colors.RESET}           {snap.ram.free_mb} MB (Cached: {snap.ram.cached_mb} MB)")
    print(f"  {Colors.BOLD}ZRAM Swap:{Colors.RESET}          {round(snap.ram.zram_used_kb/1024, 1)} MB used / {round(snap.ram.zram_total_kb/1024, 1)} MB total")
    print(f"  {Colors.BOLD}Running Services:{Colors.RESET}   {snap.running_services_count}")
    print(f"  {Colors.BOLD}Running Processes:{Colors.RESET}  {snap.running_processes_count}")

    if snap.top_processes:
        print(f"\n  {Colors.BOLD}Top 10 Memory Consuming Processes (PSS):{Colors.RESET}")
        for p in snap.top_processes[:10]:
            print(f"    • {p['name']:<40} {p['pss_mb']} MB")

    print_success(f"Snapshot saved to: {out_file}")

def cmd_list(args):
    print_banner()
    adb = get_adb(args.device)
    debloater = DebloatEngine(adb)
    
    print_info("Scanning packages on watch...")
    scan = debloater.scan_device()

    print_section(f"Installed Packages ({scan['total_installed']} total, {scan['total_disabled']} disabled)")

    for cat_id, cat_info in scan["categories"].items():
        pkgs = cat_info["packages"]
        if not pkgs and not args.all:
            continue
        print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ {cat_info['title']} ({len(pkgs)} packages){Colors.RESET}")
        for p in pkgs:
            status = f"{Colors.RED}[DISABLED]{Colors.RESET}" if p["is_disabled"] else f"{Colors.GREEN}[ACTIVE]{Colors.RESET}"
            rec = f"{Colors.CYAN}(Safe to disable){Colors.RESET}" if p.get("safety") == "recommended" else f"{Colors.DIM}(Optional){Colors.RESET}"
            print(f"  {status} {Colors.BOLD}{p['display_name']:<30}{Colors.RESET} {p['package_name']}")
            print(f"       {Colors.DIM}Memory: {p.get('memory_impact','low')} | {p.get('description','')} {rec}{Colors.RESET}")

    if args.all and scan.get("unclassified"):
        print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ Other Installed Packages ({len(scan['unclassified'])}){Colors.RESET}")
        for p in scan["unclassified"]:
            status = f"{Colors.RED}[DISABLED]{Colors.RESET}" if p["is_disabled"] else f"{Colors.GREEN}[ACTIVE]{Colors.RESET}"
            print(f"  {status} {p['package_name']}")

def cmd_debloat(args):
    print_banner()
    adb = get_adb(args.device)
    bench = BenchmarkEngine(adb)
    debloater = DebloatEngine(adb)

    # 1. Pre-Benchmark
    print_section("Step 1: Measuring Pre-Debloat System Resources")
    print_info("Analyzing current memory, processes, and service usage...")
    pre_snap = bench.capture_snapshot()
    
    print(f"  • Used RAM:           {Colors.BOLD}{pre_snap.ram.used_mb} MB{Colors.RESET} ({pre_snap.ram.used_percent}%)")
    print(f"  • Free RAM:           {pre_snap.ram.free_mb} MB")
    print(f"  • Running Services:   {pre_snap.running_services_count}")
    print(f"  • Active Processes:   {pre_snap.running_processes_count}")

    # 2. Interactive Wizard or Selection
    print_section("Step 2: Debloat Configuration")
    targets = debloater.interactive_wizard()

    if not targets:
        print_info("No packages were selected for debloating. Exiting.")
        return

    print_section(f"Step 3: Review Selected Packages ({len(targets)})")
    print("The following packages will be safely suspended:")
    for pkg in targets:
        print(f"  • {Colors.YELLOW}{pkg}{Colors.RESET}")

    if not args.yes:
        confirm = prompt_confirm(f"\nProceed with suspending these {len(targets)} packages?", default_yes=True)
        if not confirm:
            print_info("Operation cancelled by user.")
            return

    # 3. Create Backup
    print_section("Step 4: Creating Safety Backup")
    backup_file = debloater.create_backup()
    print_success(f"State saved to: {backup_file}")
    print_info("You can revert this anytime with: python3 main.py restore")

    # 4. Apply Debloat
    print_section("Step 5: Suspending Packages")
    successes, failures = debloater.apply_debloat(targets)
    print_success(f"Successfully disabled {len(successes)} packages.")
    if failures:
        print_warning(f"Failed to disable {len(failures)} packages: {', '.join(failures)}")

    # 5. Post-Benchmark
    print_section("Step 6: Measuring Post-Debloat System Resources")
    print_info("Waiting 3 seconds for system to reclaim memory...")
    time.sleep(3)
    post_snap = bench.capture_snapshot()

    # 6. Save Snapshots & Compare
    os.makedirs("snapshots", exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    with open(f"snapshots/pre_{ts}.json", "w") as f:
        json.dump(pre_snap.to_dict(), f, indent=2)
    with open(f"snapshots/post_{ts}.json", "w") as f:
        json.dump(post_snap.to_dict(), f, indent=2)

    diff = BenchmarkEngine.compare_snapshots(pre_snap, post_snap)
    print_comparison_table(diff)
    print_success("Debloating complete! Enjoy a lighter, faster, and longer-lasting Galaxy Watch.")

def cmd_compare(args):
    print_banner()
    with open(args.snapshot1, "r", encoding="utf-8") as f:
        snap1 = BenchmarkSnapshot.from_dict(json.load(f))
    with open(args.snapshot2, "r", encoding="utf-8") as f:
        snap2 = BenchmarkSnapshot.from_dict(json.load(f))

    diff = BenchmarkEngine.compare_snapshots(snap1, snap2)
    print_comparison_table(diff)

def cmd_restore(args):
    print_banner()
    adb = get_adb(args.device)
    debloater = DebloatEngine(adb)

    print_section("Package Restoration")
    if args.file:
        if not os.path.isfile(args.file):
            print_error(f"Backup file not found: {args.file}")
            sys.exit(1)
        print_info(f"Restoring packages from: {args.file}")
        restored, failed = debloater.restore_backup(args.file)
    else:
        # Check latest backup
        backups = [os.path.join("backups", f) for f in os.listdir("backups")] if os.path.exists("backups") else []
        backups = [f for f in backups if f.endswith(".json")]
        if backups:
            backups.sort(key=os.path.getmtime, reverse=True)
            latest = backups[0]
            print_info(f"Found latest backup: {latest}")
            if prompt_confirm(f"Restore from {latest}?", default_yes=True):
                restored, failed = debloater.restore_backup(latest)
            else:
                print_info("Restoring all known disabled packages instead...")
                restored, failed = debloater.restore_all_known()
        else:
            print_info("No backup file specified. Restoring all currently disabled packages...")
            restored, failed = debloater.restore_all_known()

    print_success(f"Restored {len(restored)} packages to enabled state.")
    if failed:
        print_warning(f"Failed to restore {len(failed)} packages: {', '.join(failed)}")

def main():
    parser = argparse.ArgumentParser(
        description="CleanYourWatch: Measure, debloat, and optimize Samsung Galaxy Watch Wear OS."
    )
    parser.add_argument(
        "-d", "--device",
        help=f"Target ADB device serial or IP:port (default: {DEFAULT_WATCH_DEVICE})"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # device
    subparsers.add_parser("device", help="Display connected watch hardware, battery & RAM info")

    # measure
    p_measure = subparsers.add_parser("measure", help="Capture a resource benchmark snapshot")
    p_measure.add_argument("-o", "--output", help="Output JSON path for snapshot")

    # list
    p_list = subparsers.add_parser("list", help="List installed packages categorized with impact ratings")
    p_list.add_argument("-a", "--all", action="store_true", help="Include all unclassified system packages")

    # debloat
    p_debloat = subparsers.add_parser("debloat", help="Interactive debloat wizard with before/after benchmarks")
    p_debloat.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare two benchmark snapshots")
    p_compare.add_argument("snapshot1", help="Path to before snapshot JSON")
    p_compare.add_argument("snapshot2", help="Path to after snapshot JSON")

    # restore
    p_restore = subparsers.add_parser("restore", help="Re-enable previously disabled packages")
    p_restore.add_argument("-f", "--file", help="Specific backup JSON file to restore from")

    args = parser.parse_args()

    if not args.command:
        # Default behavior if run without args: display device info and help
        cmd_device(args)
        print(f"\n{Colors.BOLD}Quick Commands:{Colors.RESET}")
        print("  python3 main.py list      - View categorized bloatware and packages")
        print("  python3 main.py measure   - Take a resource usage benchmark")
        print("  python3 main.py debloat   - Start interactive debloat with before/after benchmark")
        print("  python3 main.py restore   - Undo changes and re-enable packages")
        return

    commands = {
        "device": cmd_device,
        "measure": cmd_measure,
        "list": cmd_list,
        "debloat": cmd_debloat,
        "compare": cmd_compare,
        "restore": cmd_restore
    }

    commands[args.command](args)

if __name__ == "__main__":
    main()
