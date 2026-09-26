# MakerWorld — Listing-Kit „Display-Puck GC9A01“ (zum Reinkopieren)

Neues Modell, zweisprachig wie das Original. Upload am besten als **eigenes Modell** mit Verweis
auf das Original. Alternativ geht es als zweites Druckprofil beim Original, dann wirkt der Cover aber
weniger. In beiden Beschreibungen gegenseitig verlinken.

Bilder: `docs/img/cover-4x3.png`, `docs/img/cover-3x4.png`, Galerie siehe **Bild-Checkliste**.

---

## 1) TITEL

**DE:** Runder Display-Puck für GC9A01 1.28" + ESP32-C3 (15° gekippt, schraubenlos, Web-Flasher)

**EN:** Round Display Puck for GC9A01 1.28" + ESP32-C3 — 15° Tilt, Screwless, Browser-Flash

Alternativen:
- GC9A01 Round Desk Puck — ESP32-C3, snap-fit, no supports
- Round TFT Puck Clock/HUD — GC9A01 + ESP32-C3, 49 min print

---

## 2) SUMMARY

**DE:** Runder 15°-Puck mit angeformtem Keilfuß für das GC9A01 1.28"-TFT + ESP32-C3. Schraubenlos, ohne Support, ~49 min Druck. Dieselben 5 Browser-Firmwares wie der Original-Ständer.

**EN:** Round 15° puck with an integrated wedge foot for the GC9A01 1.28" TFT + ESP32-C3 — screwless, no supports, ~49 min print, same 5 browser-flash firmwares as the original stand.

---

## 3) KATEGORIE & TAGS

- **Kategorie:** Gadgets / Electronics
- **Tags:** `ESP32`, `ESP32-C3`, `GC9A01`, `Round Display`, `TFT`, `Desk Clock`, `Puck`, `Weather Station`, `Snap-fit`, `No Supports`, `USB-C`, `Arduino`

---

## 4) BESCHREIBUNG — DEUTSCH

### Runder Display-Puck für GC9A01 + ESP32-C3

Neue Variante meines [Tischständers für das GC9A01](https://makerworld.com/de/models/3082754-tischstander-fur-gc9a01-1-28-display-esp32-c3).
Diesmal als **runder Puck (⌀64 mm)**, 15° nach hinten gekippt, auf einem angeformten Keilfuß.
Elektronik, Verkabelung und Firmware sind identisch zum Original. Die Display-Aufnahme ist
1:1 aus dem getesteten Original übernommen.

#### ✨ Highlights
- ⭕ **Runde Form**: das runde Display sitzt mittig im runden Gehäuse
- 🔩 **Keine Schrauben**: Klemmring mit Pressrippen, Deckel per Rastwulst, ESP32 per Schnapp-Schienen am Deckel
- 🖨️ **Kein Support**: ~49 min Druck auf einem Bambu A1, ~33 g PLA, alle 3 Teile auf einer Platte
- 🔌 **USB-C hinten** mit Senkung für den Stecker
- 💻 **5 fertige Firmwares** zum Flashen direkt im Browser, ohne Arduino

#### 💻 Firmware im Browser flashen
Mit dem **Web-Flasher** (Chrome/Edge am Desktop) per Klick:
- **GC9A01 HUD**: Uhr · Wetter · Sonnenstand · Datum. WLAN und Ort richtest du beim ersten Start im Browser ein.
- **4 Demos ohne Setup:** Warp Starfield · Matrix Rain · Fire · Plasma

**👉 Web-Flasher:** https://medpex.github.io/display-case-gc9a01/

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
| BLK | 3V3 |

#### 🧰 Benötigte Elektronik (nicht enthalten)
- 1× GC9A01 1.28" Rund-TFT (240×240, SPI), gerade Stiftleiste oder Litzen
- 1× ESP32-C3 Super Mini (USB-C)
- 7–8 Litzen oder Dupont-Kabel
- optional 2× Gummifüße ⌀8 mm

#### 🛠️ Montage
1. Display von hinten in die Aufnahme legen: Glas nach vorn, Kinn/FPC **nach unten** zwischen die zwei Stifte.
2. Klemmring von hinten eindrücken (Öffnung nach unten). Die Rippen am Ring halten ihn per Presspassung.
3. Verkabeln. Am Display eine **gerade Stiftleiste nach hinten** nutzen oder direkt anlöten, eine Winkel-Stiftleiste passt nicht. Stiftleisten am ESP32 sollten zur Puck-Mitte zeigen.
4. ESP32-C3 mit dem **USB-C-Ende voran** in die Schienen am Deckel schieben, bis die Haken einrasten.
5. Deckel einsetzen (Schlitz oben auf die Nase im Gehäuse) und eindrücken, bis er einrastet.
6. Optional 2 Gummifüße unter den Fuß kleben.

Zum Öffnen den Deckel an einem der Schlitze mit dem Fingernagel heraushebeln.

#### 📄 Lizenz
**Standard-Digitaldateilizenz**: nur persönliche, nicht-kommerzielle Nutzung.

---

## 5) DESCRIPTION — ENGLISH

### Round Display Puck for GC9A01 + ESP32-C3

A new variant of my [GC9A01 desk stand](https://makerworld.com/de/models/3082754-tischstander-fur-gc9a01-1-28-display-esp32-c3),
this time as a **round puck (⌀64 mm)** tilted back by 15°, standing on an integrated wedge
foot. The electronics, wiring and firmware are identical to the original, and the display
mount is copied 1:1 from the tested original.

#### ✨ Highlights
- ⭕ **Round**: the round display sits centred in a round body
- 🔩 **No screws**: press-fit clamp ring, snap-bead lid, snap rails for the ESP32 on the lid
- 🖨️ **No supports**: ~49 min on a Bambu A1, ~33 g PLA, all 3 parts on one plate
- 🔌 **USB-C at the back** with a recess for the plug
- 💻 **5 ready-made firmwares** you flash in the browser, no Arduino needed

#### 💻 Flash in your browser
**Web flasher:** https://medpex.github.io/display-case-gc9a01/ (Chrome/Edge, desktop)
- **GC9A01 HUD**: clock · weather · sun arc · date. WiFi and location are set up in the browser on first boot.
- **4 zero-setup demos:** Warp Starfield · Matrix Rain · Fire · Plasma

#### 🔧 Wiring (GC9A01 → ESP32-C3 Super Mini)
VCC→3V3 · GND→GND · SCL→GPIO4 · SDA→GPIO6 · RES→GPIO5 · DC→GPIO7 · CS→GPIO10 · BLK→3V3

#### 🧰 Required electronics (not included)
- 1× GC9A01 1.28" round TFT · 1× ESP32-C3 Super Mini · 7–8 wires · optional 2 rubber feet ⌀8 mm

#### 🛠️ Assembly
1. Insert the display from the back: glass first, chin/FPC **down** between the two pins.
2. Press the clamp ring in from the back with its opening facing down.
3. Wire it up. On the display, use a **straight header pointing backwards** or solder directly, because a right-angle header does not fit. Headers on the ESP32 should point towards the centre.
4. Slide the ESP32-C3 into the lid rails **USB-C end first** until the hooks click.
5. Line up the lid slot with the key at the top and press the lid in until it snaps.
6. Optional: add 2 rubber feet.

#### 📄 License
**Standard Digital File License**: personal, non-commercial use only.

---

## 6) DRUCKPROFIL / PRINT SETTINGS

| Setting | Value |
|---|---|
| Printer | Bambu Lab A1 (tested slice), any 0.4 mm |
| Material | PLA |
| Layer height | 0.2 mm |
| Walls | 4 |
| Infill | 15 % gyroid |
| Supports | **None** |
| Plate | `PUCK-alle-teile.3mf` (parts already oriented) |
| Filament | ~33 g |
| Time | ~49 min (Bambu Studio 2.08, A1 0.4, PLA Basic) |

---

## 7) BILD-CHECKLISTE

- [x] Cover 4:3: `docs/img/cover-4x3.png` (Rendering mit Beispiel-HUD auf dem Glas)
- [x] Cover 3:4: `docs/img/cover-3x4.png`
- [x] Galerie-Renderings: `render-front.png`, `render-side.png`, `render-rear.png`, `render-exploded.png`, `render-lid.png`, `hero-screen.png`
- [x] `docs/wiring.png`
- [ ] **Foto vom echten Druck** nach dem Testdruck (Cover später durch Foto ersetzen, das bringt auf MakerWorld mehr)
- [ ] Foto Rückseite mit eingestecktem USB-C
- [ ] Foto Original-Ständer und Puck nebeneinander

> Hinweis: Die Cover sind Renderings. Das HUD auf dem Glas ist ein gezeichneter Beispiel-Screen.
> Bis Fotos vom echten Druck da sind, in der Beschreibung als „Render“ kennzeichnen.

---

## 8) LINKS
- **Original:** https://makerworld.com/de/models/3082754-tischstander-fur-gc9a01-1-28-display-esp32-c3
- **Web-Flasher:** https://medpex.github.io/display-case-gc9a01/
