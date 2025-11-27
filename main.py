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

# ------------------- VoiceAssistant corrigé -------------------
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
            self.speak(f"{name} est devant vous")

    def announce_text(self, text):
        if text:
            self.speak(f"Texte détecté: {text}")

    def cleanup(self):
        if self.engine:
            self.engine.stop()

# ------------------- Fin VoiceAssistant -------------------

class SmartGlassesSystem:
    def __init__(self):
        # Ajout du mode headless
        self.headless_mode = False

        print("🚀 Initialisation des Lunettes Intelligentes...")

        # Initialiser Arduino
        self.arduino_comm = ArduinoCommunication()

        # Initialiser caméra Raspberry Pi
        self.camera = CameraManager(
            camera_id=Config.CAMERA_ID,
            resolution=Config.CAMERA_RESOLUTION
        )

        # Gestion ESP32 simplifiée
        self.esp32_cam = None
        self.esp32_ip = "10.231.158.139"

        try:
            # Utiliser le module simple (single camera)
            from hardware.esp32_simple_camera import ESP32SimpleCamera
            self.esp32_cam = ESP32SimpleCamera(self.esp32_ip)
            print("✅ ESP32-CAM (single) initialisée")
        except ImportError as e:
            print(f"⚠️ ESP32 simple non disponible: {e}")
            # Fallback vers simulation
            self.esp32_cam = type('MockESP32', (), {
                'ip': self.esp32_ip,
                'is_connected': False,
                'toggle_flash': lambda: False,
                'get_frame': lambda: None
            })()
            print("🔧 Mode simulation ESP32 activé")
        except Exception as e:
            print(f"⚠️ Erreur initialisation ESP32: {e}")
            self.esp32_cam = None

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

        # Commandes vocales
        self.voice_commands = VoiceCommands(self)

        # États du système
        self.current_mode = "navigation"
        self.running = False
        self.show_detections = True
        self.last_mode_change = 0
        self.last_button_time = 0
        self.button_cooldown = 1.0

        # CORRECTION : Appliquer le correctif reconnaissance faciale
        self.fix_face_recognizer()

        # Callback pour messages Arduino
        if self.arduino_comm.connected:
            self.arduino_comm.add_message_callback(self.handle_arduino_message)

    def fix_face_recognizer(self):
        """Correction d'urgence pour la reconnaissance faciale"""
        print("🔧 Application correctif reconnaissance faciale...")
        
        # Méthode de secours
        def safe_detect_faces(frame):
            try:
                # Version ultra-simplifiée
                return []
            except Exception as e:
                print(f"❌ Erreur même avec correctif: {e}")
                return []
        
        # Remplacer la méthode problématique
        if hasattr(self, 'face_recognizer'):
            self.face_recognizer.detect_faces = safe_detect_faces
            print("✅ Correctif appliqué - Reconnaissance faciale désactivée temporairement")

    def handle_arduino_message(self, message):
        """Gérer les messages en provenance de l'Arduino"""
        try:
            print(f"📨 ARDUINO: {message}")
            
            if message.startswith("BUTTON:"):
                self.handle_button_press(message)
            elif message.startswith("JOYSTICK:"):
                self.handle_joystick(message)
            elif message.startswith("MODE_CHANGE:"):
                self.handle_mode_change(message)
            elif message.startswith("LIGHT_LEVEL:"):
                # Traitement optionnel du niveau de lumière
                pass
                
        except Exception as e:
            print(f"❌ Erreur traitement message Arduino: {e}")

    def handle_button_press(self, message):
        """Gérer l'appui sur un bouton"""
        try:
            button_id = message.split(":")[1]
            print(f"🔘 Bouton {button_id} pressé")
            
            # Actions selon le bouton
            if button_id == "1":
                self.switch_camera()
            elif button_id == "2":
                self.toggle_esp32_flash()
            elif button_id == "3":
                self.voice_assistant.speak("Fonction bouton 3")
                
        except Exception as e:
            print(f"❌ Erreur bouton: {e}")

    def handle_joystick(self, message):
        """Gérer le joystick"""
        try:
            coords = message.split(":")[1].split(",")
            x, y = int(coords[0]), int(coords[1])
            print(f"🎮 Joystick: X={x}, Y={y}")
            
            if x < 300:
                self.voice_assistant.speak("Gauche")
            elif x > 700:
                self.voice_assistant.speak("Droite")
                
        except Exception as e:
            print(f"❌ Erreur joystick: {e}")

    def handle_mode_change(self, message):
        """Changer le mode opérationnel"""
        try:
            mode_id = int(message.split(":")[1])
            modes = {
                0: "navigation",
                1: "object", 
                2: "face",
                3: "text",
                4: "ai"
            }
            new_mode = modes.get(mode_id, "navigation")
            
            if new_mode != self.current_mode:
                self.current_mode = new_mode
                print(f"🔄 Mode changé: {self.current_mode}")
                self.voice_assistant.speak(f"Mode {self.current_mode}")
                
        except Exception as e:
            print(f"❌ Erreur changement mode: {e}")

    def set_mode(self, mode):
        """Définir le mode manuellement"""
        if mode in ["navigation", "object", "face", "text", "ai"]:
            self.current_mode = mode
            print(f"🎯 Mode défini: {self.current_mode}")

    def switch_camera(self):
        """Changer de caméra"""
        try:
            new_cam = self.camera.switch_camera()
            self.voice_assistant.speak(f"Caméra {new_cam}")
        except Exception as e:
            print(f"❌ Erreur changement caméra: {e}")

    def toggle_esp32_flash(self):
        """Activer/désactiver le flash ESP32 - Version corrigée"""
        try:
            print("⚠️ Flash ESP32 temporairement désactivé (mode debug)")
            self.voice_assistant.speak("Flash non disponible")
            return False
        except Exception as e:
            print(f"❌ Erreur flash: {e}")
            return False

    def start(self):
        """Démarrer le système"""
        print("🎯 Démarrage du système...")
        self.running = True
        self.main_loop()

    def main_loop(self):
        """Boucle principale"""
        last_processing_time = 0
        processing_interval = 1.0 / Config.CAMERA_FPS
        frame_count = 0
        last_log_time = time.time()

        print("🔄 Démarrage boucle principale...")

        while self.running:
            try:
                current_time = time.time()
                frame_count += 1

                # Log toutes les 5 secondes
                if current_time - last_log_time >= 5:
                    print(f"📊 Statut: Mode={self.current_mode}, Frames={frame_count/5:.1f}fps")
                    frame_count = 0
                    last_log_time = current_time

                # Acquisition d'une frame
                frame = self.camera.get_frame()
                if frame is None:
                    print("❌ Frame vide - attente...")
                    time.sleep(0.1)
                    continue

                # Traitement selon le mode
                if current_time - last_processing_time >= processing_interval:
                    self.process_frame(frame)
                    last_processing_time = current_time

                # Affichage
                if not self.headless_mode:
                    # Ajouter le mode actuel sur la frame
                    cv2.putText(frame, f"Mode: {self.current_mode}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, "Q=Quitter, M=Changer Mode", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    cv2.imshow("Smart Glasses - Mode: " + self.current_mode, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("🎯 Arrêt demandé par touche Q")
                        break
                    elif key == ord('m'):
                        print("🔄 Changement manuel de mode")
                        self.cycle_mode()

            except Exception as e:
                print(f"❌ Erreur boucle principale: {e}")
                time.sleep(0.1)

        self.cleanup()

    def process_frame(self, frame):
        """Traiter la frame avec une seule caméra"""
        try:
            if self.current_mode == "navigation":
                # Utiliser la caméra principale pour tout
                detections = self.object_detector.detect_objects(frame)
                self.navigation_brain.process(detections, frame_width=frame.shape[1])
                if self.show_detections:
                    self.object_detector.draw_detections(frame, detections)

            elif self.current_mode == "object":
                detections = self.object_detector.detect_objects(frame)
                if detections:
                    objects = list(set([det["class"] for det in detections]))
                    self.voice_assistant.announce_objects(objects)
                if self.show_detections:
                    self.object_detector.draw_detections(frame, detections)

            elif self.current_mode == "face":
                # Utiliser la même caméra pour les visages
                try:
                    faces = self.face_recognizer.detect_faces(frame)
                    for face in faces:
                        if isinstance(face, dict) and 'name' in face:
                            if face['name'] != "Inconnu":
                                self.voice_assistant.announce_person(face['name'])
                    if self.show_detections:
                        self.face_recognizer.draw_faces(frame, faces)
                except Exception as e:
                    print(f"❌ Erreur reconnaissance faciale: {e}")

            elif self.current_mode == "text":
                # Utiliser la même caméra pour le texte
                text_info = self.text_recognizer.extract_text(frame)
                if text_info:
                    confident_texts = [t for t in text_info if t.get('confidence', 0) > 0.6]
                    if confident_texts:
                        best_text = max(confident_texts, key=lambda x: x.get('confidence', 0))
                        self.voice_assistant.announce_text(best_text['text'])
                if self.show_detections:
                    self.text_recognizer.draw_text_areas(frame, text_info)

            elif self.current_mode == "ai":
                # Mode assistant IA - traitement minimal
                pass

        except Exception as e:
            print(f"❌ Erreur globale traitement frame: {e}")

    def cycle_mode(self):
        """Changer de mode cycliquement"""
        modes = ["navigation", "object", "face", "text", "ai"]
        current_index = modes.index(self.current_mode)
        next_index = (current_index + 1) % len(modes)
        self.current_mode = modes[next_index]
        print(f"🔄 Mode changé: {self.current_mode}")
        self.voice_assistant.speak(f"Mode {self.current_mode}")

    def cleanup(self):
        """Nettoyer les ressources"""
        print("🧹 Nettoyage des ressources...")
        self.running = False
        if self.camera:
            self.camera.release()
        if self.arduino_comm:
            self.arduino_comm.disconnect()
        if self.voice_assistant:
            self.voice_assistant.cleanup()
        cv2.destroyAllWindows()
        print("✅ Système arrêté proprement")

if __name__ == "__main__":
    try:
        glasses = SmartGlassesSystem()
        glasses.start()
    except KeyboardInterrupt:
        print("\n🎯 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {e}")
    finally:
        print("🎯 Programme terminé")