#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "DHT.h"

// --- WiFi ---
const char* ssid = "enter your ssid";
const char* password = "enter your password";

// --- Server URL (replace with Raspberry Pi IP) ---
const char* serverName = "http://172.17.201.62:5000/data";   // Flask server endpoint

// --- DHT22 ---
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- MAX30102 ---
MAX30105 particleSensor;
long lastBeat = 0;
float beatAvg = 0;

// --- AD8232 ---
#define ECG_PIN 34
#define LO_PLUS 25
#define LO_MINUS 26

void setup() {
  Serial.begin(115200);

  // --- WiFi connect ---
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // --- DHT22 ---
  dht.begin();

  // --- MAX30102 ---
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found!");
    while (1);
  }
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeGreen(0);

  // --- AD8232 ---
  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);
}

void loop() {
  // --- DHT22 ---
  float tempC = dht.readTemperature();
  float hum = dht.readHumidity();

  // --- MAX30102 ---
  long irValue = particleSensor.getIR();
  if (checkForBeat(irValue)) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    int bpm = 60 / (delta / 1000.0);
    if (bpm > 40 && bpm < 180) {
      beatAvg = (beatAvg * 0.9) + (bpm * 0.1);
    }
  }

  // --- AD8232 ---
  int ecgVal;
  if ((digitalRead(LO_PLUS) == 1) || (digitalRead(LO_MINUS) == 1)) {
    ecgVal = 0;
  } else {
    ecgVal = analogRead(ECG_PIN);
  }

  // --- Send to Raspberry Pi ---
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";
    jsonData += "\"temperature\":" + String(tempC) + ",";
    jsonData += "\"humidity\":" + String(hum) + ",";
    jsonData += "\"heartrate\":" + String(beatAvg, 1) + ",";
    jsonData += "\"ecg\":" + String(ecgVal);
    jsonData += "}";

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.print("Data sent, response: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Error sending data: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }

  delay(2000); // send every 2 seconds
}
