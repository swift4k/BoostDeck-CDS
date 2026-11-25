#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""BoostDeckCDS v2: expand canvas/fuel tile; 300 HP, 350 Nm, US gallons.

Only patch the *isolated* BoostDeckCDS Mac workspace created by the v1 kit.
All anchors must match once; preserve .v1 backups before committing changes.
"""
from pathlib import Path
import argparse
import shutil
import sys


def sub1(src, old, new, label):
    n = src.count(old)
    if n != 1:
        raise ValueError('%s: expected exactly one anchor; found %d' % (label, n))
    return src.replace(old, new, 1)


def patch(work):
    mark = work / '.boostdeck-cds-v2-patched'
    if mark.exists():
        print('Already patched with v2: unchanged')
        return
    if not (work / '.boostdeck-cds-patched').is_file():
        raise ValueError('Not a v1 BoostDeckCDS workspace: refusing to edit')
    dbp = work / 'make_db.py'
    viewp = work / 'src' / 'gauge_view.hpp'
    enginep = work / 'src' / 'engine_data.cpp'
    db = dbp.read_text(encoding='utf-8')
    view = viewp.read_text(encoding='utf-8')
    engine = enginep.read_text(encoding='utf-8')
    if 'TITLE = "BOOSTDECK CDS"' not in db:
        raise ValueError('Unexpected app identity in generator')
    if 'kSlotRpmBig0' not in view or 'kSlotSpeedBig0' not in view:
        raise ValueError('Existing BoostDeckCDS RPM/speed rendering not found')

    # The existing 960x400 at scale 1.15 fills just 1104x460 physical pixels.
    # Use 1060x400 => 1219x460 within the ~1250x470 HMI content region.
    db = sub1(db, 'W, H = 960, 400', 'W, H = 1060, 400', 'wider canvas')
    db = sub1(db, '("POWER", (670, 0),', '("POWER", (770, 0),', 'right top card')
    db = sub1(db, '("TORQUE", (670, 208),', '("TORQUE", (770, 208),', 'right lower card')
    db = sub1(db, 'POWER_SCALE_MIN, TORQUE_SCALE_MIN = 150, 250',
              'POWER_SCALE_MIN, TORQUE_SCALE_MIN = 300, 350', 'generated scale constants')
    db = sub1(db, 'G_CARD = (305, 0, 350, 300)',
              'G_CARD = (305, 0, 450, 300)', 'wider RPM/speed center card')
    db = sub1(db, 'GEAR_CARD = (305, 316, 230, 84)',
              'GEAR_CARD = (305, 316, 260, 84)', 'wider gear card')
    db = sub1(db, 'FUEL_CARD = (543, 316, 112, 84)',
              'FUEL_CARD = (576, 316, 178, 84)', 'wider fuel card')
    db = sub1(db, 'FUEL_BOX = (36, 26, 44, 32)',
              'FUEL_BOX = (42, 25, 76, 34)', 'fuel number width')
    db = sub1(db, 'FUEL_UNIT_BOX = (36 + 44 + 4, 33, 28, 22)',
              'FUEL_UNIT_BOX = (122, 31, 49, 26)', 'fuel gallon suffix width')
    db = sub1(db, 'gx + 91 + k * BIG["cell"]',
              'gx + 151 + k * BIG["cell"]', 'RPM center alignment')
    db = sub1(db, 'gx + 107 + k * BIG["cell"]',
              'gx + 167 + k * BIG["cell"]', 'speed center alignment')
    # Design preview is only a sample; no source of live vehicle values.
    db = sub1(db, '"POWER": (193, 231, 0.772, 0.924, 2 if lang == "pl" else UNITS.index("PS"), "0", "250")',
              '"POWER": (190, 228, 0.633, 0.760, UNITS.index("HP"), "0", "300")',
              'preview 300 HP endpoint')
    db = sub1(db, '"TORQUE": (380, 412, 0.844, 0.916, 5, "0", "450")',
              '"TORQUE": (270, 300, 0.771, 0.857, 5, "0", "350")',
              'preview Nm endpoint')
    db = sub1(db, 'pick["FUEL"] = IMG_FUELNUM + 39',
              'pick["FUEL"] = IMG_FUELNUM + 15', 'preview fuel quantity gallons')
    db = sub1(db, 'pick["FUEL_UNIT"] = IMG_FUEL_UNIT',
              'pick["FUEL_UNIT"] = IMG_FUEL_UNIT + 1', 'preview fuel US gallons')
    # Rename the dynamic horsepower unit image and the Options menu label,
    # not merely a text caption. PS -> mechanical horsepower is converted
    # by the existing showPower(kHp, ps) logic (factor 0.98632).
    db = sub1(db, 'UNITS = ["°C", "°F", "KM", "kW", "hp", "Nm",',
              'UNITS = ["°C", "°F", "KM", "kW", "HP", "Nm",', 'uppercase HP image')
    db = sub1(db, '("Moc: hp", "Power: hp")',
              '("Moc: HP", "Power: HP")', 'uppercase HP setting label')

    view = sub1(view, 'Settings() : color(0), temp(kCelsius), power(kPs), torque(kNm), fuel(kLitre) {}',
                'Settings() : color(0), temp(kCelsius), power(kHp), torque(kNm), fuel(kGallon) {}',
                'default HP and US gallons')
    view = sub1(view, 'return st.power == kKw ? 100 : 150;',
                'return st.power == kKw ? 250 : 300;', 'HP starting scale')
    view = sub1(view, 'return st.torque == kLbFt ? 200 : 250;',
                'return st.torque == kLbFt ? 300 : 350;', 'Nm starting scale')
    view = sub1(view, 'if (!hasMax) return minimum;\n    int e = (int)(ceil(shownMax * 1.05 / step) * step);',
                'if (!hasMax || shownMax <= minimum) return minimum;\n    int e = (int)(ceil(shownMax * 1.05 / step) * step);',
                'hold requested scale until exceeded')

    engine = sub1(engine, '#define ENGINE_APP_VERSION "engine-data-0.2.0 "',
                  '#define ENGINE_APP_VERSION "boostdeck-cds-0.2.2 "', 'unique v2 log version')

    # All anchor checks passed; create recoverable originals before changes.
    for path in (dbp, viewp, enginep):
        backup = path.with_name(path.name + '.before-v2')
        if backup.exists():
            raise ValueError('Existing v2 backup needs review: ' + str(backup))
    for path in (dbp, viewp, enginep):
        shutil.copy2(str(path), str(path) + '.before-v2')
    dbp.write_text(db, encoding='utf-8')
    viewp.write_text(view, encoding='utf-8')
    enginep.write_text(engine, encoding='utf-8')
    mark.write_text('BoostDeckCDS v2: 1060x400 canvas, 300 HP, 350 Nm, fuel US gallons\n', encoding='ascii')
    print('PASS: v2 patch applied to isolated workspace, .before-v2 backups created')


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('workspace', type=Path)
    args = cli.parse_args()
    try:
        patch(args.workspace.resolve())
    except (ValueError, OSError) as exc:
        sys.exit('PATCH FAILED (no car changes): ' + str(exc))
