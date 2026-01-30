#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "DHT.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "Arduino_LED_Matrix.h"

// ---------- Sensor Pins ----------
#define DHTPIN   2
#define DHTTYPE  DHT22
#define ECG_PIN  A0
#define LO_PLUS  7
#define LO_MINUS 6

// ---------- WiFi Credentials ----------
char ssid[] = "Edge 30 Pro";      // your hotspot / router SSID
char pass[] = "malcolmcep";       // your WiFi password

// ---------- Server Info (your COMPUTER IP) ----------
char serverAddress[] = "10.159.251.149";   // <-- CHANGE: your PC IP address
int  port = 5000;                          // Flask / HTTP server port

// ---------- Objects ----------
WiFiClient wifi;
HttpClient client(wifi, serverAddress, port);

MAX30105 particleSensor;
DHT dht(DHTPIN, DHTTYPE);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
ArduinoLEDMatrix matrix;

// ---------- Heart Rate Variables ----------
long  lastBeat       = 0;
float beatsPerMinute = 0;
float beatAvg        = 0;
unsigned long lastMatrixBeat = 0;

// ---------- Heart bitmaps ----------
uint8_t heart_small[5][5] = {
  {0,1,0,1,0},
  {1,0,1,0,1},
  {0,0,1,0,0},
  {0,0,0,0,0},
  {0,0,0,0,0}
};

uint8_t heart_big[5][5] = {
  {0,1,0,1,0},
  {1,1,1,1,1},
  {1,1,1,1,1},
  {0,1,1,1,0},
  {0,0,1,0,0}
};

// ---------- WiFi helper ----------
void connectWiFi() {
  Serial.println("Starting WiFi...");

  WiFi.disconnect();
  delay(500);

  Serial.print("WiFi Firmware: ");
  Serial.println(WiFi.firmwareVersion());

  Serial.println("Scanning for networks...");
  int numNetworks = WiFi.scanNetworks();
  if (numNetworks <= 0) {
    Serial.println("No WiFi networks found!");
  } else {
    for (int i = 0; i < numNetworks; i++) {
      Serial.print("  ");
      Serial.print(WiFi.SSID(i));
      Serial.print(" (RSSI ");
      Serial.print(WiFi.RSSI(i));
      Serial.println(")");
    }
  }

  Serial.print("\nConnecting to: ");
  Serial.println(ssid);

  WiFi.begin(ssid, pass);
  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected! 🎉");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("❌ WiFi FAILED to connect!");
    Serial.println("Check:");
    Serial.println("- Hotspot 2.4 GHz only");
    Serial.println("- Security WPA2, not WPA3");
    Serial.println("- SSID/password correct");
  }
}

// ---------- Draw Heart on Matrix ----------
void drawHeart(bool big) {
  if (big)
    matrix.renderBitmap(heart_big, 5, 5);
  else
    matrix.renderBitmap(heart_small, 5, 5);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);

  // LED Matrix
  matrix.begin();
  matrix.clear();
  drawHeart(false);

  // OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 not found");
    while (1);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Initializing...");
  display.display();

  // DHT
  dht.begin();

  // MAX3010x (MAX30102/5)
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX3010x not found!");
    while (1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x7F);

  // Connect WiFi once at startup
  // Static IP Configuration
  IPAddress local_IP(10, 159, 251, 52);
  IPAddress gateway(10, 159, 251, 1);   // Assuming gateway is .1, adjust if needed
  IPAddress subnet(255, 255, 255, 0);
  
  WiFi.config(local_IP, gateway, subnet);
  
  connectWiFi();

  display.println("Ready");
  display.display();
}

void loop() {
  // ---------- 1. Read sensors ----------
  float temperature = dht.readTemperature();
  float humidity    = dht.readHumidity();
  int   ecgValue    = analogRead(ECG_PIN);
  long  irValue     = particleSensor.getIR();

  // ---------- 2. Heartbeat detection ----------
  bool beatDetected = false;
  if (checkForBeat(irValue)) {
    beatDetected = true;
    long delta = millis() - lastBeat;
    lastBeat = millis();

    if (delta > 0) {
      beatsPerMinute = 60.0 / (delta / 1000.0);
      if (beatsPerMinute < 255 && beatsPerMinute > 20) {
        beatAvg = (beatAvg * 0.9) + (beatsPerMinute * 0.1);
      }
    }
  }

  // ---------- 3. Update OLED ----------
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("Temp: "); display.print(temperature); display.println(" C");
  display.print("Hum : "); display.print(humidity);    display.println(" %");
  display.print("BPM : "); display.println(beatAvg, 1);
  display.print("ECG : "); display.println(ecgValue);
  display.display();

  // ---------- 4. LED Matrix Heart animation ----------
  if (beatDetected) {
    drawHeart(true);
    lastMatrixBeat = millis();
  } else if (millis() - lastMatrixBeat > 300) {
    drawHeart(false);
  }

  // ---------- 5. Debug over Serial ----------
  Serial.print("IR=");   Serial.print(irValue);
  Serial.print(" BPM="); Serial.print(beatAvg, 1);
  Serial.print(" Temp=");Serial.print(temperature);
  Serial.print("C Hum=");Serial.print(humidity);
  Serial.print("% ECG=");Serial.println(ecgValue);

  // ---------- 6. WiFi auto-reconnect check ----------
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost, trying to reconnect...");
    connectWiFi();
  }

  // ---------- 7. Send JSON to server (if WiFi OK) ----------
  if (WiFi.status() == WL_CONNECTED) {
    String json = "{\"temp\":" + String(temperature, 1) +
                  ",\"hum\":"   + String(humidity, 1) +
                  ",\"hr\":"    + String(beatAvg, 1) +
                  ",\"ecg\":"   + String(ecgValue) +
                  ",\"patient_id\":\"arduino_device_1\"}";

    client.beginRequest();
    client.post("/data");
    client.sendHeader("Content-Type", "application/json");
    client.sendHeader("Content-Length", json.length());
    client.beginBody();
    client.print(json);
    client.endRequest();

    int statusCode = client.responseStatusCode();
    String response = client.responseBody();
    Serial.print("HTTP Response Code: ");
    Serial.println(statusCode);
    Serial.println(response);
  } else {
    Serial.println("Skipping HTTP send (no WiFi).");
  }

  delay(50);
}
