import serial
import time
import threading
from serial.serialutil import SerialException

class ArduinoCommunicator:
    def __init__(self, port=None):
        self.port = port
        self.serial_conn = None
        self.running = True
        self.lock = threading.Lock()  # ⬅️ AJOUT POUR SYNCHRO
        
    def connect(self):
        """Connexion à l'Arduino avec gestion d'erreurs"""
        if self.port is None:
            print("🔌 Mode simulation Arduino")
            return True
            
        ports_to_try = ['COM3', 'COM4', '/dev/ttyUSB0', '/dev/ttyACM0'] if self.port == 'auto' else [self.port]
        
        for port in ports_to_try:
            try:
                print(f"🔌 Tentative de connexion sur {port}...")
                self.serial_conn = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Attente initialisation Arduino
                print(f"✅ Arduino connecté sur {port}")
                return True
            except Exception as e:
                print(f"❌ Échec sur {port}: {e}")
                
        print("❌ Aucun port Arduino trouvé")
        return False

    def read_loop(self, callback):
        """Boucle de lecture COMPLÈTEMENT REFONDUE"""
        print("📡 Démarrage boucle lecture Arduino...")
        
        while self.running:
            with self.lock:  # ⬅️ SYNCHRONISATION
                if self.serial_conn and self.serial_conn.is_open:
                    try:
                        if self.serial_conn.in_waiting > 0:
                            line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                            if line:
                                callback(line)
                    except SerialException as e:
                        print(f"❌ Erreur série: {e}")
                        break
                    except Exception as e:
                        print(f"❌ Erreur lecture: {e}")
                        # Continuer malgré l'erreur
                else:
                    # Mode simulation
                    time.sleep(1)
            
            time.sleep(0.01)  # Réduction charge CPU
        
        print("📡 Boucle lecture Arduino terminée")

    def send_command(self, command):
        """Envoi de commande sécurisé"""
        with self.lock:  # ⬅️ SYNCHRONISATION
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(f"{command}\n".encode())
                    return True
                except Exception as e:
                    print(f"❌ Erreur envoi commande: {e}")
            return False
    def stop(self):
        """Arrêt simple"""
        print("🔌 Arrêt Arduino...")
        self.running = False
        
        # Attendre que la boucle de lecture s'arrête
        time.sleep(0.5)
        
        with self.lock:  # ⬅️ SYNCHRONISATION CRITIQUE
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                    print("✅ Port série fermé")
                except Exception as e:
                    print(f"❌ Erreur fermeture port: {e}")