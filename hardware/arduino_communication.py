import serial
import time
import threading
import glob
import platform
from config.settings import Config

class ArduinoCommunication:
    def __init__(self):
        self.port = Config.get_arduino_port()
        self.baudrate = Config.ARDUINO_BAUDRATE
        self.timeout = Config.ARDUINO_TIMEOUT
        self.connected = False
        self.serial_conn = None
        self.message_callbacks = []
        self.receive_buffer = ""
        self.connect()

    def connect(self):
        """Connexion auto Arduino cross-platform"""
        if self.port is None:
            print("🔍 Recherche automatique de ports Arduino...")
            
            if platform.system() == "Windows":
                possible_ports = [f"COM{i}" for i in range(1, 20)]
            else:
                possible_ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
                
            print("📌 Ports détectés :", possible_ports)
            
            if not possible_ports:
                print("❌ Aucun port série trouvé. Branche Arduino.")
                self.connected = False
                return
        else:
            possible_ports = [self.port]
            
        for p in possible_ports:
            try:
                print(f"🔌 Tentative de connexion sur {p}...")
                self.serial_conn = serial.Serial(
                    port=p,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                time.sleep(2)
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                self.connected = True
                self.port = p
                print(f"✅ Connecté avec succès sur {p}")
                self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
                self.receive_thread.start()
                return
            except Exception as e:
                print(f"⚠ Impossible de se connecter sur {p}: {e}")
                
        print("❌ Aucun Arduino n'a répondu.")
        self.connected = False

    def _receive_loop(self):
        """Boucle de réception ULTRA-STABLE avec reconstruction des messages"""
        while self.connected:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    raw_bytes = self.serial_conn.read(self.serial_conn.in_waiting)
                    try:
                        chunk = raw_bytes.decode('utf-8', errors='ignore')
                        self.receive_buffer += chunk
                        while '\n' in self.receive_buffer:
                            line, self.receive_buffer = self.receive_buffer.split('\n', 1)
                            line = line.strip()
                            if line and self._is_valid_message(line):
                                self._handle_received_message(line)
                    except Exception as e:
                        self.receive_buffer = ""
                        continue
                time.sleep(0.02)
            except Exception as e:
                print(f"❌ Erreur critique réception: {e}")
                time.sleep(0.5)
                self.receive_buffer = ""

    def _is_valid_message(self, message):
        """Validation STRICTE des messages"""
        if not message or len(message) < 2:
            return False
        valid_patterns = [
            "BUTTON:", "JOYSTICK:", "MODE_CHANGE:",
            "LIGHT_LEVEL:", "DISTANCE:", "ARDUINO_READY"
        ]
        if not any(message.startswith(pattern) for pattern in valid_patterns):
            return False
        valid_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 :.,_-'
        if any(c not in valid_chars for c in message):
            return False
        return True

    def _handle_received_message(self, message):
        """Traiter les messages valides"""
        if any(message.startswith(pattern) for pattern in ["BUTTON:", "MODE_CHANGE:", "JOYSTICK:"]):
            print(f"📨 ARDUINO: {message}")
        for callback in self.message_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"❌ Erreur callback: {e}")

    def send_command(self, command):
        """Envoyer une commande de manière robuste"""
        if not self.connected:
            return False
        try:
            self.serial_conn.reset_output_buffer()
            full_command = command + '\n'
            self.serial_conn.write(full_command.encode('utf-8'))
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"❌ Erreur envoi commande: {e}")
            return False

    def set_system_mode(self, mode):
        """Définir le mode du système"""
        mode_ids = {
            "navigation": 0,
            "object": 1,
            "face": 2,
            "text": 3,
            "ai": 4
        }
        mode_id = mode_ids.get(mode, 0)
        self.send_command(f"MODE:{mode_id}")

    def get_ultrasonic_distance(self):
        """Obtenir la distance ultrasonique"""
        return self.send_command("GET_ULTRASONIC")

    def get_light_level(self):
        """Obtenir le niveau de luminosité"""
        return self.send_command("GET_LIGHT")

    def start_buzzer(self, duration=200, frequency=1000):
        """Démarrer le buzzer"""
        self.send_command(f"BUZZER:{duration}:{frequency}")

    def start_vibration(self, duration=500):
        """Démarrer le vibreur"""
        self.send_command(f"VIBRATE:{duration}")

    def simple_beep(self):
        """Émettre un bip simple"""
        self.send_command("BEEP")

    def add_message_callback(self, callback):
        """Ajouter un callback pour les messages Arduino"""
        self.message_callbacks.append(callback)

    def disconnect(self):
        """Fermer la connexion"""
        self.connected = False
        if self.serial_conn:
            self.serial_conn.close()
        print("✅ Connexion Arduino fermée")