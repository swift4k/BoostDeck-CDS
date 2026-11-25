# Installation walkthrough — Mac Terminal only

## Prerequisites

1. An EntryNav2/EntryEVO **Linux ARMv7**, **1280×480** HMI, safe authorized root SSH access and car-specific framework files `/opt/hmi/lib/libAppFramework.A.so`, `/opt/hmi/lib/libCoreFramework.A.so`.
2. Mac: Git, Python 3 with `venv` and pip, Docker Desktop, Apple Xcode Command Line Tools (`clang++`), ENET network to car (default root@169.254.1.0), and enough free disk space for a Docker toolchain.
3. Before installation, HMI must run normally, car safely **parked**, power stable, and `/` mounted **read-only**. Do not attempt while driving.
4. Prefer a backup of vehicle and existing plugins. **No root password or BMW library files are distributed.**

## Fresh build

From this project folder in regular **Mac Terminal** (not SSH):

```bash
bash boostdeck.sh doctor
bash boostdeck.sh fetch-libs
bash boostdeck.sh preview
bash boostdeck.sh build
```

`fetch-libs` streams the two BMW framework libraries **from your own car to the Mac only**. It neither installs anything nor modifies the head unit. Alternatively use a prior known-compatible local copy:

```bash
bash boostdeck.sh build --libs "$HOME/path/to/Entry_Evo_libs"
```

The first build clones upstream commit `899e337`, applies the dashboard transformation and later layout/US-units upgrades, generates assets with Pillow, checks the generated 1219×460 image/XML, validates live numeric conversion and sign handling with `clang++`, then uses the upstream Docker ARM toolchain. The resulting archive is at `work/source/dist/boostdeck-cds-entrynav2.tar` and preview at `work/source/res/preview_en.png`.

The build **does not access the BMW** unless you explicitly ran `fetch-libs` separately.

If Python/Pillow fails to install: verify a usable Python 3 with `venv` and Internet; retry. The script will reuse the workspace that it created, never overwrite an unrelated source folder. You may set `BOOSTDECK_HOME` to another local directory before the first build.

## Installation

```bash
bash boostdeck.sh status
bash boostdeck.sh install
```

Read the preflight and type **`INSTALL BOOSTDECK`** if you accept the filesystem risk. The installer:

1. Locally checks file integrity, ARM ELF format, resources and manifest ID.
2. Remotely checks EntryNav2 OS/paths, root read-only mount, and identity conflicts.
3. For an existing `BoostDeckCDS` installation, streams a verified backup to `work/backups/` on the Mac and records SHA-256, **before any remount**.
4. Uploads the archive into remote `/tmp`, validates `MD5SUMS`, prepares the new plugin tree, and only then temporarily remounts `/` read/write.
5. Atomically swaps the **BoostDeckCDS** plugin directory, retains an old-plugin copy outside Plugins when updating, syncs, and remounts root read-only. No firmware/ECU coding, no other plugin deletion, no automatic reboot.

Afterward, when the car is stable, perform **one normal controlled iDrive restart** and verify the new display and real CDS properties. If the app is missing from menus, the firmware's PluginApp support/setup or focus IDs may differ; don't repeat system remounts hoping it will appear.

## Updating an older BoostDeckCDS

The exact same build and install command works when a `BoostDeckCDS` folder already exists, but **only with a verified Mac backup** and matching plugin identity. The default settings migration is deliberately **not forced**: an old `settings.txt` can retain previously chosen PS/litres instead of the new constructor defaults of HP/US gallons. To use HP and US gal on an upgraded unit, change **only those two settings through the app's Options menu** (or follow the original manual settings migration after making a backup). This avoids silently overwriting the user's explicit preference.

The old `GaugeApp` and original `BoostDeck` stay installed. **Do not use the older destructive cleanup script as a generic GitHub public installer.**

## Safe verification commands (Mac Terminal)

```bash
ssh -T root@169.254.1.0 'grep " / " /proc/mounts'
# Should include ro, ... on the root filesystem before installing
bash boostdeck.sh status
```

To build a different pinned upstream, modify the build script and patch tests together. Do **not** bypass validation checks: a mismatch often means an unsupported source generation.
