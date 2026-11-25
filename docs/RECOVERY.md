# Recovery / rollback

**Only perform actions while parked and the head unit is responsive.** If in a restart loop, the unit is unsafe/unresponsive, or the root partition cannot remount read-only, stop: do not keep power-cycling it.

## Inspect status (read-only)

```bash
# MAC TERMINAL, not BMW SSH
bash boostdeck.sh status
```

## Disable without modifying system root

```bash
# MAC TERMINAL — creates a file in the writable /var/local/data partition
bash boostdeck.sh disable
```

This writes `/var/local/data/BoostDeckCDS/app.disable` and preserves all plugin files and other apps. It takes effect the next time iDrive starts this plugin. It is not an instant kill switch for an app already loaded. Do not force repeated restarts.

## Restore the prior version

An update automatically saves `work/backups/BoostDeckCDS-YYYYMMDD-HHMMSS.tar` on the Mac and a matching `.sha256` record. Keep both somewhere safe **outside the head unit**. Do not commit these files to GitHub.

```bash
# MAC TERMINAL — supply an actual file from work/backups/
shasum -a 256 -c work/backups/BoostDeckCDS-YYYYMMDD-HHMMSS.tar.sha256
bash boostdeck.sh restore work/backups/BoostDeckCDS-YYYYMMDD-HHMMSS.tar
```

The restore command validates the plugin-only backup, confirms OS/path/root safety, asks for `RESTORE BOOSTDECK`, uploads the backup to `/tmp`, then uses a similar staged directory swap. The current plugin is retained outside Plugins for manual recovery, and root is returned read-only.

**Caution:** this restores plugin files only; it does not automatically revert saved settings in `/var/local/data/BoostDeckCDS/`. The public installer does not automatically edit existing settings, so it normally needs no such recovery.

If a new install was not preceded by an older BoostDeckCDS directory, there is no saved previous version. `disable` is the intended first recovery step. A forced uninstall is intentionally not included in this first public release because removing plugins on an unknown HMI revision is riskier than leaving a disabled plugin installed.

## Re-enable after fixing the issue

```bash
# MAC TERMINAL, after verifying the head unit is stable and the app is safe to run
bash boostdeck.sh enable
```

Requires typing `ENABLE BOOSTDECK`; it only removes the matching `app.disable` flag on the writable data partition.
