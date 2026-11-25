# Compatibility matrix

| Head unit | OS / architecture | This package |
|---|---|---|
| **EntryNav2 / EntryEVO**, 1280 × 480 | Linux, ARMv7 hard-float, older glibc | **Target**, pending independent on-car validation |
| EntryNav2 / EntryEVO, 800 × 480 | Linux, ARMv7 | **Not supported** by this screen layout; upstream has a distinct small-screen generator |
| **NBT Evo** | QNX Neutrino, ARMv7 different ABI | **Not supported by the automatic builder/installer. Do not use Linux `.so`.** |
| ID7 / MGU, NBT, CIC or unknown | Other | Refuse/unsupported |

**EntryEVO** is a term found internally on EntryNav2. It is **not** identical to **NBT Evo**. The upstream project supports both with separate toolchains and paths; this package targets only the **EntryNav2** side.

The installer requires `uname -s = Linux`, ARM architecture and EntryNav2-specific library + plugin paths. It will refuse to install if the root partition is not read-only before starting or if another plugin already uses connector `30117` or focus ID `32729`.

Runtime CDS properties vary with car/firmware. Speed assumes CDS km/h, fuel assumes litres, HP is derived from PS which is itself torque/RPM-derived. Gauge endpoints are default scales rather than proof of engine capability. Verify with the instrument cluster / independent scanner. RPM and MPH remain numeric (not segmented bars) in the supplied source kits.

There is no vehicle-specific unlock or SSH-root acquisition process in this repo. You need your own authorized access, appropriate toolchain and library files.
