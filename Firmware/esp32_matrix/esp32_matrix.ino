/*
 * MATRIX RAIN  -  ESP32-C3 Super Mini + GC9A01 (240x240 round)
 * Classic falling glyph columns with fading trails. Flicker-free
 * (full-frame canvas). No WiFi needed, runs instantly.
 *
 * Wiring: SCK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Flash: arduino-cli compile --upload -p <port> \
 *   --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" esp32_matrix
 */
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include <SPI.h>

#define TFT_SCK 4
#define TFT_MOSI 6
#define TFT_RST 5
#define TFT_DC  7
#define TFT_CS  10

// glyph cell = 12x16 px (6x8 font at size 2)
#define GLYPH_W 12
#define GLYPH_H 16
#define N_COLS (240 / GLYPH_W)    // 20 columns
#define N_ROWS (240 / GLYPH_H)    // 15 rows
#define TRAIL_MIN 5               // shortest trail (rows)
#define TRAIL_MAX 12              // longest trail (rows)
#define SPEED_MIN 0.12f           // rows per frame
#define SPEED_MAX 0.42f
#define MUTATE_P 28               // 1/N chance per cell per frame to swap its glyph

Adafruit_GC9A01A tft(TFT_CS, TFT_DC, TFT_RST);
GFXcanvas16 cv(240, 240);

struct Column { float head; float speed; uint8_t trail; };
Column cols[N_COLS];
char glyphs[N_COLS][N_ROWS];      // current character per cell
uint32_t seed = 0xC0FFEE42;

// deterministic PRNG (no float rand needed)
static uint32_t rnd() { seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5; return seed; }
static float frnd() { return (rnd() & 0xFFFFFF) / (float)0xFFFFFF; }
static char rndGlyph() {
  // digits, katakana-ish ASCII mix: dense, techy shapes
  static const char SET[] = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%&*+=<>~";
  return SET[rnd() % (sizeof(SET) - 1)];
}

static uint16_t green(uint8_t v) {          // brightness 0..255 -> RGB565 green
  return (uint16_t)(v & 0xFC) << 3;
}

static void respawn(Column &c) {
  c.head  = -(float)(rnd() % N_ROWS);       // start above the screen, staggered
  c.speed = SPEED_MIN + frnd() * (SPEED_MAX - SPEED_MIN);
  c.trail = TRAIL_MIN + rnd() % (TRAIL_MAX - TRAIL_MIN + 1);
}

void setup() {
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.begin(); tft.setRotation(0); tft.fillScreen(0x0000);
  for (int c = 0; c < N_COLS; c++) {
    respawn(cols[c]);
    cols[c].head = frnd() * N_ROWS;         // initial frame: heads everywhere
    for (int r = 0; r < N_ROWS; r++) glyphs[c][r] = rndGlyph();
  }
}

void loop() {
  cv.fillScreen(0x0000);
  for (int c = 0; c < N_COLS; c++) {
    Column &col = cols[c];
    col.head += col.speed;
    if (col.head - col.trail > N_ROWS) respawn(col);

    int headRow = (int)col.head;
    for (int i = 0; i <= col.trail; i++) {
      int r = headRow - i;
      if (r < 0 || r >= N_ROWS) continue;
      if ((rnd() % MUTATE_P) == 0) glyphs[c][r] = rndGlyph();   // glyphs flicker
      uint8_t b = 255 - (uint8_t)(i * (220 / col.trail));       // fade along trail
      uint16_t colr;
      if (i == 0) colr = 0xCFFF;                                 // head: near-white
      else        colr = green(b);
      cv.drawChar(c * GLYPH_W, r * GLYPH_H, glyphs[c][r], colr, 0x0000, 2);
    }
  }
  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
}
