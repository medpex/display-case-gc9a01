# Display-Case GC9A01 — Tilted Desk Stand

A 15°-tilted desk stand for a round **GC9A01 1.28" TFT** (240×240, SPI) with an
integrated **ESP32-C3 Super Mini**. USB-C reachable from the outside. Print-ready
for Bambu Lab (0.4 mm nozzle, PLA, no supports).

> **Firmware without a toolchain:** flash the display right from your browser —
> **[open the Web Flasher »](https://medpex.github.io/display-case-gc9a01/)**
> (Chrome or Edge, desktop).

**📦 Download the model on [MakerWorld](https://makerworld.com/de/models/3082754-tischstander-fur-gc9a01-1-28-display-esp32-c3).**

![Wiring diagram](docs/wiring.png)

## Contents

```
Display-Case-GC9A01/
├── STL/                          # print-ready meshes
│   ├── FINAL-Case.stl
│   ├── FINAL-Deckel.stl          # lid (snap-fit)
│   └── FINAL-Klemmring.stl       # clamp ring (holds the display)
├── 3MF/CASE-FINAL-alle-teile.3mf # all parts in one file
├── STEP/CASE-FINAL.step          # parametric CAD (Fusion import)
├── Firmware/
│   ├── esp32_hud/                # GC9A01 HUD (clock/weather/sun/date, WiFi portal)
│   ├── esp32_starfield/          # Warp starfield demo (no WiFi)
│   ├── esp32_matrix/             # Matrix rain demo (no WiFi)
│   ├── esp32_fire/               # demoscene fire demo (no WiFi)
│   └── esp32_plasma/             # full-color plasma demo (no WiFi)
├── docs/                         # GitHub Pages web flasher + wiring diagram
└── BOM.md                        # bill of materials
```

## Wiring (GC9A01 → ESP32-C3 Super Mini)

| Display | ESP32-C3 GPIO |
|---------|---------------|
| VCC | 3V3 |
| GND | GND |
| SCL / SCK | GPIO4 |
| SDA / MOSI | GPIO6 |
| RES / RST | GPIO5 |
| DC | GPIO7 |
| CS | GPIO10 |
| BLK | 3V3 (backlight always on) |

## Firmware

Two sketches are included. Two ways to flash:

### 1. Web flasher (easiest — no software)

Open **<https://medpex.github.io/display-case-gc9a01/>** in Chrome or Edge on a
desktop, plug the ESP32-C3 in via USB-C, and click a flash button. That's it.

- **GC9A01 HUD** — rotating info display: clock, weather, daylight/sun arc and date,
  with a short random animation show once per hour. WiFi and location are set up in
  the browser on first boot (see below). No cloud, no account, no telemetry.
- **Demos** (no WiFi, no setup, run instantly):
  - **Warp Starfield** — flicker-free warp-speed flight through the stars
  - **Matrix Rain** — falling glyph columns with fading trails
  - **Fire** — old-school demoscene fire simulation
  - **Plasma** — full-color plasma waves cycling through the rainbow

#### HUD first-time setup

On first boot the HUD opens a WiFi hotspot **`GC9A01-HUD-Setup`**. Connect a
phone/laptop to it; a captive portal appears where you:

1. select your home WiFi and enter the password;
2. optionally set **City** (display label), **Latitude**, **Longitude** and
   **Timezone** (POSIX, e.g. `CET-1CEST,M3.5.0,M10.5.0/3`) for weather and the clock.

Settings are saved on the device (NVS). Time comes from NTP, weather from
[Open-Meteo](https://open-meteo.com) (no API key). Defaults to Berlin if you skip the
location fields. To change WiFi/location later, flash again — an erase re-opens the portal.

### 2. Self-compile (arduino-cli)

Requires the `esp32:esp32` core ≥ 3.3.7. Important: **`CDCOnBoot=cdc`** (otherwise no
serial / auto-upload on the C3 Super Mini).

```bash
# HUD — libs: "GFX Library for Arduino", ArduinoJson, WiFiManager (tzapu)
arduino-cli compile --upload -p /dev/cu.usbmodemXXXX \
  --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M,PartitionScheme=huge_app" \
  Firmware/esp32_hud

# Demos (starfield / matrix / fire / plasma) — libs: "Adafruit GFX Library", "Adafruit GC9A01A"
arduino-cli compile --upload -p /dev/cu.usbmodemXXXX \
  --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" \
  Firmware/esp32_starfield   # or esp32_matrix / esp32_fire / esp32_plasma
```

> Default location can also be changed in `Firmware/esp32_hud/esp32_hud.ino`
> (`DEF_CITY` / `DEF_LAT` / `DEF_LON` / `DEF_TZ`) before compiling.

## Print settings

- **Material:** PLA
- **Layer height:** 0.2 mm
- **Walls:** 1.7 mm (= 4 perimeters at 0.4 mm nozzle)
- **Infill:** ~15 % gyroid
- **Supports:** none (only a short bridge over the USB-C port, prints free)
- **Orientation:** case lying on its back/bottom; lid & clamp ring flat.

## Assembly

1. Drop the display into the boss from the front (D-shape/chin down, FPC through the notch).
2. Put the **clamp ring** on from the back — fixes the display; align its opening to the FPC.
3. Click the ESP32-C3 into the snap holder in the lower area, USB-C toward the port.
4. Wire it up per the table above.
5. Click the **lid** in (snap-fit) — bottom closes flush.
6. Optionally stick 4× rubber feet under the base.

## CAD notes

- Import `STEP/CASE-FINAL.step` into an empty Fusion document to keep editing.
- Internal Fusion length unit = cm; model authored in mm (`c(x)=x*0.1`).
- Key dimensions: wedge 58 D × 52 W × 66 H mm, wall 1.7, floor 2.0, tilt 15°.

## License

- **Hardware / 3D model / docs:** [CC BY 4.0](LICENSE) — use, remix, and share
  (including commercially); just give credit.
- Attribution: *Display-Case GC9A01 by medpex*.
```
