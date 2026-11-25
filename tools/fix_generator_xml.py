#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Repair the known upstream XML-comment bug in an isolated BoostDeckCDS checkout.

The upstream make_db.py emits an XML comment containing '(make_db.py --menu)'.
The XML specification prohibits double hyphens within comments, and strict XML
parsers reject the resulting BoostDeckCDS.xml at line 2.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: fix_generator_xml.py PATH_TO_ISOLATED_WORKSPACE')
root = Path(sys.argv[1]).expanduser().resolve()
if not (root / '.boostdeck-cds-patched').is_file():
    raise SystemExit('Refusing to edit an unpatched or original source checkout')
p = root / 'make_db.py'
text = p.read_text(encoding='utf-8')
old = '(make_db.py --menu).'
new = '(make_db.py menu option).'
if text.count(old) == 1:
    p.write_text(text.replace(old, new), encoding='utf-8')
    print('FIXED: XML comment in isolated make_db.py (removed forbidden double hyphen)')
elif new in text and old not in text:
    print('OK: XML generator comment was already fixed')
else:
    raise SystemExit('Unexpected generator text: stopping rather than modifying unknown code')
