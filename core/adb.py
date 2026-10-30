import subprocess
import shutil
import re
from typing import List, Dict, Optional, Tuple

class AdbError(Exception):
    pass

class AdbDevice:
    def __init__(self, serial: Optional[str] = None):
        self.adb_bin = shutil.which("adb")
        if not self.adb_bin:
            raise AdbError("ADB command not found in PATH. Please install Android Platform Tools.")
        
        self.serial = serial or self._autodetect_device()
        self._props_cache: Dict[str, str] = {}

    def _autodetect_device(self) -> str:
        """Autodetect connected device. Prioritizes wireless watch if multiple connected."""
        devices = self.get_connected_devices()
        if not devices:
            raise AdbError(
                "No ADB devices found. Ensure your Galaxy Watch has Wireless Debugging enabled "
                "and is paired/connected via 'adb connect <ip>:<port>'."
            )
        
        # If default user IP port 192.168.31.47:44713 is in devices, prioritize it
        for d in devices:
            if "192.168.31.47" in d:
                return d

        # Filter out mDNS duplicates if IP:port exists
        ip_ports = [d for d in devices if ":" in d and not d.startswith("adb-")]
        if ip_ports:
            return ip_ports[0]

        return devices[0]

    @classmethod
    def get_connected_devices(cls) -> List[str]:
        adb = shutil.which("adb")
        if not adb:
            return []
        try:
            res = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=5)
            devices = []
            for line in res.stdout.strip().splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception:
            return []

    def run_cmd(self, args: List[str], timeout: int = 20) -> str:
        cmd = [self.adb_bin, "-s", self.serial] + args
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if res.returncode != 0 and "disabled-user" not in res.stdout and "enabled" not in res.stdout:
                # Some adb commands write errors to stdout or stderr
                err = res.stderr.strip() or res.stdout.strip()
                raise AdbError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{err}")
            return res.stdout
        except subprocess.TimeoutExpired:
            raise AdbError(f"ADB command timed out after {timeout}s: {' '.join(cmd)}")
        except Exception as e:
            if isinstance(e, AdbError):
                raise
            raise AdbError(f"ADB execution error: {e}")

    def shell(self, shell_cmd: str, timeout: int = 25) -> str:
        return self.run_cmd(["shell", shell_cmd], timeout=timeout)

    def get_prop(self, prop_name: str) -> str:
        if prop_name not in self._props_cache:
            val = self.shell(f"getprop {prop_name}").strip()
            self._props_cache[prop_name] = val
        return self._props_cache[prop_name]

    @property
    def model(self) -> str:
        return self.get_prop("ro.product.model") or "Unknown Model"

    @property
    def brand(self) -> str:
        return self.get_prop("ro.product.brand") or "Samsung"

    @property
    def android_version(self) -> str:
        return self.get_prop("ro.build.version.release") or "Wear OS"

    @property
    def build_id(self) -> str:
        return self.get_prop("ro.build.display.id") or self.get_prop("ro.build.version.incremental") or "Unknown"

    def get_installed_packages(self) -> Dict[str, str]:
        """Returns dict of package_name -> apk_path"""
        raw = self.shell("pm list packages -f -u")
        packages = {}
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                line = line[len("package:"):]
                if "=" in line:
                    apk, pkg = line.rsplit("=", 1)
                    packages[pkg.strip()] = apk.strip()
                else:
                    packages[line.strip()] = ""
        return packages

    def get_disabled_packages(self) -> set:
        raw = self.shell("pm list packages -d")
        disabled = set()
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                disabled.add(line[len("package:"):].strip())
        return disabled

    def get_enabled_packages(self) -> set:
        raw = self.shell("pm list packages -e")
        enabled = set()
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                enabled.add(line[len("package:"):].strip())
        return enabled

    def disable_package(self, package_name: str) -> bool:
        """Safely disables package for user 0 (keeps APK intact for 100% reversible restore)"""
        out = self.shell(f"pm disable-user --user 0 {package_name}").strip()
        # Output: "Package ... new state: disabled-user"
        return "disabled" in out.lower() or "new state" in out.lower()

    def enable_package(self, package_name: str) -> bool:
        """Re-enables package"""
        out = self.shell(f"pm enable {package_name}").strip()
        return "enabled" in out.lower() or "new state" in out.lower()

    def is_package_installed(self, package_name: str) -> bool:
        out = self.shell(f"pm path {package_name}").strip()
        return bool(out and "package:" in out)
