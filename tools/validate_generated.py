#!/usr/bin/env python3
"""Fail closed when resource identities/layout differ from expected patch."""
from pathlib import Path
import sys
import re
import zipfile
import xml.etree.ElementTree as ET

p = Path(sys.argv[1])
manifest = ET.parse(p / 'BoostDeckCDS.manifest').getroot()
assert manifest.findtext('name') == 'BoostDeckCDS'
assert manifest.findtext('config/dependencies/pluginAppConnector/id') == '30117'
assert manifest.findtext('config/parameters/DescFile') == '{pluginDir}/BoostDeckCDS.xml'
xml = (p / 'BoostDeckCDS.xml').read_text()
assert 'applicationWeight="245"' in xml and 'entryButtonFocusID="32729"' in xml
assert 'BOOSTDECK CDS' in xml
assert 'DIAGNOSTIC build' not in xml
try:
    root = ET.parse(p / 'BoostDeckCDS.xml').getroot()
except ET.ParseError as ex:
    raise SystemExit(f'Generated BMW XML is invalid: {ex}. Inspect make_db.py XML comment and rerun the generator.') from ex
models = [int(x.attrib['id']) for x in root.iter() if x.tag.endswith('Model') and 'id' in x.attrib]
assert len(models) == len(set(models)), 'Duplicate model IDs'
ids = (p / 'src' / 'gauge_ids.hpp').read_text()
assert 'kSlotRpmBig0' in ids and 'kSlotRpmBig3' in ids
assert 'kSlotSpeedBig0' in ids and 'kSlotSpeedBig2' in ids
with zipfile.ZipFile(p / 'BoostDeckCDS_ALL_Texts.zip') as z:
    assert '1=BOOSTDECK CDS' in z.read('en-US.txt').decode()
for n in ('BoostDeckCDS_frames.bin', 'BoostDeckCDS_frames_c0.bin', 'BoostDeckCDS_frames_c3.bin'):
    assert (p/n).stat().st_size > 1024, n
assert (p/'res'/'preview_en.png').is_file()
print('PASS: distinct plugin, 7 additional numeric image slots, resource tables, manifest, XML and previews')
