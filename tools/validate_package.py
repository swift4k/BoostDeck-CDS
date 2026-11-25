#!/usr/bin/env python3
"""Read-only checks for an EntryNav2-only archive; never execute archive contents."""
from __future__ import annotations
import hashlib
import sys
import tarfile
from pathlib import PurePosixPath, Path

PREFIX = "opt/hmi/data/ro/Plugins/BoostDeckCDS/"
NEEDED = (
    "libBoostDeckCDS.so", "BoostDeckCDS.manifest", "BoostDeckCDS.xml",
    "BoostDeckCDS_ALL_Texts.zip", "BoostDeckCDS_ALL_Images.zip",
    "BoostDeckCDS_frames.bin", "BoostDeckCDS_frames_c0.bin",
)


def validate(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= 10000:
        raise ValueError("Missing or suspiciously small archive: " + str(path))
    with tarfile.open(path, "r:") as tf:
        by_name = {}
        for member in tf.getmembers():
            name = member.name
            pieces = PurePosixPath(name).parts
            if name.startswith("/") or ".." in pieces or not pieces:
                raise ValueError("Unsafe archive name: " + name)
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError("Links/devices are forbidden: " + name)
            if not member.isdir() and not member.isfile():
                raise ValueError("Unsupported archive member: " + name)
            normalized = name.removeprefix("./")
            if normalized in by_name:
                raise ValueError("Duplicate archive member: " + name)
            by_name[normalized] = member
        for name in NEEDED:
            full = PREFIX + name
            if full not in by_name or not by_name[full].isfile() or by_name[full].size == 0:
                raise ValueError("Missing package resource: " + full)
        if "MD5SUMS" not in by_name:
            raise ValueError("No MD5SUMS index")
        lib = tf.extractfile(by_name[PREFIX + "libBoostDeckCDS.so"]).read(20)
        if not (lib.startswith(b"\x7fELF") and lib[4] == 1 and lib[5] == 1 and
                int.from_bytes(lib[18:20], "little") == 40):
            raise ValueError("Not an ELF32 little-endian ARM EntryNav2 binary")
        manifest = tf.extractfile(by_name[PREFIX+"BoostDeckCDS.manifest"]).read().decode("utf-8", errors="replace")
        if "<id>30117</id>" not in manifest:
            raise ValueError("Connector identity mismatch")
        checksums = tf.extractfile(by_name["MD5SUMS"]).read().decode("ascii")
        validated = set()
        for line in checksums.splitlines():
            if not line.strip():
                continue
            digest, sep, name = line.partition("  ")
            if not sep:
                # md5sum also accepts binary-mode `*` delimiter
                digest, sep, name = line.partition(" *")
            if not sep or len(digest) != 32 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                raise ValueError("Bad MD5SUMS line")
            safe = name.removeprefix("./")
            if safe not in by_name or not by_name[safe].isfile() or safe in validated:
                raise ValueError("Bad/duplicate MD5SUMS entry: " + name)
            actual = hashlib.md5(tf.extractfile(by_name[safe]).read()).hexdigest()
            if actual.lower() != digest.lower():
                raise ValueError("Checksum mismatch: " + name)
            validated.add(safe)
        if not set(PREFIX + item for item in NEEDED).issubset(validated):
            raise ValueError("Checksum file does not cover all required files")
    print("PASS: ARM archive, plugin identity, files, safe paths and MD5SUMS")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 tools/validate_package.py FILE.tar")
    try:
        validate(Path(sys.argv[1]))
    except (ValueError, OSError, tarfile.TarError) as exc:
        sys.exit("PACKAGE INVALID: " + str(exc))
