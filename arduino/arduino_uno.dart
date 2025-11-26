// =============================================
// ARDUINO UNO - VERSION ULTRA-STABLE CORRIGÉE
// =============================================

// Broches LED RGB
const int RED_PIN = 9;
const int GREEN_PIN = 10;
const int BLUE_PIN = 11;

// Broches boutons
const int BUTTON_PINS[] = {2, 3, 4, 5};
const int NUM_BUTTONS = 4;

// Broches joystick
const int JOY_X_PIN = A0;
const int JOY_Y_PIN = A1;
const int JOY_BUTTON_PIN = 6;

// Broches capteur ultrason
const int TRIG_PIN = 12;
const int ECHO_PIN = 13;

// Broche photorésistance
const int LIGHT_SENSOR_PIN = A2;

// Broches sorties - A3 et A4 en sortie digitale
const int BUZZER_PIN = A3;
const int VIBRATION_PIN = A4;

// États système
enum SystemMode {
  MODE_NAVIGATION = 0,
  MODE_OBJECT_DETECTION = 1,
  MODE_FACE_RECOGNITION = 2,
  MODE_TEXT_READING = 3,
  MODE_AI_ASSISTANT = 4
};

SystemMode currentMode = MODE_NAVIGATION;

// Anti-rebond
unsigned long lastButtonPress = 0;
const unsigned long DEBOUNCE_DELAY = 1000;

// Gestion buzzer et vibreur
bool buzzerActive = false;
unsigned long buzzerStartTime = 0;
int buzzerDuration = 0;

bool vibratorActive = false;
unsigned long vibratorStartTime = 0;
int vibratorDuration = 0;

// État précédent des boutons
int lastButtonStates[] = {HIGH, HIGH, HIGH, HIGH};

// Timing pour éviter la saturation
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_READ_INTERVAL = 3000;
unsigned long lastJoystickSend = 0;
const unsigned long JOYSTICK_SEND_INTERVAL = 500;

void setup() {
  setupPins();
  
  // Communication série
  Serial.begin(9600);
  while (!Serial) {
    ; // Attendre la connexion série
  }
  
  startupSequence();
  
  Serial.println("ARDUINO_READY:Ultra Stable System Ready - A3/A4 Active");
}

void setupPins() {
  // LED RGB
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  
  // Boutons
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    lastButtonStates[i] = digitalRead(BUTTON_PINS[i]);
  }
  
  // Joystick
  pinMode(JOY_BUTTON_PIN, INPUT_PULLUP);
  
  // Ultrason
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Photorésistance
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  
  // Buzzer et vibreur - A3 et A4 en sortie digitale
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(VIBRATION_PIN, LOW);
  
  // Test initial des sorties A3-A4
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(VIBRATION_PIN, HIGH);
  delay(100);
  digitalWrite(VIBRATION_PIN, LOW);
}

void loop() {
  // Lecture Raspberry Pi
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    handleSerialMessage(message);
  }
  
  // Boutons
  checkButtonsUltraStable();
  
  // Joystick avec anti-saturation
  checkJoystickStable();
  
  // Capteurs avec timing
  readSensorsStable();
  
  // Gestion sorties
  updateBuzzer();
  updateVibrator();
  
  // LED
  updateStatusLED();
  
  delay(100);
}

void checkButtonsUltraStable() {
  unsigned long currentTime = millis();
  
  for (int i = 0; i < NUM_BUTTONS; i++) {
    int currentState = digitalRead(BUTTON_PINS[i]);
    
    // Détection front descendant
    if (currentState == LOW && lastButtonStates[i] == HIGH) {
      if (currentTime - lastButtonPress > DEBOUNCE_DELAY) {
        handleButtonPress(i + 1);
        lastButtonPress = currentTime;
      }
    }
    
    lastButtonStates[i] = currentState;
  }
}

void handleSerialMessage(String message) {
  if (message.startsWith("MODE:")) {
    int mode = message.substring(5).toInt();
    if (mode >= 0 && mode <= 4) {
      setSystemMode((SystemMode)mode);
    }
  }
  else if (message == "GET_LIGHT") {
    int lightLevel = readLightLevel();
    Serial.print("LIGHT_LEVEL:");
    Serial.println(lightLevel);
  }
  else if (message == "GET_ULTRASONIC") {
    float distance = readUltrasonic();
    Serial.print("DISTANCE:");
    Serial.println(distance);
  }
  else if (message.startsWith("BUZZER:")) {
    int duration = getValue(message, ':', 1).toInt();
    int frequency = getValue(message, ':', 2).toInt();
    startBuzzer(duration, frequency);
  }
  else if (message.startsWith("VIBRATE:")) {
    int duration = message.substring(8).toInt();
    startVibration(duration);
  }
  else if (message == "BEEP") {
    startBuzzer(200, 1000);
  }
  else if (message == "TEST_A3_A4") {
    // Commande de test spécial pour A3-A4
    startBuzzer(500, 800);
    startVibration(500);
    Serial.println("TEST_A3_A4:OK");
  }
}

void handleButtonPress(int buttonId) {
  // Envoyer UNIQUEMENT le message bouton
  Serial.print("BUTTON:");
  Serial.println(buttonId);
  
  startBuzzer(100, 800);
  startVibration(100);
  
  switch(buttonId) {
    case 1:
      setSystemMode(MODE_OBJECT_DETECTION);
      break;
    case 2:
      setSystemMode(MODE_FACE_RECOGNITION);
      break;
    case 3:
      setSystemMode(MODE_TEXT_READING);
      break;
    case 4:
      setSystemMode(MODE_AI_ASSISTANT);
      break;
  }
}

void checkJoystickStable() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastJoystickSend < JOYSTICK_SEND_INTERVAL) {
    return; // Éviter la saturation
  }
  
  int xValue = analogRead(JOY_X_PIN);
  int yValue = analogRead(JOY_Y_PIN);
  int buttonState = digitalRead(JOY_BUTTON_PIN);
  
  static int lastX = 512;
  static int lastY = 512;
  
  // Seuil augmenté pour réduire les messages
  if (abs(xValue - lastX) > 100 || abs(yValue - lastY) > 100) {
    Serial.print("JOYSTICK:");
    Serial.print(xValue);
    Serial.print(",");
    Serial.println(yValue);
    lastX = xValue;
    lastY = yValue;
    lastJoystickSend = currentTime;
  }
  
  static int lastButtonState = HIGH;
  if (buttonState == LOW && lastButtonState == HIGH) {
    Serial.println("BUTTON:5");
    startBuzzer(150, 600);
    startVibration(150);
    setSystemMode(MODE_NAVIGATION);
    lastJoystickSend = currentTime;
  }
  lastButtonState = buttonState;
}

void readSensorsStable() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastSensorRead > SENSOR_READ_INTERVAL) {
    int lightLevel = readLightLevel();
    
    // Envoyer UNIQUEMENT le niveau de lumière
    Serial.print("LIGHT_LEVEL:");
    Serial.println(lightLevel);
    
    lastSensorRead = currentTime;
  }
}

int readLightLevel() {
  return analogRead(LIGHT_SENSOR_PIN);
}

float readUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) {
    return 0.0;
  }
  
  float distance = duration * 0.034 / 2;
  return distance / 100.0;
}

void setSystemMode(SystemMode newMode) {
  currentMode = newMode;
  Serial.print("MODE_CHANGE:");
  Serial.println((int)newMode);
}

void updateStatusLED() {
  switch(currentMode) {
    case MODE_NAVIGATION:
      setRGBColor(255, 0, 0);
      break;
    case MODE_OBJECT_DETECTION:
      setRGBColor(0, 255, 0);
      break;
    case MODE_FACE_RECOGNITION:
      setRGBColor(0, 0, 255);
      break;
    case MODE_TEXT_READING:
      setRGBColor(255, 165, 0);
      break;
    case MODE_AI_ASSISTANT:
      setRGBColor(128, 0, 128);
      break;
    default:
      setRGBColor(255, 255, 255);
  }
}

void setRGBColor(int red, int green, int blue) {
  analogWrite(RED_PIN, red);
  analogWrite(GREEN_PIN, green);
  analogWrite(BLUE_PIN, blue);
}

void startBuzzer(int duration, int frequency) {
  // Sécurité : Limiter la durée et la fréquence
  duration = constrain(duration, 10, 5000);
  frequency = constrain(frequency, 50, 5000);
  
  buzzerActive = true;
  buzzerStartTime = millis();
  buzzerDuration = duration;
  
  // Forcer la broche en sortie avant tone
  pinMode(BUZZER_PIN, OUTPUT);
  tone(BUZZER_PIN, frequency, duration);
}

void startVibration(int duration) {
  // Sécurité : Limiter la durée
  duration = constrain(duration, 10, 5000);
  
  vibratorActive = true;
  vibratorStartTime = millis();
  vibratorDuration = duration;
  
  // Forcer la broche en sortie
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(VIBRATION_PIN, HIGH);
}

void updateBuzzer() {
  if (buzzerActive && (millis() - buzzerStartTime >= buzzerDuration)) {
    buzzerActive = false;
    // S'assurer que le buzzer est éteint
    noTone(BUZZER_PIN);
    digitalWrite(BUZZER_PIN, LOW);
  }
}

void updateVibrator() {
  if (vibratorActive && (millis() - vibratorStartTime >= vibratorDuration)) {
    vibratorActive = false;
    // S'assurer que le vibreur est éteint
    digitalWrite(VIBRATION_PIN, LOW);
  }
}

void startupSequence() {
  // Séquence de démarrage avec test A3-A4
  setRGBColor(255, 0, 0);
  startBuzzer(200, 500);
  delay(300);
  
  setRGBColor(0, 255, 0);
  startVibration(200);
  delay(300);
  
  setRGBColor(0, 0, 255);
  startBuzzer(200, 700);
  startVibration(200);
  delay(300);
  
  setSystemMode(MODE_NAVIGATION);
}

String getValue(String data, char separator, int index) {
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i+1 : i;
    }
  }

  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

// Fonction de test manuel pour A3-A4
void testBrochesA3A4() {
  Serial.println("TEST: Début test A3-A4...");
  
  // Test Buzzer A3
  pinMode(BUZZER_PIN, OUTPUT);
  tone(BUZZER_PIN, 1000, 300);
  Serial.println("TEST: Buzzer A3 activé");
  delay(500);
  
  // Test Vibreur A4  
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(VIBRATION_PIN, HIGH);
  Serial.println("TEST: Vibreur A4 activé");
  delay(300);
  digitalWrite(VIBRATION_PIN, LOW);
  
  Serial.println("TEST: A3-A4 terminé");
}