#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Rebrand and reskin an isolated copy of MGD4096's noncommercial Gauge App.

Source compatibility target: MGD4096/Gauge-App-for-NBTEvo-and-EntryNav2,
revision 899e337. Abort on unexpected source structure; never mutate upstream checkout.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys


def replace_once(data: str, before: str, after: str, label: str) -> str:
    found = data.count(before)
    if found != 1:
        raise ValueError(f"{label}: expected 1 matching anchor, got {found}")
    return data.replace(before, after, 1)


def replace_section(data: str, start: str, end: str, replacement: str, label: str) -> str:
    pos = data.find(start)
    if pos < 0:
        raise ValueError(f"{label}: start marker not found")
    q = data.find(end, pos + len(start))
    if q < 0:
        raise ValueError(f"{label}: end marker not found")
    return data[:pos] + replacement + data[q:]


def apply_theme(db: str) -> str:
    before = '''CARD = (21, 24, 29, 255)
TRACK = (44, 44, 42, 255)
ACCENT = (55, 138, 221, 255)
ACCENT_LIGHT = (133, 183, 235, 255)
AMBER = (250, 199, 117, 255)
RED = (226, 75, 74, 255)
TEXT = (230, 241, 251, 255)
TEXT2 = (180, 178, 169, 255)
MUTED = (136, 135, 128, 255)
FAINT = (95, 94, 90, 255)
PILL = (12, 68, 124, 255)'''
    after = '''CARD = (16, 25, 45, 255)          # midnight-blue glass cards
TRACK = (40, 57, 83, 255)
ACCENT = (24, 207, 255, 255)         # electric cyan
ACCENT_LIGHT = (141, 238, 255, 255)
AMBER = (255, 191, 65, 255)         # amber highlights
RED = (255, 82, 112, 255)           # warning coral
TEXT = (246, 250, 255, 255)
TEXT2 = (207, 224, 243, 255)
MUTED = (143, 168, 194, 255)
FAINT = (91, 119, 151, 255)
PILL = (10, 84, 113, 255)'''
    db = replace_once(db, before, after, "palette")
    a = db.index('COLORS = [\n')
    b = db.index('# Units the OPTION menu offers', a)
    db = db[:a] + '''COLORS = [
    ("electric cyan", (24, 207, 255, 255), (141, 238, 255, 255), (10, 84, 113, 255)),
    ("neon violet", (174, 112, 255, 255), (220, 186, 255, 255), (83, 41, 126, 255)),
    ("hot magenta", (255, 78, 169, 255), (255, 166, 214, 255), (116, 22, 79, 255)),
    ("lime green", (104, 236, 138, 255), (191, 255, 206, 255), (35, 101, 51, 255)),
]
COLOR_NAMES_PL = ["cyjan", "fiolet", "magenta", "zielony"]
COLOR_NAMES_EN = ["electric cyan", "neon violet", "hot magenta", "lime green"]
''' + db[b:]
    if 'TITLE = "BOOSTDECK CDS"' not in db:
        raise ValueError("menu title not correctly renamed")

    # Change the actual gauge screen layout: retain four original value cards
    # and replace the g-meter with live RPM and speed numeric image slots.
    start = '    gx, gy = G_CARD[0], G_CARD[1]\n'
    end = '    for i, (letter, x, w) in enumerate(GEAR_CELLS):\n'
    new_slots = '''    gx, gy = G_CARD[0], G_CARD[1]
    for k in range(4):
        out.append(("RPM_BIG%d" % k, gx + 91 + k * BIG["cell"], gy + 80,
                    BIG["cell"] * 3 // 2, BIG["h"], IMG_BLANK))
    for k in range(3):
        out.append(("SPEED_BIG%d" % k, gx + 107 + k * BIG["cell"], gy + 212,
                    BIG["cell"] * 3 // 2, BIG["h"], IMG_BLANK))
'''
    db = replace_section(db, start, end, new_slots, 'numerical slots')

    start = '    gc = (gx + G_C[0], gy + G_C[1])\n'
    end = '    c.rrect(*GEAR_CARD, 12, CARD)\n'
    new_bg = '''    # Centre: two brightly labelled readouts, with room for native picture-glyphs.
    c.rrect(gx + 14, gy + 45, gw - 28, 113, 12, (12, 39, 62, 255))
    c.rrect(gx + 14, gy + 171, gw - 28, 113, 12, (39, 25, 61, 255))
    c.line((gx + 29, gy + 49), (gx + gw - 29, gy + 49), ACCENT, 3)
    c.line((gx + 29, gy + 175), (gx + gw - 29, gy + 175), (174, 112, 255, 255), 3)
    c.text((gx + 17, gy + 12), "ENGINE RPM", f_title, ACCENT_LIGHT)
    c.text((gx + gw - 69, gy + 126), "RPM", f_small, MUTED)
    c.text((gx + 29, gy + 180), "ROAD SPEED", f_small, (218, 178, 255, 255))
    c.text((gx + gw - 67, gy + 252), "MPH", f_small, MUTED)
'''
    db = replace_section(db, start, end, new_bg, 'centre visuals')

    # Four corner cards: permanently different accents (plus globally selectable arc colour).
    before = '        c.text((cx + TITLE_POS[0], cy + TITLE_POS[1]), tx[name], f_title, TEXT2)\n'
    after = '''        title_colors = {"COOLANT": (24, 207, 255, 255), "OIL": (255, 114, 182, 255),
                        "POWER": (255, 191, 65, 255), "TORQUE": (104, 236, 138, 255)}
        c.text((cx + TITLE_POS[0], cy + TITLE_POS[1]), tx[name], f_title, title_colors[name])
        c.line((cx + 17, cy + 37), (cx + CARD_W - 17, cy + 37), title_colors[name], 2)
'''
    db = replace_once(db, before, after, 'colorful corner cards')
    db = replace_once(db, '    ink = (250, 250, 250, 248)\n',
                      '    ink = (24, 207, 255, 248)\n', 'cyan app menu icon')

    # Preview shows realistic sample values for the new RPM/speed slots; it is
    # illustrative and never transmitted to the BMW as telemetry.
    before = '    pick["GEAR_D"] = IMG_GEAR + 13\n'
    after = '''    pick["GEAR_D"] = IMG_GEAR + 13
    for prefix, value, digits in (("RPM", "2450", 4), ("SPEED", "62", 3)):
        for k, ch in enumerate(value.rjust(digits)):
            pick["%s_BIG%d" % (prefix, k)] = (IMG_BIG + GLYPHS.index(ch)) if ch != " " else IMG_BLANK
'''
    db = replace_once(db, before, after, 'preview samples')
    # Distinct RHMI focus identity in addition to manifest connector identity.
    db = replace_once(db,
        'applicationWeight=\\"210\\" entryButtonFocusID=\\"32751\\"',
        'applicationWeight=\\"245\\" entryButtonFocusID=\\"32729\\"',
        'unique menu identity')
    return db


def apply_view(code: str) -> str:
    start = '    const double lat = m.hasLatG() ? m.latG() : 0, lon = m.hasLonG() ? m.lonG() : 0;\n'
    end = '    gearCells(m, out + kSlotGearP);\n'
    replacement = '''    // RPM and road speed are sent as independent per-digit picture models.
    // Missing data => blank, never a fabricated zero. RPM/MPH are raw and derived CDS values.
    char rpmText[8], mphText[8];
    snprintf(rpmText, sizeof(rpmText), "%4d", clampInt(m.rpm, 0, 9999));
    snprintf(mphText, sizeof(mphText), "%3d", clampInt(m.speed * 0.62137119223733, 0, 999));
    for (int i = 0; i < 4; ++i) {
        out[kSlotRpmBig0 + i] = m.hasRpm && rpmText[i] != ' ' ? bigGlyph(rpmText[i], 0) : (unsigned)kImgBlank;
    }
    for (int i = 0; i < 3; ++i) {
        out[kSlotSpeedBig0 + i] = m.hasSpeed && mphText[i] != ' ' ? bigGlyph(mphText[i], 0) : (unsigned)kImgBlank;
    }
'''
    return replace_section(code, start, end, replacement, 'CDS RPM/speed renderer')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('source', type=Path, help='Isolated source checkout copy, not the upstream original')
    a = ap.parse_args()
    root = a.source.resolve()
    must = [root / 'make_db.py', root / 'Makefile', root / 'GaugeApp.manifest',
            root / 'src' / 'engine_data.cpp', root / 'src' / 'gauge_view.hpp']
    if not all(f.is_file() for f in must):
        raise SystemExit('Missing expected upstream files: refusing to patch')
    if (root / '.boostdeck-cds-patched').exists():
        raise SystemExit('Already patched; refusing to repeat')
    # Mutate only the new isolated copy. Keep the original checkout and car libs unchanged.
    texts = [root / 'make_db.py', root / 'Makefile', root / 'GaugeApp.manifest',
             root / 'src' / 'engine_data.cpp', root / 'src' / 'gauge_view.hpp']
    data = {f: f.read_text(encoding='utf-8') for f in texts}
    for f in texts:
        v = data[f]
        v = v.replace('GaugeApp', 'BoostDeckCDS')
        v = v.replace('GAUGE APP', 'BOOSTDECK CDS')
        v = v.replace('gauge-app', 'boostdeck-cds')
        # Change NBT Evo lowercase path too, for isolation of user settings.
        v = v.replace('gaugeapp', 'boostdeckcds')
        data[f] = v
    data[root/'make_db.py'] = apply_theme(data[root/'make_db.py'])
    data[root/'src'/'gauge_view.hpp'] = apply_view(data[root/'src'/'gauge_view.hpp'])
    manifest = data[root/'GaugeApp.manifest']
    manifest = replace_once(manifest, '<id>211</id>', '<id>30117</id>', 'unique Etch connector ID')
    data[root/'GaugeApp.manifest'] = manifest
    entry = data[root/'src'/'engine_data.cpp']
    entry = replace_once(entry,
        '1, 0, "BOOSTDECK CDS", "NBT-ENGINE", 1, &createApp, &destroyApp',
        '1, 0, "BOOSTDECK CDS", "BOOSTDECK-CDS", 1, &createApp, &destroyApp',
        'new pluginAppInfo identity')
    data[root/'src'/'engine_data.cpp'] = entry
    for f, content in data.items():
        f.write_text(content, encoding='utf-8')
    # Rename generated inputs and prebuilt outputs; make_db.py will regenerate images and XML.
    for f in sorted(root.glob('GaugeApp*')):
        f.rename(f.with_name(f.name.replace('GaugeApp', 'BoostDeckCDS', 1)))
    (root/'.boostdeck-cds-patched').write_text('BoostDeck CDS 0.1 preview build\n', encoding='ascii')
    print('Patch applied: isolated BoostDeckCDS plugin, connector 30117, focus 32729, neon look, RPM+MPH')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f'PATCH FAILED: {exc}', file=sys.stderr)
        sys.exit(1)
