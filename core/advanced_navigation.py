import time
from collections import deque

class AdvancedNavigation:
    def __init__(self, stereo_vision, arduino_comm, voice_assistant):
        self.stereo_vision = stereo_vision
        self.arduino_comm = arduino_comm
        self.voice_assistant = voice_assistant
        
        # Mémoire de navigation
        self.obstacle_history = deque(maxlen=10)
        self.last_detection_time = 0
        self.navigation_mode = "auto"  # auto, manual, avoid
        
    def analyze_environment(self):
        """Analyser l'environnement avec tous les capteurs"""
        environment_data = {}
        
        # 1. Stéréovision pour les distances précises
        img_left, img_right = self.stereo_vision.get_stereo_frames()
        if img_left is not None and img_right is not None:
            depth_map = self.stereo_vision.calculate_depth_map(img_left, img_right)
            stereo_distances = self.stereo_vision.get_obstacle_distances(depth_map)
            environment_data["stereo"] = stereo_distances
        
        # 2. Capteur ultrason pour vérification
        ultrasonic_distance = self.arduino_comm.read_ultrasonic()
        if ultrasonic_distance:
            environment_data["ultrasonic"] = ultrasonic_distance
        
        return environment_data
    
    def generate_navigation_instructions(self, environment_data):
        """Générer des instructions de navigation intelligentes"""
        instructions = []
        
        # Fusion des données des capteurs
        stereo_data = environment_data.get("stereo", {})
        ultrasonic_data = environment_data.get("ultrasonic", float('inf'))
        
        # Détection des obstacles critiques
        min_distance = min([
            stereo_data.get("centre", float('inf')),
            stereo_data.get("gauche", float('inf')), 
            stereo_data.get("droite", float('inf')),
            ultrasonic_data
        ])
        
        # Générer instructions selon les distances
        if min_distance < 0.5:  # 50cm - DANGER
            instructions.append(("danger", "Arrêt immédiat ! Obstacle très proche"))
            
            # Chercher la meilleure direction d'évitement
            left_dist = stereo_data.get("gauche", float('inf'))
            right_dist = stereo_data.get("droite", float('inf'))
            
            if left_dist > right_dist and left_dist > 1.0:
                instructions.append(("warning", "Contournez par la gauche"))
            elif right_dist > left_dist and right_dist > 1.0:
                instructions.append(("warning", "Contournez par la droite"))
            else:
                instructions.append(("warning", "Reculez prudemment"))
                
        elif min_distance < 1.0:  # 1m - ALERTE
            instructions.append(("warning", f"Obstacle à {min_distance:.1f}m devant vous"))
            
        elif min_distance < 2.0:  # 2m - INFORMATION
            instructions.append(("info", f"Obstacle à {min_distance:.1f}m"))
            
        # Navigation libre
        else:
            centre_dist = stereo_data.get("centre", float('inf'))
            if centre_dist > 3.0:
                instructions.append(("info", "Chemin libre devant vous"))
        
        return instructions
    
    def navigate(self):
        """Boucle principale de navigation"""
        environment_data = self.analyze_environment()
        instructions = self.generate_navigation_instructions(environment_data)
        
        # Annoncer l'instruction la plus urgente
        if instructions:
            priority_instruction = instructions[0]  # (niveau, message)
            self.voice_assistant.speak(priority_instruction[1])
            
            # Retour haptique selon l'urgence
            if priority_instruction[0] == "danger":
                self.arduino_comm.send_vibration(1000)
                self.arduino_comm.send_beep(3)
            elif priority_instruction[0] == "warning":
                self.arduino_comm.send_vibration(500)
                self.arduino_comm.send_beep(2)
        
        return instructions