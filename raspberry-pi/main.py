#!/usr/bin/env python3
# COORDINATEUR PRINCIPAL - Version corrigée

import cv2
import time
import threading
from camera_processor import CameraProcessor
from arduino_communicator import ArduinoCommunicator

class SmartGlassesController:
    def __init__(self):
        # Essaie différentes IPs possibles pour l'ESP32
        self.esp32_ip = self.find_esp32_ip()
        self.arduino_port = None  # Auto-détection
        
        # Modules
        self.camera_processor = CameraProcessor(self.esp32_ip)
        self.arduino_comm = ArduinoCommunicator(self.arduino_port)
        
        self.current_mode = "navigation"
        self.running = True

    def find_esp32_ip(self):
        """Trouve automatiquement l'IP de l'ESP32"""
        possible_ips = [
            "10.231.158.139",  # Ton IP précédente
            "192.168.1.100",
            "192.168.1.101", 
            "192.168.0.100",
            "192.168.0.101"
        ]
        
        for ip in possible_ips:
            try:
                import requests
                response = requests.get(f"http://{ip}/status", timeout=2)
                if "ESP32" in response.text:
                    print(f"🎯 ESP32 trouvé à: {ip}")
                    return ip
            except:
                continue
        
        print("⚠️  ESP32 non trouvé - utilisation de l'IP par défaut")
        return "10.231.158.139"  # IP par défaut

    def setup(self):
        print("🚀 Initialisation Smart Glasses...")
        
        # Initialisation modules
        self.arduino_comm.connect()
        self.camera_processor.setup()
        
        print("✅ Système prêt")

    def run(self):
        try:
            print("🤖 Démarrage des threads...")
            
            # Démarrer les threads
            threads = []
            
            # Thread ESP32 seulement si accessible
            if self.camera_processor.test_esp32_connection():
                threads.append(threading.Thread(target=self.camera_processor.process_esp32_stream))
            else:
                print("⚠️  Thread ESP32 désactivé (connexion impossible)")
            
            # Thread RPi camera
            threads.append(threading.Thread(target=self.camera_processor.process_rpi_camera))
            
            # Thread Arduino
            threads.append(threading.Thread(target=self.arduino_comm.read_loop, 
                                          args=(self.handle_arduino_message,)))
            
            for thread in threads:
                thread.daemon = True
                thread.start()
                print(f"✅ Thread démarré: {thread.name}")
            
            # Boucle principale
            print("🔄 Boucle principale démarrée")
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé...")
            self.cleanup()
        except Exception as e:
            print(f"❌ Erreur dans run(): {e}")
            self.cleanup()

    def handle_arduino_message(self, message):
        """Traite les messages de l'Arduino"""
        print(f"📨 Arduino: {message}")
        
        if message.startswith("BUTTON:"):
            button_id = int(message.split(":")[1])
            self.handle_button_press(button_id)
        elif message.startswith("DISTANCE:") and self.current_mode == "navigation":
            distance = float(message.split(":")[1])
            if distance < 50.0:
                self.arduino_comm.send_command("BUZZER:300,800")

    def handle_button_press(self, button_id):
        """Gestion des boutons"""
        modes = {
            1: "object_detection",
            2: "face_recognition", 
            3: "text_reading",
            4: "ai_assistant",
            5: "navigation"
        }
        
        if button_id in modes:
            self.change_mode(modes[button_id])

    def change_mode(self, new_mode):
        """Changement de mode"""
        print(f"🔄 Mode: {self.current_mode} → {new_mode}")
        self.current_mode = new_mode
        
        # Feedback Arduino
        colors = {
            "navigation": "255,0,0",
            "object_detection": "0,255,0", 
            "face_recognition": "0,0,255",
            "text_reading": "255,165,0",
            "ai_assistant": "128,0,128"
        }
        
        if new_mode in colors:
            self.arduino_comm.send_command(f"LED:{colors[new_mode]}")

    def cleanup(self):
        self.running = False
        self.arduino_comm.disconnect()
        cv2.destroyAllWindows()
        print("🧹 Nettoyage terminé")

if __name__ == "__main__":
    controller = SmartGlassesController()
    controller.setup()
    controller.run()