#!/usr/bin/env python3
import cv2
import time
import threading
import signal
import sys
import os
from camera_processor import CameraProcessor
from arduino_communicator import ArduinoCommunicator

class SmartGlassesController:
    def __init__(self):
        self.esp32_ip = "10.231.158.139"
        self.arduino_port = None
        
        self.camera_processor = CameraProcessor(self.esp32_ip)
        self.arduino_comm = ArduinoCommunicator(self.arduino_port)
        
        self.current_mode = "navigation"
        self.running = True
        
        # Capture du signal Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handler ULTRA ROBUSTE qui force l'arrêt"""
        print(f"\n💀 SIGNAL {signum} - ARRÊT FORCÉ IMMÉDIAT!")
        self.running = False
        self.emergency_cleanup()
        os._exit(1)  # 💀 FORCE L'ARRÊT IMMÉDIAT

    def emergency_cleanup(self):
        """Nettoyage d'urgence - NE PEUT PAS ÉCHOUER"""
        try:
            print("🚨 NETTOYAGE D'URGENCE...")
            self.running = False
            
            # 1. Fermer TOUTES les fenêtres OpenCV
            try:
                cv2.destroyAllWindows()
                # Forcer la fermeture
                for i in range(5):
                    cv2.waitKey(1)
            except:
                pass
            
            # 2. Arrêt Arduino
            try:
                if hasattr(self, 'arduino_comm'):
                    self.arduino_comm.stop()
            except:
                pass
                
            print("✅ Nettoyage d'urgence terminé")
            
        except Exception as e:
            print(f"⚠️  Erreur nettoyage d'urgence: {e}")

    def setup(self):
        """Initialisation"""
        print("🚀 Initialisation Smart Glasses...")
        self.arduino_comm.connect()
        self.camera_processor.setup()
        
        # Initialisation du modèle YOLO
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')
            print("✅ YOLOv8 initialisé avec succès!")
        except Exception as e:
            print(f"❌ Erreur initialisation YOLO: {e}")
            self.model = None
            
        print("✅ Système prêt")

    def handle_arduino_message(self, message):
        """Traitement des messages Arduino"""
        if not self.running:
            return
        print(f"📨 Arduino: {message}")
        
        if message.startswith("BUTTON:"):
            button_value = int(message.split(":")[1])
            self.handle_button_press(button_value)

    def handle_button_press(self, button_value):
        """Gestion des boutons"""
        if not self.running:
            return
            
        modes = ["navigation", "object_detection", "face_recognition", 
                "text_reading", "ai_assistant"]
        
        if 0 <= button_value < len(modes):
            new_mode = modes[button_value]
            if new_mode != self.current_mode:
                print(f"🔄 Mode: {self.current_mode} → {new_mode}")
                self.current_mode = new_mode

    def run(self):
        """Boucle principale ULTRA SIMPLE"""
        try:
            print("🤖 Démarrage système...")
            
            # Démarrer UNIQUEMENT le thread Arduino en arrière-plan
            arduino_thread = threading.Thread(
                target=self.arduino_comm.read_loop,
                args=(self.handle_arduino_message,),
                daemon=True
            )
            arduino_thread.start()
            print("✅ Thread Arduino démarré")
            
            # ✅ LA CAMÉRA DANS LE THREAD PRINCIPAL - CRITIQUE !
            print("📷 Démarrage caméra RPi dans thread principal...")
            self.camera_processor.process_rpi_camera_main_thread(self)
            
        except KeyboardInterrupt:
            print("\n🛑 Ctrl+C dans run()")
        except Exception as e:
            print(f"❌ Erreur run(): {e}")
        finally:
            self.emergency_cleanup()

if __name__ == "__main__":
    controller = None
    try:
        controller = SmartGlassesController()
        controller.setup()
        controller.run()
    except KeyboardInterrupt:
        print("\n🎯 Arrêt demandé par Ctrl+C")
        if controller:
            controller.emergency_cleanup()
    except Exception as e:
        print(f"💥 ERREUR: {e}")
        if controller:
            controller.emergency_cleanup()
    finally:
        print("🎯 Programme TERMINÉ")
        # Force la fermeture si bloqué
        try:
            sys.exit(0)
        except:
            os._exit(0)