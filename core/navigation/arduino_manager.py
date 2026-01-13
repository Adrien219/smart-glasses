"""
ArduinoManager - Gestion centralisée de l'Arduino Uno
"""
import serial
import time
import logging
import threading
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

class ArduinoManager:
    """
    Gère la communication avec l'Arduino Uno.
    Version simplifiée basée sur arduino_uno_adapter.
    """
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        
        # Dernières données
        self.last_ultrasonic = None
        self.last_light = None
        self.last_timestamp = 0
        
        # Callbacks
        self.data_callbacks = []
        
        # Verrou
        self.lock = threading.RLock()
        
        logger.info(f"ArduinoManager initialisé pour {port}")
    
    def start(self) -> bool:
        """Démarre la connexion et la lecture."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2.0,
                write_timeout=2.0
            )
            
            # Attendre l'initialisation Arduino
            time.sleep(3)
            
            # Vider le buffer
            while self.serial_conn.in_waiting:
                self.serial_conn.readline()
            
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            logger.info("✅ ArduinoManager démarré")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage ArduinoManager: {e}")
            return False
    
    def _read_loop(self):
        """Boucle de lecture des données Arduino."""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        self._process_line(line)
            except Exception as e:
                logger.error(f"Erreur lecture Arduino: {e}")
                time.sleep(0.1)
    
    def _process_line(self, line: str):
        """Traite une ligne reçue de l'Arduino."""
        try:
            if ':' not in line:
                return
            
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            timestamp = time.time()
            
            with self.lock:
                if key == "ULTRASONIC":
                    try:
                        distance = float(value)
                        if 2.0 <= distance <= 400.0:
                            self.last_ultrasonic = distance
                            self.last_timestamp = timestamp
                    except ValueError:
                        pass
                
                elif key == "LIGHT":
                    try:
                        self.last_light = int(value)
                    except ValueError:
                        pass
                
                # Notifier les callbacks
                self._notify_callbacks(key, value)
                
        except Exception as e:
            logger.error(f"Erreur traitement ligne: {e}")
    
    def _notify_callbacks(self, key: str, value: str):
        """Notifie les callbacks enregistrés."""
        for callback in self.data_callbacks:
            try:
                callback(key, value)
            except Exception:
                pass
    
    def register_callback(self, callback: Callable[[str, str], None]):
        """Enregistre un callback pour les données."""
        self.data_callbacks.append(callback)
    
    def get_latest_ultrasonic(self) -> Optional[Dict[str, Any]]:
        """Récupère la dernière mesure ultrasonique."""
        with self.lock:
            if self.last_ultrasonic is not None:
                return {
                    'distance': self.last_ultrasonic,
                    'angle': 0.0,
                    'timestamp': self.last_timestamp
                }
        return None
    
    def send_command(self, command: str) -> bool:
        """Envoie une commande à l'Arduino."""
        if not self.serial_conn:
            return False
        
        try:
            full_cmd = f"{command}\n"
            self.serial_conn.write(full_cmd.encode('ascii'))
            self.serial_conn.flush()
            return True
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """Vérifie si l'Arduino est connecté."""
        return self.running and self.serial_conn and self.serial_conn.is_open
    
    def stop(self):
        """Arrête proprement le manager."""
        self.running = False
        
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        
        if self.serial_conn:
            self.serial_conn.close()
        
        logger.info("ArduinoManager arrêté")
