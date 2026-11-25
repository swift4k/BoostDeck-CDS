# How BoostDeck CDS gets vehicle data — investigation and architecture

> Technical background for developers and BMW owners. This is an explanation of the **EntryNav2 / EntryEVO implementation**, not a universal claim that every BMW exposes the same CDS properties. Observations from one investigated head unit are distinguished from source-code behavior and unverified possibilities.

## Short answer

BoostDeck CDS does **not** read the OBD-II diagnostic socket, open a raw CAN-bus interface, send UDS diagnostic requests to the DME, or rely on a connected laptop after installation. It runs **on the head unit** as a native BMW HMI `PluginApp`, subscribing to BMW **CDS (Car Data Service)** property-change notifications through the proprietary application framework already present on compatible EntryNav2 systems.

The head unit and the BMW software stack handle any underlying vehicle-network routing. The application receives higher-level named data properties, such as `engine.RPMSpeed` and `driving.speedActual`, through the supported framework callback boundary. It does not need to reverse-engineer CAN arbitration IDs or inject vehicle-network messages for this dashboard.

```text
Vehicle ECUs / BMW vehicle networks
                  |
         BMW head-unit services
                  |
     BMW CDS / HMI app framework
                  |
 PluginApp::cdsAddPropertyChangedEventHandler
                  |
 UTF-16 property-value callbacks (JSON-like texts)
                  |
    parse and validate latest Metrics
                  |
       calculate / convert display values
                  |
      image-frame + digit selection
                  |
 PluginApp::updateModel(raImageModel, BMW Image)
                  |
         Native iDrive RHMI screen
```

## The original obstacle: direct vehicle-data access

We started by exploring lower-level ways to ask the car for live metrics from a head-unit shell. This was useful for understanding the environment, but **none of these attempts produced a verified, reusable direct diagnostic or CAN endpoint for BoostDeck**:

| Investigated approach | What we observed or examined | Why we did not build on it |
|---|---|---|
| Raw CAN / a Linux device port | Searched the device nodes and running processes for vehicle/CAN interfaces. | We did not establish a usable, documented `/dev`/SocketCAN endpoint that would safely provide RPM, speed, coolant, etc. to an ordinary plugin. This is *not* proof that the car has no CAN bus or that the HMI never accesses it. |
| ENET / Ethernet diagnostics / DME requests | Used Ethernet and SSH for development. Examined diagnostic routing strings in `/usr/local/lib/libEthDiagMM.so.0.0.0`, including EthDiagMM, HSFZ/IP configuration and VMOST-related names; a gateway such as `169.254.94.6` was recorded during investigation. | Strings and routing components are not a documented, functioning high-level API for our display. Establishing a safe diagnostic transport, ECU targeting and request protocol would have been a separate project. The Mac/ENET link remains **an installation and debugging path**, not the running dashboard's telemetry feed. |
| MOST / virtual MOST / internal sockets | On one EntryNav2 software build (`202003311616`), processes included `ipcvmost`, `vmostd`, `vmostMMP`, and `NavStartup`. vMOST libraries and Unix sockets such as `/var/run/vmost_sockstream` were present; no usable `/dev/*most*` interface was established. | These components indicate internal messaging/transport infrastructure. They do **not** by themselves grant a public API for live RPM/speed or DME fault codes. We did not demonstrate a stable decoding/protocol route for this app. |
| D-Bus / navigation / RueKo | Looked for D-Bus tooling, services, and navigation/cluster interfaces. `busctl`, `gdbus`, and `dbus-monitor` were unavailable in the investigated shell; `RueKoIC`, `RICServiceGuidance`, and `REMOTEINSTRUMENTCLUSTER` were considered as leads, without a proven live-data path. | Navigation/remote-instrument-cluster commands are not interchangeable with engine telemetry. Missing command-line utilities also does **not** prove the absence of a bus or library. No supported interface was established from this avenue. |

The practical lesson: **being able to SSH into a head unit is not the same as having a directly usable CAN, OBD or DME diagnostic socket**. We stopped treating lower-level transport discovery as a requirement for showing values the HMI already had access to.

## The successful route: native CDS subscription

The underlying [MGD4096 Gauge App](https://github.com/MGD4096/Gauge-App-for-NBTEvo-and-EntryNav2) already implements the relevant `PluginApp`/CDS model. Our combined source-build project **retains that underlying data transport**, rather than replacing it with a Mac relay, Bluetooth OBD dongle, custom CAN wiring, or a Linux socket reader. The C++ entry point is based on the BMW application framework exposed by `libAppFramework.A.so` and `libCoreFramework.A.so` copied from an owner's own compatible unit; those proprietary libraries are **not distributed here**.

In the inspected application source (`src/engine_data.cpp`, as produced from the pinned upstream plus patches), startup and updates work as follows:

1. BMW's HMI loads the application's manifest and initializes a native `PluginApp`. Its RHMI XML defines the dashboard screen and image-model IDs.
2. `onInit()` prepares the dashboard, schedules CDS subscription after approximately **1,500 ms**, and initially leaves unavailable readings blank.
3. `subscribeRun()` loops over the property list and registers `PluginApp::cdsAddPropertyChangedEventHandler(property, 0, delegate)` for each property.
4. BMW calls our delegate when it publishes a property update. The callback carries a `BasicString<unsigned short>` value, which the parser narrows from UTF-16 to ASCII for the expected numeric JSON-like fields.
5. The parser updates a mutex-protected `Metrics` state, setting `has...` validity flags. Missing/malformed/out-of-range data is **not** silently represented as a real reading of zero.
6. A render task runs approximately every **200 ms** (up to ~5 screen updates/second), selects pre-generated digit/arc frames, and calls `PluginApp::updateModel(...)` for changed image models. iDrive renders those images inside the RHMI layout.
7. Recorded display maxima/settings can be stored on the head unit's writable data partition; this is not vehicle ECU programming.

These values are consumed locally by the app after it has been installed. **The Mac is not queried whenever an RPM update appears.** ENET/SSH is needed only for the developer's build, inspection, and guarded installation workflow.

### Subscribed CDS properties

The source's `src/cds_values.hpp` defines eight subscriptions (spelling/capitalization matters):

| CDS property | Parsed fields | Dashboard meaning / assumptions |
|---|---|---|
| `engine.temperature` | `temperature.engine`, `temperature.oil` | Coolant and oil in °C, subject to the vehicle's published values |
| `engine.RPMSpeed` | `RPMSpeed` | Engine speed in revolutions/minute |
| `engine.torque` | `torque` | Nm; may be signed, including negative overrun torque |
| `driving.gear` | `gear` | Interpreted by inherited gear mapping; may vary by drivetrain/firmware |
| `driving.acceleration` | `acceleration.lateral`, `.longitudinal` | Extra upstream signal; treated as likely m/s², not needed to make the RPM/speed tiles work |
| `driving.speedActual` | `speedActual` | Interpreted as km/h, converted to MPH for US display |
| `sensors.fuel` | `fuel.tanklevel` | Interpreted as litres remaining; converted to US gallons if selected |
| `vehicle.language` | `language` | UI language selection where supported |

Representative payloads from the parser's documented format (examples, **not a recorded log from every car**):

```json
{"RPMSpeed":2450}
{"speedActual":100}
{"temperature":{"engine":92,"oil":104}}
{"torque":270}
{"fuel":{"range":522,"reserve":0,"tanklevel":39}}
```

For example, `driving.speedActual = 100` displays about **62 MPH** after multiplying by `0.62137119223733`. The app is showing the reported vehicle speed, not reading GPS. `tanklevel = 39` litres becomes about **10 US gal** (`39 / 3.785411784`); fuel quantity is an estimate and its interpretation must be confirmed per vehicle.

**Horsepower is calculated**, not received as a separate measured ECU horsepower channel. The parser computes positive engine power in metric PS approximately as `max(torque_Nm, 0) × RPM / 7023.5` and the UI converts PS to mechanical HP with factor `0.98632` where the HP display setting is used. It is an indicative modeled engine-output value, not a dynamometer measurement and not necessarily wheel horsepower.

The temperature and torque gauges also show tracked maxima. The upstream code requires corroborating samples before accepting a new maximum, which reduces one-sample spikes. Conversion choices include °C/°F, PS/kW/HP, Nm/lb-ft, and L/US gal. **Do not assume that a populated CDS property is valid on every chassis or firmware variant**.

## Why the interface uses generated pictures instead of HTML

This dashboard is a native **RHMI** plugin, not a CarPlay web page. Python `make_db.py` generates the layout XML, background artwork, picture-number glyphs and pre-rendered gauge frames at build time. The installed native C++ library loads those resources and updates `raImageModel` values. In the upstream implementation, trying to bundle all frames directly in the HMI image database caused the images to fail to display on an EntryNav2; frames are instead loaded as application resources and sent through image-model updates.

The v1 foundation establishes the separate BoostDeck plugin identity, blue-tile interface and live numeric RPM/MPH. Later supplied features expand the canvas to 1060×400 design pixels (output 1219×460 for a 1280×480 screen), revise fuel layout, set 300 HP / 350 Nm starting scales, and default to US HP and gallons. These are **display/units/layout changes**, not additional lower-level vehicle network access.

## EntryNav2, EntryEVO and NBT Evo are not the same target

BMW naming is especially confusing here. **EntryEVO** may be used internally for the **EntryNav2** Linux ARMv7 software family. That does not make it the same as **NBT Evo**, which uses **QNX** and requires a different application binary, libraries, toolchain and installation paths. This project's automated builder/installer intentionally targets EntryNav2/EntryEVO Linux only. It does not claim that the same `.so` will load on NBT Evo. An EVO-compatible native port must be separately built and verified; see [NBT_EVO_PORT.md](NBT_EVO_PORT.md).

## What CDS does NOT unlock

CDS access is **not a general-purpose diagnostic interface**. The working subscriptions above do not establish reading/clearing DME fault codes, flashing/coding ECUs, misfire counters, boost pressure, air/fuel ratio, oil pressure, alternator/battery health, individual wheel speeds, knock/timing, or an unrestricted D-Bus/MOST/CAN API. Those need separately demonstrated interfaces and safety controls. Never promise such features from the existence of a head-unit Ethernet port, a `libEthDiagMM` symbol, or a CDS engine RPM callback.

## Debugging and verifying your own vehicle

On EntryNav2, the native implementation logs property registration and early raw samples to its writable data log (example: `/var/local/data/BoostDeckCDS/boostdeck-cds.log`). The source also supports opt-in USB logging; see the inspected `src/engine_data.cpp`. A message of the form `CDS engine.RPMSpeed = '{...}' -> ok` is meaningful evidence that a given property was received; successful registration **alone is not proof** that the car ever sent a usable value. If a property is absent or reports an error, the app should display unavailable data rather than fake telemetry. Verify RPM, speed and temperatures against the cluster or a trusted scan tool on each vehicle.

For a new compatible unit, check its operating system/ABI, library exports, plugin framework, HMI XML models, CDS property availability, and correct units before installing. The public repo deliberately excludes proprietary framework libraries, SSH credentials, firmware images and any diagnostic-port exploit.

## Evidence and limitations of this write-up

- **Verified from the source examined for this project:** the eight property names, registration API, 1.5-second delayed subscription, UTF-16 parsing, range/validity checks, ~200 ms render loop, numeric conversions and RHMI image-model update architecture.
- **Recorded during one head-unit investigation:** EntryNav2 firmware string `202003311616`, vMOST-related processes/sockets, EthDiagMM library/symbol exploration, and absence of a *demonstrated* direct-diagnostic route from the shell.
- **Not established here:** a complete packet trace of the ECU-to-HMI route, a decoded raw MOST/CAN protocol, a working OBD/DME diagnostic request endpoint, or compatibility across all BMW head-unit software versions and vehicle models.

This summary documents **why CDS was the practical, lower-risk application-level solution**, without pretending we accessed low-level ports we never successfully verified.
