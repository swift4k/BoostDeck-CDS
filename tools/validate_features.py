#!/usr/bin/env python3
"""Validate integrated BoostDeck source, generated geometry/assets and unit choices."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image
p = Path(sys.argv[1])
src = (p/'make_db.py').read_text()
view = (p/'src/gauge_view.hpp').read_text()
assert 'W, H = 1060, 400' in src
assert 'FUEL_CARD = (576, 316, 178, 84)' in src
assert 'FUEL_UNIT_BOX = (122, 31, 49, 26)' in src
assert 'POWER_SCALE_MIN, TORQUE_SCALE_MIN = 300, 350' in src
assert 'power(kHp), torque(kNm), fuel(kGallon)' in view
assert 'UNITS = ["°C", "°F", "KM", "kW", "HP",' in src
assert 'UNITS.index("HP")' in src
assert '("Moc: HP", "Power: HP")' in src
assert 'return st.power == kKw ? 250 : 300;' in view
assert 'return st.torque == kLbFt ? 300 : 350;' in view
im = Image.open(p/'res/preview_en.png')
assert im.size == (1219, 460), 'Unexpected preview size: %r' % (im.size,)
xml = ET.parse(p/'BoostDeckCDS.xml')
# HMI background component must use x=12 and y=4.
background_image = next(node for node in xml.iter() if node.tag == 'image' and node.attrib.get('model') == '99')
properties = {q.attrib['id']: q.attrib['value'] for q in background_image.iter('property')}
assert properties['20'] == '12' and properties['21'] == '4', properties
assert properties['9'] == '1219' and properties['10'] == '460', properties
# The package archive is validated separately after cross-compilation.
print('PASS: 1219x460 layout, 178px fuel card, US gallons, 300 HP / 350 Nm starting scales')
