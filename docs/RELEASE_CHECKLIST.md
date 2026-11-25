# Pre-publication test checklist

- [ ] `PYTHONPATH=tools python3 -m unittest discover -s tests -p 'test_*.py'` passes.
- [ ] `bash -n boostdeck.sh` and `sh -n scripts/remote_entrynav2.sh` pass.
- [ ] On a **clean Mac** with authorized EntryNav2 framework libraries, `bash boostdeck.sh build` completes and its archive passes `tools/validate_package.py`.
- [ ] `bash boostdeck.sh preview` shows the expected **1219 × 460** blue-tile layout, 300 HP/350 Nm scales, HP, US gallons and numeric RPM/MPH.
- [ ] Check archive's `.so` target architecture/symbol dependencies against matching real EntryNav2 firmware before installing.
- [ ] Verify on at least one compatible **parked** test vehicle: menu presence, startup stability, accurate telemetry, no crashes, no SSH requirement at runtime.
- [ ] Verify fresh installation, guarded upgrade backup, `app.disable` and restore with a **spare/test unit** or simulated safe filesystem.
- [ ] Verify unit returns to `ro` after every successful install and failure path.
- [ ] Check 1280×480 screen only; **do not** claim NBT Evo/QNX or 800×480 support.
- [ ] Verify upstream license obligations, preserve the original SPDX notices, and review the included full PolyForm license and preserve any required third-party notices.
- [ ] Review the publication for BMW-proprietary `.so`, passwords, firmware dumps, personal data/logs, and generated car binaries.
- [ ] Clearly label GitHub Release `experimental / source-build only` until on-car tests pass.
