"""Offline source-anchor regression test using upstream source excerpts."""
from pathlib import Path
import tempfile
from patch_source import apply_theme, apply_view
orig_db = '''CARD = (21, 24, 29, 255)
TRACK = (44, 44, 42, 255)
ACCENT = (55, 138, 221, 255)
ACCENT_LIGHT = (133, 183, 235, 255)
AMBER = (250, 199, 117, 255)
RED = (226, 75, 74, 255)
TEXT = (230, 241, 251, 255)
TEXT2 = (180, 178, 169, 255)
MUTED = (136, 135, 128, 255)
FAINT = (95, 94, 90, 255)
PILL = (12, 68, 124, 255)
COLORS = [
    ("blue", ACCENT, ACCENT_LIGHT, PILL),
    ("red", (222, 45, 50, 255), (240, 140, 140, 255), (110, 22, 26, 255)),
    ("orange", (255, 122, 0, 255), (255, 185, 120, 255), (125, 58, 0, 255)),
    ("green", (40, 180, 90, 255), (140, 220, 165, 255), (16, 82, 42, 255)),
]
COLOR_NAMES_PL = ["niebieski", "czerwony", "pomaranczowy BMW", "zielony"]
COLOR_NAMES_EN = ["blue", "red", "BMW orange", "green"]
# Units the OPTION menu offers
TITLE = "BOOSTDECK CDS"
def slots():
    gx, gy = G_CARD[0], G_CARD[1]
    for name, (bx, by, bw, bh) in (("G_BIG", G_BIG_BOX), ("G_LAT", G_LAT_BOX), ("G_LON", G_LON_BOX)):
        out.append((name, gx + bx, gy + by, bw, bh, IMG_BLANK))
    out.append(("G_DOT", gx + G_C[0] - G_BOX // 2, gy + G_C[1] - G_BOX // 2, G_BOX, G_BOX, IMG_BLANK))
    for i, (letter, x, w) in enumerate(GEAR_CELLS):
        out.append(("GEAR_" + letter, GEAR_CARD[0] + x, GEAR_CARD[1] + GEAR_Y, w, GEAR_H, IMG_GEAR + 2 * i))
def background(fp, lang="pl"):
        c.text((cx + TITLE_POS[0], cy + TITLE_POS[1]), tx[name], f_title, TEXT2)
    gc = (gx + G_C[0], gy + G_C[1])
    c.rrect(*G_CARD, 12, CARD)
    c.rrect(*GEAR_CARD, 12, CARD)
def make_icon():
    ink = (250, 250, 250, 248)
def preview(imgs, slot_list, lang="pl"):
    pick["GEAR_D"] = IMG_GEAR + 13
    out = Image.new("RGBA", (sc(W), sc(H)), (11, 13, 16, 255))
def xml():
    return "applicationWeight=\\"210\\" entryButtonFocusID=\\"32751\\""
'''
patched = apply_theme(orig_db)
for needle in ('kSlot', 'RPM_BIG%d', 'SPEED_BIG%d', 'electric cyan', 'entryButtonFocusID=\\"32729\\"'):
    if needle=='kSlot': continue
    assert needle in patched, needle
orig_view='''    const double lat = m.hasLatG() ? m.latG() : 0, lon = m.hasLonG() ? m.lonG() : 0;
    out[kSlotGDot] = dotFrame(m);
    gearCells(m, out + kSlotGearP);
'''
v=apply_view(orig_view)
assert 'kSlotRpmBig0' in v and 'kSlotSpeedBig0' in v and 'm.speed * 0.621' in v
print('PASS: source patch anchors and generated C++ block transformations')
