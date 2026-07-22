/*
 * WARP STARFIELD  -  ESP32-C3 Super Mini + GC9A01 (240x240 rund)
 * Flimmerfreies Warp-Feld (Vollbild-Canvas). Kein WLAN noetig.
 *
 * Verkabelung: SCK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Flash: arduino-cli compile --upload -p <port> \
 *   --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" esp32_starfield
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

#define NUM_STARS 140
#define CX 120
#define CY 120
#define MAX_DEPTH 128.0f
#define SPEED 1.9f
#define SPAWN 10.0f   // Startradius im 3D-Raum

Adafruit_GC9A01A tft(TFT_CS, TFT_DC, TFT_RST);
GFXcanvas16 cv(240, 240);

struct Star { float x, y, z; };
Star stars[NUM_STARS];
uint32_t seed = 0x12345678;

// deterministischer PRNG (kein Math.random-Aequivalent noetig)
float frnd() {
  seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
  return (seed & 0xFFFFFF) / (float)0xFFFFFF;
}

void respawn(Star &s) {
  s.x = (frnd() * 2 - 1) * SPAWN;
  s.y = (frnd() * 2 - 1) * SPAWN;
  s.z = MAX_DEPTH;
}

uint16_t shade(float z) {
  float b = 1.0f - (z / MAX_DEPTH);       // nah = hell
  if (b < 0) b = 0; if (b > 1) b = 1;
  uint8_t v = (uint8_t)(b * 255);
  // leichter Blaustich in der Ferne
  uint8_t r = v, g = v, bl = (uint8_t)(v * 0.6f + 100 * (1 - b));
  return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (bl >> 3);
}

void setup() {
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.begin(); tft.setRotation(0); tft.fillScreen(0x0000);
  for (int i = 0; i < NUM_STARS; i++) { respawn(stars[i]); stars[i].z = frnd() * MAX_DEPTH; }
}

void loop() {
  cv.fillScreen(0x0000);
  for (int i = 0; i < NUM_STARS; i++) {
    Star &s = stars[i];
    float pz = s.z;
    s.z -= SPEED;
    if (s.z <= 1) { respawn(s); continue; }

    float k = 120.0f / s.z, pk = 120.0f / pz;
    int x  = CX + (int)(s.x * k),  y  = CY + (int)(s.y * k);
    int px = CX + (int)(s.x * pk), py = CY + (int)(s.y * pk);
    if (x < 0 || x > 239 || y < 0 || y > 239) { respawn(s); continue; }

    uint16_t c = shade(s.z);
    cv.drawLine(px, py, x, y, c);          // Warp-Strich
    if (s.z < MAX_DEPTH * 0.4f) cv.drawPixel(x, y, 0xFFFF);  // heller Kopf nah
  }
  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
}
