// =============================================
// ESP32-CAM SMART GLASSES - STREAM + FLASH AUTO
// =============================================

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiClient.h>

// Configuration WiFi
const char* ssid = "Galaxy M33 5G A87F";
const char* password = "@drien219";

WebServer server(80);

// ✅ Broches ESP32-CAM AI-Thinker
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ✅ Flash et photorésistance
#define FLASH_PIN          4
#define LIGHT_SENSOR_PIN  13    // Broche analogique pour photorésistance
#define LIGHT_THRESHOLD   500   // Seuil lumière faible (à ajuster)

bool cameraActive = false;
bool autoFlash = true;
int currentLightLevel = 0;

// Timing
unsigned long lastLightCheck = 0;
const unsigned long LIGHT_CHECK_INTERVAL = 2000; // 2 secondes

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32-CAM Smart Glasses - Stream + Flash Auto");
  
  // Initialisation flash et photorésistance
  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(FLASH_PIN, LOW);
  
  // WiFi
  setupWiFi();
  
  // Caméra
  if (setupCamera()) {
    cameraActive = true;
    Serial.println("✅ Caméra prête");
  }
  
  // Routes serveur
  server.on("/", HTTP_GET, handleRoot);
  server.on("/stream", HTTP_GET, handleStream);
  server.on("/snapshot", HTTP_GET, handleSnapshot);
  server.on("/flash", HTTP_GET, handleFlashControl);
  server.on("/status", HTTP_GET, handleStatus);
  
  server.begin();
  Serial.println("✅ Serveur web démarré");
}

bool setupCamera() {
  camera_config_t config;
  
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  
  // ⚙️ CONFIGURATION STABLE
  config.xclk_freq_hz = 10000000;    // 10MHz
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; // 640x480
  config.jpeg_quality = 12;
  config.fb_count = 1;
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Erreur caméra: 0x%x\n", err);
    return false;
  }
  
  // Réglages caméra
  sensor_t *s = esp_camera_sensor_get();
  s->set_vflip(s, 1);    // Flip vertical
  s->set_hmirror(s, 0);  // Pas de miroir horizontal
  
  return true;
}

// ✅ STREAM PRINCIPAL
void handleStream() {
  WiFiClient client = server.client();
  
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);
  
  Serial.println("📹 Début stream - Détection faciale/billets");
  
  while (client.connected()) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("❌ Frame vide");
      continue;
    }
    
    client.write("--frame\r\n");
    client.write("Content-Type: image/jpeg\r\n\r\n");
    client.write(fb->buf, fb->len);
    client.write("\r\n");
    
    esp_camera_fb_return(fb);
    
    delay(50); // ~20 FPS
  }
  
  Serial.println("Client déconnecté");
}

// ✅ SNAPSHOT
void handleSnapshot() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Erreur capture");
    return;
  }
  
  server.setContentLength(fb->len);
  server.send(200, "image/jpeg");
  server.client().write(fb->buf, fb->len);
  
  esp_camera_fb_return(fb);
  Serial.println("📸 Snapshot envoyé");
}

// ✅ CONTRÔLE FLASH
void handleFlashControl() {
  String action = server.arg("action");
  
  if (action == "on") {
    digitalWrite(FLASH_PIN, HIGH);
    autoFlash = false;
    server.send(200, "text/plain", "Flash ON");
    Serial.println("💡 Flash activé manuellement");
  }
  else if (action == "off") {
    digitalWrite(FLASH_PIN, LOW);
    autoFlash = false;
    server.send(200, "text/plain", "Flash OFF");
    Serial.println("💡 Flash désactivé");
  }
  else if (action == "auto") {
    autoFlash = true;
    server.send(200, "text/plain", "Flash AUTO");
    Serial.println("💡 Mode flash auto activé");
  }
  else {
    server.send(400, "text/plain", "Action invalide: on/off/auto");
  }
}

// ✅ STATUS COMPLET
void handleStatus() {
  String status = "🤖 SMART GLASSES - ESP32-CAM\n";
  status += "📡 IP: " + WiFi.localIP().toString() + "\n";
  status += "📷 Caméra: " + String(cameraActive ? "✅ Active" : "❌ Inactive") + "\n";
  status += "💡 Flash: " + String(digitalRead(FLASH_PIN) ? "ON" : "OFF") + "\n";
  status += "🔧 Mode: " + String(autoFlash ? "AUTO" : "MANUEL") + "\n";
  status += "🌞 Luminosité: " + String(currentLightLevel) + "\n";
  status += "💾 Mémoire libre: " + String(esp_get_free_heap_size()) + " bytes\n";
  
  server.send(200, "text/plain", status);
}

// ✅ INTERFACE WEB
void handleRoot() {
  String html = R"rawliteral(
<html>
<head>
  <title>Smart Glasses - ESP32-CAM</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial; margin: 20px; background: #f0f0f0; }
    .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
    .stream-container { text-align: center; margin: 20px 0; }
    img { max-width: 100%; border: 2px solid #333; border-radius: 5px; }
    .controls { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
    .button { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }
    .button:hover { background: #0056b3; }
    .status { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🤖 Smart Glasses - ESP32-CAM</h1>
    
    <div class="stream-container">
      <h3>📹 Stream Live - Détection Faciale/Billets</h3>
      <img src="/stream" alt="Live Stream">
    </div>
    
    <div class="controls">
      <a class="button" href="/stream">Lancer Stream</a>
      <a class="button" href="/snapshot">Prendre Photo</a>
      <a class="button" href="/flash?action=on">Flash ON</a>
      <a class="button" href="/flash?action=off">Flash OFF</a>
      <a class="button" href="/flash?action=auto">Flash AUTO</a>
      <a class="button" href="/status">Status</a>
    </div>
    
    <div class="status">
      <h4>📊 Informations système:</h4>
      <p>Stream optimisé pour la détection faciale et reconnaissance de billets</p>
      <p>Flash automatique selon la luminosité ambiante</p>
    </div>
  </div>
</body>
</html>
)rawliteral";

  server.send(200, "text/html", html);
}

// ✅ GESTION FLASH AUTOMATIQUE
void checkLightLevel() {
  currentLightLevel = analogRead(LIGHT_SENSOR_PIN);
  
  if (autoFlash) {
    if (currentLightLevel < LIGHT_THRESHOLD) {
      digitalWrite(FLASH_PIN, HIGH);
    } else {
      digitalWrite(FLASH_PIN, LOW);
    }
  }
  
  // Log toutes les 10 secondes
  static unsigned long lastLog = 0;
  if (millis() - lastLog > 10000) {
    Serial.printf("🌞 Luminosité: %d | Flash: %s | Mode: %s\n", 
                  currentLightLevel,
                  digitalRead(FLASH_PIN) ? "ON" : "OFF",
                  autoFlash ? "AUTO" : "MANUEL");
    lastLog = millis();
  }
}

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connexion WiFi");
  for(int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print(".");
  }
  
  if(WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connecté!");
    Serial.print("📡 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Échec WiFi - Mode AP");
    WiFi.softAP("SmartGlasses-ESP32", "12345678");
    Serial.print("📡 Mode AP - IP: ");
    Serial.println(WiFi.softAPIP());
  }
}

void loop() {
  server.handleClient();
  
  // ✅ Vérification lumière toutes les 2 secondes
  if (millis() - lastLightCheck > LIGHT_CHECK_INTERVAL) {
    checkLightLevel();
    lastLightCheck = millis();
  }
  
  delay(2);
}