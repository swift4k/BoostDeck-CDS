"""Offline tests. Run: PYTHONPATH=tools python3 -m unittest discover -s tests -p 'test_*.py'"""
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from patch_features import patch as patch_v4
from validate_package import validate as validate_package
from validate_backup import validate as validate_backup

class MergePatchTest(unittest.TestCase):
    def test_v4_patch_applies_to_fresh_v1_contract(self):
        # Deliberately synthesize the exact v1 textual anchors the original v4 supplied.
        # This tests the complete update routine, not just independent string snippets.
        db = '''TITLE = "BOOSTDECK CDS"
W, H = 960, 400
("POWER", (670, 0),
("TORQUE", (670, 208),
POWER_SCALE_MIN, TORQUE_SCALE_MIN = 150, 250
G_CARD = (305, 0, 350, 300)
GEAR_CARD = (305, 316, 230, 84)
FUEL_CARD = (543, 316, 112, 84)
FUEL_BOX = (36, 26, 44, 32)
FUEL_UNIT_BOX = (36 + 44 + 4, 33, 28, 22)
gx + 91 + k * BIG["cell"]
gx + 107 + k * BIG["cell"]
"POWER": (193, 231, 0.772, 0.924, 2 if lang == "pl" else UNITS.index("PS"), "0", "250")
"TORQUE": (380, 412, 0.844, 0.916, 5, "0", "450")
pick["FUEL"] = IMG_FUELNUM + 39
pick["FUEL_UNIT"] = IMG_FUEL_UNIT
UNITS = ["°C", "°F", "KM", "kW", "hp", "Nm",
("Moc: hp", "Power: hp")
'''
        view = '''kSlotRpmBig0 kSlotSpeedBig0
Settings() : color(0), temp(kCelsius), power(kPs), torque(kNm), fuel(kLitre) {}
return st.power == kKw ? 100 : 150;
return st.torque == kLbFt ? 200 : 250;
if (!hasMax) return minimum;
    int e = (int)(ceil(shownMax * 1.05 / step) * step);
'''
        engine = '#define ENGINE_APP_VERSION "engine-data-0.2.0 "\n'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'src').mkdir(); (root/'.boostdeck-cds-patched').write_text('v1\n')
            (root/'make_db.py').write_text(db)
            (root/'src/gauge_view.hpp').write_text(view)
            (root/'src/engine_data.cpp').write_text(engine)
            patch_v4(root)
            merged=(root/'make_db.py').read_text()
            self.assertIn('W, H = 1060, 400',merged)
            self.assertIn('FUEL_CARD = (576, 316, 178, 84)',merged)
            self.assertIn('UNITS.index("HP")',merged)
            self.assertIn('"FUEL"] = IMG_FUELNUM + 15',merged)
            self.assertIn('fuel(kGallon)',(root/'src/gauge_view.hpp').read_text())
            self.assertTrue((root/'.boostdeck-cds-v2-patched').exists())
            old=merged
            patch_v4(root)
            self.assertEqual(old,(root/'make_db.py').read_text())
            self.assertTrue((root/'make_db.py.before-v2').exists())

class PackageSafetyTest(unittest.TestCase):
    root='opt/hmi/data/ro/Plugins/BoostDeckCDS/'
    def synthetic(self,filename,wrong=False):
        names={
            'libBoostDeckCDS.so': b'\x7fELF\x01\x01'+b'\x00'*12 + b'\x28\x00'+b'\x00'*200,
            'BoostDeckCDS.manifest':b'<manifest><id>30117</id></manifest>',
            'BoostDeckCDS.xml':b'<x entryButtonFocusID="32729" />',
            'BoostDeckCDS_ALL_Texts.zip':b'fake-texts',
            'BoostDeckCDS_ALL_Images.zip':b'fake-images',
            'BoostDeckCDS_frames.bin':b'fake-frames',
            'BoostDeckCDS_frames_c0.bin':b'fake-frames-c0',
        }
        # 10,000 byte minimum required by validator
        names['libBoostDeckCDS.so'] += b'\0'*15000
        lines=[]
        with tarfile.open(filename,'w') as tf:
            for short,body in names.items():
                n=self.root+short
                i=tarfile.TarInfo(n);i.size=len(body)
                tf.addfile(i,io.BytesIO(body))
                lines.append(hashlib.md5(body).hexdigest()+'  '+n)
            if wrong:
                lines[0]='0'*32+'  '+self.root+'libBoostDeckCDS.so'
            data=('\n'.join(lines)+'\n').encode()
            i=tarfile.TarInfo('MD5SUMS');i.size=len(data)
            tf.addfile(i,io.BytesIO(data))
    def test_valid_and_corrupted_archives(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'build.tar';self.synthetic(p)
            validate_package(p)
            self.synthetic(p,wrong=True)
            with self.assertRaisesRegex(ValueError,'Checksum mismatch'):
                validate_package(p)
    def test_reject_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.tar'
            with tarfile.open(p,'w') as tf:
                b=b'x'*12000
                info=tarfile.TarInfo('../../malicious.so');info.size=len(b);tf.addfile(info,io.BytesIO(b))
            with self.assertRaises(ValueError):validate_package(p)
    def test_backup_validation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'backup.tar'
            files={'libBoostDeckCDS.so':b'\x7fELF'+b'\0'*20000,
                   'BoostDeckCDS.manifest':b'<id>30117</id>',
                   'BoostDeckCDS.xml':b'XML',
                   'BoostDeckCDS_frames.bin':b'frames'}
            with tarfile.open(p,'w') as tf:
                for name,body in files.items():
                    m=tarfile.TarInfo('BoostDeckCDS/'+name);m.size=len(body)
                    tf.addfile(m,io.BytesIO(body))
            validate_backup(p)

if __name__=='__main__': unittest.main()
