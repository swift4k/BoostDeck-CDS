#!/bin/bash
# Run in macOS regular Terminal. Never run this directly on the head unit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BD_HOME="${BOOSTDECK_HOME:-$ROOT/work}"
SRC="$BD_HOME/source"
UP="$BD_HOME/upstream"
VENV="$BD_HOME/.venv"
PY="$VENV/bin/python3"
ARCHIVE="$SRC/dist/boostdeck-cds-entrynav2.tar"
PIN="899e337"
GIT_URL="https://github.com/MGD4096/Gauge-App-for-NBTEvo-and-EntryNav2.git"
HOST="${BOOSTDECK_HOST:-169.254.1.0}"
TARGET="root@$HOST"

fail() { echo "ERROR: $*" >&2; exit 1; }
info() { printf '\n=== %s ===\n' "$*"; }
mac() { [ "$(uname -s)" = Darwin ] || fail "Use regular macOS Terminal (not BMW SSH)."; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"; }
sshcar() { ssh -T -o ConnectTimeout=7 "$TARGET" "$@"; }
help() {
cat <<'EOF'
BoostDeck CDS — source build and installer (EntryNav2 / EntryEVO only)

USAGE (regular Mac Terminal):
  bash boostdeck.sh doctor
  bash boostdeck.sh fetch-libs            # read 2 framework libs from your OWN car, no car writes
  bash boostdeck.sh preview [--source PATH]
  bash boostdeck.sh build   [--source PATH] [--libs PATH]
  bash boostdeck.sh status
  bash boostdeck.sh install               # fresh install or guarded upgrade, with Mac backup
  bash boostdeck.sh disable               # write only a data-partition off switch
  bash boostdeck.sh enable                # remove off-switch, with explicit confirmation
  bash boostdeck.sh restore PATH.tar      # restore a verified, previously backed-up plugin

Optional environment: BOOSTDECK_HOST (default 169.254.1.0),
BOOSTDECK_HOME (default <repo>/work), BOOSTDECK_FONT (path to Arial.ttf).
No NBT Evo/QNX installer is provided; no SSH passwords or BMW binaries are bundled.
EOF
}

check_home() {
  case "$BD_HOME" in /|"" ) fail "Unsafe workspace";; esac
  mkdir -p "$BD_HOME"
}

setup_python() {
  need python3
  python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || fail "Python 3.10+ is required"
  if [ ! -x "$PY" ]; then
    info 'Creating isolated Python environment (may need Internet for Pillow)'
    python3 -m venv "$VENV" || fail "python3 venv unavailable; install Python 3.10+ and retry"
  fi
  if ! "$PY" -c 'from PIL import Image' 2>/dev/null; then
    "$PY" -m pip install -r "$ROOT/requirements.txt"
  fi
}

source_checkout() {
  if [ -n "$SOURCE_OVERRIDE" ]; then
    [ -f "$SOURCE_OVERRIDE/make_db.py" ] || fail "No make_db.py at --source $SOURCE_OVERRIDE"
    printf '%s\n' "$SOURCE_OVERRIDE"
    return
  fi
  if [ ! -d "$UP" ]; then
    info "Cloning the licensed upstream source (requires Internet)"
    need git
    git clone "$GIT_URL" "$UP"
  fi
  [ -d "$UP/.git" ] || fail "Unexpected upstream checkout: $UP"
  git -C "$UP" checkout --detach "$PIN" >/dev/null || fail "Pinned source $PIN missing. Use --source PATH to a known checkout."
  # Never modify an upstream working tree beyond the controlled git checkout above.
  printf '%s\n' "$UP"
}

prepare() {
  check_home
  setup_python
  SOURCE_OVERRIDE=""
  LIB_OVERRIDE=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --source) [ $# -ge 2 ] || fail "--source needs a directory"; SOURCE_OVERRIDE="$(cd "$2" && pwd)"; shift 2;;
      --libs) [ $# -ge 2 ] || fail "--libs needs a directory"; LIB_OVERRIDE="$(cd "$2" && pwd)"; shift 2;;
      *) fail "Unknown option: $1";;
    esac
  done
  if [ ! -d "$SRC" ]; then
    local base stage
    base="$(source_checkout | tail -n 1)"
    stage="$BD_HOME/.source-stage-$$"
    [ ! -e "$stage" ] || fail "Temporary workspace exists"
    trap 'rm -rf "$stage"' EXIT
    info 'Copy upstream source into separate workspace (original untouched)'
    cp -R "$base" "$stage"
    python3 "$ROOT/tools/patch_source.py" "$stage"
    info 'Apply wide-layout and US-units improvements directly to the new copy'
    python3 "$ROOT/tools/patch_features.py" "$stage"
    python3 "$ROOT/tools/fix_generator_xml.py" "$stage"
    printf 'Integrated BoostDeck source; pinned upstream %s\n' "$PIN" > "$stage/.boostdeck-integrated-source"
    mv "$stage" "$SRC"
    trap - EXIT
  else
    [ -f "$SRC/.boostdeck-integrated-source" ] || fail "Existing workspace is not our merged build: $SRC"
    [ -f "$SRC/.boostdeck-cds-patched" ] && [ -f "$SRC/.boostdeck-cds-v2-patched" ] || fail "Patch markers missing; cannot resume"
    info 'Reusing validated merged source; no overwrite'
  fi

  local font="${BOOSTDECK_FONT:-/System/Library/Fonts/Supplemental/Arial.ttf}"
  if [ ! -f "$font" ]; then
    if [ -f /Library/Fonts/Arial.ttf ]; then font=/Library/Fonts/Arial.ttf;
    else fail "Arial.ttf not found; set BOOSTDECK_FONT=/path/to/Arial.ttf"; fi
  fi
  info 'Generating 1219x460 native preview / image assets'
  (cd "$SRC" && "$PY" make_db.py --screen 1280x480 --x 12 --y 4 --font "$font")
  "$PY" "$ROOT/tools/validate_generated.py" "$SRC"
  "$PY" "$ROOT/tools/validate_features.py" "$SRC"
  need clang++
  info 'Running C++98 telemetry and unit tests'
  clang++ -std=c++98 -Wall -Wextra -I"$SRC" "$ROOT/tests/host_smoke.cpp" -o "$BD_HOME/host_smoke"
  "$BD_HOME/host_smoke"
}

find_libs() {
  local dir="${LIB_OVERRIDE:-}"
  if [ -z "$dir" ]; then
    for candidate in "$BD_HOME/private/Entry_Evo_libs" \
                     "$HOME/bmw-cds-probe/Gauge-App-for-NBTEvo-and-EntryNav2/lib/Entry_Evo_libs"; do
      if [ -s "$candidate/libAppFramework.A.so" ] && [ -s "$candidate/libCoreFramework.A.so" ]; then
        dir="$candidate"; break
      fi
    done
  fi
  [ -n "$dir" ] || fail "Missing BMW framework libs. Run 'bash boostdeck.sh fetch-libs' or --libs PATH. They cannot legally be bundled."
  [ -s "$dir/libAppFramework.A.so" ] && [ -s "$dir/libCoreFramework.A.so" ] || fail "Both EntryNav2 framework libraries are required at $dir"
  mkdir -p "$SRC/lib/Entry_Evo_libs"
  cp "$dir/libAppFramework.A.so" "$dir/libCoreFramework.A.so" "$SRC/lib/Entry_Evo_libs/"
}

build() {
  mac
  prepare "$@"
  find_libs
  need docker
  docker info >/dev/null 2>&1 || fail "Start Docker Desktop first"
  info 'Building ARMv7 EntryNav2 library and installation archive (car untouched)'
  if ! docker image inspect gauge-entrynav2-tc >/dev/null 2>&1; then
    docker build --platform linux/amd64 -t gauge-entrynav2-tc "$SRC/toolchain"
  fi
  (cd "$SRC" && bash toolchain/tc-entrynav2.sh make entrynav2-dist)
  "$PY" "$ROOT/tools/validate_package.py" "$ARCHIVE"
  info 'BUILD OK — NOT INSTALLED'
  printf 'Package: %s\nPreview: %s\n' "$ARCHIVE" "$SRC/res/preview_en.png"
  shasum -a 256 "$ARCHIVE"
}

fetch_libs() {
  mac
  check_home
  local dest="$BD_HOME/private/Entry_Evo_libs"
  mkdir -p "$dest"
  info "Read-only fetch of BMW-proprietary frameworks from your own EntryNav2 at $HOST"
  echo 'These files stay on YOUR Mac under work/private/, which is git-ignored.'
  sshcar 'test "$(uname -s)" = Linux && test -d /opt/hmi/data/ro/Plugins && test -s /opt/hmi/lib/libAppFramework.A.so && test -s /opt/hmi/lib/libCoreFramework.A.so' || fail 'This is not a compatible accessible EntryNav2, or required libraries are missing.'
  for lib in libAppFramework.A.so libCoreFramework.A.so; do
    [ ! -e "$dest/$lib" ] || fail "Existing $dest/$lib — refusing to overwrite"
    sshcar "cat /opt/hmi/lib/$lib" > "$dest/$lib" || { rm -f "$dest/$lib"; fail "Could not fetch $lib"; }
    [ "$(dd if="$dest/$lib" bs=4 count=1 2>/dev/null)" = "$(printf '\177ELF')" ] || fail "Not an ELF library: $lib"
  done
  info "Copied frameworks to $dest; do not upload these to GitHub"
}

status() {
  mac
  sshcar 'sh -s status' < "$ROOT/scripts/remote_entrynav2.sh"
}

disable() {
  mac
  echo 'This writes only the BoostDeckCDS app.disable flag on the writable data partition.'
  sshcar 'sh -s disable' < "$ROOT/scripts/remote_entrynav2.sh"
}

enable() {
  mac
  echo 'This allows BoostDeckCDS to run again at the next HMI start.'
  local answer; read -r -p 'Type ENABLE BOOSTDECK to continue: ' answer
  [ "$answer" = 'ENABLE BOOSTDECK' ] || fail 'Canceled'
  sshcar 'sh -s enable' < "$ROOT/scripts/remote_entrynav2.sh"
}

install() {
  mac
  [ -s "$ARCHIVE" ] || fail "No ARM archive. Run: bash boostdeck.sh build"
  python3 "$ROOT/tools/validate_package.py" "$ARCHIVE"
  info 'Remote safety preflight (does not change the BMW)'
  sshcar 'sh -s check' < "$ROOT/scripts/remote_entrynav2.sh"
  echo 'The BMW must be PARKED, ignition stable and HMI operating normally.'
  echo 'Install may briefly remount the system root writable. All other apps are left alone.'
  local answer
  read -r -p 'Type INSTALL BOOSTDECK to continue: ' answer
  [ "$answer" = 'INSTALL BOOSTDECK' ] || fail 'Canceled. No system changes.'
  local installed
  installed="$(sshcar 'if test -d /opt/hmi/data/ro/Plugins/BoostDeckCDS; then echo yes; else echo no; fi')"
  if [ "$installed" = yes ]; then
    mkdir -p "$BD_HOME/backups"
    local backup="$BD_HOME/backups/BoostDeckCDS-$(date +%Y%m%d-%H%M%S).tar"
    [ ! -e "$backup" ] || fail "Backup filename already exists"
    info "Backing up existing plugin to Mac: $backup"
    sshcar 'tar -cf - -C /opt/hmi/data/ro/Plugins BoostDeckCDS' > "$backup"
    python3 "$ROOT/tools/validate_backup.py" "$backup"
    shasum -a 256 "$backup" > "$backup.sha256"
    cat "$backup.sha256"
  fi
  local token="$(date +%Y%m%d%H%M%S)-$$" remote="/tmp/bdcds-$token.tar"
  info 'Streaming validated archive to remote /tmp (no system partition writes yet)'
  sshcar "umask 077; cat > '$remote'" < "$ARCHIVE"
  info 'Installing with staged atomic directory swap and root read-only restoration'
  sshcar "BD_ARCHIVE='$remote' sh -s install" < "$ROOT/scripts/remote_entrynav2.sh"
  echo 'Success reported by remote installer. A normal, controlled iDrive restart may be needed.'
  echo 'Do not remove GaugeApp/BoostDeck. Verify live data before any other changes.'
}

restore() {
  mac
  [ $# -eq 1 ] || fail 'Usage: bash boostdeck.sh restore /path/to/BoostDeckCDS-backup.tar'
  local backup="$1"
  python3 "$ROOT/tools/validate_backup.py" "$backup"
  if [ -f "$backup.sha256" ]; then
    shasum -a 256 -c "$backup.sha256" || fail "Backup SHA-256 verification failed"
  else
    echo 'WARNING: no saved SHA-256 sidecar; restore authenticity cannot be independently checked.'
  fi
  sshcar 'sh -s check' < "$ROOT/scripts/remote_entrynav2.sh"
  info 'Restoring a prior Mac backup, replacing only BoostDeckCDS'
  local answer; read -r -p 'Type RESTORE BOOSTDECK to continue: ' answer
  [ "$answer" = 'RESTORE BOOSTDECK' ] || fail 'Canceled'
  local token="$(date +%Y%m%d%H%M%S)-$$" remote="/tmp/bdcds-restore-$token.tar"
  sshcar "umask 077; cat > '$remote'" < "$backup"
  sshcar "BD_ARCHIVE='$remote' sh -s restore" < "$ROOT/scripts/remote_entrynav2.sh"
  echo 'Restore completed. Observe behavior after ONE normal iDrive restart.'
}

cmd="${1:-help}"; [ $# -eq 0 ] || shift
case "$cmd" in
  help|-h|--help) help;;
  doctor) mac; for x in git python3 clang++ docker ssh shasum; do command -v "$x" || true; done; echo "Workspace: $BD_HOME"; echo 'See docs/INSTALL.md for the head-unit and library prerequisites.';;
  fetch-libs) fetch_libs "$@";;
  preview) mac; prepare "$@"; echo "Preview: $SRC/res/preview_en.png"; open "$SRC/res/preview_en.png";;
  build) build "$@";;
  status) status "$@";;
  disable) disable "$@";;
  enable) enable "$@";;
  install) install "$@";;
  restore) restore "$@";;
  *) fail "Unknown subcommand: $cmd";;
esac
