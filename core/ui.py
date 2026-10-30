import sys
from typing import List, Dict, Any, Optional

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    RESET = '\033[0m'

    @classmethod
    def strip(cls, text: str) -> str:
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
   ____ _                      __   __                __          __      __       __  
  / ___| | ___  __ _ _ __     \\ \\ / /___  _   _ _ __  \\ \\        / /___ _/ /______/ /_ 
 | |   | |/ _ \\/ _` | '_ \\     \\ V // _ \\| | | | '__|  \\ \\  /\\  / // _` / __/ __/ '_ \\ 
 | |___| |  __/ (_| | | | |     | || (_) | |_| | |      \\ \\/  \\/ /| (_| | (_| (__| | | |
  \\____|_|\\___|\\__,_|_| |_|     |_| \\___/ \\__,_|_|       \\__/\\__/  \\__,_|\\___\\___|_| |_|
{Colors.RESET}{Colors.DIM}   Safely debloat, measure, and optimize Samsung Galaxy Watch & Wear OS devices{Colors.RESET}
"""
    print(banner)

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══ {title.upper()} {'═' * (55 - len(title))}{Colors.RESET}\n")

def print_success(msg: str):
    print(f"  {Colors.GREEN}✔{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f"  {Colors.YELLOW}▲{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"  {Colors.RED}✖{Colors.RESET} {msg}")

def print_info(msg: str):
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")

def format_delta(val: float, unit: str = "", positive_is_good: bool = True) -> str:
    if val > 0:
        col = Colors.GREEN if positive_is_good else Colors.RED
        return f"{col}+{val}{unit}{Colors.RESET}"
    elif val < 0:
        col = Colors.RED if positive_is_good else Colors.GREEN
        return f"{col}{val}{unit}{Colors.RESET}"
    return f"{Colors.DIM}0{unit}{Colors.RESET}"

def print_device_card(info: Dict[str, Any]):
    print(f"  {Colors.BOLD}Device:{Colors.RESET}        {Colors.GREEN}{info.get('model', 'Unknown')}{Colors.RESET} ({info.get('brand', 'Samsung')})")
    print(f"  {Colors.BOLD}Serial / IP:{Colors.RESET}   {info.get('serial', 'N/A')}")
    print(f"  {Colors.BOLD}Wear OS Ver:{Colors.RESET}   Android {info.get('android_version', 'N/A')} ({info.get('build_id', 'N/A')})")
    if 'battery' in info:
        b = info['battery']
        charge_icon = "⚡" if b.charging else "🔋"
        print(f"  {Colors.BOLD}Battery:{Colors.RESET}       {charge_icon} {b.level}% ({b.temperature_c}°C, {b.voltage_mv}mV)")
    if 'storage' in info:
        s = info['storage']
        print(f"  {Colors.BOLD}Storage:{Colors.RESET}       {s.used_gb} GB used / {s.total_gb} GB total ({s.use_percent}% used, {s.avail_gb} GB free)")
    if 'ram' in info:
        r = info['ram']
        print(f"  {Colors.BOLD}Memory (RAM):{Colors.RESET} {r.used_mb} MB used / {r.total_mb} MB total ({r.used_percent}% used, {r.free_mb} MB free)")

def print_comparison_table(diff: Dict[str, Any]):
    print_section("Benchmark Results: Before vs After")

    rows = [
        ("RAM Used", f"{diff['ram_used_before_mb']} MB", f"{diff['ram_used_after_mb']} MB", format_delta(-diff['ram_freed_mb'], " MB", positive_is_good=False)),
        ("RAM Free", f"{diff['free_ram_before_mb']} MB", f"{diff['free_ram_after_mb']} MB", format_delta(diff['free_ram_gained_mb'], " MB", positive_is_good=True)),
        ("ZRAM Swap Freed", "-", "-", format_delta(diff['zram_freed_mb'], " MB", positive_is_good=True)),
        ("Running Services", str(diff['services_before']), str(diff['services_after']), format_delta(-diff['services_reduced'], "", positive_is_good=False)),
        ("Running Processes", str(diff['processes_before']), str(diff['processes_after']), format_delta(-diff['processes_reduced'], "", positive_is_good=False)),
        ("Packages Disabled", "-", str(diff['packages_disabled_count']), f"{Colors.GREEN}+{diff['packages_disabled_count']}{Colors.RESET}"),
        ("Storage Used (/data)", f"{diff['storage_used_before_gb']} GB", f"{diff['storage_used_after_gb']} GB", format_delta(-diff['storage_freed_gb'], " GB", positive_is_good=False))
    ]

    header_fmt = f"  {Colors.BOLD}{'Metric':<24} {'Before':<16} {'After':<16} {'Change':<16}{Colors.RESET}"
    sep = f"  {'─' * 70}"
    print(header_fmt)
    print(sep)
    for metric, before, after, change in rows:
        print(f"  {metric:<24} {before:<16} {after:<16} {change:<16}")
    print(sep)

    if diff.get("killed_processes"):
        print(f"\n  {Colors.BOLD}Processes Unloaded from RAM:{Colors.RESET}")
        for p in diff["killed_processes"]:
            print(f"    • {p['name']} ({p['freed_mb']} MB freed)")

def prompt_choice(question: str, options: List[str], default_idx: int = 0) -> int:
    """Prompts the user with numbered options and returns chosen index (0-based)."""
    print(f"\n{Colors.BOLD}{question}{Colors.RESET}")
    for idx, opt in enumerate(options):
        prefix = f"{Colors.GREEN}●{Colors.RESET}" if idx == default_idx else "○"
        def_tag = f" {Colors.DIM}(Default){Colors.RESET}" if idx == default_idx else ""
        print(f"  [{idx + 1}] {opt}{def_tag}")
    
    while True:
        try:
            choice = input(f"Select option [1-{len(options)}] (Enter for default {default_idx + 1}): ").strip()
            if not choice:
                return default_idx
            val = int(choice) - 1
            if 0 <= val < len(options):
                return val
            print(f"Please enter a number between 1 and {len(options)}.")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            sys.exit(0)

def prompt_confirm(question: str, default_yes: bool = True) -> bool:
    y_n = "[Y/n]" if default_yes else "[y/N]"
    while True:
        try:
            resp = input(f"{Colors.BOLD}{question}{Colors.RESET} {y_n}: ").strip().lower()
            if not resp:
                return default_yes
            if resp in ("y", "yes"):
                return True
            if resp in ("n", "no"):
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            sys.exit(0)
