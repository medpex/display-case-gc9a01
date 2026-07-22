/*
 * PLASMA  -  ESP32-C3 Super Mini + GC9A01 (240x240 round)
 * Old-school full-color plasma: four overlaid sine fields mapped through
 * a rotating HSV palette. Flicker-free (full-frame canvas). No WiFi needed.
 *
 * Wiring: SCK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Flash: arduino-cli compile --upload -p <port> \
 *   --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" esp32_plasma
 */
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include <SPI.h>
#include <math.h>

#define TFT_SCK 4
#define TFT_MOSI 6
#define TFT_RST 5
#define TFT_DC  7
#define TFT_CS  10

#define BLOCK 6                   // px per plasma cell (6 -> 40x40 grid)
#define HUE_DRIFT 14.0f           // deg hue rotation per second
#define TIME_SCALE 0.9f           // overall animation speed

Adafruit_GC9A01A tft(TFT_CS, TFT_DC, TFT_RST);
GFXcanvas16 cv(240, 240);

static uint16_t hsv565(float h, float s, float v) {
  h = fmodf(h, 360); if (h < 0) h += 360;
  float c = v * s, x = c * (1 - fabsf(fmodf(h / 60.0f, 2) - 1)), m = v - c, r, g, b;
  if (h < 60) { r=c; g=x; b=0; } else if (h < 120) { r=x; g=c; b=0; }
  else if (h < 180) { r=0; g=c; b=x; } else if (h < 240) { r=0; g=x; b=c; }
  else if (h < 300) { r=x; g=0; b=c; } else { r=c; g=0; b=x; }
  uint8_t R=(r+m)*255, G=(g+m)*255, B=(b+m)*255;
  return ((R & 0xF8) << 8) | ((G & 0xFC) << 3) | (B >> 3);
}

void setup() {
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.begin(); tft.setRotation(0); tft.fillScreen(0x0000);
  cv.fillScreen(0x0000);
}

void loop() {
  float t = millis() / 1000.0f * TIME_SCALE;
  float hueBase = t * HUE_DRIFT;

  for (int y = 0; y < 240; y += BLOCK) {
    for (int x = 0; x < 240; x += BLOCK) {
      int dx = x + BLOCK / 2 - 120, dy = y + BLOCK / 2 - 120;
      if (dx * dx + dy * dy > 120 * 120) continue;       // outside round panel
      float d = sqrtf((float)(dx * dx + dy * dy));
      // four classic plasma terms: two axis waves, one diagonal, one radial
      float v = sinf(x * 0.052f + t)
              + sinf(y * 0.047f - t * 1.3f)
              + sinf((x + y) * 0.031f + t * 0.7f)
              + sinf(d * 0.058f - t * 1.8f);
      float n = (v + 4.0f) / 8.0f;                        // 0..1
      cv.fillRect(x, y, BLOCK, BLOCK, hsv565(hueBase + n * 300.0f, 0.95f, 0.35f + 0.65f * n));
    }
  }
  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
}
