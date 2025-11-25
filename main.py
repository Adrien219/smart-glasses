import cv2
import time
import sys
import os
import numpy as np

# Pour éviter les messages ALSA/Jack sur Raspberry Pi
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["AUDIODEV"] = "hw:0,0"
DEVNULL = open(os.devnull, "w")

sys.path.append(os.path.join(os.path.dirname(__file__)))

from hardware.camera_manager import CameraManager
from hardware.arduino_communication import ArduinoCommunication
from core.object_detector import ObjectDetector
from core.face_recognizer import FaceRecognizer
from core.text_recognizer import TextRecognizer
from core.navigation_brain import NavigationBrain
from core.ai_assistant import AIAssistant
from core.voice_commands import VoiceCommands
from config.settings import Config

# ---------------- VoiceAssistant corrigé ----------------
import threading
import queue
import platform
import subprocess

IS_PI = platform.machine().startswith("arm") or platform.system() == "Linux"

class VoiceAssistant:
    def __init__(self, arduino_comm=None):
        print("🎤 Initialisation de l'assistant vocal...")
        self.arduino_comm = arduino_comm
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.last_speech_time = 0
        self.speech_cooldown = 3.0

        try:
            if IS_PI:
                print("🔧 Mode Raspberry Pi → utilisation espeak-ng")
                self.engine = None
            else:
                import pyttsx3
                print("🔧 Mode Desktop → utilisation pyttsx3")
                self.engine = pyttsx3.init()
                self.setup_voice()

            self.process_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.process_thread.start()
            print("✅ Assistant vocal initialisé!")

        except Exception as e:
            print(f"❌ Erreur initialisation assistant vocal: {e}")
            self.engine = None

    def setup_voice(self):
        if self.engine is None:
            return
        voices = self.engine.getProperty('voices')
        french_voice = None
        for voice in voices:
            if 'french' in voice.name.lower() or 'français' in voice.name.lower():
                french_voice = voice.id
                break
        if french_voice:
            self.engine.setProperty('voice', french_voice)
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 0.9)

    def speak(self, text, priority=False, haptic_feedback=True):
        current_time = time.time()
        if current_time - self.last_speech_time < self.speech_cooldown and not priority:
            return
        self.speech_queue.put((text, haptic_feedback))
        self.last_speech_time = current_time

    def _process_queue(self):
        while True:
            try:
                if not self.speech_queue.empty() and not self.is_speaking:
                    text, haptic_feedback = self.speech_queue.get()
                    self.is_speaking = True

                    # Retour haptique
                    if haptic_feedback and self.arduino_comm:
                        self.arduino_comm.simple_beep()

                    if IS_PI:
                        subprocess.run(["espeak-ng", "-v", "fr", text], stdout=DEVNULL, stderr=DEVNULL)
                    elif self.engine:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    else:
                        print(f"🔊 {text}")

                    self.is_speaking = False
                    time.sleep(0.05)
            except Exception as e:
                print(f"❌ Erreur synthèse vocale: {e}")
                self.is_speaking = False
                time.sleep(0.5)

    def announce_objects(self, objects_list):
        if objects_list:
            self.speak(f"Objets détectés: {', '.join(objects_list)}")

    def announce_person(self, name):
        if name.lower() == "inconnu":
            self.speak("Personne inconnue détectée")
        else:
            self.speak(f"{name} est devant toi")

    def announce_text(self, text):
        if text:
            self.speak(f"Texte détecté: {text}")

    def cleanup(self):
        if self.engine:
            self.engine.stop()

# ---------------- Fin VoiceAssistant ----------------

class SmartGlassesSystem:
    def __init__(self):
        print("🚀 Initialisation des Lunettes Intelligentes...")
        
        # Initialiser Arduino
        self.arduino_comm = ArduinoCommunication()
        
        # Initialiser caméra Raspberry Pi
        self.camera = CameraManager(
            camera_id=Config.CAMERA_ID,
            resolution=Config.CAMERA_RESOLUTION
        )
        
        # Initialiser ESP32-CAM (avec gestion d'erreur)
        self.esp32_cam = None
        try:
            from hardware.esp32_camera import ESP32Camera
            if hasattr(Config, 'ESP32_CAM_URL'):
                self.esp32_cam = ESP32Camera(Config.ESP32_CAM_URL)
                print("✅ ESP32-CAM initialisée")
            else:
                print("⚠️  ESP32_CAM_URL non configurée - ESP32 désactivé")
        except ImportError as e:
            print(f"⚠️  ESP32-CAM non disponible: {e}")
        except Exception as e:
            print(f"⚠️  Erreur initialisation ESP32: {e}")
        
        # Initialiser les modules de traitement
        self.object_detector = ObjectDetector()
        self.face_recognizer = FaceRecognizer()
        self.text_recognizer = TextRecognizer()
        self.voice_assistant = VoiceAssistant(arduino_comm=self.arduino_comm)

        # NavigationBrain
        self.navigation_brain = NavigationBrain(
            voice=self.voice_assistant,
            arduino_comm=self.arduino_comm
        )
        
        self.ai_assistant = AIAssistant(self.voice_assistant)
        
        # ✅ AJOUT: Commandes vocales
        self.voice_commands = VoiceCommands(self)
        
        # États du système
        self.current_mode = "navigation"
        self.running = False
        self.show_detections = True
        self.last_mode_change = 0
        self.last_button_time = 0
        self.button_cooldown = 1.0
        
        # Callback pour messages Arduino
        if self.arduino_comm.connected:
            self.arduino_comm.add_message_callback(self.handle_arduino_message)

    # ... Le reste de ton main.py reste identique ...
    # handle_arduino_message, handle_button_press, handle_joystick, handle_mode_change, set_mode
    # start, main_loop, process_frame, draw_overlay, save_image, cleanup

if __name__ == "__main__":
    glasses = SmartGlassesSystem()
    glasses.start()
