# MakerWorld — Listing-Kit (zum Reinkopieren)

Alles fertig zum Einfügen in das MakerWorld-Upload-Formular. Reihenfolge folgt den
Formularfeldern. Zweisprachig (DE zuerst, EN darunter für internationale Reichweite —
MakerWorld-Publikum ist global; EN bringt deutlich mehr Downloads/Boosts).

Bild `docs/wiring.png` als Galerie-/Instruction-Bild hochladen. Cover-Foto vom
gedruckten Teil noch aufnehmen (siehe **Bild-Checkliste** unten).

---

## 1) TITEL (Design Name)

**Empfehlung (DE):**
> Runder Tischständer für GC9A01 1.28" Display + ESP32-C3 (Web-Flasher, schraubenlos)

**Empfehlung (EN):**
> Round Desk Stand for GC9A01 1.28" Display + ESP32-C3 — Browser-Flash, Screwless

**Alternativen (Titel darf kurz & suchstark sein):**
- GC9A01 1.28" Round Display Case & Desk Stand (ESP32-C3, no screws)
- Info-Display Ständer — GC9A01 + ESP32-C3, 5 Firmwares im Browser flashen
- Round TFT Desk Clock/HUD — GC9A01 + ESP32-C3, snap-fit, web flasher

---

## 2) SUMMARY / KURZBESCHREIBUNG (1 Zeile)

**DE:** 15° gekippter, schraubenloser Tischständer für ein rundes GC9A01 1.28"-TFT mit ESP32-C3 — inkl. 5 fertigen Firmwares, die man ohne Software direkt im Browser flasht.

**EN:** 15°-tilted, screwless desk stand for a round GC9A01 1.28" TFT with ESP32-C3 — includes 5 ready-made firmwares you flash straight from your browser, no software.

---

## 3) KATEGORIE & TAGS

- **Kategorie:** Gadgets / Electronics (bzw. „Hobby & DIY → Electronics")
- **Tags:** `ESP32`, `ESP32-C3`, `GC9A01`, `Round Display`, `TFT`, `Desk Stand`, `Clock`, `Weather Station`, `Snap-fit`, `No Supports`, `USB-C`, `Arduino`

---

## 4) BESCHREIBUNG (Description) — DEUTSCH

### Runder Info-Display-Ständer für GC9A01 + ESP32-C3

Gekippter (15°) Tischständer für ein rundes **GC9A01 1.28"-TFT** (240×240, SPI) mit
integriertem **ESP32-C3 Super Mini**. USB-C bleibt von außen erreichbar — Flashen und
Strom ohne Öffnen. Komplett **schraubenlos**: Display per Klemmring fixiert, Deckel per
Snap-Fit. Druckt **ohne Support** (nur eine kurze, frei druckende Brücke über dem USB-C-Port).

**Getestet:** Display-Aufnahme, Klemmring, Deckel-Snap und USB-C-Port per Testdruck bestätigt.

#### ✨ Highlights
- 🔩 **Keine Schrauben** — Display per Klemmring, Deckel per Snap-Fit
- 🖨️ **Kein Support** nötig
- 🔌 **USB-C von außen** zugänglich
- 🧩 3 Teile, ~25–30 g PLA gesamt
- 💻 **5 fertige Firmwares**, die du **ohne Arduino/Toolchain direkt im Browser flashst**

#### 💻 Firmware im Browser flashen — keine Software nötig
Über den **Web-Flasher** (Chrome/Edge am Desktop) flashst du per Klick:
- **GC9A01 HUD** — rotierendes Info-Display: Uhr · Wetter · Sonnenstand/Tageslicht · Datum,
  dazu einmal pro Stunde eine kleine Animations-Show. WLAN & Ort werden beim ersten Start
  bequem im Browser eingerichtet (Captive-Portal).
- **4 Demos ohne Setup:** Warp Starfield · Matrix Rain · Fire · Plasma

**👉 Web-Flasher:** https://medpex.github.io/display-case-gc9a01/

**HUD-Ersteinrichtung:** Beim 1. Start spannt das Display den WLAN-Hotspot
`GC9A01-HUD-Setup` auf → damit verbinden → WLAN wählen und optional Ort (Stadt/Breite/Länge)
+ Zeitzone setzen. Danach: Zeit per NTP, Wetter per Open-Meteo — **kein API-Key, kein
Account, keine Cloud, keine Telemetrie.** Ohne Ortsangabe: Default Berlin.

#### 🔧 Verkabelung (GC9A01 → ESP32-C3 Super Mini)
| Display | ESP32-C3 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SCL / SCK | GPIO4 |
| SDA / MOSI | GPIO6 |
| RES / RST | GPIO5 |
| DC | GPIO7 |
| CS | GPIO10 |
| BLK | 3V3 (Backlight dauerhaft an) |

→ Verkabelungs-Diagramm siehe Galerie.

#### 🧰 Benötigte Elektronik (nicht enthalten)
- 1× GC9A01 1.28" Rund-TFT, 240×240, SPI (7-Pin + BLK)
- 1× ESP32-C3 Super Mini (USB-C)
- 7× Dupont-Kabel female/female
- optional: 4× selbstklebende Gummifüße

#### 🛠️ Montage
1. Display von vorn in die Aufnahme legen (D-Form/Kinn nach unten, FPC durch die Ausbuchtung).
2. Klemmring von hinten aufsetzen (Öffnung zum FPC ausrichten) — fixiert das Display.
3. ESP32-C3 auf den Boden setzen, USB-C zum Port.
4. Laut Tabelle verkabeln.
5. Deckel einklicken (Snap-Fit).
6. Optional 4× Gummifüße unter den Boden.

#### 📄 Lizenz
**Standard-Digitaldateilizenz** — nur persönliche, nicht-kommerzielle Nutzung.
Kein Teilen, Remixen, Weiterverbreiten oder kommerzielle Nutzung ohne Genehmigung.
Quellcode, Firmware & Doku: https://github.com/medpex/display-case-gc9a01

---

## 5) DESCRIPTION — ENGLISH

### Round Info-Display Desk Stand for GC9A01 + ESP32-C3

A 15°-tilted desk stand for a round **GC9A01 1.28" TFT** (240×240, SPI) with an integrated
**ESP32-C3 Super Mini**. USB-C stays reachable from the outside — flash and power without
opening it. Completely **screwless**: the display is held by a clamp ring, the lid snaps in.
Prints **without supports** (only a short self-bridging span over the USB-C port).

**Tested:** display mount, clamp ring, lid snap and USB-C port all confirmed by a test print.

#### ✨ Highlights
- 🔩 **No screws** — clamp ring for the display, snap-fit lid
- 🖨️ **No supports** needed
- 🔌 **USB-C accessible** from outside
- 🧩 3 parts, ~25–30 g PLA total
- 💻 **5 ready-made firmwares** you flash **straight from your browser** — no Arduino, no toolchain

#### 💻 Flash firmware in your browser — no software
Using the **web flasher** (Chrome/Edge on desktop), flash with one click:
- **GC9A01 HUD** — rotating info display: clock · weather · daylight/sun arc · date, plus a
  short animation show once an hour. WiFi & location are set up in the browser on first boot.
- **4 zero-setup demos:** Warp Starfield · Matrix Rain · Fire · Plasma

**👉 Web flasher:** https://medpex.github.io/display-case-gc9a01/

**HUD first-time setup:** on first boot it opens a WiFi hotspot `GC9A01-HUD-Setup` → connect →
pick your WiFi and optionally set City/Latitude/Longitude + Timezone. Time via NTP, weather via
Open-Meteo — **no API key, no account, no cloud, no telemetry.** Defaults to Berlin.

#### 🔧 Wiring (GC9A01 → ESP32-C3 Super Mini)
| Display | ESP32-C3 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SCL / SCK | GPIO4 |
| SDA / MOSI | GPIO6 |
| RES / RST | GPIO5 |
| DC | GPIO7 |
| CS | GPIO10 |
| BLK | 3V3 (backlight always on) |

→ See the wiring diagram in the gallery.

#### 🧰 Required electronics (not included)
- 1× GC9A01 1.28" round TFT, 240×240, SPI (7-pin + BLK)
- 1× ESP32-C3 Super Mini (USB-C)
- 7× Dupont female/female jumper wires
- optional: 4× self-adhesive rubber feet

#### 🛠️ Assembly
1. Drop the display into the mount from the front (D-shape/chin down, FPC through the notch).
2. Put the clamp ring on from the back (opening aligned to the FPC) — it fixes the display.
3. Place the ESP32-C3 on the floor, USB-C toward the port.
4. Wire it up per the table.
5. Snap the lid in.
6. Optionally add 4 rubber feet.

#### 📄 License
**Standard Digital File License** — personal, non-commercial use only. No sharing,
remixing, redistribution or commercial use without permission.
Source, firmware & docs: https://github.com/medpex/display-case-gc9a01

---

## 6) DRUCKPROFIL / PRINT SETTINGS (MakerWorld „Print Profile"-Felder)

| Setting | Value |
|---|---|
| Material | PLA |
| Nozzle | 0.4 mm |
| Layer height | 0.2 mm |
| Walls / Perimeters | 1.7 mm (4 @ 0.4 mm) |
| Infill | ~15 % Gyroid |
| Supports | **None** |
| Plate orientation | Case on its back/bottom; lid & clamp ring flat |
| Filament used | ~25–30 g total |
| Est. print time | ~2–3 h (drucker-/profilabhängig) |

**Teile (3):** `FINAL-Case.stl`, `FINAL-Deckel.stl`, `FINAL-Klemmring.stl`
(bzw. `CASE-FINAL-alle-teile.3mf` = alle in einer Platte).

> ⚠️ Vor Upload STL/3MF neu exportieren — Deckel-Snap wurde zuletzt gefixt
> (Widerhaken 0,5 mm nach außen). Alte Dateien haben den Fix noch nicht.

---

## 7) BILD-CHECKLISTE (Cover + Galerie)

MakerWorld belohnt gute Fotos. Reihenfolge = Cover zuerst.
- [x] **Web-/App-Cover 4:3:** `docs/img/cover-4x3.png` (1600×1200, fertig)
- [x] **App-Cover 3:4:** `docs/img/cover-3x4.png` (1200×1600, fertig)
- [x] Galerie: `gallery-matrix.jpg`, `gallery-clock.jpg`, `gallery-weather.jpg`, `gallery-sun.jpg`, `gallery-wifi-setup.jpg`, `gallery-matrix-angle.jpg` (alle in `docs/img/`)
- [x] **`docs/wiring.png`** (Verkabelungs-Diagramm)
- [ ] noch schön: 3 Teile zerlegt nebeneinander (Case / Deckel / Klemmring)
- [ ] noch schön: Rückseite mit sichtbarem USB-C-Port
- [ ] optional: Screenshot der Web-Flasher-Seite (zeigt „flash im Browser")

---

## 8) LINKS

- **Web-Flasher:** https://medpex.github.io/display-case-gc9a01/
- **GitHub (Source/Firmware/Doku):** https://github.com/medpex/display-case-gc9a01
