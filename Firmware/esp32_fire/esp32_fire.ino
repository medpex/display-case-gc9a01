/*
 * FIRE  -  ESP32-C3 Super Mini + GC9A01 (240x240 round)
 * Classic demoscene fire propagation (a la PSX Doom), 80x80 cell grid
 * rendered at 3x3 px. Flicker-free (full-frame canvas). No WiFi needed.
 *
 * Wiring: SCK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Flash: arduino-cli compile --upload -p <port> \
 *   --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" esp32_fire
 */
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include <SPI.h>

#define TFT_SCK 4
#define TFT_MOSI 6
#define TFT_RST 5
#define TFT_DC  7
#define TFT_CS  10

#define CELL 3                    // px per fire cell
#define FW (240 / CELL)           // 80 cells wide
#define FH (240 / CELL)           // 80 cells high
#define N_PAL 37                  // classic 37-step fire palette
#define WIND 1                    // 0 = straight up, 1 = slight drift

Adafruit_GC9A01A tft(TFT_CS, TFT_DC, TFT_RST);
GFXcanvas16 cv(240, 240);

uint8_t fire[FW * FH];            // palette index per cell
uint16_t pal[N_PAL];
uint32_t seed = 0xF12EF12E;

static uint32_t rnd() { seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5; return seed; }

// classic black -> red -> orange -> yellow -> white ramp
static void buildPalette() {
  static const uint8_t RGB[N_PAL][3] = {
    {7,7,7},{31,7,7},{47,15,7},{71,15,7},{87,23,7},{103,31,7},{119,31,7},{143,39,7},
    {159,47,7},{175,63,7},{191,71,7},{199,71,7},{223,79,7},{223,87,7},{223,87,7},{215,95,7},
    {215,95,7},{215,103,15},{207,111,15},{207,119,15},{207,127,15},{207,135,23},{199,135,23},{199,143,23},
    {199,151,31},{191,159,31},{191,159,31},{191,167,39},{191,167,39},{191,175,47},{183,175,47},{183,183,47},
    {183,183,55},{207,207,111},{223,223,159},{239,239,199},{255,255,255}
  };
  for (int i = 0; i < N_PAL; i++)
    pal[i] = ((RGB[i][0] & 0xF8) << 8) | ((RGB[i][1] & 0xFC) << 3) | (RGB[i][2] >> 3);
}

static inline void spreadFire(int src) {
  int r = rnd() & 3;                          // 0..3
  int dst = src - r + WIND;                   // sideways drift
  if (dst < FW) return;                       // stay inside (skip top row wrap)
  int v = fire[src] - (r & 1);                // cool down by 0 or 1
  fire[dst - FW] = (v < 0) ? 0 : v;
}

void setup() {
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.begin(); tft.setRotation(0); tft.fillScreen(0x0000);
  buildPalette();
  memset(fire, 0, sizeof(fire));
  for (int x = 0; x < FW; x++) fire[(FH - 1) * FW + x] = N_PAL - 1;   // bottom row = fuel
}

void loop() {
  cv.fillScreen(0x0000);
  // propagate (bottom row stays hot)
  for (int x = 0; x < FW; x++)
    for (int y = 1; y < FH; y++)
      spreadFire(y * FW + x);

  // render round-masked
  for (int y = 0; y < FH; y++) {
    for (int x = 0; x < FW; x++) {
      int px = x * CELL + CELL / 2 - 120, py = y * CELL + CELL / 2 - 120;
      if (px * px + py * py > 120 * 120) continue;      // outside round panel
      uint8_t v = fire[y * FW + x];
      if (v == 0) continue;                              // canvas already black
      cv.fillRect(x * CELL, y * CELL, CELL, CELL, pal[v]);
    }
  }
  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
}
