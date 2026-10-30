import time
from typing import Dict, Any, Tuple
from core.adb import AdbDevice
from core.ui import (
    print_section,
    print_info,
    print_success,
    print_warning,
    Colors
)

class WatchTuner:
    """Manages low-level Android settings for Wear OS speed & battery optimization."""
    
    TUNINGS = [
        {
            "key": "window_animation_scale",
            "namespace": "global",
            "default": "1.0",
            "optimized": "0.5",
            "name": "Window Animation Scale",
            "description": "Reduces window opening transition times by 50% for instant responsiveness."
        },
        {
            "key": "transition_animation_scale",
            "namespace": "global",
            "default": "1.0",
            "optimized": "0.5",
            "name": "Transition Animation Scale",
            "description": "Speeds up app-to-app and tile-to-tile navigation animations."
        },
        {
            "key": "animator_duration_scale",
            "namespace": "global",
            "default": "1.0",
            "optimized": "0.5",
            "name": "Animator Duration Scale",
            "description": "Cuts UI element and notification animation delay in half."
        },
        {
            "key": "wifi_scan_always_enabled",
            "namespace": "global",
            "default": "1",
            "optimized": "0",
            "name": "Wi-Fi Background Scanning",
            "description": "Prevents continuous Wi-Fi radio probing for location when Wi-Fi is turned off."
        }
    ]

    def __init__(self, adb: AdbDevice):
        self.adb = adb

    def get_setting(self, namespace: str, key: str) -> str:
        out = self.adb.shell(f"settings get {namespace} {key}").strip()
        return out if out != "null" else ""

    def put_setting(self, namespace: str, key: str, value: str) -> bool:
        self.adb.shell(f"settings put {namespace} {key} {value}")
        # Verify
        current = self.get_setting(namespace, key)
        return current == value

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for item in self.TUNINGS:
            val = self.get_setting(item["namespace"], item["key"])
            status[item["key"]] = {
                "name": item["name"],
                "current": val or item["default"],
                "default": item["default"],
                "optimized": item["optimized"],
                "description": item["description"],
                "is_optimized": val == item["optimized"]
            }
        return status

    def apply_optimizations(self, animation_speed: str = "0.5") -> Tuple[int, int]:
        """Applies 0.5x animation speed and battery scanning optimizations."""
        applied = 0
        failed = 0

        for item in self.TUNINGS:
            target_val = animation_speed if "animation" in item["key"] else item["optimized"]
            try:
                ok = self.put_setting(item["namespace"], item["key"], target_val)
                if ok:
                    applied += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return applied, failed

    def restore_defaults(self) -> Tuple[int, int]:
        """Reverts all settings back to factory defaults (1.0 animations, standard scanning)."""
        restored = 0
        failed = 0

        for item in self.TUNINGS:
            try:
                ok = self.put_setting(item["namespace"], item["key"], item["default"])
                if ok:
                    restored += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return restored, failed
