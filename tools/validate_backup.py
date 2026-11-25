#!/usr/bin/env python3
"""Validate a BoostDeckCDS-only Mac plugin backup before allowing restore."""
import sys
import tarfile
from pathlib import Path, PurePosixPath

def validate(p):
    p = Path(p)
    if not p.is_file() or p.stat().st_size < 10000:
        raise ValueError('Missing or too-small backup')
    with tarfile.open(p, 'r:') as tf:
        names = set()
        for m in tf.getmembers():
            name = m.name.removeprefix('./')
            parts = PurePosixPath(name).parts
            if not parts or parts[0] != 'BoostDeckCDS' or '..' in parts or m.issym() or m.islnk() or m.isdev():
                raise ValueError('Unexpected backup entry: ' + m.name)
            if name in names:
                raise ValueError('Duplicate backup entry: ' + name)
            names.add(name)
        for n in ('libBoostDeckCDS.so','BoostDeckCDS.manifest','BoostDeckCDS.xml','BoostDeckCDS_frames.bin'):
            if 'BoostDeckCDS/' + n not in names:
                raise ValueError('Missing backup resource: ' + n)
        mf = tf.extractfile('BoostDeckCDS/BoostDeckCDS.manifest').read().decode('utf-8',errors='replace')
        if '<id>30117</id>' not in mf:
            raise ValueError('Wrong manifest connector ID')
    print('PASS: usable BoostDeckCDS backup (store SHA-256 separately)')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 tools/validate_backup.py FILE.tar')
    try: validate(sys.argv[1])
    except (ValueError, OSError, tarfile.TarError) as e: sys.exit('INVALID BACKUP: ' + str(e))
