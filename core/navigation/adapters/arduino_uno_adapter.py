"""
Adaptateur spécifique pour l'Arduino Uno du projet smart-glasses.
Correspond exactement au code Arduino fourni.
"""
import serial
import time
import logging
import threading

logger = logging.getLogger(__name__)

class ArduinoUnoAdapter:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        """
        Adaptateur pour l'Arduino Uno avec le code ultra-stable.
        
        Args:
            port: Port série (défaut: /dev/ttyUSB0)
            baudrate: 9600 (doit correspondre au Serial.begin(9600))
            timeout: Timeout en secondes
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        
        # Données
        self.last_distance = None      # en centimètres
        self.last_light_level = None   # 0-1023
        self.last_distance_time = 0
        self.last_light_time = 0
        
        # Gestion des commandes
        self.command_lock = threading.Lock()
        self.command_response = None
        self.command_waiting = False
        
        # Thread de lecture passive
        self.reading_thread = None
        self.running = False
        
        self._connect()
        
        if self.serial_conn:
            self._start_reading_thread()
    
    def _connect(self):
        """Établit la connexion série."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            time.sleep(2)  # Laisser l'Arduino démarrer (startupSequence)
            
            # Vider le buffer initial
            if self.serial_conn.in_waiting:
                self.serial_conn.read(self.serial_conn.in_waiting)
            
            logger.info(f"Connecté à Arduino Uno sur {self.port}")
            logger.info("Système ultra-stable - A3/A4 Active")
            
        except Exception as e:
            logger.error(f"Erreur connexion Arduino: {e}")
            self.serial_conn = None
    
    def _send_command(self, command):
        """
        Envoie une commande à l'Arduino.
        
        Format attendu par handleSerialMessage():
        - "GET_ULTRASONIC" → répond "DISTANCE:xxx"
        - "GET_LIGHT" → répond "LIGHT_LEVEL:xxx"
        - "MODE:x" → change le mode
        - "BUZZER:duration:frequency" → active le buzzer
        - "VIBRATE:duration" → active le vibreur
        - "BEEP" → bip court
        """
        if not self.serial_conn:
            logger.warning("Connexion série non disponible")
            return None
        
        with self.command_lock:
            try:
                # Préparer la commande (ajouter \n)
                if not command.endswith('\n'):
                    command += '\n'
                
                # Vider le buffer d'entrée
                self.serial_conn.reset_input_buffer()
                
                # Envoyer la commande
                self.serial_conn.write(command.encode())
                logger.debug(f"Commande envoyée: {command.strip()}")
                
                # Attendre la réponse (avec timeout)
                start_time = time.time()
                response = None
                
                while time.time() - start_time < self.timeout:
                    if self.serial_conn.in_waiting:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            response = line
                            break
                    time.sleep(0.01)
                
                return response
                
            except Exception as e:
                logger.error(f"Erreur envoi commande '{command}': {e}")
                return None
    
    def _reading_loop(self):
        """Boucle de lecture passive pour les messages automatiques."""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        logger.debug(f"Message Arduino: {line}")
                        
                        # Traiter les messages automatiques
                        if line.startswith("LIGHT_LEVEL:"):
                            try:
                                light = int(line.split(":")[1])
                                self.last_light_level = light
                                self.last_light_time = time.time()
                                logger.debug(f"Niveau lumière mis à jour: {light}")
                            except:
                                pass
                        
                        elif line.startswith("MODE_CHANGE:"):
                            mode = int(line.split(":")[1])
                            mode_names = {
                                0: "NAVIGATION",
                                1: "OBJECT_DETECTION", 
                                2: "FACE_RECOGNITION",
                                3: "TEXT_READING",
                                4: "AI_ASSISTANT"
                            }
                            mode_name = mode_names.get(mode, f"INCONNU({mode})")
                            logger.info(f"Mode Arduino changé: {mode_name}")
                        
                        elif line.startswith("BUTTON:"):
                            button_id = int(line.split(":")[1])
                            logger.info(f"Bouton {button_id} pressé")
                        
                        elif line.startswith("JOYSTICK:"):
                            # Format: "JOYSTICK:xValue,yValue"
                            pass  # Ignorer pour le moment
                        
                        elif line.startswith("ARDUINO_READY"):
                            logger.info("Arduino prêt")
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Erreur lecture thread: {e}")
                time.sleep(0.1)
    
    def _start_reading_thread(self):
        """Démarre le thread de lecture passive."""
        self.running = True
        self.reading_thread = threading.Thread(
            target=self._reading_loop,
            name="ArduinoReader",
            daemon=True
        )
        self.reading_thread.start()
        logger.debug("Thread de lecture passive démarré")
    
    def get_distance(self):
        """
        Demande et obtient la distance ultrasonique.
        
        Returns:
            float: Distance en centimètres, ou None si erreur.
        """
        # Ton Arduino retourne la distance en mètres (voir ligne: return distance / 100.0)
        # Nous devons convertir en centimètres
        
        response = self._send_command("GET_ULTRASONIC")
        
        if response and response.startswith("DISTANCE:"):
            try:
                # Extraire la valeur
                distance_str = response.split(":")[1]
                distance_m = float(distance_str)
                
                # Convertir mètres → centimètres
                distance_cm = distance_m * 100.0
                
                # Valider la plage (2cm à 400cm)
                if 2 <= distance_cm <= 400:
                    self.last_distance = distance_cm
                    self.last_distance_time = time.time()
                    logger.debug(f"Distance ultrasonique: {distance_cm:.1f} cm")
                    return distance_cm
                else:
                    logger.warning(f"Distance hors plage: {distance_cm:.1f} cm")
                    return None
                    
            except ValueError as e:
                logger.error(f"Erreur conversion distance: {e}, réponse: {response}")
                return None
        
        elif response:
            logger.warning(f"Réponse inattendue: {response}")
            return None
        else:
            logger.warning("Pas de réponse à GET_ULTRASONIC")
            return self.last_distance  # Retourner la dernière valeur connue
    
    def get_light_level(self):
        """Obtient le niveau de lumière (0-1023)."""
        # Si nous avons une valeur récente (< 3 secondes), la retourner
        if self.last_light_level and (time.time() - self.last_light_time < 3.5):
            return self.last_light_level
        
        # Sinon, demander explicitement
        response = self._send_command("GET_LIGHT")
        
        if response and response.startswith("LIGHT_LEVEL:"):
            try:
                light = int(response.split(":")[1])
                self.last_light_level = light
                self.last_light_time = time.time()
                return light
            except:
                return self.last_light_level
        
        return self.last_light_level
    
    def set_mode(self, mode):
        """
        Change le mode de l'Arduino.
        
        Args:
            mode: 0=NAVIGATION, 1=OBJECT_DETECTION, 2=FACE_RECOGNITION, 
                  3=TEXT_READING, 4=AI_ASSISTANT
        """
        if 0 <= mode <= 4:
            response = self._send_command(f"MODE:{mode}")
            return response is not None
        else:
            logger.error(f"Mode invalide: {mode}")
            return False
    
    def activate_buzzer(self, duration_ms=200, frequency_hz=1000):
        """Active le buzzer."""
        return self._send_command(f"BUZZER:{duration_ms}:{frequency_hz}") is not None
    
    def activate_vibration(self, duration_ms=200):
        """Active le vibreur."""
        return self._send_command(f"VIBRATE:{duration_ms}") is not None
    
    def quick_beep(self):
        """Émet un bip court."""
        return self._send_command("BEEP") is not None
    
    def is_healthy(self):
        """Vérifie si l'Arduino est connecté et répond."""
        if not self.serial_conn:
            return False
        
        # Vérifier la connexion en envoyant une commande simple
        try:
            response = self._send_command("GET_LIGHT")
            return response is not None and response.startswith("LIGHT_LEVEL:")
        except:
            return False
    
    def cleanup(self):
        """Ferme la connexion proprement."""
        self.running = False
        
        if self.reading_thread:
            self.reading_thread.join(timeout=1.0)
        
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
        
        logger.info("Connexion Arduino fermée")
    
    def __del__(self):
        """Destructeur."""
        self.cleanup()
