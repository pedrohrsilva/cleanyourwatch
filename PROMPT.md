# CleanYourWatch - Agent Execution Guide

Use this prompt template when delegating Samsung Galaxy Watch debloating and resource benchmarking to an AI coding assistant.

```markdown
You are optimizing a Samsung Galaxy Watch 6 (SM-R940) running Wear OS using the CleanYourWatch toolkit.

Device IP:Port: 192.168.31.47:44713 (paired via `adb pair` if needed, then `adb connect`)

Your goals:
1. Benchmark current system resources (Total/Used/Free RAM, ZRAM swap, running background services, and top memory consumers) using `python3 main.py measure`.
2. Inspect installed packages and list all bloatware candidates using `python3 main.py list`.
3. Confirm with the user their choices on:
   - Contactless Payments: Keep Samsung Pay, Google Wallet, both, or neither.
   - Samsung Health suite: Keep or disable.
   - Voice Assistants: Disable Bixby Wakeup & Assistant, or keep specific assistant.
   - Stock Samsung apps & watchfaces: Which convenience apps to retain.
4. Execute debloating safely with `python3 main.py debloat` (which automatically creates a full safety backup and benchmarks before/after).
5. Display the Before vs After delta comparison table to demonstrate RAM freed, services stopped, and storage recovered.
```
