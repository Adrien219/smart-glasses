# smart-glasses
Ce projet consiste à développer des lunettes intelligentes assistées par intelligence artificielle, destinées à aider les personnes aveugles ou malvoyantes à se déplacer de manière plus sûre et autonome.




# 📋 DOCUMENTATION TECHNIQUE ULTRA-DÉTAILLÉE - SMART GLASSES

## 🎯 **OBJECTIF GLOBAL DU PROJET**

### **Problématique Adressée**
Créer un système de lunettes intelligentes **assistant les personnes malvoyantes** en fournissant une perception augmentée de l'environnement via :
- **Reconnaissance visuelle** en temps réel des obstacles, objets, textes et visages
- **Interface non-visuelle** par retour vocal et haptique
- **Navigation autonome** avec guidage contextuel
- **Interaction mains-libres** via commandes vocales et contrôles physiques simples

### **Public Cible Principal**
- Personnes malvoyantes et non-voyantes
- Personnes âgées avec déficience visuelle
- Professionnels en situation de handicap visuel

## 🏗️ **ARCHITECTURE SYSTÈME COMPLÈTE**

### **📁 Structure Détaillée du Dépôt GitHub**

```
smart-glasses/
├── 🖥️  RASPBERY-PI/ (Version de production)
│   ├── main.py
│   ├── camera_processor.py
│   ├── arduino_communicator.py
│   ├── hardware/
│   │   ├── camera_manager.py
│   │   └── arduino_communication.py
│   ├── core/
│   │   ├── object_detector.py
│   │   ├── face_recognizer.py
│   │   ├── text_recognizer.py
│   │   ├── navigation_brain.py
│   │   ├── ai_assistant.py
│   │   └── voice_commands.py
│   ├── config/
│   │   └── settings.py
│   └── web/ (Interface de contrôle)
│
├── 💻 WINDOWS/ (Version de développement)
│   └── main.py
│
├── 🔌 HARDWARE/ (Schémas électroniques)
│   ├── arduino/
│   └── esp32/
│
└── 📚 DOCS/ (Documentation)
```

### **🔄 Flux de Données Principal**

```
[Capteurs Matériels]
        ↓
[Microcontrôleurs Arduino/ESP32]
        ↓
[Communication Série/WiFi]
        ↓
[Contrôleur Principal Raspberry Pi]
        ↓
[Modules de Traitement IA]
        ↓
[Gestionnaire de Décisions]
        ↓
[Sorties Utilisateur (Vocale/Haptique)]
```

## 🔧 **COMPOSANTS LOGICIELS DÉTAILLÉS**

### **1. 🎛️ COUCHE MATÉRIELLE (Hardware)**

#### **`hardware/camera_manager.py`**
```python
FONCTIONNALITÉS :
├── 📷 Gestion multi-sources caméra
│   ├── Camera Raspberry Pi (module CSI)
│   ├── Camera USB (logitech, etc.)
│   └── Fallback automatique si module manquant
├── ⚙️ Configuration résolution dynamique
│   ├── 640x480 (défaut)
│   ├── 1280x720 (HD)
│   └── Adaptation automatique aux performances
├── 🔄 Switch dynamique entre caméras
│   ├── Basculement via commande bouton
│   ├── Conservation du contexte
│   └── Réinitialisation propre
└── 🛡️ Gestion d'erreurs robuste
    ├── Timeouts de connexion
    ├── Reconnexion automatique
    └── Mode dégradé sans caméra
```

#### **`hardware/arduino_communication.py`**
```python
ARCHITECTURE :
├── 🔌 Détection automatique des ports
│   ├── Scan COM1-COM10 (Windows)
│   ├── Scan /dev/ttyUSB*, /dev/ttyACM* (Linux)
│   └── Priorisation des ports actifs
├── 📨 Protocole de communication
│   ├── Format: "COMMAND:VALUE\n"
│   ├── Commands: BUTTON, JOYSTICK, MODE_CHANGE, LIGHT_LEVEL
│   └── Baud rate: 9600 (stabilité)
├── 🔄 Système de callbacks
│   ├── Enregistrement multiples listeners
│   ├── Distribution asynchrone des messages
│   └── Gestion des priorités
└── ⚡ Envoi de commandes
    ├── LED:r,g,b → Contrôle LED RGB
    ├── BEEP:freq,duration → Retour haptique
    └── Validation de réception
```

#### **`hardware/esp32_simple_camera.py`** (✅ NOUVEAU)
```python
COMPOSANTS TECHNIQUES :
├── 🌐 Client HTTP Stream
│   ├── URL: http://{ip}/stream
│   ├── Format: MJPEG over HTTP
│   └── Timeout: 3 secondes
├── 🧵 Thread de Capture
│   ├── Thread séparé non-bloquant
│   ├── Buffer de frame unique
│   └── Synchronisation verrou minimal
├── 🔧 Gestion Connexion
│   ├── Test de vivacité périodique
│   ├── Reconnexion automatique
│   └── Fallback vers mode simulation
├── 💡 Contrôle Flash
│   ├── Endpoint: /flash
│   ├── Méthode: GET
│   └── Retour: 200 OK / Timeout
└── 🗜️ Optimisations
    ├── Skip frames si buffer plein
    ├── Délai configurable (30 FPS)
    └── Libération mémoire garantie
```

### **2. 🧠 INTELLIGENCE ARTIFICIELLE (Core)**

#### **`core/object_detector.py`**
```python
MODÈLE YOLOv8 - CONFIGURATION :
├── 🎯 Modèle: yolov8n.pt (nano - optimisé RPi)
│   ├── 80 classes COCO
│   ├── Input: 640x640
│   └── Optimisé CPU/GPU faible puissance
├── 🔍 Pipeline de Détection
│   ├── Preprocessing: Normalisation RGB
│   ├── Inference: YOLOv8 via Ultralytics
│   ├── Post-processing: NMS + filtrage confiance
│   └── Formatage: [{class, confidence, bbox}]
├── 🖼️ Visualisation
│   ├── Bounding boxes colorées
│   ├── Labels avec scores
│   └── Overlay transparent
└-- ⚡ Performances
    ├── CPU: ~100-150ms/frame
    ├── GPU: ~20-50ms/frame (si disponible)
    └-- Optimisation: Half-precision
```

#### **`core/face_recognizer.py`**
```python
RECONNAISSANCE FACIALE - ÉTAT :
├-- ⚠️ ACTUELLEMENT DÉSACTIVÉ (Correctif appliqué)
│   └-- safe_detect_faces() → [] (retour vide)
├-- 🏗️ ARCHITECTURE ORIGINALE
│   ├-- Bibliothèque: face_recognition (dlib)
│   ├-- Encodages: 128-dimensions
│   ├-- Matching: distance euclidienne
│   └-- Base: known_faces/ (dataset entraîné)
├-- 📊 Métriques
│   ├-- Précision: ~99% LFW
│   ├-- Latence: ~200-300ms/face
│   └-- Mémoire: ~100MB/1000 visages
└-- 🔧 PROBLÈME IDENTIFIÉ
    ├-- Erreur: "tuple indices must be integers or slices, not str"
    ├-- Cause: Format de retour face_locations incompatible
    └-- Solution: Conversion explicite en int
```

#### **`core/text_recognizer.py`**
```python
OCR EASYOCR - IMPLÉMENTATION :
├-- 🏗️ Moteur: EasyOCR
│   ├-- Langues: ['fr', 'en']
│   ├-- Backbone: CRNN + CTC
│   └-- Détecteur: CRAFT
├-- 📝 Pipeline Texte
│   ├-- Détection régions texte
│   ├-- Reconnaissance caractères
│   ├-- Filtrage confiance (>0.6)
│   └-- Agrégation lignes
├-- 🎯 Performances
│   ├-- CPU: ~500-1000ms/image
│   ├-- Précision: ~85-90% texte clair
│   └-- Support: multi-langues
└-- ⚡ Optimisations
    ├-- Redimensionnement image
    ├-- ROI selection
    └-- Cache modèles
```

#### **`core/navigation_brain.py`**
```python
LOGIQUE DE NAVIGATION :
├-- 🧭 Analyse Spatiale
│   ├-- Position obstacles dans frame
│   ├-- Zones: gauche, centre, droite
│   ├-- Distance estimée (taille bbox)
│   └-- Trajectoire recommandée
├-- 🗣️ Instructions Vocales
│   ├-- "Obstacle à gauche - Serrez à droite"
│   ├-- "Passage libre - Avancez droit"
│   ├-- "Porte détectée - Centrez-vous"
│   └-- Urgence: "Arrêt - Obstacle proche"
├-- ⚠️ Système d'Alerte
│   ├-- Niveaux: Info, Avertissement, Danger
│   ├-- Priorisation alertes
│   └-- Éviction doublons
└-- 📊 Cartographie Mentale
    ├-- Mémoire obstacles récents
    ├-- Pattern reconnaissance environnements
    └-- Adaptation comportementale
```

#### **`core/ai_assistant.py`**
```python
ASSISTANT OPENAI :
├-- 🌐 Intégration API
│   ├-- Modèle: gpt-3.5-turbo (équilibre coût/performance)
│   ├-- Token limit: 4096
│   └-- Temperature: 0.7 (créativité contrôlée)
├-- 💬 Contexte Conversationnel
│   ├-- Memory: 10 derniers échanges
│   ├-- Context: "Vous êtes un assistant pour personne malvoyante"
│   └-- Personnalisation: ton calme et informatif
├-- 🔄 Workflow Interaction
│   ├-- Écoute commande vocale
│   ├-- Transcription → OpenAI
│   ├-- Synthèse réponse vocale
│   └-- Log conversation
└-- ⚡ Limitations
    ├-- Dépendance connexion Internet
    ├-- Latence: 2-5 secondes/réponse
    └-- Coût API à monitorer
```

#### **`core/voice_commands.py`**
```python
SYSTÈME DE COMMANDES VOCALES :
├-- 🎤 Reconnaissance (À IMPLÉMENTER)
│   ├-- Bibliothèque: SpeechRecognition
│   ├-- Moteurs: Google, Sphinx, Vosk
│   └-- Micro: USB ou intégré RPi
├-- 🗣️ Commandes Supportées
│   ├-- "Change mode" → cycle modes
│   ├-- "Lisez ce texte" → activation OCR
│   ├-- "Qui est là ?" → reconnaissance faciale
│   ├-- "Où suis-je ?" → description environnement
│   └-- "Aide" → liste commandes
├-- 🔧 Configuration
│   ├-- Sensibilité microphone
│   ├-- Mot-clé d'activation
│   └-- Timeout écoute
└-- 🛡️ Robustesse
    ├-- Filtrage bruit ambiant
    ├-- Correction phrases incomplètes
    └-- Fallback commandes simples
```

### **3. 🔊 SYSTÈME VOCAL (VoiceAssistant)**

```python
ARCHITECTURE VOCALE COMPLÈTE :
├-- 🎙️ Synthèse Vocale Multi-Plateformes
│   ├-- Windows: pyttsx3 (offline)
│   │   ├-- Voices: Microsoft Hortense (fr)
│   │   ├-- Rate: 160 mots/minute
│   │   └-- Volume: 90%
│   ├-- Raspberry Pi: espeak-ng (offline)
│   │   ├-- Langue: français
│   │   ├-- Pitch: 50
│   │   └-- Amplitude: 100
│   └-- Fallback: print console
├-- 📨 Système File d'Attente
│   ├-- PriorityQueue: messages urgents prioritaires
│   ├-- Cooldown: 3 secondes entre messages
│   ├-- Gestion concurrence: Lock threading
│   └-- Éviction doublons
├-- 📳 Retour Haptique
│   ├-- Buzzer: bips patterns
│   ├-- Durée: 100-500ms
│   ├-- Fréquence: 1000Hz
│   └-- Synchronisation vocale
└-- 🎚️ Contrôle Audio
    ├-- Interruption messages non-urgents
    ├-- Volume adaptatif environnement
    └-- Test santé vocal au démarrage
```

### **4. ⚙️ CONFIGURATION (Settings)**

#### **`config/settings.py`**
```python
CONFIGURATION GLOBALE DÉTAILLÉE :
├-- 📷 Paramètres Caméra
│   ├-- CAMERA_ID: 0 (index USB)
│   ├-- CAMERA_RESOLUTION: (640, 480)
│   ├-- CAMERA_FPS: 30
│   └-- CAMERA_ROTATION: 0
├-- 🧠 IA et Modèles
│   ├-- YOLO_MODEL_PATH: 'yolov8n.pt'
│   ├-- YOLO_CONFIDENCE: 0.5
│   ├-- FACE_RECOGNITION_TOLERANCE: 0.6
│   └-- OCR_LANGUAGES: ['fr', 'en']
├-- 🔌 Communication
│   ├-- ARDUINO_BAUDRATE: 9600
│   ├-- ARDUINO_TIMEOUT: 1
│   ├-- ESP32_CAM_URL: 'http://10.231.158.139/stream'
│   └-- ESP32_STATUS_URL: 'http://10.231.158.139/status'
├-- 🎮 Contrôles
│   ├-- JOYSTICK_DEADZONE: 100
│   ├-- BUTTON_COOLDOWN: 1.0
│   └-- MODE_CHANGE_DELAY: 0.5
├-- 🔊 Audio
│   ├-- VOICE_RATE: 160
│   ├-- VOICE_VOLUME: 0.9
│   ├-- BEEP_DURATION: 0.1
│   └-- SPEECH_COOLDOWN: 3.0
└-- 🖥️ Interface
    ├-- HEADLESS_MODE: False
    ├-- SHOW_DETECTIONS: True
    └-- DISPLAY_FPS: True
```

## 🔌 **ARCHITECTURE MATÉRIELLE DÉTAILLÉE**

### **📊 Spécifications Techniques Matérielles**

#### **Raspberry Pi 4 (Cerveau Central)**
```
SPECIFICATIONS :
├-- Processeur: Broadcom BCM2711 Quad core Cortex-A72 @ 1.5GHz
├-- Mémoire: 4GB LPDDR4
├-- Stockage: MicroSD 32GB+ Classe 10
├-- Connectivité:
│   ├-- WiFi 5 (802.11ac)
│   ├-- Bluetooth 5.0
│   ├-- 2x USB 3.0, 2x USB 2.0
│   └-- GPIO 40-pins
├-- Alimentation: 5V/3A USB-C
└-- Refroidissement: Ventilactif + dissipateur

INTERFACES UTILISÉES :
├-- CSI: Camera Module V2
├-- USB1: Arduino Nano
├-- USB2: Camera USB (backup)
├-- GPIO: Éventuels capteurs additionnels
└-- WiFi: Connection ESP32-CAM
```

#### **Arduino Nano (Contrôleur Périphérique)**
```
CARACTÉRISTIQUES :
├-- Microcontrôleur: ATmega328P
├-- Clock: 16MHz
├-- Mémoire: 32KB Flash, 2KB SRAM
├-- Entrées/Sorties:
│   ├-- 14 Digital I/O (dont 6 PWM)
│   ├-- 8 Analog Inputs
│   └-- Communication: UART, I2C, SPI
└-- Alimentation: 5V via USB

BROCHEAGE DÉTAILLÉ :
├-- ANALOGIQUES :
│   ├-- A0: Joystick X-axis
│   ├-- A1: Joystick Y-axis  
│   ├-- A2: Capteur lumière
│   └-- A3-A7: Réservés
├-- DIGITALES :
│   ├-- D2: Bouton 1 (Mode Navigation)
│   ├-- D3: Bouton 2 (Mode Objets)
│   ├-- D4: Bouton 3 (Mode Visages)
│   ├-- D5: Bouton 4 (Mode Texte)
│   ├-- D6: Bouton 5 (Mode IA)
│   ├-- D9: Buzzer (PWM)
│   ├-- D10: LED Rouge (PWM)
│   ├-- D11: LED Verte (PWM)
│   └-- D12: LED Bleue (PWM)
└-- COMMUNICATION :
    ├-- D0(RX)/D1(TX): Serial USB
    └-- D13: LED intégrée (debug)
```

#### **ESP32-CAM (Module Vision Secondaire)**
```
SPÉCIFICATIONS :
├-- Processeur: ESP32-S Dual-Core 240MHz
├-- Mémoire: 520KB SRAM, 4MB PSRAM
├-- Camera: OV2640 2MP
├-- Connectivité: WiFi 802.11 b/g/n
├-- Flash LED: GPIO4
└-- Alimentation: 5V externe (critique)

CONFIGURATION RÉSEAU :
├-- Mode: Station (se connecte à WiFi existant)
├-- IP: 10.231.158.139 (statique via DHCP reservation)
├-- Port: 80 (HTTP)
└-- Endpoints:
    ├-- /stream → Flux MJPEG
    ├-- /status → Health check
    └-- /flash → Contrôle LED
```

### **🔋 Considérations Alimentation**

```
BESOINS ÉNERGÉTIQUES :
├-- Raspberry Pi 4: 3A @ 5V = 15W
├-- Arduino Nano: 0.5A @ 5V = 2.5W  
├-- ESP32-CAM: 0.5A @ 5V = 2.5W (pic démarrage)
├-- Camera RPi: 0.25A @ 5V = 1.25W
└-- TOTAL: ~4.25A @ 5V = 21.25W

SOLUTION RECOMMANDÉE :
├-- Batterie: Powerbank 20000mAh @ 5V/3A
├-- Autonomie estimée: 3-4 heures
└-- Gestion énergie: Shutdown propre via software
```

## 🎮 **MODES DE FONCTIONNEMENT DÉTAILLÉS**

### **Mode 0: 🧭 NAVIGATION**
```python
OBJECTIF: Guidance sécuritaire dans l'environnement

FONCTIONNEMENT :
├-- 🔍 Détection en Temps Réel
│   ├-- Objets: personne, chaise, table, porte, escalier
│   ├-- Obstacles: mur, meuble, véhicule
│   └-- Structures: couloir, porte, rampe
├-- 🗺️ Analyse Spatiale
│   ├-- Cartographie obstacles gauche/centre/droite
│   ├-- Estimation distances relatives
│   ├-- Couloirs de circulation
│   └-- Points d'intérêt (portes, escaliers)
├-- 🗣️ Instructions Vocales
│   ├-- "Obstacle à 2m - Serrez à droite"
│   ├-- "Couloir libre - Avancez droit"  
│   ├-- "Porte détectée à gauche - Direction 10h"
│   └-- "Attention: escalier devant - Arrêtez"
└-- ⚠️ Système d'Alerte
    ├-- Niveau 1: Information (obstacles lointains)
    ├-- Niveau 2: Avertissement (obstacles proches)
    ├-- Niveau 3: Danger (collision imminente)
    └-- Priorisation: danger > proximité > information
```

### **Mode 1: 📦 RECONNAISSANCE OBJETS**
```python
OBJECTIF: Identifier et annoncer les objets environnants

CLASSES DÉTECTÉES (sélection):
├-- 🏠 Domestique: 
│   ├-- chaise, table, lit, canapé, télévision
│   ├-- frigo, four, micro-ondes, évier
│   └-- horloge, vase, livre, téléphone
├-- 🍽️ Nourriture:
│   ├-- pomme, banane, orange, sandwich
│   ├-- bouteille, verre, tasse, assiette
│   └-- couteau, fourchette, cuillère
├-- 🚪 Mobilier:
│   ├-- porte, fenêtre, toilette, lavabo
│   ├-- escalier, interrupteur, miroir
│   └-- placard, étagère, commode
├-- 👤 Personnes & Animaux:
│   ├-- personne, enfant, chien, chat
│   └-- oiseau, cheval, mouton
└-- 🚗 Extérieur:
    ├-- voiture, moto, vélo, bus, train
    ├-- panneau, feu tricolore, banc
    └-- arbre, fleur, herbe

ANNONCES VOCALES:
├-- Format: "Objets détectés: [liste]"
├-- Filtrage: objets avec confidence > 50%
├-- Limite: 5 objets maximum par annonce
└-- Cooldown: 3 secondes entre annonces
```

### **Mode 2: 👤 RECONNAISSANCE FACIALE** 
```python
⚠️ ACTUELLEMENT DÉSACTIVÉ - Correctif appliqué

ARCHITECTURE ORIGINALE:
├-- 🗂️ Base de Visages Connus
│   ├-- Dossier: known_faces/
│   ├-- Format: images JPG/PNG
│   ├-- Nommage: "prenom_nom.jpg"
│   └-- Entraînement: automatique au démarrage
├-- 🔍 Pipeline Reconnaissance
│   ├-- Détection visages: HOG + SVM
│   ├-- Encodage: ResNet 128D
│   ├-- Comparaison: distance euclidienne
│   └-- Seuil: tolerance=0.6
├-- 🎯 Performance Attendue
│   ├-- Précision: 99.38% LFW
│   ├-- Latence: 200ms/face
│   └-- Multi-faces: jusqu'à 10 simultanées
└-- 🗣️ Annonces
    ├-- Connu: "Adrien est devant vous"
    ├-- Inconnu: "Personne non reconnue"
    └-- Multiple: "3 personnes détectées"

PROBLÈME ACTUEL:
├-- Erreur: "tuple indices must be integers or slices, not str"
├-- Localisation: face_recognition.face_locations()
├-- Cause: Format de retour incompatible
└-- Solution: Wrapper de conversion types
```

### **Mode 3: 📝 LECTURE TEXTE**
```python
OBJECTIF: Lire et annoncer le texte dans l'environnement

CAS D'USAGE:
├-- 📖 Lecture documents: livres, magazines, journaux
├-- 🏷️ Étiquettes: produits, médicaments, nourriture
├-- 🚏 Signalétique: panneaux, rues, portes
├-- 🖥️ Écrans: téléphone, ordinateur, télévision
└-- 📄 Formulaires: administrations, banques

CONFIGURATION OCR:
├-- Moteur: EasyOCR
├-- Langues: français, anglais
├-- Détecteur: CRAFT (Character Region Awareness)
├-- Reconnaissance: CRNN (Convolutional Recurrent NN)
└-- Post-processing: correction orthographique

SEUILS ET FILTRES:
├-- Confidence minimale: 0.6 (60%)
├-- Longueur minimale: 2 caractères
├-- Filtrage bruit: symboles isolés
└-- Agrégation: lignes → paragraphes

ANNONCES:
├-- Format: "Texte détecté: [contenu]"
├-- Limite: 200 caractères par annonce
├-- Priorité: plus haute confidence
└-- Fréquence: immédiate si nouveau texte
```

### **Mode 4: 🤖 ASSISTANT IA**
```python
OBJECTIF: Assistant conversationnel contextuel

CAPACITÉS:
├-- 💬 Questions générales: connaissances, calculs
├-- 🏠 Contexte domestique: recettes, conseils
├-- 🚶 Orientation: directions, transports
├-- 📅 Organisation: agenda, rappels
└-- 🆘 Urgence: contacts, procédures

INTÉGRATION OPENAI:
├-- Modèle: gpt-3.5-turbo
├-- Contexte système: "Assistant pour personne malvoyante"
├-- Memory: 10 derniers messages
├-- Temperature: 0.7 (créativité équilibrée)
└-- Max tokens: 500 (réponses concises)

WORKFLOW:
├-- 1. Écoute commande vocale (À IMPLÉMENTER)
├-- 2. Transcription speech-to-text
├-- 3. Envoi à OpenAI API
├-- 4. Réception et parsing réponse
└-- 5. Synthèse vocale réponse

LIMITATIONS:
├-- Dépendance Internet
├-- Latence: 2-5 secondes
├-- Coût: ~$0.002/request
└-- Confidentialité: données externes
```

## ⚡ **SYSTÈME DE COMMUNICATION DÉTAILLÉ**

### **Protocole Arduino ↔ Raspberry Pi**

```
FORMAT DES MESSAGES:
┌-- STRUCTURE: "COMMAND:VALUE\n"
├-- ENCODAGE: ASCII
├-- BAUD RATE: 9600
└-- PARITÉ: 8N1

COMMANDES REÇUES (Arduino → RPi):
├-- "BUTTON:X"          // Bouton X pressé (1-5)
├-- "JOYSTICK:X,Y"      // Position joystick (0-1023)
├-- "MODE_CHANGE:X"     // Changement mode rotatif (0-4)  
├-- "LIGHT_LEVEL:X"     // Niveau luminosité (0-1023)
└-- "ARDUINO_READY"     // Initialisation terminée

COMMANDES ENVOYÉES (RPi → Arduino):
├-- "LED:R,G,B"         // Contrôle LED RGB (0-255)
├-- "BEEP:FREQ,DURATION" // Buzzer (Hz, ms)
└-- "VIBRATE:PATTERN"   // Moteur vibration (À IMPLÉMENTER)
```

### **Communication ESP32-CAM**

```
ENDPOINTS HTTP ESP32:
├-- GET /stream
│   └-- Retour: Flux MJPEG (multipart/x-mixed-replace)
├-- GET /status  
│   └-- Retour: "OK" (texte simple)
├-- GET /flash
│   └-- Action: Bascule LED flash
└-- GET /capture
    └-- Retour: Image JPEG unique

CONFIGURATION RÉSEAU:
├-- Mode: Station WiFi
├-- SSID: [configuré dans code]
├-- Password: [configuré dans code]
├-- IP: Dynamique (DHCP) avec réservation
└-- Port: 80

GESTION ERREURS:
├-- Timeout connexion: 3 secondes
├-- Reconnexion automatique: toutes les 5 secondes
├-- Fallback: mode simulation
└-- Logs: détaillés avec codes erreur HTTP
```

## 🛠️ **ÉTAT D'AVANCEMENT DÉTAILLÉ**

### **✅ FONCTIONNALITÉS COMPLÈTEMENT OPÉRATIONNELLES**

#### **Noyau Système**
- [x] **Initialisation automatique** de tous les composants
- [x] **Gestion d'erreurs robuste** avec fallbacks
- [x] **Communication Arduino** bidirectionnelle stable
- [x] **Système de logging** détaillé avec métriques
- [x] **Arrêt propre** avec libération ressources

#### **Vision par Ordinateur**
- [x] **Détection d'objets YOLOv8** temps réel
- [x] **OCR texte EasyOCR** avec filtrage confidence
- [x] **Multi-sources caméra** (RPi + USB + ESP32)
- [x] **Visualisation temps réel** avec overlay

#### **Interface Utilisateur**
- [x] **Changement de modes** via boutons physiques
- [x] **Retour vocal** avec file d'attente prioritaire
- [x] **Retour haptique** (buzzer + LED)
- [x] **Contrôle joystick** avec zones mortes
- [x] **Affichage temps réel** avec informations système

#### **Intégration Matérielle**
- [x] **Support Raspberry Pi** optimisé
- [x] **Support Windows** (développement)
- [x] **Communication série Arduino** stable
- [x] **Stream ESP32-CAM** avec reconnexion
- [x] **Gestion alimentation** et ressources

### **🔄 FONCTIONNALITÉS EN DÉVELOPPEMENT**

#### **Améliorations Stabilité**
- [ ] **Reconnaissance faciale** (correctif permanent)
- [ ] **Gestion mémoire** optimisée long terme
- [ ] **Watchdog système** redémarrage auto
- [ ] **Sauvegarde état** entre redémarrages

#### **Nouvelles Fonctionnalités**
- [ ] **Commandes vocales** (speech-to-text)
- [ ] **Interface web** contrôle distant
- [ ] **Cartographie environnement** 
- [ ] **Mode urgence** contacts + localisation
- [ ] **Système de plugins** extensible

### **🚧 DÉFIS TECHNIQUES EN COURS**

#### **Performance**
```
PROBLÈME: Latence OCR sur CPU
├-- Actuel: 500-1000ms/image
├-- Cible: <200ms/image
├-- Solutions:
│   ├-- Optimisation modèle EasyOCR
│   ├-- Détection ROI préalable
│   └-- Hardware accélération
└-- Priorité: Moyenne

PROBLÈME: Consommation mémoire YOLO
├-- Actuel: ~500MB
├-- Cible: <200MB  
├-- Solutions:
│   ├-- Modèle yolov8s (small)
│   ├-- Quantization INT8
│   └-- Cleanup mémoire périodique
└-- Priorité: Basse
```

#### **Robustesse**
```
PROBLÈME: ESP32 déconnexions fréquentes
├-- Cause: Alimentation instable
├-- Impact: Perte flux vidéo secondaire
├-- Solutions:
│   ├-- Alimentation externe dédiée
│   ├-- Timeout adaptatif
│   └-- Cache dernières frames
└-- Priorité: Élevée

PROBLÈME: Reconnaissance faciale plantage
├-- Erreur: "tuple indices must be integers or slices, not str"
├-- Cause: Incompatibilité bibliothèque
├-- Solution: Wrapper de conversion
└-- Priorité: Élevée
```

## 🔮 **ROADMAP FUTURE DÉTAILLÉE**

### **Phase 1: Stabilisation (1-2 mois)**
```
OBJECTIF: Système production-ready
├-- ✅ [Fait] Communication matérielle stable
├-- 🔄 [En Cours] Correctif reconnaissance faciale
├-- 📝 [Planifié] Tests intensifs utilisateurs
├-- 🐛 [Planifié] Correction bugs critiques
└-- 📊 [Planifié] Métriques performance

LIVRABLES:
├-- Version 1.0 stable
├-- Documentation utilisateur
└-- Scripts installation automatisée
```

### **Phase 2: Fonctionnalités Avancées (3-6 mois)**
```
OBJECTIF: Expérience utilisateur enrichie
├-- 🗣️ Interface vocale complète (STT + TTS)
├-- 🌐 Interface web contrôle distant
├-- 🗺️ Cartographie et navigation avancée
├-- 📱 Application mobile companion
└-- 🔌 API externe pour extensions

LIVRABLES:
├-- Version 2.0 avec interface vocale
├-- Application mobile
└-- Documentation développeur
```

### **Phase 3: Optimisation (6-12 mois)**
```
OBJECTIF: Performance et accessibilité
├-- ⚡ Optimisation temps réel (latence <100ms)
├-- 🔋 Gestion énergie (autonomie 8h+)
├-- 🌍 Multi-langues (ES, DE, IT, etc.)
├-- ♿ Accessibilité avancée
└-- 📦 Packaging produit commercial

LIVRABLES:
├-- Version 3.0 optimisée
├-- Kits matériels prêts à l'emploi
└-- Certification accessibilité
```

## 💾 **INSTRUCTIONS POUR REPRISE DÉVELOPPEMENT**

### **Environnement de Développement**
```bash
# 1. Cloner le dépôt
git clone https://github.com/Adrien219/smart-glasses.git
cd smart-glasses

# 2. Environnement virtuel
python -m venv smartglasses-env
source smartglasses-env/bin/activate  # Linux/Mac
# OU
smartglasses-env\Scripts\activate    # Windows

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
cp config/settings.example.py config/settings.py
# Éditer settings.py avec vos paramètres

# 5. Test
cd raspberry-pi
python main.py
```

### **Structure pour Nouveau Développeur**
```
POINTS D'ENTRÉE PRINCIPAUX:
├-- 🚀 main.py → Contrôleur principal
├-- ⚙️ config/settings.py → Configuration
├-- 🔌 hardware/ → Communication matérielle
├-- 🧠 core/ → Intelligence artificielle  
└-- 📚 docs/ → Documentation

POINTS D'ATTENTION:
├-- Gestion des threads: toujours utiliser daemon=True
├-- Communication série: fermer proprement dans finally
├-- Mémoire: libérer explicitement les modèles IA lourds
└-- Logs: utiliser le système de logging intégré
```

### **Tests et Débogage**
```python
# Test individuel modules
python -c "from hardware.arduino_communication import ArduinoCommunication; a = ArduinoCommunication(); print(a.connect())"

# Test caméra seule  
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()"

# Mode debug
export SMARTGLASSES_DEBUG=1
python main.py
```

Cette documentation technique ultra-détaillée permet à n'importe quel développeur de reprendre le projet en ayant une compréhension complète de l'architecture, des composants, de leur état actuel et des prochaines étapes. Le système est fonctionnel mais nécessite des améliorations de stabilité et de nouvelles fonctionnalités pour atteindre sa pleine potentiel. 🚀