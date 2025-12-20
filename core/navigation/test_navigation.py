#!/usr/bin/env python3
"""
Script de test pour le module de navigation.
Permet de vérifier chaque composant individuellement.
"""
import time
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_camera():
    """Test de la caméra."""
    try:
        from core.navigation.adapters.camera_adapter import CameraAdapter
        
        config = {
            'fov_deg': 62.2,
            'width': 640,
            'height': 480,
            'fps': 5,
            'rotation': 0
        }
        
        camera = CameraAdapter(config)
        logger.info("Caméra initialisée")
        
        # Capturer quelques frames
        for i in range(5):
            frame = camera.capture_frame()
            if frame is not None:
                logger.info(f"Frame {i+1}: {frame.shape}")
            time.sleep(0.2)
        
        camera.close()
        logger.info("Test caméra réussi")
        return True
        
    except Exception as e:
        logger.error(f"Erreur test caméra: {e}")
        return False

def test_ultrasonic():
    """Test du capteur ultrasonique."""
    try:
        from core.navigation.adapters.hc_sr04_adapter import UltrasonicAdapter
        
        # Mode simulation si RPi.GPIO n'est pas disponible
        ultrasonic = UltrasonicAdapter(trig_pin=23, echo_pin=24)
        logger.info("Capteur ultrasonique initialisé")
        
        # Prendre quelques mesures
        for i in range(5):
            distance = ultrasonic.get_distance()
            logger.info(f"Mesure {i+1}: {distance:.1f} cm")
            time.sleep(0.5)
        
        ultrasonic.cleanup()
        logger.info("Test ultrasonique réussi")
        return True
        
    except Exception as e:
        logger.error(f"Erreur test ultrasonique: {e}")
        return False

def test_eoh():
    """Test de l'histogramme EOH."""
    try:
        from core.navigation.fusion.eoh import EgocentricOccupancyHistogram
        
        eoh = EgocentricOccupancyHistogram(bins=13, fov_deg=62.2)
        logger.info("EOH initialisé")
        
        # Simuler quelques mises à jour
        for i in range(10):
            bearing = (i - 5) * 10  # -50 à +40 degrés
            distance = 100 + i * 20
            eoh.update(bearing, distance, confidence=0.8)
            
            snapshot = eoh.get_snapshot()
            logger.info(f"Update {i+1}: min_distance={snapshot.min_distance}")
        
        logger.info("Test EOH réussi")
        return True
        
    except Exception as e:
        logger.error(f"Erreur test EOH: {e}")
        return False

def test_full_module():
    """Test complet du module de navigation."""
    try:
        from core.navigation import NavigationModule
        
        logger.info("Test du module complet (mode simulation)...")
        
        # Créer une configuration de test
        import yaml
        
        test_config = {
            'camera': {
                'fov_deg': 62.2,
                'width': 320,
                'height': 240,
                'fps': 5
            },
            'ultrasonic': {
                'trig_pin': 23,
                'echo_pin': 24,
                'sample_rate_hz': 10
            },
            'detection': {
                'model_path': 'yolov8n.pt',
                'confidence_threshold': 0.5,
                'iou_threshold': 0.3,
                'classes': [0, 1, 2]
            },
            'system': {
                'debug_mode': True,
                'telemetry_interval_s': 2
            }
        }
        
        # Sauvegarder la config temporaire
        config_path = 'test_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Créer et démarrer le module
        nav = NavigationModule(config_path)
        
        # Définir un callback de test
        def test_callback(data):
            logger.info(f"Callback: {data}")
        
        nav.register_callback('on_alert', test_callback)
        nav.register_callback('on_state_change', test_callback)
        
        logger.info("Démarrage du module...")
        nav.start()
        
        # Laisser tourner pendant 10 secondes
        logger.info("Test en cours (10 secondes)...")
        time.sleep(10)
        
        # Obtenir des statistiques
        stats = nav.get_state()
        logger.info(f"Statistiques: {stats}")
        
        # Arrêter
        nav.stop()
        
        # Nettoyer
        Path(config_path).unlink(missing_ok=True)
        
        logger.info("Test module complet réussi")
        return True
        
    except Exception as e:
        logger.error(f"Erreur test module complet: {e}", exc_info=True)
        return False

def main():
    """Exécute tous les tests."""
    logger.info("Démarrage des tests du module de navigation")
    
    tests = [
        ("Camera", test_camera),
        ("Ultrasonic", test_ultrasonic),
        ("EOH", test_eoh),
        ("Module complet", test_full_module)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✓ {test_name}: SUCCÈS")
            else:
                logger.error(f"✗ {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"✗ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
        
        time.sleep(1)
    
    # Résumé
    logger.info(f"\n{'='*50}")
    logger.info("RÉSUMÉ DES TESTS")
    logger.info(f"{'='*50}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✓ SUCCÈS" if success else "✗ ÉCHEC"
        logger.info(f"{test_name:20} {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("✅ Tous les tests ont réussi!")
    else:
        logger.warning(f"⚠ {total - passed} tests ont échoué")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)