/*
 * GC9A01 HUD  -  ESP32-C3 Super Mini + GC9A01 (240x240 round)
 * Rotating info display: Clock | Weather | Sun/Daylight | Date  (+ AURORA show)
 *
 * White-label build — contains NO personal data. WiFi, location and timezone are
 * configured by the end user through a captive-portal on first boot:
 *   1) Flash, then power the device.
 *   2) It opens a WiFi hotspot "GC9A01-HUD-Setup" — join it with a phone/laptop.
 *   3) Pick your WiFi and (optionally) set City / Latitude / Longitude / Timezone.
 *   4) Settings are stored in flash (NVS); the clock/weather then run via NTP + Open-Meteo.
 * To change WiFi or location later: erase flash and re-flash, or hold no button —
 * simply re-open the portal by flashing again.
 *
 * Weather: Open-Meteo (no API key). Time: NTP. No cloud account, no telemetry.
 *
 * Wiring: SCLK=4  MOSI=6  RST=5  DC=7  CS=10  VCC=3V3  GND=GND  (BLK=3V3)
 * Libraries: GFX Library for Arduino, ArduinoJson, WiFiManager (tzapu)
 * Build: arduino-cli ... --fqbn esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=huge_app
 */

#include <Arduino_GFX_Library.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <WiFiManager.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>
#include <sys/time.h>
#include <math.h>

// loopTask stack bump (inline TLS fetch needs headroom)
SET_LOOP_TASK_STACK_SIZE(16 * 1024);

// ---------- Pins ----------
static const int8_t PIN_SCLK = 4, PIN_MOSI = 6, PIN_RST = 5, PIN_DC = 7, PIN_CS = 10;

// ---------- WiFi setup portal ----------
static const char* AP_NAME = "GC9A01-HUD-Setup";   // hotspot SSID shown on first boot
static const uint16_t PORTAL_TIMEOUT_S = 180;       // portal stays open, then falls back

// ---------- NTP ----------
static const char* NTP1 = "pool.ntp.org", *NTP2 = "time.google.com", *NTP3 = "time.nist.gov";
static const uint32_t RESYNC_MS = 3600000UL;

// ---------- Location / timezone DEFAULTS (user-overridable via portal, stored in NVS) ----------
// If you self-compile you can change these; end users set them in the setup portal.
static const char* DEF_CITY = "BERLIN";
static const char* DEF_LAT  = "52.5200";
static const char* DEF_LON  = "13.4050";
static const char* DEF_TZ   = "CET-1CEST,M3.5.0,M10.5.0/3";   // POSIX TZ (Europe/Berlin incl. DST)

// runtime config (loaded from NVS or defaults)
char cfgCity[24], cfgLat[16], cfgLon[16], cfgTz[48];
char wxUrl[352];                 // built from cfgLat/cfgLon at boot
Preferences prefs;
bool shouldSaveCfg = false;

// ---------- Weather refresh ----------
static const uint32_t WX_REFRESH_MS = 900000UL;   // 15 min
static const uint32_t WX_RETRY_MS   = 30000UL;    // error retry
static const int FORECAST_STORE = 48;             // hours kept
static const int SPARK_HOURS = 12;                // hours shown
static const size_t MIN_HEAP_FETCH = 45000;       // below this: skip fetch

// ---------- Operation ----------
static const int DAILY_REBOOT_HOUR = 4;
static const uint16_t TRANSITION_MS = 280;

// ---------- Geometry ----------
static const int16_t CX = 120, CY = 120, R = 120;
static const uint32_t SPI_HZ = 40000000UL;

// ---------- Display ----------
Arduino_DataBus *bus = new Arduino_HWSPI(PIN_DC, PIN_CS, PIN_SCLK, PIN_MOSI, GFX_NOT_DEFINED);
Arduino_GFX *panel   = new Arduino_GC9A01(bus, PIN_RST, 0, true);

// Framebuffer statically in .bss (the C3's largest contiguous heap block is too small
// for a 115 KB canvas malloc -> would crash-loop). Canvas begin() then allocates nothing.
static uint16_t FRAMEBUF[240 * 240];
class StaticCanvas : public Arduino_Canvas {
public:
  StaticCanvas(int16_t w, int16_t h, Arduino_G *output, uint16_t *buf)
      : Arduino_Canvas(w, h, output) { _framebuffer = buf; }
};
Arduino_Canvas *gfx = new StaticCanvas(240, 240, panel, FRAMEBUF);
bool gfxOk = false;

// ---------- Colors (LUMEN) ----------
uint16_t L_INK, L_WELL, L_WELL_D, L_STEEL, L_STEELD, L_HAIR, L_IVORY,
         L_AMBER, L_AMBER_M, L_ICE, L_ICE_D, L_ALERT, L_ALERT_D, L_GREEN;

// ---------- Weather model ----------
struct Weather {
  bool valid = false;
  float t = 0, tmax = 0, tmin = 0, wind = 0;
  int hum = 0, code = -1;
  char sunrise[6] = "--:--", sunset[6] = "--:--";
  int8_t hourly[FORECAST_STORE];
};
Weather wx;
uint32_t wxNext = 0;
int wxErr = 0;

// ---------- State ----------
bool timeValid = false;
uint32_t lastResync = 0, screenStart = 0, reconnectLast = 0;
uint8_t screen = 0;
bool rebootedToday = false;
uint32_t transStart = 0; bool inTransition = false;

static const char* WD[] = {"Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"};
static const char* MO[] = {"Jan","Feb","Maerz","April","Mai","Juni","Juli","Aug","Sep","Okt","Nov","Dez"};

// ================= drawing helpers =================
static inline void polar(float deg, float len, float &x, float &y) {
  float r = deg * (float)M_PI / 180.0f;
  x = CX + sinf(r) * len; y = CY - cosf(r) * len;
}
static int textW(const char* s, uint8_t sz) { return (int)strlen(s) * 6 * sz; }
static int printAt(int x, int yTop, const char* s, uint8_t sz, uint16_t col) {
  gfx->setTextColor(col); gfx->setTextSize(sz); gfx->setCursor(x, yTop); gfx->print(s);
  return x + textW(s, sz);
}
static void centerText(int cx, int cy, const char* s, uint8_t sz, uint16_t col) {
  printAt(cx - textW(s, sz) / 2, cy - 4 * sz, s, sz, col);
}
static void degMark(int x, int yTop, uint8_t sz, uint16_t col) { gfx->drawCircle(x + 2*sz, yTop + 2*sz, sz, col); }

static inline float easeOutCubic(float t) { float f = t-1.0f; return f*f*f + 1.0f; }
static void drawIrisMask(float p) {
  int rVis = (int)(128 * easeOutCubic(p));
  for (int r = 128; r > rVis; r--) gfx->drawCircle(CX, CY, r, L_INK);
}
static void drawBase() {
  gfx->fillScreen(L_INK);
  gfx->fillCircle(CX, CY, 118, L_WELL);
  gfx->drawCircle(CX, CY, 116, L_STEELD);
}
static void eyebrow(const char* s, uint16_t col) { centerText(120, 30, s, 1, col); }
static void navPips(int active, int n) {
  int sp = 10, y = 214, x0 = CX - (n-1)*sp/2;
  for (int i = 0; i < n; i++) gfx->fillCircle(x0+i*sp, y, i==active?3:2, i==active?L_AMBER:L_STEEL);
}

// ================= time / holiday =================
static bool getNow(struct tm &ti, float &subsec) {
  struct timeval tv; gettimeofday(&tv, NULL);
  time_t t = tv.tv_sec; localtime_r(&t, &ti);
  subsec = tv.tv_usec / 1000000.0f;
  return ti.tm_year > (2020 - 1900);
}
static long daysUntil(int y, int mon, int d) {
  struct timeval tv; gettimeofday(&tv, NULL);
  time_t now = tv.tv_sec; struct tm n; localtime_r(&now, &n);
  n.tm_hour = n.tm_min = n.tm_sec = 0;
  time_t nowMid = mktime(&n);
  struct tm tgt = {0}; tgt.tm_year = y-1900; tgt.tm_mon = mon-1; tgt.tm_mday = d; tgt.tm_isdst = -1;
  return (long)round(difftime(mktime(&tgt), nowMid) / 86400.0);
}
static int hhmmToMin(const char* s) { int h,m; if (sscanf(s, "%d:%d", &h, &m) == 2) return h*60+m; return -1; }

static void easter(int y, int &mon, int &day) {
  int a=y%19,b=y/100,c=y%100,d=b/4,e=b%4,f=(b+8)/25,g=(b-f+1)/3;
  int h=(19*a+b-d-g+15)%30,i=c/4,k=c%4,l=(32+2*e+2*i-h-k)%7,m=(a+11*h+22*l)/451;
  mon=(h+l-7*m+114)/31; day=((h+l-7*m+114)%31)+1;
}
static const char* holiday(const struct tm &ti) {
  int y=ti.tm_year+1900, m=ti.tm_mon+1, d=ti.tm_mday;
  if (m==1&&d==1) return "Neujahr";
  if (m==5&&d==1) return "Tag der Arbeit";
  if (m==10&&d==3) return "Tag dt. Einheit";
  if (m==12&&d==25) return "1. Weihnacht";
  if (m==12&&d==26) return "2. Weihnacht";
  int em,ed; easter(y,em,ed); long diff = -daysUntil(y,em,ed);
  if (diff==-2) return "Karfreitag";
  if (diff==1)  return "Ostermontag";
  if (diff==39) return "Himmelfahrt";
  if (diff==50) return "Pfingstmontag";
  return nullptr;
}

// ================= weather fetch =================
static void extractHHMM(const char* iso, char out[6]) {
  const char* t = strchr(iso, 'T');
  if (t && strlen(t+1) >= 5) { memcpy(out, t+1, 5); out[5] = '\0'; }
}
static bool fetchWeather() {
  if (WiFi.status() != WL_CONNECTED) { wxErr = -1; return false; }
  if (ESP.getFreeHeap() < MIN_HEAP_FETCH) { wxErr = -4; return false; }
  WiFiClientSecure client; client.setInsecure();
  HTTPClient http; http.setConnectTimeout(6000); http.setTimeout(6000);
  if (!http.begin(client, wxUrl)) { wxErr = -2; return false; }
  int code = http.GET(); wxErr = code;
  bool ok = false;
  if (code == 200) {
    String payload = http.getString();
    JsonDocument doc;
    if (!deserializeJson(doc, payload)) {
      wx.t    = doc["current"]["temperature_2m"]     | 0.0f;
      wx.hum  = doc["current"]["relative_humidity_2m"]| 0;
      wx.code = doc["current"]["weather_code"]        | -1;
      wx.wind = doc["current"]["wind_speed_10m"]      | 0.0f;
      wx.tmax = doc["daily"]["temperature_2m_max"][0] | 0.0f;
      wx.tmin = doc["daily"]["temperature_2m_min"][0] | 0.0f;
      extractHHMM(doc["daily"]["sunrise"][0] | "", wx.sunrise);
      extractHHMM(doc["daily"]["sunset"][0]  | "", wx.sunset);
      JsonArray h = doc["hourly"]["temperature_2m"];
      for (int i = 0; i < FORECAST_STORE; i++)
        wx.hourly[i] = (i < (int)h.size()) ? (int8_t)roundf(h[i].as<float>()) : 0;
      wx.valid = true; ok = true;
    } else wxErr = -3;
  }
  http.end();
  Serial.printf("[wx] ok=%d err=%d heap=%u\n", ok, wxErr, ESP.getFreeHeap());
  return ok;
}

// ================= weather icons =================
static const char* wxLabel(int c) {
  if (c==0) return "Klar"; if (c==1) return "Heiter"; if (c==2) return "Wolkig"; if (c==3) return "Bedeckt";
  if (c==45||c==48) return "Nebel"; if (c>=51&&c<=57) return "Niesel"; if (c>=61&&c<=67) return "Regen";
  if (c>=71&&c<=77) return "Schnee"; if (c>=80&&c<=82) return "Schauer"; if (c>=85&&c<=86) return "Schneeschauer";
  if (c>=95) return "Gewitter"; return "--";
}
static void drawWxIcon(int cx, int cy, int c) {
  bool rain=(c>=51&&c<=67)||(c>=80&&c<=82)||c>=95, snow=(c>=71&&c<=77)||(c>=85&&c<=86);
  bool cloud=(c>=2&&c<=48)||rain||snow, sun=(c<=1);
  if (sun) {
    for (int a=0;a<360;a+=45){ float x1,y1,x2,y2; polar(a,11,x1,y1); polar(a,16,x2,y2);
      gfx->drawLine(cx+(x1-CX),cy+(y1-CY),cx+(x2-CX),cy+(y2-CY),L_AMBER);}
    gfx->fillCircle(cx,cy,9,L_AMBER); return;
  }
  if (c==1) gfx->fillCircle(cx+9,cy-7,6,L_AMBER);
  if (cloud){ gfx->fillCircle(cx-7,cy,7,L_IVORY); gfx->fillCircle(cx+5,cy-3,9,L_IVORY);
    gfx->fillCircle(cx+11,cy+2,6,L_IVORY); gfx->fillRect(cx-11,cy+2,24,7,L_IVORY);}
  if (rain) for (int i=-1;i<=1;i++) gfx->drawLine(cx+i*7,cy+11,cx+i*7-3,cy+18,L_ICE);
  if (snow) for (int i=-1;i<=1;i++) gfx->fillCircle(cx+i*7,cy+15,2,L_ICE);
}

// ================= screens =================
static void screenClock(const struct tm &ti, float subsec) {
  char eb[36]; snprintf(eb, sizeof(eb), "%s . %d. %s", WD[ti.tm_wday], ti.tm_mday, MO[ti.tm_mon]);
  eyebrow(eb, L_STEEL);
  char t[8]; snprintf(t, sizeof(t), "%02d:%02d", ti.tm_hour, ti.tm_min);
  centerText(120, 102, t, 6, L_IVORY);
  int bx=60, by=150, bw=120;
  gfx->fillRoundRect(bx, by, bw, 4, 2, L_HAIR);
  float sf = (ti.tm_sec + subsec) / 60.0f; int fw = (int)(sf * bw);
  if (fw > 0) gfx->fillRoundRect(bx, by, fw, 4, 2, L_ICE);
  char kw[10]; strftime(kw, sizeof(kw), "KW %V", &ti); centerText(120, 176, kw, 1, L_STEEL);
  navPips(0, 4);
}

static void screenWeather(const struct tm &ti, float subsec) {
  (void)subsec;
  eyebrow(cfgCity, L_STEEL);
  if (!wx.valid){ centerText(120,104,"WETTER LAEDT",2,L_AMBER);
    char e[20]; snprintf(e,sizeof(e),"http=%d",wxErr); centerText(120,132,e,1,L_STEEL); navPips(1,4); return; }
  char t[6]; snprintf(t,sizeof(t),"%.0f",wx.t);
  int w=textW(t,6), sx=86-w/2, yt=96-24;
  int ex=printAt(sx,yt,t,6,L_IVORY); degMark(ex,yt,3,L_IVORY);
  centerText(86,132,wxLabel(wx.code),1,L_STEEL);
  drawWxIcon(172,80,wx.code);
  int x0=44,x1=196,y0=150,y1=182,start=ti.tm_hour, lo=127,hi=-127;
  for (int i=0;i<SPARK_HOURS;i++){ int v=wx.hourly[(start+i)%FORECAST_STORE]; if(v<lo)lo=v; if(v>hi)hi=v; }
  if (hi==lo) hi=lo+1;
  int pxs[SPARK_HOURS], pys[SPARK_HOURS];
  for (int i=0;i<SPARK_HOURS;i++){ int v=wx.hourly[(start+i)%FORECAST_STORE];
    pxs[i]=x0+i*(x1-x0)/(SPARK_HOURS-1); pys[i]=y1-(v-lo)*(y1-y0)/(hi-lo); }
  for (int i=0;i<SPARK_HOURS-1;i++){ gfx->drawLine(pxs[i],pys[i]+1,pxs[i+1],pys[i+1]+1,L_ICE_D);
    gfx->drawLine(pxs[i],pys[i],pxs[i+1],pys[i+1],L_ICE); }
  gfx->fillCircle(pxs[SPARK_HOURS-1],pys[SPARK_HOURS-1],3,L_AMBER);
  char hh[6]; snprintf(hh,sizeof(hh),"%d",hi); printAt(x0,y0-8,hh,1,L_STEEL);
  char ll[6]; snprintf(ll,sizeof(ll),"%d",lo); printAt(x0,y1+3,ll,1,L_STEEL);
  navPips(1,4);
}

static void screenSun(const struct tm &ti, float subsec) {
  (void)subsec;
  eyebrow("SONNE", L_STEEL);
  gfx->fillRect(0, 150, 240, 90, L_WELL_D);
  gfx->drawFastHLine(20, 150, 200, L_STEEL);
  int prevx=40, prevy=150;
  for (int x=40; x<=200; x+=4){ float nx=(x-120)/80.0f; int yy=150-(int)((1.0f-nx*nx)*88.0f);
    gfx->drawLine(prevx,prevy+1,x,yy+1,L_AMBER_M); gfx->drawLine(prevx,prevy,x,yy,L_AMBER); prevx=x; prevy=yy; }
  int sr=hhmmToMin(wx.sunrise), ss=hhmmToMin(wx.sunset);
  if (wx.valid && sr>0 && ss>sr){
    int now=ti.tm_hour*60+ti.tm_min; float f=constrain((float)(now-sr)/(ss-sr),0.0f,1.0f);
    int sxp=40+(int)(f*160); float nx=(sxp-120)/80.0f; int syp=150-(int)((1.0f-nx*nx)*88.0f);
    bool day=(now>=sr && now<=ss); uint16_t sc=day?L_AMBER:L_STEEL;
    for (int a=0;a<360;a+=45){ float x1,y1,x2,y2; polar(a,9,x1,y1); polar(a,13,x2,y2);
      gfx->drawLine(sxp+(x1-CX),syp+(y1-CY),sxp+(x2-CX),syp+(y2-CY),sc); }
    gfx->fillCircle(sxp,syp,6,sc); gfx->fillCircle(sxp,syp,3,L_IVORY);
  }
  if (sr>0 && ss>sr){ int len=ss-sr; char dl[8]; snprintf(dl,sizeof(dl),"%d:%02d",len/60,len%60);
    centerText(120,112,dl,5,L_IVORY); }
  else centerText(120,112,"--:--",5,L_STEEL);
  centerText(120,136,"TAGESLICHT",1,L_STEEL);
  printAt(46,166,wx.sunrise,1,L_IVORY); printAt(196-textW(wx.sunset,1),166,wx.sunset,1,L_IVORY);
  centerText(52,178,"auf",1,L_STEEL); centerText(190,178,"unter",1,L_STEEL);
  navPips(2,4);
}

static void screenDate(const struct tm &ti, float subsec) {
  (void)subsec;
  eyebrow("HEUTE", L_STEEL);
  const char* hn = holiday(ti);
  if (hn) centerText(120,50,hn,1,L_AMBER);
  centerText(120,72,WD[ti.tm_wday],2,L_IVORY);
  char dd[4]; snprintf(dd,sizeof(dd),"%d",ti.tm_mday); centerText(120,118,dd,7,L_IVORY);
  char my[16]; snprintf(my,sizeof(my),"%s %d",MO[ti.tm_mon],ti.tm_year+1900); centerText(120,162,my,1,L_STEEL);
  char kwb[4]; strftime(kwb,sizeof(kwb),"%V",&ti); int kw=atoi(kwb);
  int x0=44,x1=196,y=184;
  for (int w=1; w<=52; w++){ int x=x0+(w-1)*(x1-x0)/51; bool on=(w==kw);
    gfx->drawFastVLine(x, on?y-5:y-2, on?7:4, on?L_AMBER:L_STEEL); }
  char kl[10]; snprintf(kl,sizeof(kl),"KW %d",kw); centerText(120,200,kl,1,L_STEEL);
  navPips(3,4);
}

// ================= AURORA — random show (>=1x/h, 50 s) =================
static const uint32_t AURORA_MS = 50000UL;
static bool     aurActive = false;
static uint32_t aurStart  = 0;
static int      aurHour   = -1, aurAtSec = 0;
static bool     aurFired  = false, aurInit = false;
static uint32_t aurSeed   = 0x1234ABCDu;
static float frnd() { aurSeed = aurSeed*1664525u + 1013904223u; return (float)((aurSeed>>9)&0xFFFF)/65535.0f; }

static const int STAR_N = 120;
static float starX[STAR_N], starY[STAR_N], starZ[STAR_N];
static void auroraEnter() { aurActive = true; aurStart = millis(); aurInit = false; aurSeed ^= millis()*2654435761u; }
static void starInit() { for (int i=0;i<STAR_N;i++){ starX[i]=frnd()*2-1; starY[i]=frnd()*2-1; starZ[i]=frnd()*0.9f+0.1f; } aurInit=true; }

static void fxStarfield(float t) {
  (void)t; gfx->fillScreen(L_INK);
  const float K = 92.0f;
  for (int i=0;i<STAR_N;i++){
    starZ[i]-=0.013f; if (starZ[i]<=0.05f){ starX[i]=frnd()*2-1; starY[i]=frnd()*2-1; starZ[i]=1.0f; }
    float sx=CX+starX[i]/starZ[i]*K, sy=CY+starY[i]/starZ[i]*K;
    float pz=starZ[i]+0.06f, pxp=CX+starX[i]/pz*K, pyp=CY+starY[i]/pz*K;
    float b=1.0f-starZ[i];
    uint16_t col = b>0.78f ? L_IVORY : b>0.42f ? L_ICE : L_ICE_D;
    gfx->drawLine(pxp,pyp,sx,sy,col);
    if (b>0.86f) gfx->fillCircle(sx,sy,1,L_AMBER);
  }
}
static void fxPlasma(float t) {
  const int bs=8;
  for (int y=0;y<240;y+=bs) for (int x=0;x<240;x+=bs){
    int dx=x+bs/2-CX, dy=y+bs/2-CY; if (dx*dx+dy*dy>118*118) continue;
    float d=sqrtf((float)(dx*dx+dy*dy));
    float v=sinf(x*0.045f+t)+sinf(y*0.05f-t*1.1f)+sinf((x+y)*0.03f+t*0.7f)+sinf(d*0.06f-t*1.6f);
    v=(v+4.0f)/8.0f;
    uint16_t col = v<0.35f?L_INK : v<0.55f?L_ICE_D : v<0.72f?L_ICE : v<0.88f?L_AMBER_M : L_AMBER;
    gfx->fillRect(x,y,bs,bs,col);
  }
}
static void fxLissajous(float t) {
  gfx->fillScreen(L_INK);
  const float A=94.0f, a=3.0f, b=2.0f, ph=t*0.6f, rot=t*0.32f; const int M=95;
  for (int i=0;i<M;i++){
    float p=t*2.2f - i*0.055f;
    float x=A*sinf(a*p+ph), y=A*sinf(b*p);
    float rx=x*cosf(rot)-y*sinf(rot), ry=x*sinf(rot)+y*cosf(rot);
    int sx=CX+(int)rx, sy=CY+(int)ry; float f=1.0f-(float)i/M;
    if (f>0.6f){ gfx->drawCircle(sx,sy,3,L_AMBER_M); gfx->fillCircle(sx,sy,2,L_AMBER); }
    else if (f>0.3f) gfx->fillCircle(sx,sy,1,L_ICE);
    else gfx->drawPixel(sx,sy,L_ICE_D);
  }
}
static void screenAurora() {
  if (!aurInit) starInit();
  uint32_t e=millis()-aurStart; float t=e/1000.0f;
  int phase=(e/16000UL)%3;
  if (phase==0) fxStarfield(t); else if (phase==1) fxPlasma(t); else fxLissajous(t);
  if (e<2600) centerText(120,120,"AURORA",3,L_IVORY);
  gfx->drawCircle(CX,CY,118,L_STEELD);
}

// ---------- screen registry ----------
struct ScreenDef { void (*draw)(const struct tm&, float); uint32_t dwell; void (*onEnter)(); };
static const uint32_t DWELL_CLOCK_MS = 180000UL;  // clock: 3 min
static const uint32_t DWELL_OTHER_MS = 60000UL;   // others: 1 min
static const ScreenDef SCREENS[] = {
  { screenClock,   DWELL_CLOCK_MS, nullptr },
  { screenWeather, DWELL_OTHER_MS, nullptr },
  { screenSun,     DWELL_OTHER_MS, nullptr },
  { screenDate,    DWELL_OTHER_MS, nullptr },
};
static const uint8_t SCREEN_COUNT = sizeof(SCREENS)/sizeof(SCREENS[0]);

// ================= config (NVS) + WiFi portal =================
static void loadConfig() {
  prefs.begin("hud", true);
  strlcpy(cfgCity, prefs.getString("city", DEF_CITY).c_str(), sizeof(cfgCity));
  strlcpy(cfgLat,  prefs.getString("lat",  DEF_LAT ).c_str(), sizeof(cfgLat));
  strlcpy(cfgLon,  prefs.getString("lon",  DEF_LON ).c_str(), sizeof(cfgLon));
  strlcpy(cfgTz,   prefs.getString("tz",   DEF_TZ  ).c_str(), sizeof(cfgTz));
  prefs.end();
}
static void saveConfig() {
  prefs.begin("hud", false);
  prefs.putString("city", cfgCity); prefs.putString("lat", cfgLat);
  prefs.putString("lon", cfgLon);   prefs.putString("tz",  cfgTz);
  prefs.end();
}
static void buildWxUrl() {
  snprintf(wxUrl, sizeof(wxUrl),
    "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
    "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    "&hourly=temperature_2m"
    "&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset"
    "&timezone=auto&forecast_days=2", cfgLat, cfgLon);
}
static void onSaveCfg() { shouldSaveCfg = true; }

// Show a static message screen (used before/while the WiFi portal is open).
static void showSetupMsg(const char* l1, const char* l2, const char* l3) {
  if (!gfxOk) return;
  drawBase();
  if (l1) centerText(120, 92,  l1, 2, L_AMBER);
  if (l2) centerText(120, 124, l2, 1, L_IVORY);
  if (l3) centerText(120, 144, l3, 1, L_ICE);
  gfx->flush();
}

void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis(); while (!Serial && millis() - t0 < 1500) delay(10);

  bool pb = panel->begin(SPI_HZ);
  bool cb = gfx->begin(GFX_SKIP_OUTPUT_BEGIN);
  gfxOk = pb && cb && (gfx->getFramebuffer() != nullptr);
  L_INK   =gfx->color565(0x05,0x07,0x0A); L_WELL  =gfx->color565(0x12,0x1B,0x26); L_WELL_D=gfx->color565(0x0A,0x11,0x19);
  L_STEEL =gfx->color565(0x3B,0x4A,0x5A); L_STEELD=gfx->color565(0x21,0x2C,0x37); L_HAIR  =gfx->color565(0x16,0x1D,0x26);
  L_IVORY =gfx->color565(0xEA,0xF0,0xF6);
  L_AMBER =gfx->color565(0xFF,0xB2,0x24); L_AMBER_M=gfx->color565(0xB3,0x7A,0x16);
  L_ICE   =gfx->color565(0x35,0xD2,0xDE); L_ICE_D =gfx->color565(0x12,0x45,0x4A);
  L_ALERT =gfx->color565(0xFF,0x3B,0x30); L_ALERT_D=gfx->color565(0x52,0x14,0x11);
  L_GREEN =gfx->color565(0x22,0xE0,0x6A);

  for (int i=0;i<FORECAST_STORE;i++) wx.hourly[i]=0;

  loadConfig();

  // WiFi + optional location config via captive portal.
  showSetupMsg("WiFi Setup", "join hotspot:", AP_NAME);
  WiFiManager wm;
  WiFiManagerParameter pCity("city", "City (label)",     cfgCity, sizeof(cfgCity)-1);
  WiFiManagerParameter pLat ("lat",  "Latitude",         cfgLat,  sizeof(cfgLat)-1);
  WiFiManagerParameter pLon ("lon",  "Longitude",        cfgLon,  sizeof(cfgLon)-1);
  WiFiManagerParameter pTz  ("tz",   "Timezone (POSIX)", cfgTz,   sizeof(cfgTz)-1);
  wm.addParameter(&pCity); wm.addParameter(&pLat); wm.addParameter(&pLon); wm.addParameter(&pTz);
  wm.setSaveConfigCallback(onSaveCfg);
  wm.setConfigPortalTimeout(PORTAL_TIMEOUT_S);
  wm.setConnectTimeout(20);

  bool connected = wm.autoConnect(AP_NAME);

  if (shouldSaveCfg) {
    strlcpy(cfgCity, pCity.getValue(), sizeof(cfgCity));
    strlcpy(cfgLat,  pLat.getValue(),  sizeof(cfgLat));
    strlcpy(cfgLon,  pLon.getValue(),  sizeof(cfgLon));
    strlcpy(cfgTz,   pTz.getValue(),   sizeof(cfgTz));
    saveConfig();
  }

  buildWxUrl();
  setenv("TZ", cfgTz, 1); tzset();
  if (connected) {
    showSetupMsg("WiFi OK", "syncing time", "NTP...");
    configTzTime(cfgTz, NTP1, NTP2, NTP3);
  } else {
    showSetupMsg("No WiFi", "offline", "clock only after sync");
  }
  lastResync = millis(); screenStart = millis();
}

void loop() {
  uint32_t frameStart = millis();
  bool online = (WiFi.status() == WL_CONNECTED);

  if (!gfxOk) { delay(1000); return; }

  // light auto-reconnect if the link dropped (creds are stored by WiFiManager)
  if (!online && millis()-reconnectLast > 15000) { reconnectLast = millis(); WiFi.reconnect(); }

  if (online && millis()-lastResync > RESYNC_MS) { configTzTime(cfgTz, NTP1, NTP2, NTP3); lastResync=millis(); }
  if (online && millis() >= wxNext) { bool ok = fetchWeather(); wxNext = millis() + (ok ? WX_REFRESH_MS : WX_RETRY_MS); }

  struct tm ti; float subsec; timeValid = getNow(ti, subsec);
  if (timeValid){
    if (ti.tm_hour==DAILY_REBOOT_HOUR && !rebootedToday){ rebootedToday=true; ESP.restart(); }
    if (ti.tm_hour!=DAILY_REBOOT_HOUR) rebootedToday=false;
    if (ti.tm_hour != aurHour){ aurHour=ti.tm_hour; aurFired=false; aurAtSec=(int)(frnd()*(3600-60)); }
    int secOfHour = ti.tm_min*60 + ti.tm_sec;
    if (!aurFired && !aurActive && secOfHour>=aurAtSec){ aurFired=true; auroraEnter(); }
  }
  if (aurActive && millis()-aurStart >= AURORA_MS) aurActive=false;

  if (aurActive) { screenAurora(); gfx->flush(); uint32_t elA=millis()-frameStart; if (elA<30) delay(30-elA); return; }

  drawBase();

  if (!timeValid){
    centerText(120,98,"SYNC",3,L_IVORY);
    float a=(millis()%1500)/1500.0f*360.0f, sx,sy; polar(a,58,sx,sy); gfx->fillCircle(sx,sy,4,L_AMBER);
    centerText(120,150,online?"WLAN OK - warte NTP":"kein WLAN",1,online?L_ICE:L_AMBER);
  } else {
    if (millis()-screenStart > SCREENS[screen].dwell){
      screen=(screen+1)%SCREEN_COUNT; screenStart=millis();
      transStart=millis(); inTransition=true;
      if (SCREENS[screen].onEnter) SCREENS[screen].onEnter();
    }
    SCREENS[screen].draw(ti, subsec);
    if (inTransition){
      float p=(float)(millis()-transStart)/TRANSITION_MS;
      if (p>=1.0f) inTransition=false; else drawIrisMask(p);
    }
  }

  gfx->flush();
  uint32_t el = millis()-frameStart;
  if (el < 30) delay(30-el);
}
