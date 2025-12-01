import cv2
import time
import sys
import os
import numpy as np

# Pour éviter les messages ALSA/Jack sur Raspberry Pi
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["AUDIODEV"] = "null"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

# Redirection des erreurs audio
DEVNULL = open(os.devnull, "w")
sys.stderr = DEVNULL

sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import des modules avec gestion d'erreur améliorée
try:
    from hardware.camera_manager import CameraManager
    from hardware.arduino_communication import ArduinoCommunication
    from core.object_detector import ObjectDetector
    from core.face_recognizer import FaceRecognizer
    from core.text_recognizer import TextRecognizer
    from core.navigation_brain import NavigationBrain
    from core.ai_assistant import AIAssistant
    from core.voice_commands import VoiceCommands
    from config.settings import Config
except ImportError as e:
    print(f"❌ Erreur import modules: {e}")
    print("🔧 Vérification des fichiers...")
    # Création des dossiers manquants si nécessaire
    for folder in ['hardware', 'core', 'config']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Dossier créé: {folder}")

# ------------------- VoiceAssistant optimisé -------------------
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
        self.speech_cooldown = 2.0  # Réduit le cooldown

        try:
            if IS_PI:
                print("🔧 Mode Raspberry Pi → utilisation espeak-ng")
                self.engine = None
                # Test espeak
                result = subprocess.run(["which", "espeak-ng"], capture_output=True)
                if result.returncode != 0:
                    print("⚠️ espeak-ng non trouvé, utilisation de espeak")
            else:
                try:
                    import pyttsx3
                    print("🔧 Mode Desktop → utilisation pyttsx3")
                    self.engine = pyttsx3.init()
                    self.setup_voice()
                except Exception as e:
                    print(f"⚠️ pyttsx3 non disponible: {e}")
                    self.engine = None

            self.process_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.process_thread.start()
            print("✅ Assistant vocal initialisé!")

        except Exception as e:
            print(f"❌ Erreur initialisation assistant vocal: {e}")
            self.engine = None

    def setup_voice(self):
        """Configuration de la voix"""
        if self.engine is None:
            return
        try:
            voices = self.engine.getProperty('voices')
            french_voice = None
            for voice in voices:
                if 'french' in voice.name.lower() or 'français' in voice.name.lower():
                    french_voice = voice.id
                    break
            
            if french_voice:
                self.engine.setProperty('voice', french_voice)
            self.engine.setProperty('rate', 160)
            self.engine.setProperty('volume', 0.8)
        except Exception as e:
            print(f"⚠️ Configuration voix échouée: {e}")

    def speak(self, text, priority=False, haptic_feedback=True):
        """Synthèse vocale avec file d'attente"""
        if not text or text.strip() == "":
            return
            
        current_time = time.time()
        if current_time - self.last_speech_time < self.speech_cooldown and not priority:
            return
            
        self.speech_queue.put((text, haptic_feedback))
        self.last_speech_time = current_time

    def _process_queue(self):
        """Traitement de la file d'attente vocale"""
        while True:
            try:
                text, haptic_feedback = self.speech_queue.get()
                self.is_speaking = True

                # Retour haptique
                if haptic_feedback and self.arduino_comm:
                    try:
                        self.arduino_comm.simple_beep()
                    except:
                        pass

                # Synthèse vocale
                if IS_PI:
                    try:
                        subprocess.run(["espeak", "-v", "fr+f2", "-s", "150", text], 
                                     stdout=DEVNULL, stderr=DEVNULL, timeout=10)
                    except:
                        subprocess.run(["espeak", text], stdout=DEVNULL, stderr=DEVNULL, timeout=10)
                elif self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    print(f"🔊 {text}")

                self.is_speaking = False
                time.sleep(0.1)  # Réduit le délai
                
            except Exception as e:
                print(f"❌ Erreur synthèse vocale: {e}")
                self.is_speaking = False
                time.sleep(0.5)

    def announce_objects(self, objects_list):
        """Annonce des objets détectés"""
        if objects_list and len(objects_list) > 0:
            # Limiter à 3 objets pour éviter les annonces trop longues
            limited_objects = objects_list[:3]
            self.speak(f"Objets: {', '.join(limited_objects)}")

    def announce_person(self, name):
        """Annonce d'une personne"""
        if name.lower() == "inconnu":
            self.speak("Personne inconnue")
        else:
            self.speak(f"{name} détecté")

    def announce_text(self, text):
        """Annonce de texte"""
        if text and len(text.strip()) > 0:
            # Limiter la longueur du texte
            if len(text) > 50:
                text = text[:47] + "..."
            self.speak(f"Texte: {text}")

    def cleanup(self):
        """Nettoyage des ressources"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass

# ------------------- Fin VoiceAssistant -------------------

class SmartGlassesSystem:
    def __init__(self):
        # Mode headless pour fonctionnement sans affichage
        self.headless_mode = False
        self.running = False

        print("🚀 Initialisation des Lunettes Intelligentes...")

        # Initialisation Arduino avec gestion d'erreur
        try:
            self.arduino_comm = ArduinoCommunication()
            print("✅ Arduino initialisé")
        except Exception as e:
            print(f"❌ Erreur Arduino: {e}")
            self.arduino_comm = None

        # Initialisation caméra avec fallback
        self.camera = None
        try:
            self.camera = CameraManager(
                camera_id=getattr(Config, 'CAMERA_ID', 0),
                resolution=getattr(Config, 'CAMERA_RESOLUTION', (640, 480))
            )
            print("✅ Caméra initialisée")
        except Exception as e:
            print(f"❌ Erreur caméra: {e}")

        # Gestion ESP32 - Version simple sans blocage
        self.esp32_cam = None
        self.esp32_ip = "10.231.158.139"

        class SimpleESP32:
            def __init__(self, ip):
                self.ip = ip
                self.is_connected = False
                self.current_frame = None
                
            def get_frame(self):
                return None
                
            def toggle_flash(self):
                print("⚠️ Flash ESP32 non disponible")
                return False

        self.esp32_cam = SimpleESP32(self.esp32_ip)
        print("🔧 ESP32 en mode simulation")

        # Initialisation des modules IA avec fallback
        try:
            self.object_detector = ObjectDetector()
            print("✅ Détecteur d'objets initialisé")
        except Exception as e:
            print(f"❌ Erreur détecteur objets: {e}")
            self.object_detector = None

        # Initialisation reconnaissance faciale
        self.face_recognizer = None
        self.face_recognition_enabled = False
        self.setup_face_recognition()

        try:
            self.text_recognizer = TextRecognizer()
            print("✅ OCR initialisé")
        except Exception as e:
            print(f"❌ Erreur OCR: {e}")
            self.text_recognizer = None

        # Initialisation Voice Assistant
        self.voice_assistant = VoiceAssistant(arduino_comm=self.arduino_comm)

        # Modules optionnels
        try:
            self.navigation_brain = NavigationBrain(
                voice=self.voice_assistant,
                arduino_comm=self.arduino_comm
            )
        except:
            self.navigation_brain = None

        try:
            self.ai_assistant = AIAssistant(self.voice_assistant)
        except:
            self.ai_assistant = None

        try:
            self.voice_commands = VoiceCommands(self)
        except:
            self.voice_commands = None

        # États du système
        self.current_mode = "navigation"
        self.show_detections = True
        self.last_mode_change = 0
        self.modes = ["navigation", "object", "face", "text", "ai"]

        # Callback pour messages Arduino
        if self.arduino_comm and hasattr(self.arduino_comm, 'add_message_callback'):
            self.arduino_comm.add_message_callback(self.handle_arduino_message)

        print("✅ Système initialisé avec succès!")

    def setup_face_recognition(self):
        """Configuration de la reconnaissance faciale avec known_faces"""
        try:
            # Utiliser le vrai module de reconnaissance faciale
            from core.face_recognizer import FaceRecognizer
            self.face_recognizer = FaceRecognizer()
            self.face_recognition_enabled = True
            print("✅ Reconnaissance faciale avancée initialisée")
            
        except Exception as e:
            print(f"❌ Erreur reconnaissance faciale avancée: {e}")
            print("🔧 Retour à la détection basique...")
            self.apply_face_recognition_fix()

    def apply_face_recognition_fix(self):
        """Correctif d'urgence pour la reconnaissance faciale"""
        print("🔧 Application correctif reconnaissance faciale...")
        
        class SafeFaceRecognizer:
            def __init__(self):
                self.face_cascade = None
                self.init_face_detection()
                
            def init_face_detection(self):
                """Initialisation de la détection faciale avec OpenCV"""
                try:
                    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    if os.path.exists(cascade_path):
                        self.face_cascade = cv2.CascadeClassifier(cascade_path)
                        print("✅ Détecteur de visages OpenCV initialisé")
                    else:
                        print("⚠️ Fichier cascade non trouvé")
                except Exception as e:
                    print(f"❌ Erreur détection faciale: {e}")
                    
            def detect_faces(self, frame):
                """Détection basique des visages"""
                if self.face_cascade is None:
                    return []
                    
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30)
                    )
                    
                    results = []
                    for (x, y, w, h) in faces:
                        results.append({
                            'bbox': (x, y, w, h),
                            'name': 'Personne',
                            'confidence': 0.8
                        })
                    return results
                except Exception as e:
                    print(f"❌ Erreur détection: {e}")
                    return []
                    
            def draw_faces(self, frame, faces):
                """Dessiner les rectangles autour des visages"""
                for face in faces:
                    if 'bbox' in face:
                        x, y, w, h = face['bbox']
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, face['name'], (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        self.face_recognizer = SafeFaceRecognizer()
        self.face_recognition_enabled = False
        print("✅ Correctif appliqué - Détection basique activée")

    def handle_arduino_message(self, message):
        """Gérer les messages Arduino"""
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
            
            current_time = time.time()
            if current_time - getattr(self, 'last_button_time', 0) < 0.5:  # Anti-spam
                return
                
            self.last_button_time = current_time
            
            if button_id == "1":
                self.switch_camera()
            elif button_id == "2":
                self.toggle_esp32_flash()
            elif button_id == "3":
                self.voice_assistant.speak("Bouton 3")
                
        except Exception as e:
            print(f"❌ Erreur bouton: {e}")

    def handle_joystick(self, message):
        """Gérer le joystick"""
        try:
            coords = message.split(":")[1].split(",")
            x, y = int(coords[0]), int(coords[1])
            
            # Seuils ajustés pour éviter les annonces trop fréquentes
            if x < 200:
                self.voice_assistant.speak("Gauche", haptic_feedback=False)
            elif x > 800:
                self.voice_assistant.speak("Droite", haptic_feedback=False)
                
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

    def switch_camera(self):
        """Changer de caméra"""
        try:
            if self.camera and hasattr(self.camera, 'switch_camera'):
                new_cam = self.camera.switch_camera()
                self.voice_assistant.speak(f"Caméra {new_cam}")
            else:
                self.voice_assistant.speak("Changement caméra indisponible")
        except Exception as e:
            print(f"❌ Erreur changement caméra: {e}")
            self.voice_assistant.speak("Erreur caméra")

    def toggle_esp32_flash(self):
        """Activer/désactiver le flash ESP32"""
        try:
            if self.esp32_cam and hasattr(self.esp32_cam, 'toggle_flash'):
                result = self.esp32_cam.toggle_flash()
                if result:
                    self.voice_assistant.speak("Flash activé")
                else:
                    self.voice_assistant.speak("Flash désactivé")
            else:
                print("⚠️ Flash ESP32 non disponible")
                self.voice_assistant.speak("Flash non disponible")
        except Exception as e:
            print(f"❌ Erreur flash: {e}")
            self.voice_assistant.speak("Erreur flash")

    def start(self):
        """Démarrer le système"""
        if not self.camera:
            print("❌ Aucune caméra disponible - arrêt")
            return
            
        print("🎯 Démarrage du système...")
        self.running = True
        self.main_loop()

    def main_loop(self):
        """Boucle principale optimisée"""
        last_processing_time = 0
        processing_interval = 1.0 / getattr(Config, 'CAMERA_FPS', 10)  # Fallback à 10 FPS
        frame_count = 0
        last_log_time = time.time()
        last_frame_time = time.time()

        print("🔄 Démarrage boucle principale...")

        while self.running:
            try:
                current_time = time.time()
                frame_count += 1

                # Log périodique (toutes les 10 secondes)
                if current_time - last_log_time >= 10:
                    fps = frame_count / (current_time - last_log_time)
                    print(f"📊 Statut: Mode={self.current_mode}, FPS={fps:.1f}")
                    frame_count = 0
                    last_log_time = current_time

                # Acquisition frame avec timeout
                frame_start = time.time()
                frame = None
                
                if self.camera:
                    frame = self.camera.get_frame()
                
                if frame is None:
                    # Attente réduite pour frame vide
                    time.sleep(0.05)
                    continue

                frame_time = time.time() - frame_start
                if frame_time > 0.1:  # Si capture trop lente
                    print(f"⚠️ Capture lente: {frame_time:.2f}s")

                # Traitement selon le mode (avec intervalle)
                if current_time - last_processing_time >= processing_interval:
                    self.process_frame(frame)
                    last_processing_time = current_time

                # Affichage (optionnel)
                if not self.headless_mode:
                    self.display_frame(frame)

                # Gestion des touches
                if not self.headless_mode:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("🎯 Arrêt demandé par touche Q")
                        break
                    elif key == ord('m'):
                        self.cycle_mode()
                    elif key == ord('d'):
                        self.show_detections = not self.show_detections
                        print(f"🔍 Détections: {'ON' if self.show_detections else 'OFF'}")

                # Petite pause pour éviter la surcharge CPU
                time.sleep(0.01)

            except KeyboardInterrupt:
                print("\n🎯 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                print(f"❌ Erreur boucle principale: {e}")
                time.sleep(0.1)  # Pause plus longue en cas d'erreur

        self.cleanup()

    def display_frame(self, frame):
        """Affichage de la frame avec informations"""
        try:
            # Ajouter les informations sur la frame
            cv2.putText(frame, f"Mode: {self.current_mode}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Afficher le statut de la reconnaissance faciale
            if self.current_mode == "face":
                if self.esp32_cam and self.esp32_cam.is_connected:
                    cam_source = "ESP32"
                else:
                    cam_source = "USB"
                
                status = f"Reconnaissance: {cam_source} - {'Avancée' if self.face_recognition_enabled else 'Basique'}"
                cv2.putText(frame, status, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            cv2.putText(frame, "Q=Quitter, M=Mode, D=Détections", (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            cv2.imshow("Smart Glasses - " + self.current_mode, frame)
        except Exception as e:
            print(f"❌ Erreur affichage: {e}")

    def process_frame(self, frame):
        """Traiter la frame selon le mode actuel"""
        try:
            if self.current_mode == "navigation":
                self.process_navigation_mode(frame)
            elif self.current_mode == "object":
                self.process_object_mode(frame)
            elif self.current_mode == "face":
                self.process_face_mode(frame)
            elif self.current_mode == "text":
                self.process_text_mode(frame)
            elif self.current_mode == "ai":
                self.process_ai_mode(frame)
                
        except Exception as e:
            print(f"❌ Erreur traitement frame: {e}")

    def process_navigation_mode(self, frame):
        """Mode navigation avec détection d'objets"""
        if self.object_detector:
            detections = self.object_detector.detect_objects(frame)
            if self.navigation_brain:
                self.navigation_brain.process(detections, frame_width=frame.shape[1])
            if self.show_detections:
                self.object_detector.draw_detections(frame, detections)

    def process_object_mode(self, frame):
        """Mode détection d'objets"""
        if self.object_detector:
            detections = self.object_detector.detect_objects(frame)
            if detections:
                objects = list(set([det.get("class", "inconnu") for det in detections]))
                self.voice_assistant.announce_objects(objects)
            if self.show_detections:
                self.object_detector.draw_detections(frame, detections)

    def process_face_mode(self, frame):
        """Mode reconnaissance faciale simplifié"""
        if self.face_recognizer:
            try:
                faces = self.face_recognizer.detect_faces(frame)
                
                # Annoncer UNIQUEMENT si changement
                if not hasattr(self, 'last_face_names'):
                    self.last_face_names = []
                    
                current_names = [face['name'] for face in faces if face['name'] != "Inconnu"]
                current_names = list(set(current_names))  # Supprimer les doublons
                
                # Vérifier si les noms ont changé
                if current_names != self.last_face_names:
                    if current_names:
                        self.voice_assistant.speak(f"Personnes: {', '.join(current_names)}")
                    elif faces:
                        self.voice_assistant.speak(f"{len(faces)} personne(s) inconnue(s)")
                    
                    self.last_face_names = current_names
                    
                if self.show_detections:
                    self.face_recognizer.draw_faces(frame, faces)
                    
            except Exception as e:
                print(f"❌ Erreur reconnaissance faciale: {e}")

    def process_text_mode(self, frame):
        """Mode reconnaissance de texte"""
        if self.text_recognizer:
            text_info = self.text_recognizer.extract_text(frame)
            if text_info:
                confident_texts = [t for t in text_info if t.get('confidence', 0) > 0.5]
                if confident_texts:
                    best_text = max(confident_texts, key=lambda x: x.get('confidence', 0))
                    self.voice_assistant.announce_text(best_text.get('text', ''))
            if self.show_detections:
                self.text_recognizer.draw_text_areas(frame, text_info)

    def process_ai_mode(self, frame):
        """Mode assistant IA"""
        if self.ai_assistant:
            # Traitement IA optionnel
            pass
        cv2.putText(frame, "Mode Assistant IA", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    def cycle_mode(self):
        """Changer de mode cycliquement"""
        current_index = self.modes.index(self.current_mode)
        next_index = (current_index + 1) % len(self.modes)
        self.current_mode = self.modes[next_index]
        print(f"🔄 Mode changé: {self.current_mode}")
        self.voice_assistant.speak(f"Mode {self.current_mode}")

    def cleanup(self):
        """Nettoyer les ressources"""
        print("🧹 Nettoyage des ressources...")
        self.running = False
        
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
                
        if self.arduino_comm:
            try:
                self.arduino_comm.disconnect()
            except:
                pass
                
        if self.voice_assistant:
            try:
                self.voice_assistant.cleanup()
            except:
                pass
                
        try:
            cv2.destroyAllWindows()
        except:
            pass
            
        try:
            DEVNULL.close()
        except:
            pass
            
        print("✅ Système arrêté proprement")

if __name__ == "__main__":
    try:
        glasses = SmartGlassesSystem()
        glasses.start()
    except KeyboardInterrupt:
        print("\n🎯 Arrêt demandé par l'utilisateur (Ctrl+C)")
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🎯 Programme terminé")