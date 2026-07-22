/*
 * MEGA CLOCK  -  ESP32-C3 Super Mini + GC9A01 (240x240 round)
 * Smooth analog clock, flicker-free (full-frame canvas).
 *
 * Time source: WiFi + NTP. On first boot the ESP opens a WiFi setup
 * hotspot ("MegaClock-Setup"); connect to it with a phone/laptop and pick
 * your network. Time then stays correct via NTP. If no WiFi is configured
 * or reachable, it falls back to the compile-time epoch (offline clock).
 *
 * Wiring: SCK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Libraries: Adafruit GFX, Adafruit GC9A01A, WiFiManager (tzapu)
 *
 * Flash (self-compile):
 *   arduino-cli compile --upload -p <port> \
 *     --fqbn "esp32:esp32:esp32c3:CDCOnBoot=cdc,FlashSize=4M" \
 *     --build-property "compiler.cpp.extra_flags=-DBUILD_EPOCH=$(date +%s)UL" \
 *     esp32_clock
 */
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <sys/time.h>
#include <time.h>
#include <math.h>

// ---- Display pins ----
#define TFT_SCK 4
#define TFT_MOSI 6
#define TFT_RST 5
#define TFT_DC  7
#define TFT_CS  10
#define LED_PIN 8

// ---- Time / network config ----
#define WIFI_AP_NAME        "MegaClock-Setup"   // hotspot SSID for first-time setup
#define WIFI_PORTAL_TIMEOUT 180                 // s: portal stays open, then falls back
#define NTP_SERVER_1        "pool.ntp.org"
#define NTP_SERVER_2        "time.google.com"
#define TZ_BERLIN           "CET-1CEST,M3.5.0,M10.5.0/3"  // Europe/Berlin incl. DST
#define NTP_WAIT_MS         15000UL             // max wait for first NTP sync
#define NTP_MIN_VALID_EPOCH 1735689600UL        // 2025-01-01, "time is real" threshold

#ifndef BUILD_EPOCH
#define BUILD_EPOCH 1721390000
#endif
#define BOOT_COMP 6   // seconds compensation for upload+boot (fallback path only)

Adafruit_GC9A01A tft(TFT_CS, TFT_DC, TFT_RST);
GFXcanvas16 cv(240, 240);

static const int16_t CX = 120, CY = 120;
static const float DEG = M_PI / 180.0f;
const char* WD[7] = {"SON","MON","DIE","MIT","DON","FRE","SAM"};
const char* MO[12]= {"Jan","Feb","Mar","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"};

uint16_t hsv565(float h, float s, float v) {
  h = fmodf(h, 360); if (h < 0) h += 360;
  float c = v * s, x = c * (1 - fabsf(fmodf(h / 60.0f, 2) - 1)), m = v - c, r, g, b;
  if (h < 60) { r=c; g=x; b=0; } else if (h < 120) { r=x; g=c; b=0; }
  else if (h < 180) { r=0; g=c; b=x; } else if (h < 240) { r=0; g=x; b=c; }
  else if (h < 300) { r=x; g=0; b=c; } else { r=c; g=0; b=x; }
  uint8_t R=(r+m)*255, G=(g+m)*255, B=(b+m)*255;
  return ((R & 0xF8) << 8) | ((G & 0xFC) << 3) | (B >> 3);
}

void hand(float ang, float len, float w, float tail, uint16_t col) {
  float a = (ang - 90) * DEG, ca = cosf(a), sa = sinf(a), px = -sa, py = ca;
  float tx = CX + ca * len, ty = CY + sa * len;
  float b1x = CX + px * w - ca * tail, b1y = CY + py * w - sa * tail;
  float b2x = CX - px * w - ca * tail, b2y = CY - py * w - sa * tail;
  cv.fillTriangle(tx, ty, b1x, b1y, b2x, b2y, col);
}

void drawFace(float hueBase) {
  cv.fillScreen(0x0000);
  cv.fillCircle(CX, CY, 119, 0x0841);
  cv.fillCircle(CX, CY, 113, 0x0000);
  for (int i = 0; i < 60; i++) {
    float a = (i * 6 - 90) * DEG, ca = cosf(a), sa = sinf(a);
    bool maj = (i % 5 == 0);
    float ri = maj ? 96 : 104, ro = 112;
    uint16_t c = maj ? hsv565(hueBase, 0.6, 1.0) : 0x39C7;
    cv.drawLine(CX + ca * ri, CY + sa * ri, CX + ca * ro, CY + sa * ro, c);
    if (maj) cv.drawLine(CX + ca * ri + 1, CY + sa * ri, CX + ca * ro + 1, CY + sa * ro, c);
  }
}

// Center a text line on the canvas at a given y (size-1 font = 6px/char).
void centerText(const char* s, int16_t y, uint16_t col) {
  int w = strlen(s) * 6;
  cv.setTextSize(1); cv.setTextColor(col);
  cv.setCursor(CX - w / 2, y); cv.print(s);
}

// Simple boot/setup message screen (used while the WiFi portal is open).
void showMessage(const char* l1, const char* l2, const char* l3) {
  cv.fillScreen(0x0000);
  cv.fillCircle(CX, CY, 119, 0x0841);
  cv.fillCircle(CX, CY, 113, 0x0000);
  if (l1) centerText(l1, CY - 24, hsv565(200, 0.4, 1.0));
  if (l2) centerText(l2, CY -  4, 0xFFFF);
  if (l3) centerText(l3, CY + 16, 0x8C71);
  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
}

// Set the RTC to the compile-time epoch as an offline fallback.
void setFallbackTime() {
  struct timeval tv; tv.tv_sec = (time_t)BUILD_EPOCH + BOOT_COMP; tv.tv_usec = 0;
  settimeofday(&tv, NULL);
}

// True once the system clock holds a plausible (post-2025) time.
bool timeIsReal() {
  time_t now = time(NULL);
  return (uint32_t)now >= NTP_MIN_VALID_EPOCH;
}

// Blocking WiFi setup + first NTP sync. Draws status on the TFT.
// Always returns; on failure the clock keeps the fallback time.
void syncTime() {
  setenv("TZ", TZ_BERLIN, 1); tzset();
  setFallbackTime();

  showMessage("WiFi Setup", "join hotspot:", WIFI_AP_NAME);

  WiFiManager wm;
  wm.setConfigPortalTimeout(WIFI_PORTAL_TIMEOUT);
  wm.setConnectTimeout(20);
  bool connected = wm.autoConnect(WIFI_AP_NAME);

  if (!connected) {
    showMessage("No WiFi", "offline mode", "compile-time clock");
    delay(1500);
    return;
  }

  showMessage("WiFi OK", "syncing time", "NTP...");
  configTzTime(TZ_BERLIN, NTP_SERVER_1, NTP_SERVER_2);

  uint32_t t0 = millis();
  while (!timeIsReal() && (millis() - t0) < NTP_WAIT_MS) {
    delay(200);
  }
  // SNTP keeps re-syncing in the background from here on.
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.begin(); tft.setRotation(0); tft.fillScreen(0x0000);

  syncTime();
}

void loop() {
  struct timeval tv; gettimeofday(&tv, NULL);
  struct tm lt; localtime_r(&tv.tv_sec, &lt);
  float ms = tv.tv_usec / 1000000.0f;
  float sec = lt.tm_sec + ms, mn = lt.tm_min + sec / 60.0f, hr = (lt.tm_hour % 12) + mn / 60.0f;
  float hue = fmodf(millis() / 120.0f, 360.0f);

  drawFace(hue);
  cv.setTextSize(2); cv.setTextColor(hsv565(hue, 0.3, 1.0));
  cv.setCursor(CX - 11, CY - 88); cv.print("12");
  cv.setCursor(CX + 78, CY - 8);  cv.print("3");
  cv.setCursor(CX - 5, CY + 74);  cv.print("6");
  cv.setCursor(CX - 86, CY - 8);  cv.print("9");

  char buf[24];
  cv.setTextSize(1); cv.setTextColor(0x8C71);
  snprintf(buf, sizeof(buf), "%s %02d.%s", WD[lt.tm_wday], lt.tm_mday, MO[lt.tm_mon]);
  int w = strlen(buf) * 6; cv.setCursor(CX - w / 2, CY - 52); cv.print(buf);

  for (int i = 0; i < (int)sec; i++) {
    float a = (i * 6 - 90) * DEG;
    cv.drawPixel(CX + cosf(a) * 88, CY + sinf(a) * 88, hsv565(hue + 120, 0.9, 0.9));
  }

  hand(hr * 30, 56, 6, 14, hsv565(hue, 0.15, 1.0));
  hand(mn * 6,  84, 4, 16, hsv565(hue, 0.15, 1.0));
  hand(sec * 6, 92, 1.6, 22, hsv565(20, 1.0, 1.0));

  cv.fillCircle(CX, CY, 7, hsv565(hue, 0.9, 1.0));
  cv.fillCircle(CX, CY, 3, 0x0000);

  cv.setTextSize(2); cv.setTextColor(hsv565(hue, 0.5, 1.0));
  snprintf(buf, sizeof(buf), "%02d:%02d:%02d", lt.tm_hour, lt.tm_min, lt.tm_sec);
  w = strlen(buf) * 12; cv.setCursor(CX - w / 2, CY + 40); cv.print(buf);

  tft.drawRGBBitmap(0, 0, cv.getBuffer(), 240, 240);
  digitalWrite(LED_PIN, (lt.tm_sec & 1) ? LOW : HIGH);
}
