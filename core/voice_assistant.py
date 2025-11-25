import threading
import queue
import time
import subprocess
import platform
import os

# Détection automatique du Raspberry Pi
IS_PI = platform.machine().startswith("arm") or platform.system() == "Linux"

# Supprimer complètement les warnings ALSA/Jack
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["AUDIODEV"] = "hw:0,0"
DEVNULL = open(os.devnull, "w")

class VoiceAssistant:
    def __init__(self, arduino_comm=None):
        print("🎤 Initialisation de l'assistant vocal...")

        self.arduino_comm = arduino_comm
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.last_speech_time = 0
        self.speech_cooldown = 3.0

        try:
            if IS_PI:
                print("🔧 Mode Raspberry Pi → utilisation espeak-ng")
                self.engine = None  # pas de pyttsx3 sur Pi
            else:
                import pyttsx3
                print("🔧 Mode Desktop → utilisation pyttsx3")
                self.engine = pyttsx3.init()
                self.setup_voice()

            self.process_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.process_thread.start()

            print("✅ Assistant vocal initialisé!")

        except Exception as e:
            print(f"❌ Erreur initialisation assistant vocal: {e}")
            self.engine = None

    def setup_voice(self):
        """Configurer la voix française (Desktop uniquement)"""
        if self.engine is None:
            return
        voices = self.engine.getProperty('voices')
        french_voice = None
        for voice in voices:
            if 'french' in voice.name.lower() or 'français' in voice.name.lower():
                french_voice = voice.id
                break
        if french_voice:
            self.engine.setProperty('voice', french_voice)
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 0.9)

    def speak(self, text, priority=False, haptic_feedback=True):
        """Ajouter un texte à la file d'attente vocale"""
        current_time = time.time()
        if current_time - self.last_speech_time < self.speech_cooldown and not priority:
            return
        self.speech_queue.put((text, haptic_feedback))
        self.last_speech_time = current_time

    def _process_queue(self):
        """Traiter la file d'attente"""
        while True:
            try:
                if not self.speech_queue.empty() and not self.is_speaking:
                    text, haptic_feedback = self.speech_queue.get()
                    self.is_speaking = True

                    # Retour haptique
                    if haptic_feedback and self.arduino_comm:
                        self.arduino_comm.simple_beep()

                    # 🔊 Synthèse vocale
                    if IS_PI:
                        subprocess.run(
                            ["espeak-ng", "-v", "fr", text],
                            stdout=DEVNULL, stderr=DEVNULL, check=True
                        )
                    elif self.engine:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    else:
                        print(f"🔊 {text}")

                    self.is_speaking = False
                    time.sleep(0.05)

            except Exception as e:
                print(f"❌ Erreur synthèse vocale: {e}")
                self.is_speaking = False
                time.sleep(0.5)

    # Fonctions utilitaires
    def announce_objects(self, objects_list):
        if objects_list:
            self.speak(f"Objets détectés: {', '.join(objects_list)}")

    def announce_person(self, name):
        if name.lower() == "inconnu":
            self.speak("Personne inconnue détectée")
        else:
            self.speak(f"{name} est devant vous")

    def announce_text(self, text):
        if text:
            self.speak(f"Texte détecté: {text}")

    def cleanup(self):
        if self.engine:
            self.engine.stop()
