# SM-L715U / Android 17: custom-profile device report

Test date: 2026-11-17. This is a short functional report from one device, not a
general safe-disable profile for all Galaxy watches.

## Device and tested revision

- Device-reported model: `SM-L715U`.
- Android release property: `17`.
- Firmware: `CP2A.260330.023.L715USQS1AZH4`; security patch: `2026-08-05`.
- CleanYourWatch revision: `da9dbdeba3538bd80e5013e7707fab3cfb2df647`, unchanged.
- The original `main.py` commands `device`, `list --all`, `measure`,
  `debloat -t ... -y`, and `compare` were used with an explicit target device.
- The bundled SM-R940 catalog was treated as a reference. No stock
  `safe`, `balanced`, or `extreme` preset was applied.
- LTE was not in use; telephony and eSIM components were retained.

## Preparation and selected packages

Before this run, five earlier package disables were undone, their original
`enabled=0` default states verified, and four assistant/shortcut settings restored
from a local configuration backup. After a reboot, the disabled-package list again
matched the two packages disabled before any maintenance.

A fresh local configuration backup and baseline were captured. The original CLI
also created its own package-state backup before each of three small batches.
Every target below was inspected with `dumpsys package` and initially enabled in
its default state.

| Package | Inspected role / reason selected |
| --- | --- |
| `com.samsung.android.bixby.agent` | Unwanted Bixby assistant app |
| `com.samsung.android.bixby.wakeup` | Unwanted Bixby invocation/wake-up component |
| `com.google.android.wearable.assistant` | Unwanted Google Assistant app declaring a voice-interaction service |
| `com.samsung.android.samsungpay.gear` | Unused Samsung Wallet/payment app |
| `com.samsung.android.spay` | Wallet-specific data-sync/session bridge; inspected manually, absent from the bundled catalog |
| `com.sec.android.diagmonagent` | Diagnostic/analytics collection; user opted out |
| `com.samsung.android.watch.runestone.app` | Rubin personalization and pattern collection; user opted out |

The groups were assistants (three packages), payments (two), and diagnostics/
personalization (two). The CLI's custom-target support was used, with independent
state and visual checks after each group.

The final disabled-package diff contained exactly these seven additions. The two
previously disabled packages stayed disabled. The installed package set remained
at 282; no APKs were uninstalled and no app data was cleared.

Samsung Health, existing sensor settings, stock faces, AOD, Find My Device, updates,
Samsung account/cloud, ecosystem apps, factory-test services, connectivity, and
emergency/safety components were retained. No `tune` settings were applied.

## Three-sample resource comparison

There were three separate original `measure` snapshots per phase, with roughly
10 seconds plus collection time between samples. The table reports the median of
each metric independently; it is not a single snapshot. All six samples were
unplugged. There was no reboot between the baseline and final measurement phases.

| Metric | Before, median | After, median | Change |
| --- | ---: | ---: | ---: |
| Used RAM (`dumpsys meminfo`, MiB) | 1,334.7 | 1,271.3 | -63.4 |
| Free RAM (`dumpsys meminfo`, MiB) | 442.2 | 505.8 | +63.6 |
| Available RAM (`/proc/meminfo MemAvailable`, MiB) | 273.5 | 373.3 | +99.8 |
| Physical ZRAM use (MiB) | 149.4 | 149.0 | -0.4 |
| Running services | 92 | 86 | -6 |
| Processes counted by the repository's filter | 107 | 93 | -14 |
| Disabled packages | 2 | 9 | +7 |
| Used data storage (GiB, rounded by CLI) | 4.14 | 4.14 | 0 |
| Battery level (%) | 78 | 77 | -1 percentage point |

Used-RAM samples were 1,319.1 / 1,335.1 / 1,334.7 MiB before and
1,271.3 / 1,276.2 / 1,241.9 MiB after. The observed median reduction was 63.4 MiB,
or approximately 4.75% of baseline used RAM.

`MemAvailable` was collected separately; it is not currently a field emitted by
the original CLI. The original `compare` command was also run on representative
snapshots; its result is distinct from this independently aggregated table.

These are uncontrolled short-session measurements, not proof that all of the
difference was caused by package disabling. Background work and UI activity can
change memory use; a Health screen was active during one batch, and final samples
were taken after returning to the watch face. Immediate CLI comparisons after the
built-in three-second delay sometimes showed increased used RAM, so a single
instantaneous comparison should not be treated as a stable result.

The CLI labels binary units as MB/GB; this report uses MiB/GiB for division by
1024. Its free-RAM figure includes memory classified as reclaimable by
`dumpsys`; it differs from Linux `MemFree` and `MemAvailable`. Process counts use
the original repository's filter, not all kernel threads. Physical ZRAM use is
reported separately from occupied or total swap. No battery-life gain was measured
or projected from the one-percentage-point battery change.

## Functional and reboot checks

- The watch face, app drawer, tile carousel, and Samsung Health home screen were
  visually checked after the changes and remained usable.
- The final process-name snapshot had no matches for the seven target packages;
  this does not rule out every component running under a shared UID.
- Two Rubin alarms remained scheduled immediately after its package was disabled:
  a keep-alive alarm and a location-update alarm.
- After all benchmark samples were saved, a separate reboot was performed.
  All seven disables persisted and the two original disabled states were preserved.
- The post-reboot alarm dump had no references to the target packages. Job-scheduler
  references were confined to its cached UID-to-package map, and matching process
  names were absent. The final watch face was checked again.

Notifications, phone sync, calls, LTE, workouts, fall detection/SOS, long-term
stability, and full-charge-cycle battery life were not comprehensively tested.
Keeping their packages enabled is not a claim that these functions were verified.

## Firmware-specific findings and follow-up improvements

1. **IntelliVoice is broader than a voice assistant on this firmware.**
   `com.samsung.android.intellivoiceservice` declares SmartReply, Translation,
   Summarization, Correction, and other text/AI services. It was retained despite
   being grouped under voice assistants in the bundled catalog. Future catalog
   wording or presets should distinguish these functions by model/firmware.
2. **Assistant removal can change selections and shortcuts.**
   During the preceding disable/restore cycle, Android cleared `secure assistant`
   and `secure voice_interaction_service`, and changed
   `secure raise_trigger_default_assistant` and
   `global setting_home_key_long_press` to Bixby components even with Bixby disabled.
   Save and verify these settings as well as package states. Physical-button behavior
   was not tested; this is an observation about the stored assignments.
3. **A package-state restore is not a complete configuration restore.**
   The current CLI backup records enabled/disabled lists but not those assistant
   settings. A targeted local restore script was prepared to restore only this
   run's seven packages to their original defaults and restore the four settings.
   That seven-package restore path was not exercised. The earlier five-package
   restoration and setting comparisons were exercised before this run.
4. **Scheduled work merits a separate check.**
   A successful `disable-user` response did not immediately remove the observed
   Rubin alarms. Check package state and scheduled work separately; in this run
   the alarms disappeared after the verification reboot. Their presence alone
   does not prove that a disabled component could execute.
5. **A top-20 list is not a process-liveness check.**
   An app disappearing from the benchmark's top-process list may simply have
   fallen below that list. Confirm process state independently before describing
   it as unloaded or counting its old PSS as reclaimed RAM.

These are observations and proposed follow-ups, not code fixes or new automatic
disable recommendations. They should not be generalized to SM-R940 or other
firmware without checking the actual device.

## Privacy

Only this manually summarized report is contributed. Local backups, raw
properties/settings, package inventories, snapshots, logs, screenshots, network
addresses, serial numbers, pairing details, precise session times, and user
health/activity data are excluded.
