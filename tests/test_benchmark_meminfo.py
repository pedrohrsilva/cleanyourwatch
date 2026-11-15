import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.benchmark import BenchmarkEngine  # noqa: E402

PROC_MEMINFO = """MemTotal:        1317656 kB
MemFree:           54980 kB
MemAvailable:     227160 kB
Buffers:            1234 kB
Cached:           237496 kB
SwapCached:        11111 kB
SwapTotal:        922352 kB
SwapFree:         297680 kB
"""

TRUNCATED_DUMPSYS = """Applications Memory Usage (in Kilobytes):
Uptime: 123 Realtime: 456

Total PSS by process:
    120,345K: system (pid 900)
     60,100K: com.samsung.android.wear.shealth (pid 2000)
      9,499K: com.google.wear.services (pid 1063)

*** SERVICE 'meminfo' DUMP TIMEOUT (10000ms) EXPIRED ***
"""


class ParseProcMeminfoTest(unittest.TestCase):
    def test_parses_totals_from_proc_meminfo(self) -> None:
        ram = BenchmarkEngine._parse_proc_meminfo(PROC_MEMINFO)
        self.assertEqual(ram.total_kb, 1317656)
        self.assertEqual(ram.free_kb, 227160)  # MemAvailable
        self.assertEqual(ram.used_kb, 1317656 - 227160)
        self.assertEqual(ram.cached_kb, 237496)
        self.assertEqual(ram.zram_used_kb, 922352 - 297680)
        self.assertEqual(ram.zram_total_kb, 922352)

    def test_falls_back_to_memfree_when_memavailable_missing(self) -> None:
        ram = BenchmarkEngine._parse_proc_meminfo("MemTotal: 1000 kB\nMemFree: 300 kB\n")
        self.assertEqual(ram.free_kb, 300)
        self.assertEqual(ram.used_kb, 700)
        self.assertEqual(ram.zram_total_kb, 0)

    def test_empty_input_returns_zeroes(self) -> None:
        ram = BenchmarkEngine._parse_proc_meminfo("")
        self.assertEqual(ram.total_kb, 0)
        self.assertEqual(ram.used_kb, 0)


class ParseTruncatedDumpsysTest(unittest.TestCase):
    def test_top_processes_parsed_when_dump_times_out(self) -> None:
        engine = BenchmarkEngine.__new__(BenchmarkEngine)
        ram, procs = engine._parse_meminfo(TRUNCATED_DUMPSYS)
        self.assertEqual(ram.total_kb, 0)
        self.assertEqual([p["name"] for p in procs], [
            "system", "com.samsung.android.wear.shealth", "com.google.wear.services"
        ])
        self.assertEqual(procs[0]["pid"], 900)


if __name__ == "__main__":
    unittest.main()
