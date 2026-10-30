from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class PackageSafety(str, Enum):
    RECOMMENDED = "recommended"      # Safe bloatware / telemetry / demo apps
    OPTIONAL = "optional"            # User features (Bixby, Samsung Pay, Browser, etc.)
    KEEP_DEFAULT = "keep_default"    # Useful components user might want unless specific preference
    CRITICAL = "critical"            # NEVER disable: bootloop / bricks UI / system services

class Category(str, Enum):
    TELEMETRY = "telemetry_and_bloat"
    VOICE = "voice_assistants"
    PAYMENTS = "payments"
    HEALTH = "samsung_health"
    ECOSYSTEM = "samsung_ecosystem"
    WATCHFACES = "samsung_stock_watchfaces"
    GOOGLE_APPS = "google_apps"
    USER_APPS = "third_party_apps"
    CRITICAL_SYSTEM = "critical_system"

@dataclass
class PackageDefinition:
    package_name: str
    display_name: str
    category: str
    safety: str
    description: str
    memory_impact: str = "low"  # low, medium, high
    battery_impact: str = "low" # low, medium, high
    depends_on: List[str] = field(default_factory=list)

@dataclass
class RamStats:
    total_kb: int = 0
    used_kb: int = 0
    free_kb: int = 0
    cached_kb: int = 0
    zram_used_kb: int = 0
    zram_total_kb: int = 0

    @property
    def total_mb(self) -> float:
        return round(self.total_kb / 1024, 1)

    @property
    def used_mb(self) -> float:
        return round(self.used_kb / 1024, 1)

    @property
    def free_mb(self) -> float:
        return round(self.free_kb / 1024, 1)

    @property
    def cached_mb(self) -> float:
        return round(self.cached_kb / 1024, 1)

    @property
    def used_percent(self) -> float:
        if self.total_kb == 0:
            return 0.0
        return round((self.used_kb / self.total_kb) * 100, 1)

@dataclass
class ProcessMemory:
    name: str
    pid: Optional[int]
    rss_kb: int = 0
    pss_kb: int = 0

    @property
    def rss_mb(self) -> float:
        return round(self.rss_kb / 1024, 1)

    @property
    def pss_mb(self) -> float:
        return round(self.pss_kb / 1024, 1)

@dataclass
class StorageStats:
    total_gb: float = 0.0
    used_gb: float = 0.0
    avail_gb: float = 0.0
    use_percent: int = 0

@dataclass
class BatteryStats:
    level: int = 0
    temperature_c: float = 0.0
    voltage_mv: int = 0
    charging: bool = False

@dataclass
class BenchmarkSnapshot:
    timestamp: str
    device_model: str
    device_serial: str
    android_version: str
    build_id: str
    ram: RamStats
    storage: StorageStats
    battery: BatteryStats
    running_services_count: int
    running_processes_count: int
    cpu_load_1m: float
    cpu_load_5m: float
    cpu_load_15m: float
    top_processes: List[Dict[str, Any]] = field(default_factory=list)
    enabled_packages_count: int = 0
    disabled_packages_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkSnapshot":
        ram = RamStats(**data["ram"])
        storage = StorageStats(**data["storage"])
        battery = BatteryStats(**data["battery"])
        d = dict(data)
        d["ram"] = ram
        d["storage"] = storage
        d["battery"] = battery
        return cls(**d)
