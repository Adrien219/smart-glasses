"""
Adaptateur pour le capteur ultrasonique HC-SR04.
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class UltrasonicAdapter:
    """Adaptateur pour le capteur HC-SR04."""
    
    def __init__(self, trig_pin: int = 23, echo_pin: int = 24, 
                 max_distance: float = 400.0, timeout_us: int = 30000):
        """
        Initialise l'adaptateur ultrasonique.
        
        Args:
            trig_pin: GPIO pour trigger
            echo_pin: GPIO pour echo
            max_distance: Distance maximale en cm
            timeout_us: Timeout en microsecondes
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.max_distance = max_distance
        self.timeout_us = timeout_us
        
        # Temps maximal pour le son aller-retour (en secondes)
        self.max_time = (max_distance * 2) / 34300  # vitesse du son ~343 m/s
        
        self.gpio = None
        self.last_read_time = 0
        self.last_distance = None
        self.error_count = 0
        self.max_error_count = 5
        
        self._initialize_gpio()
        
        logger.info(f"UltrasonicAdapter initialisé: TRIG={trig_pin}, ECHO={echo_pin}, "
                   f"max={max_distance}cm")
    
    def _initialize_gpio(self):
        """Initialise les GPIO pour le HC-SR04."""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trig_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            
            # Initialiser le trigger à LOW
            GPIO.output(self.trig_pin, False)
            time.sleep(0.5)  # Stabilisation
            
            self.gpio = GPIO
            logger.info("GPIO initialisé avec succès")
            
        except ImportError:
            logger.warning("RPi.GPIO non disponible, mode simulation activé")
            self.gpio = None
    
    def get_distance(self) -> float:
        """
        Mesure la distance avec le capteur ultrasonique.
        
        Returns:
            Distance en cm, ou max_distance en cas d'erreur
        """
        if self.gpio is None:
            # Mode simulation pour le développement
            return self._simulate_distance()
        
        try:
            # Envoyer l'impulsion trigger
            self.gpio.output(self.trig_pin, True)
            time.sleep(0.00001)  # 10 µs
            self.gpio.output(self.trig_pin, False)
            
            # Attendre que l'echo passe à HIGH
            timeout_start = time.time()
            while self.gpio.input(self.echo_pin) == 0:
                if time.time() - timeout_start > 0.1:  # 100ms timeout
                    raise TimeoutError("Timeout attente echo HIGH")
            
            # Mesurer le temps HIGH
            pulse_start = time.time()
            timeout_start = time.time()
            
            while self.gpio.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end - pulse_start > self.max_time:
                    # Distance supérieure au maximum
                    self.last_distance = self.max_distance
                    self.last_read_time = time.time()
                    self.error_count = 0
                    return self.max_distance
                
                if time.time() - timeout_start > 0.1:  # 100ms timeout
                    raise TimeoutError("Timeout attente echo LOW")
            
            # Calculer la distance
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * 34300) / 2  # en cm
            
            # Filtrer les valeurs aberrantes
            if distance <= 0 or distance > self.max_distance:
                logger.warning(f"Distance aberrante: {distance}cm")
                distance = self.max_distance
            
            # Appliquer un filtre simple
            if self.last_distance is not None:
                # Moyenne mobile simple pour lisser le bruit
                alpha = 0.7
                distance = alpha * distance + (1 - alpha) * self.last_distance
            
            self.last_distance = distance
            self.last_read_time = time.time()
            self.error_count = 0
            
            return distance
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Erreur lecture ultrason: {e}")
            
            if self.error_count > self.max_error_count:
                logger.error(f"Trop d'erreurs ({self.error_count}), réinitialisation GPIO")
                self._reset_gpio()
            
            # Retourner la dernière valeur valide ou max_distance
            return self.last_distance if self.last_distance else self.max_distance
    
    def _simulate_distance(self) -> float:
        """Simule une lecture de distance pour le développement."""
        import random
        
        # Simulation d'un objet qui s'approche puis s'éloigne
        current_time = time.time()
        cycle_time = 10  # secondes pour un cycle complet
        
        # Distance sinusoidale entre 30cm et 200cm
        base_distance = 115 + 85 * (1 + (current_time % cycle_time) / cycle_time)
        
        # Ajouter du bruit
        noise = random.uniform(-5, 5)
        
        distance = max(30, min(self.max_distance, base_distance + noise))
        
        self.last_distance = distance
        self.last_read_time = current_time
        
        return distance
    
    def _reset_gpio(self):
        """Réinitialise les GPIO."""
        if self.gpio:
            self.gpio.cleanup()
            time.sleep(0.1)
            self._initialize_gpio()
            self.error_count = 0
            logger.info("GPIO réinitialisé")
    
    def cleanup(self):
        """Nettoie les GPIO."""
        if self.gpio:
            try:
                self.gpio.cleanup()
                logger.info("GPIO nettoyé")
            except:
                pass
    
    def get_status(self) -> dict:
        """Retourne le statut du capteur."""
        return {
            'last_distance': self.last_distance,
            'last_read_time': self.last_read_time,
            'error_count': self.error_count,
            'max_distance': self.max_distance,
            'gpio_initialized': self.gpio is not None
        }
    
    def __del__(self):
        """Destructeur."""
        self.cleanup()