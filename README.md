# Display-Case GC9A01 — Tilted Desk Stand

A 15°-tilted desk stand for a round **GC9A01 1.28" TFT** (240×240, SPI) with an
integrated **ESP32-C3 Super Mini**. USB-C reachable from the outside. Print-ready
for Bambu Lab (0.4 mm nozzle, PLA, no supports).

> **Firmware without a toolchain:** flash the display right from your browser —
> **[open the Web Flasher »](https://medpex.github.io/display-case-gc9a01/)**
> (Chrome or Edge, desktop).

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
│   ├── esp32_clock/              # Mega Clock (analog, WiFi/NTP time)
│   └── esp32_starfield/          # Warp starfield demo
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
desktop, plug the ESP32-C3 in via USB-C, and click **Flash Clock** or
**Flash Starfield**. That's it.

- **Mega Clock** — smooth analog clock. On first boot it opens a WiFi setup
  hotspot named **`MegaClock-Setup`**; connect to it, pick your network, and the
  clock syncs the time via NTP (Europe/Berlin, incl. DST). No WiFi configured →
  it falls back to an offline clock. No cloud, no account.
- **Warp Starfield** — flicker-free warp-speed animation, runs instantly.

### 2. Self-compile (arduino-cli)

Requires the `esp32:esp32` core ≥ 3.3.7 and the libraries
`Adafruit GFX Library`, `Adafruit GC9A01A`, and `WiFiManager` (tzapu).
Important: **`CDCOnBoot=cdc`** (otherwise no serial / auto-upload on the C3 Super Mini).

```bash
# Clock (compile-time epoch is only a fallback; NTP is preferred)
arduino-cli compile --upload -p /dev/cu.usbmodemXXXX \
  --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" \
  --build-property "compiler.cpp.extra_flags=-DBUILD_EPOCH=$(date +%s)UL" \
  Firmware/esp32_clock

# Starfield
arduino-cli compile --upload -p /dev/cu.usbmodemXXXX \
  --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" \
  Firmware/esp32_starfield
```

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
