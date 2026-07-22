# MakerWorld-Beschreibung (zum Reinkopieren)

> Text für das Beschreibungsfeld auf MakerWorld. Bild `docs/wiring.png` als
> Instruction-/Galeriebild hochladen. Links anpassen, sobald GitHub-Repo +
> Pages live sind.

---

## Runder Tischständer für GC9A01 1.28" Display (ESP32-C3)

Gekippter (15°) Tischständer für ein rundes **GC9A01 1.28"-TFT** (240×240, SPI)
mit integriertem **ESP32-C3 Super Mini**. USB-C bleibt von außen erreichbar.
Komplett **schraubenlos**: Display per Klemmring fixiert, Deckel per Snap-Fit.

**Druckfertig & getestet** — Display-Mount, Deckel-Snap und USB-C-Port per
Testdruck bestätigt.

### ✨ Highlights
- Kein Support nötig (nur eine kurze, frei druckende Brücke über dem USB-C-Port)
- Keine Schrauben — alles Snap-Fit / Klemmring
- USB-C von außen zugänglich (Flashen/Strom ohne Öffnen)
- 3 Teile, ~25–30 g PLA gesamt

### 🖨️ Druckeinstellungen
| Einstellung | Wert |
|---|---|
| Material | PLA |
| Layerhöhe | 0.2 mm |
| Wände | 1.7 mm (4 Perimeter @ 0.4 mm Düse) |
| Infill | ~15 % Gyroid |
| Support | nein |
| Ausrichtung | Case auf Rückseite liegend; Deckel & Klemmring flach |

### 🔌 Elektronik (nicht enthalten)
- 1× GC9A01 1.28" Rund-TFT, 240×240, SPI (7-Pin + BLK)
- 1× ESP32-C3 Super Mini (USB-C)
- 7× Dupont-Kabel female/female
- optional 4× Gummifüße

### 🔧 Verkabelung (GC9A01 → ESP32-C3)
| Display | ESP32-C3 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SCL/SCK | GPIO4 |
| SDA/MOSI | GPIO6 |
| RES/RST | GPIO5 |
| DC | GPIO7 |
| CS | GPIO10 |
| BLK | 3V3 |

→ Verkabelungs-Diagramm siehe Bilder.

### 💻 Firmware — im Browser flashen, keine Software nötig
Zwei fertige Firmwares (analoge **Uhr** mit WLAN/NTP-Zeit, und **Warp-Starfield**).
Direkt aus dem Browser flashen (Chrome/Edge, Desktop) — kein Arduino, kein Setup:

**👉 Web-Flasher: https://medpex.github.io/display-case-gc9a01/**

Die Uhr öffnet beim ersten Start einen WLAN-Hotspot `MegaClock-Setup` zur
Netzwerk-Eingabe, danach holt sie die Zeit per NTP (kein Cloud-Account).
Quellcode & Doku: https://github.com/medpex/display-case-gc9a01

### 📄 Lizenz
CC BY 4.0 — frei nutzen, remixen, auch kommerziell. Bitte Namensnennung:
*Display-Case GC9A01 by medpex*.
