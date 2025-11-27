# voice.py
"""
Simple non-blocking TTS using pyttsx3.
On Raspberry Pi you may prefer espeak via subprocess.
"""
import pyttsx3
import threading

class VoiceAssistant:
    def __init__(self, rate=150, volume=1.0, voice=None):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            if voice:
                try:
                    self.engine.setProperty('voice', voice)
                except Exception:
                    pass
        except Exception as e:
            print("TTS init failed:", e)
            self.engine = None

    def _speak(self, text):
        if not self.engine:
            print("[TTS]", text)
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)

    def speak(self, text):
        t = threading.Thread(target=self._speak, args=(text,), daemon=True)
        t.start()
