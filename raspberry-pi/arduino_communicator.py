import serial
import time
import sys

class ArduinoCommunicator:
    def __init__(self, port=None):
        # Ports à essayer selon l'OS
        if port:
            self.possible_ports = [port]
        else:
            if sys.platform.startswith('win'):
                self.possible_ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7']
            else:  # Linux/Raspberry Pi
                self.possible_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyUSB1']
        
        self.serial_conn = None
        
    def connect(self):
        for port in self.possible_ports:
            try:
                print(f"🔌 Tentative de connexion sur {port}...")
                self.serial_conn = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Attente initialisation
                print(f"✅ Arduino connecté sur {port}")
                return
            except Exception as e:
                print(f"❌ Échec sur {port}: {e}")
                continue
        
        print("⚠️  Aucun Arduino détecté - Mode simulation activé")
        self.serial_conn = None
            
    def send_command(self, command):
        if self.serial_conn:
            try:
                self.serial_conn.write(f"{command}\n".encode())
                print(f"📤 Command envoyée: {command}")
            except Exception as e:
                print(f"❌ Erreur envoi Arduino: {e}")
        else:
            print(f"🔧 [SIMULATION] Command: {command}")
                
    def read_loop(self, callback):
        while True:
            if self.serial_conn and self.serial_conn.in_waiting > 0:
                try:
                    line = self.serial_conn.readline().decode().strip()
                    if line:
                        callback(line)
                except Exception as e:
                    print(f"❌ Erreur lecture Arduino: {e}")
            else:
                # Simulation de données pour le test
                time.sleep(1)
                # callback("BUTTON:1")  # Décommente pour simuler des boutons
                
            time.sleep(0.1)
            
    def disconnect(self):
        if self.serial_conn:
            self.serial_conn.close()