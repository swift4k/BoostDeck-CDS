# NBT Evo (QNX) porting status — not an install guide

The original Gauge App upstream describes *two distinct* targets:

- **EntryNav2 / EntryEVO**: Linux, ARMv7 hard-float, `lib/Entry_Evo_libs`, plugin root `/opt/hmi/data/ro/Plugins` and `mount -o remount,rw /`.
- **NBT Evo**: QNX Neutrino 6.5, distinct ARM ABI, requires licensed QNX SDP `qcc`, car-matched `lib/NBT_evo_libs`, and uses different QNX plugin paths and remount operations.

The supplied BoostDeck CDS scripts were built around an **EntryNav2-specific Linux Docker toolchain and installer**. This public project deliberately **does not** build an NBT Evo binary or accept NBT Evo as an install target. Even if the native screen assets are shareable in principle, binary compatibility and install safety have **not** been evaluated on QNX.

A future NBT Evo port requires a contributor with authorized QNX SDP, matching framework libraries, a test car/bench, platform-specific application library output, separate archive validator and separate QNX-specific install/rollback implementation. Do **not** take the Linux ARMv7 `.tar` and change its filename to make it "Evo-compatible".

For technical background see the upstream project's `README.md`, `Makefile`, and `docs/NbtEvo_Installation_EN.md`. This file provides information for contributors and intentionally does not contain executable QNX installation instructions.
