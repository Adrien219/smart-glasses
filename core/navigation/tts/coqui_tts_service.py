"""
Service TTS (Text-to-Speech) utilisant Coqui TTS.
Gère la synthèse vocale asynchrone avec file d'attente prioritaire.
"""
import os
import time
import threading
import queue
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TTSWorker:
    """Worker TTS asynchrone avec file d'attente prioritaire."""
    
    def __init__(self, config: Dict, tts_queue: queue.PriorityQueue):
        """
        Initialise le service TTS.
        
        Args:
            config: Configuration TTS
            tts_queue: File d'attente prioritaire pour les messages
        """
        self.config = config
        self.tts_queue = tts_queue
        
        # État du worker
        self.running = False
        self.currently_speaking = False
        self.tts_model = None
        self.tts = None
        
        # Cache pour les phrases fréquentes
        self.audio_cache = {}
        self.cache_dir = Path(config.get('cache_dir', 'tts_cache'))
        self.cache_dir.mkdir(exist_ok=True)
        
        # Statistiques
        self.stats = {
            'messages_processed': 0,
            'cache_hits': 0,
            'synthesis_time_total': 0.0,
            'last_synthesis_time': 0.0
        }
        
        # Phrases pré-chargées
        self.preloaded_phrases = {}
        
        self._initialize_tts()
        
        logger.info("TTSWorker initialisé")
    
    def _initialize_tts(self):
        """Initialise le moteur TTS Coqui."""
        try:
            from TTS.api import TTS
            
            model_name = self.config.get('model_name', 'tts_models/fr/mai/tacotron2-DDC')
            use_cuda = self.config.get('use_cuda', False)
            
            logger.info(f"Chargement modèle TTS: {model_name}")
            
            # Initialiser TTS
            self.tts = TTS(model_name=model_name, progress_bar=False, gpu=use_cuda)
            self.tts_model = model_name
            
            # Tester la synthèse
            test_output = self.cache_dir / "test.wav"
            self.tts.tts_to_file(
                text="Test d'initialisation",
                file_path=str(test_output)
            )
            
            if test_output.exists():
                test_output.unlink()  # Supprimer le fichier test
            
            logger.info(f"TTS initialisé avec succès: {model_name}")
            
        except ImportError:
            logger.error("Coqui TTS non installé. Installation: pip install TTS")
            self.tts = None
            
        except Exception as e:
            logger.error(f"Erreur initialisation TTS: {e}")
            self.tts = None
    
    def preload_phrase(self, text: str):
        """Pré-charge une phrase dans le cache."""
        if self.tts is None or not text:
            return
        
        try:
            # Créer un hash pour la phrase
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_file = self.cache_dir / f"{text_hash}.wav"
            
            # Si déjà en cache, ne rien faire
            if cache_file.exists():
                self.preloaded_phrases[text_hash] = str(cache_file)
                return
            
            # Synthétiser et sauvegarder
            self.tts.tts_to_file(
                text=text,
                file_path=str(cache_file)
            )
            
            if cache_file.exists():
                self.preloaded_phrases[text_hash] = str(cache_file)
                logger.debug(f"Phrase pré-chargée: '{text[:30]}...'")
            
        except Exception as e:
            logger.error(f"Erreur pré-chargement phrase: {e}")
    
    def synthesize(self, text: str, priority: int = 2) -> Optional[str]:
        """
        Synthétise du texte en parole.
        
        Args:
            text: Texte à synthétiser
            priority: Priorité du message
            
        Returns:
            Chemin du fichier audio ou None en cas d'erreur
        """
        if self.tts is None or not text:
            logger.warning(f"TTS non disponible ou texte vide: '{text}'")
            return None
        
        start_time = time.time()
        
        try:
            # Créer un hash pour la phrase
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_file = self.cache_dir / f"{text_hash}.wav"
            
            # Vérifier le cache
            if cache_file.exists():
                self.stats['cache_hits'] += 1
                self.stats['last_synthesis_time'] = time.time() - start_time
                return str(cache_file)
            
            # Vérifier les phrases pré-chargées
            if text_hash in self.preloaded_phrases:
                cache_file = Path(self.preloaded_phrases[text_hash])
                if cache_file.exists():
                    self.stats['cache_hits'] += 1
                    self.stats['last_synthesis_time'] = time.time() - start_time
                    return str(cache_file)
            
            # Synthétiser la phrase
            logger.debug(f"Synthèse TTS: '{text[:50]}...' (priorité: {priority})")
            
            self.tts.tts_to_file(
                text=text,
                file_path=str(cache_file),
                speaker_wav=self.config.get('speaker_wav')
            )
            
            if cache_file.exists():
                synthesis_time = time.time() - start_time
                self.stats['synthesis_time_total'] += synthesis_time
                self.stats['last_synthesis_time'] = synthesis_time
                
                logger.debug(f"Synthèse terminée en {synthesis_time:.2f}s: {cache_file.name}")
                return str(cache_file)
            else:
                logger.error(f"Échec synthèse TTS: fichier non créé")
                return None
            
        except Exception as e:
            logger.error(f"Erreur synthèse TTS: {e}")
            return None
    
    def play_audio(self, audio_file: str):
        """
        Joue un fichier audio.
        
        Args:
            audio_file: Chemin vers le fichier audio
        """
        if not os.path.exists(audio_file):
            logger.error(f"Fichier audio non trouvé: {audio_file}")
            return
        
        try:
            # Utiliser aplay pour Raspberry Pi (ALSA)
            import subprocess
            
            cmd = ['aplay', '-q', audio_file]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10  # Timeout de 10 secondes
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lecture audio: {result.stderr.decode()}")
            
            # Nettoyer le fichier audio (optionnel)
            if not self.config.get('keep_audio_files', False):
                try:
                    Path(audio_file).unlink()
                except:
                    pass
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout lecture audio")
        except Exception as e:
            logger.error(f"Erreur lecture audio: {e}")
    
    def run(self):
        """Boucle principale du worker TTS."""
        self.running = True
        
        logger.info("Démarrage TTSWorker")
        
        while self.running:
            try:
                # Attendre un message (bloquant avec timeout)
                try:
                    priority, message_data = self.tts_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Extraire les données du message
                text = message_data.get('text', '')
                msg_priority = message_data.get('priority', 2)
                
                if not text:
                    logger.warning("Message TTS vide, ignoré")
                    continue
                
                # Marquer comme en train de parler
                self.currently_speaking = True
                
                # Synthétiser la parole
                audio_file = self.synthesize(text, msg_priority)
                
                if audio_file:
                    # Jouer l'audio
                    self.play_audio(audio_file)
                    
                    # Mettre à jour les statistiques
                    self.stats['messages_processed'] += 1
                
                # Marquer comme terminé
                self.currently_speaking = False
                self.tts_queue.task_done()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Erreur dans TTSWorker: {e}")
                self.currently_speaking = False
                time.sleep(0.1)
        
        logger.info("Arrêt TTSWorker")
    
    def stop(self):
        """Arrête le worker TTS."""
        self.running = False
        
        # Vider la file d'attente
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break
        
        logger.info("TTSWorker arrêté")
    
    def get_status(self) -> Dict:
        """Retourne le statut du service TTS."""
        return {
            'running': self.running,
            'currently_speaking': self.currently_speaking,
            'model_loaded': self.tts is not None,
            'model_name': self.tts_model,
            'queue_size': self.tts_queue.qsize(),
            'cache_size': len(self.preloaded_phrases),
            'stats': self.stats.copy()
        }
    
    def clear_cache(self):
        """Vide le cache audio."""
        try:
            # Supprimer tous les fichiers .wav dans le cache
            for file in self.cache_dir.glob("*.wav"):
                file.unlink()
            
            self.audio_cache.clear()
            self.preloaded_phrases.clear()
            
            logger.info("Cache TTS vidé")
            
        except Exception as e:
            logger.error(f"Erreur vidage cache: {e}")
    
    def warmup_cache(self, phrases: list):
        """
        Préchauffe le cache avec des phrases courantes.
        
        Args:
            phrases: Liste de phrases à précharger
        """
        logger.info(f"Préchauffage cache TTS avec {len(phrases)} phrases")
        
        for phrase in phrases:
            self.preload_phrase(phrase)
        
        logger.info(f"Cache préchauffé: {len(self.preloaded_phrases)} phrases")