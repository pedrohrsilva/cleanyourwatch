# CleanYourWatch - Universal Agent Prompt

Copy and paste the prompt below into your AI coding assistant (Cursor, Claude Code, Gemini CLI, Antigravity, GitHub Copilot, Codex, etc.) along with your watch's IP address:

```markdown
Debloat, optimize, and benchmark my Wear OS smartwatch using the CleanYourWatch repository.

Watch Model: [e.g. Galaxy Watch 6 SM-R940]
Watch IP:Port: [e.g. 192.168.31.47:44713] (or mention if already connected via adb)

Please follow this structured workflow:
1. Connect & Verify:
   - Verify the watch is accessible via ADB (`adb connect <watch_ip>:<port>`).
   - If pairing is needed, guide me through `adb pair <watch_ip>:<pairing_port>` with the 6-digit code.
   - Run `python3 main.py device` to confirm model, battery, storage, and current memory status.

2. Pre-Debloat Resource Benchmark:
   - Capture a pre-debloat resource snapshot (`python3 main.py measure`).
   - Report the current used RAM, free RAM, ZRAM swap, running background services, and top memory-consuming processes.

3. Preference Checklist:
   Ask me what I want to keep vs disable before modifying anything:
   - Contactless Payments: Keep Samsung Pay, Google Wallet, both, or disable both?
   - Samsung Health: Keep health tracking (steps, workouts, ECG/BP), or disable to free ~60MB RAM?
   - Voice Assistants: Disable always-listening mic drain ("Hi Bixby") / Google Assistant, or keep one?
   - Samsung Ecosystem Apps: Keep Samsung Browser, Voice Recorder, SmartThings, Modes & Routines, or disable non-essential ones?
   - Stock Watch Faces: Keep or disable pre-installed Samsung stock watch faces?

4. Safety Backup & Execution:
   - Ensure an automated state backup is created in `backups/` before touching any package.
   - Disable chosen packages using safe user-level suspension (`pm disable-user --user 0`).
   - Strictly respect the critical blacklist (never touch System UI, Bluetooth, Watch Face Runtime, Settings, Phone, Keyboard).

5. Post-Debloat Benchmark & Reporting:
   - Measure post-debloat resources (`python3 main.py measure`).
   - Print a side-by-side comparison table showing:
     * RAM freed (MB and %)
     * Free RAM headroom gained
     * Top processes unloaded from memory
     * Estimated battery savings per charge
```
