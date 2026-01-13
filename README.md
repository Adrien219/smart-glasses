# 🕶️ Smart Glasses for Visually Impaired

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4B-red.svg)
![Arduino](https://img.shields.io/badge/Arduino-Uno-green.svg)

## 📋 Description
A smart glasses system designed to assist visually impaired individuals with real-time obstacle detection, navigation guidance, and environmental awareness using Raspberry Pi 4 and Arduino.

## ✨ Features
- **🎯 Real-time obstacle detection** using ultrasonic sensors
- **🔊 Voice alerts** for distance warnings
- **💡 Ambient light sensing** for environmental awareness
- **📱 Modular architecture** for easy expansion
- **🔌 Arduino integration** for sensor data collection

## 🛠️ Hardware Requirements
- Raspberry Pi 4 (4GB recommended)
- Arduino Uno/Nano
- HC-SR04 Ultrasonic Sensor
- LDR Light Sensor
- Microphone & Speaker
- Power Bank

## 🚀 Quick Start
```bash
# Clone the repository
git clone https://github.com/jmk/smart-glasses.git
cd smart-glasses

# Test basic functionality
python3 final_test_minimal.py

# Run advanced tests
python3 test_advanced.py
# Créer un .gitignore complet
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
pycache/
*.pyc

# Environnements
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# Modèles ML volumineux (ne pas pousser sur GitHub)
*.pt
*.pth
*.h5
*.model
yolov8n.pt

# Données d'entraînement
known_faces/
*.jpg
*.jpeg
*.png
*.pkl

# Configuration locale
config/local_*.yaml
*.local

# Fichiers temporaires
tmp/
temp/
*.tmp
*.temp
*.backup.*

# Fichiers système
.DS_Store
Thumbs.db

# Fichiers compilés Arduino
*.hex
*.elf
*.eep
*.bin

# Packages
*.7z
*.dmg
*.gz
*.iso
*.jar
*.rar
*.tar
*.zip

# Sécurité
secrets.yaml
credentials.json
*.pem
*.key

# Télémetrie/données
telemetry/

# Fichiers de debug
debug_*.py
test_*.py
*_test.py
