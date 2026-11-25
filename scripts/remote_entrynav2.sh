#!/bin/sh
# Piped over SSH by boostdeck.sh. POSIX sh / BusyBox compatible.
# No commands from an untrusted archive are executed.
set -eu
MODE="${1:-check}"
PLUGIN_BASE=/opt/hmi/data/ro/Plugins
DEST="$PLUGIN_BASE/BoostDeckCDS"
SYSTEM_BASE=/opt/hmi/data/ro

root_is_ro() {
  awk '$2 == "/" {n=split($4,f,","); for(i=1;i<=n;i++) if(f[i]=="ro") ok=1} END {exit (ok?0:1)}' /proc/mounts
}
platform() {
  [ "$(uname -s)" = Linux ] || { echo 'REFUSED: NBT Evo/QNX and non-Linux systems are unsupported'; exit 1; }
  case "$(uname -m)" in armv7*|armv6*|armhf) : ;; *) echo 'REFUSED: expected ARMv7 Linux head unit'; exit 1;; esac
  [ -d "$PLUGIN_BASE" ] && [ -d /opt/hmi/lib ] || { echo 'REFUSED: EntryNav2 system paths not present'; exit 1; }
  [ -s /opt/hmi/lib/libAppFramework.A.so ] && [ -s /opt/hmi/lib/libCoreFramework.A.so ] || {
    echo 'REFUSED: EntryNav2 framework libraries missing'; exit 1;
  }
}
check_collisions() {
  for f in "$PLUGIN_BASE"/*/*.manifest; do
    [ -f "$f" ] || continue
    case "$f" in "$DEST"/*) continue ;; esac
    if grep -q '<id>30117</id>' "$f"; then echo "REFUSED: connector 30117 collision at $f"; exit 1; fi
  done
  for f in "$PLUGIN_BASE"/*/*.xml; do
    [ -f "$f" ] || continue
    case "$f" in "$DEST"/*) continue ;; esac
    if grep -q 'entryButtonFocusID="32729"' "$f"; then echo "REFUSED: menu focus ID 32729 collision at $f"; exit 1; fi
  done
}

case "$MODE" in
  status)
    platform
    printf 'Unit: %s / %s\n' "$(uname -s)" "$(uname -m)"
    if root_is_ro; then echo 'Root filesystem: read-only'; else echo 'WARNING: root filesystem is not read-only'; fi
    if [ -d "$DEST" ]; then
      echo 'BoostDeckCDS plugin: present'
      ls -l "$DEST"/libBoostDeckCDS.so "$DEST"/BoostDeckCDS.manifest 2>/dev/null || :
    else echo 'BoostDeckCDS plugin: absent'; fi
    if [ -e /var/local/data/BoostDeckCDS/app.disable ]; then echo 'Off-switch: ACTIVE'; else echo 'Off-switch: inactive'; fi
    exit 0;;
  disable)
    platform
    mkdir -p /var/local/data/BoostDeckCDS
    touch /var/local/data/BoostDeckCDS/app.disable
    echo 'BoostDeckCDS off-switch set; effective on next HMI start. Other apps untouched.'
    exit 0;;
  enable)
    platform
    if [ -f /var/local/data/BoostDeckCDS/app.disable ]; then
      rm /var/local/data/BoostDeckCDS/app.disable
      echo 'BoostDeckCDS off-switch removed; app will be permitted on next HMI start.'
    else echo 'BoostDeckCDS was already enabled.'; fi
    exit 0;;
  check|install|restore) platform; root_is_ro || { echo 'STOP: system root must already be read-only'; exit 1; }; check_collisions;;
  *) echo "Unknown remote operation: $MODE" >&2; exit 1;;
esac

if [ "$MODE" = check ]; then
  if [ -d "$DEST" ]; then echo 'Preflight OK: supported EntryNav2, existing BoostDeckCDS (update requires backup).';
  else echo 'Preflight OK: supported EntryNav2, fresh BoostDeckCDS install.'; fi
  exit 0
fi

[ -n "${BD_ARCHIVE:-}" ] && [ -f "$BD_ARCHIVE" ] || { echo 'Missing staged archive'; exit 1; }
case "$BD_ARCHIVE" in /tmp/bdcds-*.tar) : ;; *) echo 'Unexpected archive location'; exit 1;; esac
STAGE="/tmp/bdcds-stage-$$"
INCOMING="$SYSTEM_BASE/.BoostDeckCDS-incoming-$$"
OLD="$SYSTEM_BASE/.BoostDeckCDS-previous-$(date +%Y%m%d%H%M%S)-$$"
[ ! -e "$STAGE" ] && [ ! -e "$INCOMING" ] && [ ! -e "$OLD" ] || exit 1
mounted_rw=0
swapped_old=0
cleanup() {
  code=$?
  trap - 0
  if [ "$mounted_rw" -eq 1 ]; then
    # Remove our own incomplete staging directory (never touch unrelated plugins).
    if [ -d "$INCOMING" ]; then rm -rf "$INCOMING" || :; fi
    # If a rename failed mid-swap, recover the old plugin while still writable.
    if [ "$swapped_old" -eq 1 ] && [ ! -d "$DEST" ] && [ -d "$OLD" ]; then
      mv "$OLD" "$DEST" || echo 'URGENT: rollback failed, investigate before rebooting'
    fi
    sync
    mount -o remount,ro / || echo 'URGENT: root still writable; do not reboot repeatedly'
  fi
  [ ! -d "$STAGE" ] || rm -rf "$STAGE"
  [ ! -f "$BD_ARCHIVE" ] || rm -f "$BD_ARCHIVE"
  exit "$code"
}
trap cleanup 0
trap 'exit 1' 1 2 15
mkdir "$STAGE"
tar -xf "$BD_ARCHIVE" -C "$STAGE"
if [ "$MODE" = install ]; then
  [ -f "$STAGE/MD5SUMS" ] || { echo 'Archive missing MD5SUMS'; exit 1; }
  (cd "$STAGE" && md5sum -c MD5SUMS) || { echo 'Checksum failure'; exit 1; }
  NEW="$STAGE/opt/hmi/data/ro/Plugins/BoostDeckCDS"
else
  NEW="$STAGE/BoostDeckCDS"
fi
[ -s "$NEW/libBoostDeckCDS.so" ] && [ -s "$NEW/BoostDeckCDS.manifest" ] && [ -s "$NEW/BoostDeckCDS.xml" ] && [ -s "$NEW/BoostDeckCDS_frames.bin" ] || {
  echo 'Missing required staged plugin files'; exit 1;
}
grep -q '<id>30117</id>' "$NEW/BoostDeckCDS.manifest" || { echo 'Wrong manifest ID'; exit 1; }
grep -q 'entryButtonFocusID="32729"' "$NEW/BoostDeckCDS.xml" || { echo 'Wrong menu ID'; exit 1; }

# The only writes to the system partition occur below this line.
mount -o remount,rw / || exit 1
mounted_rw=1
cp -R "$NEW" "$INCOMING" || exit 1
chmod 755 "$INCOMING/libBoostDeckCDS.so"
[ -s "$INCOMING/BoostDeckCDS_frames.bin" ] || exit 1
if [ -d "$DEST" ]; then
  mv "$DEST" "$OLD" || exit 1
  swapped_old=1
fi
if ! mv "$INCOMING" "$DEST"; then
  echo 'Could not move staged plugin into place; attempting rollback'
  exit 1
fi
sync
mount -o remount,ro / || { echo 'URGENT: remount read-only failed'; exit 1; }
mounted_rw=0
root_is_ro || { echo 'URGENT: root not read-only'; exit 1; }
printf 'SUCCESS: %s installed at %s\n' "$MODE" "$DEST"
if [ "$swapped_old" -eq 1 ]; then
  printf 'Previous plugin retained at %s (and installer created a Mac backup)\n' "$OLD"
fi
