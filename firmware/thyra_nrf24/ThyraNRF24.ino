/*
 * ThyraNRF24 - Serial command interface for nRF24L01+ on RF-Nano v3
 * Board: Arduino Nano (ATmega328P, CH340)
 * Baud: 115200
 *
 * Commands (newline-terminated):
 *   status               - show config JSON
 *   scan                 - scan all 128 channels for activity, JSON output
 *   sniff [channel]      - receive packets on channel (0-127), default 76
 *   sniff_stop           - stop sniffing
 *   set_channel <n>      - set RX channel (0-127)
 *   set_rate <r>         - set data rate: 250, 1000, 2000 (kbps)
 *   set_addr <hex>       - set RX address (10 hex chars, e.g. e7e7e7e7e7)
 *   tx <channel> <hex>   - transmit hex payload on channel
 *   help                 - list commands
 */

#include <SPI.h>
#include <RF24.h>

// RF-Nano v3: CE=D8, CSN=D9
RF24 radio(8, 9);

static bool sniffing = false;
static uint8_t current_channel = 76;
static uint32_t current_rate = RF24_1MBPS;
static uint8_t rx_addr[5] = {0xe7, 0xe7, 0xe7, 0xe7, 0xe7};

// ── Helpers ────────────────────────────────────────────────────────────────

bool hexToBytes(const char* hex, uint8_t* out, int len) {
  int hexlen = strlen(hex);
  if (hexlen != len * 2) return false;
  for (int i = 0; i < len; i++) {
    char hi = hex[i * 2], lo = hex[i * 2 + 1];
    auto nibble = [](char c) -> int {
      if (c >= '0' && c <= '9') return c - '0';
      if (c >= 'a' && c <= 'f') return c - 'a' + 10;
      if (c >= 'A' && c <= 'F') return c - 'A' + 10;
      return -1;
    };
    int h = nibble(hi), l = nibble(lo);
    if (h < 0 || l < 0) return false;
    out[i] = (h << 4) | l;
  }
  return true;
}

void printHex(const uint8_t* buf, int len) {
  for (int i = 0; i < len; i++) {
    if (buf[i] < 0x10) Serial.print("0");
    Serial.print(buf[i], HEX);
  }
}

const char* rateName() {
  if (current_rate == RF24_250KBPS) return "250KBPS";
  if (current_rate == RF24_2MBPS)   return "2MBPS";
  return "1MBPS";
}

void applyConfig() {
  radio.setChannel(current_channel);
  radio.setDataRate((rf24_datarate_e)current_rate);
  radio.openReadingPipe(1, rx_addr);
}

// ── Commands ───────────────────────────────────────────────────────────────

void doStatus() {
  Serial.print(F("{\"ready\":true,\"channel\":"));
  Serial.print(current_channel);
  Serial.print(F(",\"rate\":\""));
  Serial.print(rateName());
  Serial.print(F("\",\"addr\":\""));
  printHex(rx_addr, 5);
  Serial.print(F("\",\"sniffing\":"));
  Serial.print(sniffing ? "true" : "false");
  Serial.println(F(",\"version\":\"1.0\"}"));
}

void doScan() {
  sniffing = false;
  radio.stopListening();

  const int PASSES = 100;
  uint8_t hits[128] = {0};

  for (int pass = 0; pass < PASSES; pass++) {
    for (int ch = 0; ch < 128; ch++) {
      radio.setChannel(ch);
      radio.startListening();
      delayMicroseconds(200);
      radio.stopListening();
      if (radio.testCarrier()) hits[ch]++;
    }
  }

  // output channels with activity
  Serial.print(F("["));
  bool first = true;
  for (int ch = 0; ch < 128; ch++) {
    if (hits[ch] > 0) {
      if (!first) Serial.print(",");
      Serial.print(F("{\"ch\":"));
      Serial.print(ch);
      Serial.print(F(",\"freq_mhz\":"));
      Serial.print(2400 + ch);
      Serial.print(F(",\"hits\":"));
      Serial.print(hits[ch]);
      Serial.print(F(",\"pct\":"));
      Serial.print((hits[ch] * 100) / PASSES);
      Serial.print("}");
      first = false;
    }
  }
  Serial.println("]");

  // restore
  radio.setChannel(current_channel);
  radio.setDataRate((rf24_datarate_e)current_rate);
}

void startSniff(int ch) {
  current_channel = ch;
  applyConfig();
  radio.startListening();
  sniffing = true;
  Serial.print(F("{\"sniffing\":true,\"channel\":"));
  Serial.print(ch);
  Serial.print(F(",\"freq_mhz\":"));
  Serial.print(2400 + ch);
  Serial.println(F("}"));
}

void doTx(int ch, const char* hexdata) {
  uint8_t payload[32];
  int hexlen = strlen(hexdata);
  int paylen = hexlen / 2;
  if (paylen < 1 || paylen > 32 || !hexToBytes(hexdata, payload, paylen)) {
    Serial.println(F("{\"error\":\"bad hex payload\"}"));
    return;
  }

  bool was_sniffing = sniffing;
  sniffing = false;
  radio.stopListening();
  radio.setChannel(ch);

  uint8_t tx_addr[5];
  memcpy(tx_addr, rx_addr, 5);
  radio.openWritingPipe(tx_addr);

  bool ok = radio.write(payload, paylen);
  Serial.print(F("{\"tx\":\""));
  Serial.print(ok ? "ok" : "fail");
  Serial.print(F("\",\"channel\":"));
  Serial.print(ch);
  Serial.print(F(",\"bytes\":"));
  Serial.print(paylen);
  Serial.println(F("}"));

  // restore
  radio.setChannel(current_channel);
  radio.setDataRate((rf24_datarate_e)current_rate);
  if (was_sniffing) {
    radio.startListening();
    sniffing = true;
  }
}

// ── Command Parser ─────────────────────────────────────────────────────────

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd == "help") {
    Serial.println(F("{\"commands\":[\"status\",\"scan\",\"sniff [ch]\",\"sniff_stop\",\"set_channel <n>\",\"set_rate <250|1000|2000>\",\"set_addr <10hex>\",\"tx <ch> <hex>\",\"help\"]}"));

  } else if (cmd == "status") {
    doStatus();

  } else if (cmd == "scan") {
    Serial.println(F("{\"scanning\":true,\"channels\":128,\"passes\":100}"));
    doScan();

  } else if (cmd == "sniff_stop") {
    sniffing = false;
    radio.stopListening();
    Serial.println(F("{\"sniffing\":false}"));

  } else if (cmd.startsWith("sniff")) {
    int ch = current_channel;
    sscanf(cmd.c_str() + 5, " %d", &ch);
    if (ch < 0 || ch > 127) { Serial.println(F("{\"error\":\"channel 0-127\"}")); return; }
    startSniff(ch);

  } else if (cmd.startsWith("set_channel ")) {
    int ch = atoi(cmd.c_str() + 12);
    if (ch < 0 || ch > 127) { Serial.println(F("{\"error\":\"channel 0-127\"}")); return; }
    current_channel = ch;
    applyConfig();
    Serial.print(F("{\"channel\":")); Serial.print(ch); Serial.println(F("}"));

  } else if (cmd.startsWith("set_rate ")) {
    int r = atoi(cmd.c_str() + 9);
    if      (r == 250)  current_rate = RF24_250KBPS;
    else if (r == 2000) current_rate = RF24_2MBPS;
    else                current_rate = RF24_1MBPS;
    applyConfig();
    Serial.print(F("{\"rate\":\"")); Serial.print(rateName()); Serial.println(F("\"}"));

  } else if (cmd.startsWith("set_addr ")) {
    uint8_t addr[5];
    if (!hexToBytes(cmd.c_str() + 9, addr, 5)) {
      Serial.println(F("{\"error\":\"addr must be 10 hex chars\"}"));
      return;
    }
    memcpy(rx_addr, addr, 5);
    applyConfig();
    Serial.print(F("{\"addr\":\""));
    printHex(rx_addr, 5);
    Serial.println(F("\"}"));

  } else if (cmd.startsWith("tx ")) {
    int ch = 0;
    char hexbuf[65] = {0};
    int parsed = sscanf(cmd.c_str() + 3, "%d %64s", &ch, hexbuf);
    if (parsed < 2) { Serial.println(F("{\"error\":\"usage: tx <channel> <hexdata>\"}")); return; }
    doTx(ch, hexbuf);

  } else {
    Serial.print(F("{\"error\":\"unknown: "));
    Serial.print(cmd);
    Serial.println(F("\"}"));
  }
}

// ── Sniff Loop ─────────────────────────────────────────────────────────────

void checkSniff() {
  if (!sniffing) return;
  if (!radio.available()) return;

  uint8_t buf[32];
  uint8_t len = radio.getDynamicPayloadSize();
  if (len == 0 || len > 32) { radio.flush_rx(); return; }
  radio.read(buf, len);

  Serial.print(F("{\"packet\":\""));
  printHex(buf, len);
  Serial.print(F("\",\"ch\":"));
  Serial.print(current_channel);
  Serial.print(F(",\"len\":"));
  Serial.print(len);
  Serial.println(F("}"));
}

// ── Setup / Loop ───────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(500);

  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV16); // 1 MHz — safe for RF-Nano PCB trace
  radio.begin();  // ignore return value — chip confirmed via raw SPI diag
  radio.setPALevel(RF24_PA_MAX);
  radio.setPayloadSize(32);
  radio.enableDynamicPayloads();
  radio.enableAckPayload();
  applyConfig();

  doStatus();
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }
  checkSniff();
}
