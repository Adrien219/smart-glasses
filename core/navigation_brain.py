import time

class NavigationBrain:
    def __init__(self, voice, arduino_comm):
        self.voice = voice
        self.arduino = arduino_comm
        self.last_message = ""
        self.last_message_time = 0
        self.cooldown = 3.0  # Secondes entre les messages
        self.last_beep_time = 0
        
        # Configuration des distances (en pixels - plus la valeur est grande, plus l'objet est proche)
        self.CRITICAL_DIST = 150   # Très proche
        self.DANGER_DIST = 100     # Proche  
        self.AWARE_DIST = 50       # Loin
        
        # Classes d'objets
        self.DANGEROUS_CLASSES = {
            "person", "car", "bicycle", "motorcycle", "bus", "truck", 
            "stop sign", "traffic light"
        }
        self.OBSTACLE_CLASSES = {
            "chair", "couch", "bed", "table", "bench"
        }

    def get_position(self, bbox, frame_width):
        """Détermine la position de l'objet dans le cadre"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        
        if center_x < frame_width * 0.4:
            return "à gauche"
        elif center_x > frame_width * 0.6:
            return "à droite"
        else:
            return "devant"

    def estimate_distance(self, bbox):
        """Estime la distance relative basée sur la hauteur de la bounding box"""
        x1, y1, x2, y2 = bbox
        height = y2 - y1
        return height  # Plus la hauteur est grande, plus l'objet est proche

    def speak_once(self, message):
        """Évite la répétition rapide des mêmes messages"""
        now = time.time()
        if message == self.last_message and now - self.last_message_time < self.cooldown:
            return False
        
        self.last_message = message
        self.last_message_time = now
        self.voice.speak(message)
        return True

    def beep(self, level):
        """Émet un bip selon le niveau de danger"""
        now = time.time()
        if now - self.last_beep_time < 0.5:  # Anti-spam des bips
            return
        
        try:
            if self.arduino and self.arduino.connected:
                if level == "critical":
                    self.arduino.simple_beep()
                elif level == "danger":
                    self.arduino.simple_beep()
                self.last_beep_time = now
        except:
            pass

    def process(self, detections, frame_width=640):
        """Traite les détections pour la navigation"""
        if not detections:
            return

        critical_objects = []
        danger_objects = []
        aware_objects = []

        for det in detections:
            obj_class = det["class"]
            bbox = det["bbox"]
            position = self.get_position(bbox, frame_width)
            distance = self.estimate_distance(bbox)

            # Classification par priorité
            if distance > self.CRITICAL_DIST and obj_class in self.DANGEROUS_CLASSES:
                critical_objects.append((obj_class, position))
            elif distance > self.DANGER_DIST and obj_class in self.DANGEROUS_CLASSES:
                danger_objects.append((obj_class, position))
            elif distance > self.AWARE_DIST and obj_class in self.OBSTACLE_CLASSES:
                aware_objects.append((obj_class, position))

        # Traitement par ordre de priorité
        if critical_objects:
            obj, pos = critical_objects[0]
            self.speak_once(f"Attention! {obj} {pos}, très proche")
            self.beep("critical")
        elif danger_objects:
            obj, pos = danger_objects[0]
            self.speak_once(f"{obj} {pos}, proche")
            self.beep("danger")
        elif aware_objects:
            obj, pos = aware_objects[0]
            self.speak_once(f"{obj} {pos}")
            self.beep("aware")