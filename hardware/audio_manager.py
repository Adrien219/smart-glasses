import pyaudio
import wave
import threading
import time

class AudioManager:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.is_playing = False
        
    def play_audio_file(self, filename):
        """Jouer un fichier audio"""
        def _play():
            self.is_playing = True
            try:
                wf = wave.open(filename, 'rb')
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                data = wf.readframes(1024)
                while data and self.is_playing:
                    stream.write(data)
                    data = wf.readframes(1024)
                
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                print(f"❌ Erreur lecture audio: {e}")
            finally:
                self.is_playing = False
        
        if not self.is_playing:
            thread = threading.Thread(target=_play, daemon=True)
            thread.start()
    
    def stop_audio(self):
        """Arrêter la lecture audio"""
        self.is_playing = False
    
    def cleanup(self):
        """Nettoyer les ressources audio"""
        self.audio.terminate()