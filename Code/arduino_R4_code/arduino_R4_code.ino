#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "DHT.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "Arduino_LED_Matrix.h"   // ⭐ NEW for Uno R4 LED matrix

// ---------- Sensor Pins ----------
#define DHTPIN 2
#define DHTTYPE DHT22
#define ECG_PIN A0
#define LO_PLUS 7
#define LO_MINUS 6

// ---------- WiFi Credentials ----------
char ssid[] = "Enter your username";      // <-- Change this
char pass[] = "Enter your password";  // <-- Change this

// ---------- Server Info ----------
char serverAddress[] = "10.159.251.149";   // <-- Raspberry Pi IP
int port = 5000;                          // Flask port

// ---------- Objects ----------
WiFiClient wifi;
HttpClient client = HttpClient(wifi, serverAddress, port);
MAX30105 particleSensor;
DHT dht(DHTPIN, DHTTYPE);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
ArduinoLEDMatrix matrix;  // ⭐ LED matrix controller

// ---------- Heart Rate Variables ----------
long lastBeat = 0;
float beatsPerMinute;
float beatAvg = 0;
unsigned long lastMatrixBeat = 0;

// ---------- Heart Frames for Matrix ❤️ ----------
// Removed 'const' to fix compilation error
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

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);

  // --- Initialize matrix ---
  matrix.begin();
  matrix.clear();
  matrix.renderBitmap(heart_small, 5, 5);

  // --- OLED ---
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 not found");
    while(1);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Initializing...");
  display.display();

  // --- DHT ---
  dht.begin();

  // --- MAX30102 ---
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found!");
    while(1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x7F);

  // --- Wi-Fi ---
  Serial.print("Connecting to WiFi ");
  Serial.println(ssid);
  display.println("Connecting WiFi...");
  display.display();
  
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  display.println("WiFi Connected!");
  display.display();
}

// ---------- Draw Heart on Matrix ----------
void drawHeart(bool big) {
  if (big)
    matrix.renderBitmap(heart_big, 5, 5);
  else
    matrix.renderBitmap(heart_small, 5, 5);
}

// ---------- Main Loop ----------
void loop() {
  // 1️⃣ Read Sensors
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int ecgValue = analogRead(ECG_PIN);
  long irValue = particleSensor.getIR();

  // 2️⃣ Heartbeat Detection
  bool beatDetected = false;
  if (checkForBeat(irValue)) {
    beatDetected = true;
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      beatAvg = (beatAvg * 0.9) + (beatsPerMinute * 0.1);
    }
  }

  // 3️⃣ Display on OLED
  display.clearDisplay();
  display.setCursor(0,0);
  display.print("Temp: "); display.print(temperature); display.println(" C");
  display.print("Hum : "); display.print(humidity); display.println(" %");
  display.print("BPM : "); display.println(beatAvg, 1);
  display.print("ECG : "); display.println(ecgValue);
  display.display();

  // 4️⃣ LED Matrix Heartbeat ❤️
  if (beatDetected) {
    drawHeart(true);                     // Big heart on beat
    lastMatrixBeat = millis();
  } else if (millis() - lastMatrixBeat > 300) {
    drawHeart(false);                    // Back to small heart
  }

  // 5️⃣ Debug Serial
  Serial.print("IR="); Serial.print(irValue);
  Serial.print(" BPM="); Serial.print(beatAvg, 1);
  Serial.print(" Temp="); Serial.print(temperature);
  Serial.print("C Hum="); Serial.print(humidity);
  Serial.print("% ECG="); Serial.println(ecgValue);

  // 6️⃣ Send JSON to Raspberry Pi Flask Server
  String json = "{\"temperature\":" + String(temperature,1) +
                ",\"humidity\":" + String(humidity,1) +
                ",\"heartrate\":" + String(beatAvg,1) +
                ",\"ecg\":" + String(ecgValue) + "}";

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

  delay(20);  // short delay for smooth reading
}
