#!/usr/bin/env python3
"""
Script principal pour les smart-glasses.
Intègre le module de navigation avec les autres composants.
"""
import time
import logging
import signal
import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Configure le logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_glasses.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Fonction principale."""
    logger = setup_logging()
    logger.info("Démarrage des Smart Glasses")
    
    # Variables globales
    navigation_module = None
    
    def signal_handler(sig, frame):
        """Gère les signaux d'arrêt."""
        nonlocal navigation_module
        logger.info(f"Signal {sig} reçu, arrêt en cours...")
        
        if navigation_module:
            navigation_module.stop()
        
        logger.info("Arrêt terminé")
        sys.exit(0)
    
    # Enregistrer les handlers de signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Importer et initialiser le module de navigation
        from core.navigation import NavigationModule
        
        # Configuration
        config_path = "config/navigation.yaml"
        
        # Vérifier si le fichier de configuration existe
        if not Path(config_path).exists():
            logger.warning(f"Fichier de configuration {config_path} non trouvé")
            config_path = None  # Utiliser la configuration par défaut
        
        # Créer le module de navigation
        navigation_module = NavigationModule(config_path)
        
        # Définir les callbacks
        def on_alert(data):
            logger.info(f"ALERTE: {data}")
            # Ici, tu pourrais déclencher d'autres actions
            # comme des vibrations ou des LEDs
        
        def on_state_change(data):
            logger.info(f"Changement d'état: {data['old_state']} -> {data['new_state']}")
        
        def on_guidance(data):
            logger.info(f"Guidage: {data}")
        
        def on_telemetry(data):
            # Log uniquement toutes les 10 secondes pour éviter le spam
            if 'timestamp' in data and data['timestamp'] % 10 < 0.1:
                logger.debug(f"Télémetrie: état={data.get('state', 'unknown')}, "
                           f"FPS={data.get('fps', {}).get('camera', 0)}")
        
        # Enregistrer les callbacks
        navigation_module.register_callback('on_alert', on_alert)
        navigation_module.register_callback('on_state_change', on_state_change)
        navigation_module.register_callback('on_guidance', on_guidance)
        navigation_module.register_callback('on_telemetry', on_telemetry)
        
        # Démarrer le module
        logger.info("Démarrage du module de navigation...")
        navigation_module.start()
        
        # Message vocal de démarrage
        navigation_module.force_announce(
            "Système de navigation prêt. Surveillance activée.",
            priority='medium'
        )
        
        logger.info("Système opérationnel. Appuyez sur Ctrl+C pour arrêter.")
        
        # Boucle principale
        last_stats_time = time.time()
        
        while True:
            time.sleep(1)
            
            # Afficher des statistiques périodiques
            current_time = time.time()
            if current_time - last_stats_time > 30:  # Toutes les 30 secondes
                if navigation_module:
                    stats = navigation_module.get_performance_stats()
                    logger.info(
                        f"Stats: uptime={stats['uptime_seconds']:.0f}s, "
                        f"FPS={stats['frames_per_second']:.1f}, "
                        f"latency={stats['average_latencies']['detection']*1000:.0f}ms"
                    )
                last_stats_time = current_time
        
    except KeyboardInterrupt:
        logger.info("Interruption par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
    finally:
        # Nettoyage
        if navigation_module:
            navigation_module.stop()
        
        logger.info("Application terminée")

if __name__ == "__main__":
    main()