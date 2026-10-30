import re
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from core.models import (
    BenchmarkSnapshot,
    RamStats,
    StorageStats,
    BatteryStats,
    ProcessMemory
)
from core.adb import AdbDevice

class BenchmarkEngine:
    def __init__(self, adb: AdbDevice):
        self.adb = adb

    def capture_snapshot(self) -> BenchmarkSnapshot:
        """Captures a complete snapshot of device resources."""
        timestamp = datetime.now().isoformat()
        
        # 1. Device identity
        model = self.adb.model
        serial = self.adb.serial
        android_ver = self.adb.android_version
        build_id = self.adb.build_id

        # 2. Memory (dumpsys meminfo)
        meminfo_out = self.adb.shell("dumpsys meminfo", timeout=45)
        ram, top_procs = self._parse_meminfo(meminfo_out)
        if ram.total_kb == 0:
            time.sleep(3)
            meminfo_out = self.adb.shell("dumpsys meminfo", timeout=45)
            ram, top_procs = self._parse_meminfo(meminfo_out)

        # 3. Storage (df -k /data)
        df_out = self.adb.shell("df -k /data")
        storage = self._parse_storage(df_out)

        # 4. Battery (dumpsys battery)
        battery_out = self.adb.shell("dumpsys battery")
        battery = self._parse_battery(battery_out)

        # 5. Service & Process counts
        services_out = self.adb.shell("dumpsys activity services | grep 'ServiceRecord{' | wc -l")
        try:
            services_count = int(services_out.strip())
        except ValueError:
            services_count = 0

        procs_out = self.adb.shell("ps -A | grep -E 'u0_a|system' | wc -l")
        try:
            procs_count = int(procs_out.strip())
        except ValueError:
            procs_count = 0

        # 6. CPU Load average (/proc/loadavg)
        load_out = self.adb.shell("cat /proc/loadavg")
        load_1m, load_5m, load_15m = self._parse_loadavg(load_out)

        # 7. Package counts
        disabled = self.adb.get_disabled_packages()
        enabled = self.adb.get_enabled_packages()

        return BenchmarkSnapshot(
            timestamp=timestamp,
            device_model=model,
            device_serial=serial,
            android_version=android_ver,
            build_id=build_id,
            ram=ram,
            storage=storage,
            battery=battery,
            running_services_count=services_count,
            running_processes_count=procs_count,
            cpu_load_1m=load_1m,
            cpu_load_5m=load_5m,
            cpu_load_15m=load_15m,
            top_processes=top_procs,
            enabled_packages_count=len(enabled),
            disabled_packages_count=len(disabled)
        )

    def _parse_meminfo(self, out: str) -> Tuple[RamStats, List[Dict[str, Any]]]:
        def parse_kb(val: str) -> int:
            return int(val.replace(',', '').replace('K', '').strip())

        total_m = re.search(r'Total RAM:\s+([\d,]+)K', out)
        free_m = re.search(r'Free RAM:\s+([\d,]+)K', out)
        used_m = re.search(r'Used RAM:\s+([\d,]+)K', out)
        zram_m = re.search(r'ZRAM:\s+([\d,]+)K\s+physical used for\s+([\d,]+)K\s+in swap', out)

        cached_kb = 0
        cached_m = re.search(r'Free RAM:.*?(\d[\d,]*K)\s+cached pss', out)
        if cached_m:
            try:
                cached_kb = parse_kb(cached_m.group(1))
            except Exception:
                pass

        total_kb = parse_kb(total_m.group(1)) if total_m else 0
        free_kb = parse_kb(free_m.group(1)) if free_m else 0
        used_kb = parse_kb(used_m.group(1)) if used_m else 0
        zram_used = parse_kb(zram_m.group(1)) if zram_m else 0
        zram_total = parse_kb(zram_m.group(2)) if zram_m else 0

        ram = RamStats(
            total_kb=total_kb,
            used_kb=used_kb,
            free_kb=free_kb,
            cached_kb=cached_kb,
            zram_used_kb=zram_used,
            zram_total_kb=zram_total
        )

        # Parse top processes
        top_procs = []
        pss_section = re.search(r'Total PSS by process:(.*?)(?:Total PSS by category:|Total RAM:)', out, re.DOTALL)
        if pss_section:
            proc_lines = re.findall(r'^\s*([\d,]+)K:\s+([^\s(]+)(?:\s+\(pid\s+(\d+))?', pss_section.group(1), re.MULTILINE)
            for mem_str, name, pid_str in proc_lines[:20]:
                pid = int(pid_str) if pid_str else None
                pss_kb = parse_kb(mem_str)
                top_procs.append({
                    "name": name,
                    "pid": pid,
                    "pss_kb": pss_kb,
                    "pss_mb": round(pss_kb / 1024, 1)
                })

        return ram, top_procs

    def _parse_storage(self, out: str) -> StorageStats:
        lines = out.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 5:
                try:
                    # 1K-blocks used available Use%
                    total_kb = float(parts[1])
                    used_kb = float(parts[2])
                    avail_kb = float(parts[3])
                    percent = int(parts[4].replace('%', ''))
                    return StorageStats(
                        total_gb=round(total_kb / (1024 * 1024), 2),
                        used_gb=round(used_kb / (1024 * 1024), 2),
                        avail_gb=round(avail_kb / (1024 * 1024), 2),
                        use_percent=percent
                    )
                except Exception:
                    pass
        return StorageStats()

    def _parse_battery(self, out: str) -> BatteryStats:
        level_m = re.search(r'level:\s+(\d+)', out)
        temp_m = re.search(r'temperature:\s+(\d+)', out)
        volt_m = re.search(r'voltage:\s+(\d+)', out)
        plugged_m = re.search(r'(AC|USB|Wireless)\s+powered:\s+true', out)

        level = int(level_m.group(1)) if level_m else 0
        temp = (float(temp_m.group(1)) / 10.0) if temp_m else 0.0
        volt = int(volt_m.group(1)) if volt_m else 0
        charging = bool(plugged_m)

        return BatteryStats(
            level=level,
            temperature_c=round(temp, 1),
            voltage_mv=volt,
            charging=charging
        )

    def _parse_loadavg(self, out: str) -> Tuple[float, float, float]:
        parts = out.strip().split()
        if len(parts) >= 3:
            try:
                return float(parts[0]), float(parts[1]), float(parts[2])
            except ValueError:
                pass
        return 0.0, 0.0, 0.0

    @staticmethod
    def compare_snapshots(before: BenchmarkSnapshot, after: BenchmarkSnapshot) -> Dict[str, Any]:
        """Calculates differences between before and after snapshots."""
        ram_diff_mb = round(after.ram.used_mb - before.ram.used_mb, 1)
        ram_diff_pct = round(after.ram.used_percent - before.ram.used_percent, 1)
        ram_freed_mb = round(before.ram.used_mb - after.ram.used_mb, 1)
        free_ram_gained_mb = round(after.ram.free_mb - before.ram.free_mb, 1)

        services_diff = after.running_services_count - before.running_services_count
        procs_diff = after.running_processes_count - before.running_processes_count
        packages_disabled_diff = after.disabled_packages_count - before.disabled_packages_count

        zram_freed_mb = round((before.ram.zram_used_kb - after.ram.zram_used_kb) / 1024, 1)
        storage_freed_gb = round(before.storage.used_gb - after.storage.used_gb, 3)

        # Check top processes freed
        before_names = {p["name"]: p for p in before.top_processes}
        after_names = {p["name"]: p for p in after.top_processes}
        
        killed_or_freed_procs = []
        for name, p_data in before_names.items():
            if name not in after_names:
                killed_or_freed_procs.append({
                    "name": name,
                    "freed_mb": p_data["pss_mb"]
                })

        return {
            "ram_used_before_mb": before.ram.used_mb,
            "ram_used_after_mb": after.ram.used_mb,
            "ram_freed_mb": ram_freed_mb,
            "ram_diff_pct": ram_diff_pct,
            "free_ram_before_mb": before.ram.free_mb,
            "free_ram_after_mb": after.ram.free_mb,
            "free_ram_gained_mb": free_ram_gained_mb,
            "zram_freed_mb": zram_freed_mb,
            "services_before": before.running_services_count,
            "services_after": after.running_services_count,
            "services_reduced": -services_diff,
            "processes_before": before.running_processes_count,
            "processes_after": after.running_processes_count,
            "processes_reduced": -procs_diff,
            "packages_disabled_count": packages_disabled_diff,
            "storage_used_before_gb": before.storage.used_gb,
            "storage_used_after_gb": after.storage.used_gb,
            "storage_freed_gb": storage_freed_gb,
            "killed_processes": killed_or_freed_procs
        }
