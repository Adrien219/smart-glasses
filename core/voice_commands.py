import speech_recognition as sr
import threading
import time
import queue

class VoiceCommands:
    def __init__(self, smart_glasses_system):
        self.system = smart_glasses_system
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.listening_thread = None
        
        # Calibration du microphone pour le bruit ambiant
        print("🎤 Calibration du microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("✅ Microphone calibré!")
        
        # Dictionnaire des commandes vocales
        self.voice_commands = {
            # Changement de modes
            "mode navigation": "navigation",
            "mode objets": "object", 
            "mode objet": "object",
            "mode détection d'objets": "object",
            "mode visages": "face",
            "mode reconnaissance faciale": "face",
            "mode texte": "text",
            "mode lecture": "text",
            "mode assistant": "ai",
            "mode ia": "ai",
            
            # Commandes de navigation
            "où suis-je": "where_am_i",
            "que vois-tu": "what_do_you_see",
            "qui est là": "who_is_there",
            "décris la scène": "describe_scene",
            "obstacles": "detect_obstacles",
            "guide moi": "guide_me",
            
            # Commandes système
            "arrête": "stop",
            "démarre": "start",
            "aide": "help",
            "statut": "status",
            
            # Commandes de lecture
            "lis le texte": "read_text",
            "texte devant": "read_text",
            
            # Commandes d'assistant
            "que peux-tu faire": "capabilities",
            "commandes disponibles": "available_commands"
        }

    def start_listening(self):
        """Démarre l'écoute des commandes vocales"""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listening_thread.start()
        print("🎤 Reconnaissance vocale activée - Dites 'aide' pour la liste des commandes")

    def stop_listening(self):
        """Arrête l'écoute des commandes vocales"""
        self.is_listening = False
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)
        print("🔇 Reconnaissance vocale désactivée")

    def _listen_loop(self):
        """Boucle d'écoute principale"""
        while self.is_listening:
            try:
                # Écoute avec timeout pour pouvoir vérifier is_listening
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Transcription
                try:
                    command = self.recognizer.recognize_google(audio, language='fr-FR')
                    command = command.lower()
                    print(f"🎤 Commande vocale détectée: '{command}'")
                    
                    # Traitement de la commande
                    self._process_voice_command(command)
                    
                except sr.UnknownValueError:
                    # Pas de parole détectée ou incompréhensible
                    pass
                except sr.RequestError as e:
                    print(f"❌ Erreur service reconnaissance vocale: {e}")
                    
            except sr.WaitTimeoutError:
                # Timeout normal, on continue la boucle
                continue
            except Exception as e:
                print(f"❌ Erreur écoute vocale: {e}")
                time.sleep(1)

    def _process_voice_command(self, command_text):
        """Traite la commande vocale et déclenche l'action correspondante"""
        # Recherche de correspondance dans les commandes
        for voice_cmd, action in self.voice_commands.items():
            if voice_cmd in command_text:
                self._execute_command(action, command_text)
                return
        
        # Si aucune commande reconnue
        self.system.voice_assistant.speak("Commande non reconnue. Dites 'aide' pour la liste des commandes.")

    def _execute_command(self, action, original_command):
        """Exécute l'action correspondant à la commande"""
        try:
            if action in ["navigation", "object", "face", "text", "ai"]:
                # Changement de mode
                self.system.set_mode(action)
                self.system.voice_assistant.speak(f"Mode {action} activé")
                
            elif action == "what_do_you_see":
                self._handle_what_do_you_see()
                
            elif action == "who_is_there":
                self._handle_who_is_there()
                
            elif action == "read_text":
                self._handle_read_text()
                
            elif action == "describe_scene":
                self._handle_describe_scene()
                
            elif action == "guide_me":
                self._handle_guide_me()
                
            elif action == "help":
                self._handle_help()
                
            elif action == "capabilities":
                self._handle_capabilities()
                
            elif action == "available_commands":
                self._handle_available_commands()
                
            else:
                self.system.voice_assistant.speak(f"Commande {action} en cours de développement")
                
        except Exception as e:
            print(f"❌ Erreur exécution commande {action}: {e}")
            self.system.voice_assistant.speak("Erreur lors de l'exécution de la commande")

    def _handle_what_do_you_see(self):
        """Traite la commande 'que vois-tu'"""
        # Capture une frame et détecte les objets
        frame = self.system.camera.get_frame()
        if frame is not None:
            detections = self.system.object_detector.detect_objects(frame)
            if detections:
                objects = list(set([det['class'] for det in detections]))
                objects_text = ", ".join(objects[:5])  # Limiter à 5 objets
                response = f"Je vois: {objects_text}"
            else:
                response = "Je ne vois aucun objet pour le moment"
        else:
            response = "Problème avec la caméra"
        
        self.system.voice_assistant.speak(response)

    def _handle_who_is_there(self):
        """Traite la commande 'qui est là'"""
        frame = self.system.camera.get_frame()
        if frame is not None:
            faces = self.system.face_recognizer.detect_faces(frame)
            if faces:
                names = [face['name'] for face in faces if face['name'] != "Inconnu"]
                if names:
                    names_text = ", ".join(names)
                    response = f"Je vois: {names_text}"
                else:
                    response = "Je vois des personnes mais je ne les reconnais pas"
            else:
                response = "Je ne vois personne"
        else:
            response = "Problème avec la caméra"
        
        self.system.voice_assistant.speak(response)

    def _handle_read_text(self):
        """Traite la commande 'lis le texte'"""
        frame = self.system.camera.get_frame()
        if frame is not None:
            text_info = self.system.text_recognizer.extract_text(frame)
            if text_info:
                # Prendre le texte avec la plus haute confiance
                best_text = max(text_info, key=lambda x: x['confidence'])
                response = f"Je lis: {best_text['text']}"
            else:
                response = "Je ne vois pas de texte"
        else:
            response = "Problème avec la caméra"
        
        self.system.voice_assistant.speak(response)

    def _handle_describe_scene(self):
        """Traite la commande 'décris la scène'"""
        frame = self.system.camera.get_frame()
        if frame is None:
            self.system.voice_assistant.speak("Problème avec la caméra")
            return
            
        # Détection complète
        objects = self.system.object_detector.detect_objects(frame)
        faces = self.system.face_recognizer.detect_faces(frame)
        text_info = self.system.text_recognizer.extract_text(frame)
        
        description_parts = []
        
        if objects:
            obj_names = list(set([det['class'] for det in objects[:3]]))
            description_parts.append(f"objets: {', '.join(obj_names)}")
            
        if faces:
            known_faces = [face['name'] for face in faces if face['name'] != "Inconnu"]
            if known_faces:
                description_parts.append(f"personnes: {', '.join(known_faces)}")
            else:
                description_parts.append("personnes non reconnues")
                
        if text_info:
            description_parts.append("texte détecté")
            
        if description_parts:
            response = "Scène: " + ", ".join(description_parts)
        else:
            response = "Rien de particulier à décrire"
            
        self.system.voice_assistant.speak(response)

    def _handle_guide_me(self):
        """Traite la commande 'guide moi'"""
        self.system.voice_assistant.speak("Mode guidage activé. Je vais vous aider à naviguer.")
        # Ici vous pourriez activer un mode de guidage spécial
        self.system.set_mode("navigation")

    def _handle_help(self):
        """Affiche l'aide des commandes vocales"""
        help_text = """
Commandes disponibles:
- Modes: 'mode navigation', 'mode objets', 'mode visages', 'mode texte', 'mode assistant'
- Informations: 'que vois-tu', 'qui est là', 'décris la scène'
- Lecture: 'lis le texte'
- Navigation: 'guide moi', 'obstacles'
- Aide: 'aide', 'commandes disponibles'
        """
        print(help_text)
        self.system.voice_assistant.speak("Je vous ai affiché la liste des commandes dans la console. Dites par exemple 'mode objets' pour changer de mode.")

    def _handle_capabilities(self):
        """Décrit les capacités du système"""
        capabilities = """
Je peux:
- Détecter et reconnaître les objets autour de vous
- Reconnaître les visages des personnes que vous connaissez  
- Lire le texte devant vous
- Vous guider et détecter les obstacles
- Répondre à vos questions
        """
        print(capabilities)
        self.system.voice_assistant.speak("Je peux détecter objets, reconnaître visages, lire texte, et vous guider. Dites 'aide' pour les commandes.")

    def _handle_available_commands(self):
        """Liste les commandes disponibles"""
        self._handle_help()