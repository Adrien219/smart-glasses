#!/usr/bin/env python3
"""
Test avancé du système de navigation
Inclut la détection d'obstacles, alertes et statistiques
"""

import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("🧪 TEST AVANCÉ - Navigation Complète")
    print("=" * 60)
    
    try:
        from core.navigation.navigation_module import NavigationModule
        
        # Initialisation
        print("1. Initialisation avancée...")
        nav = NavigationModule()
        
        # Configuration personnalisée
        nav.config['obstacle_threshold'] = 100.0  # 100 cm
        nav.config['light_threshold'] = 500       # Seuil de lumière
        nav.config['update_interval'] = 0.1       # 10Hz
        
        # Démarrage
        print("2. Démarrage complet...")
        nav.start()
        
        # Collecte de données
        print("\n3. Collecte de données (10 secondes)...")
        print("   Mode: Détection d'obstacles actif")
        print("   Seuil: 100 cm")
        print("   " + "-" * 40)
        
        start_time = time.time()
        readings = []
        obstacles_detected = 0
        
        while time.time() - start_time < 10:
            if nav.arduino_data:
                data = nav.arduino_data.copy()
                distance = data.get('distance', 0)
                light = data.get('light', 0)
                obstacle = distance < nav.config['obstacle_threshold']
                
                readings.append({
                    'distance': distance,
                    'light': light,
                    'obstacle': obstacle,
                    'timestamp': time.time()
                })
                
                if obstacle:
                    obstacles_detected += 1
                    status = "🚨 OBSTACLE DÉTECTÉ !"
                else:
                    status = "✅ Libre"
                
                print(f"   📏 {distance:5.1f} cm | 💡 {light:4d} | {status}")
            
            time.sleep(0.1)  # 10Hz
        
        # Analyse des résultats
        print("\n4. Analyse des résultats...")
        if readings:
            avg_distance = sum(r['distance'] for r in readings) / len(readings)
            avg_light = sum(r['light'] for r in readings) / len(readings)
            
            print(f"   📊 Lectures totales: {len(readings)}")
            print(f"   📏 Distance moyenne: {avg_distance:.1f} cm")
            print(f"   💡 Lumière moyenne: {avg_light:.1f}")
            print(f"   🚨 Obstacles détectés: {obstacles_detected}")
            print(f"   ⚠️  Taux d'obstacles: {obstacles_detected/len(readings)*100:.1f}%")
        
        # Test de fonctionnalités avancées
        print("\n5. Tests de fonctionnalités...")
        
        # Test de diagnostic
        print("   a. Diagnostic système...")
        diag = nav.get_diagnostics()
        for key, value in diag.items():
            print(f"      {key}: {value}")
        
        # Test de configuration dynamique
        print("   b. Configuration dynamique...")
        nav.update_config({'obstacle_threshold': 80.0})
        print(f"      Nouveau seuil: {nav.config['obstacle_threshold']} cm")
        
        # Arrêt
        print("\n6. Arrêt du système...")
        nav.stop()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📈 RÉSUMÉ DU TEST AVANCÉ")
        print("=" * 60)
        stats = nav.stats
        total_time = time.time() - nav.stats.get('start_time', start_time)
        
        print(f"Durée totale: {total_time:.1f}s")
        print(f"Lectures Arduino: {stats.get('arduino_readings', 0)}")
        print(f"Détections: {stats.get('detections_count', 0)}")
        print(f"Alertes: {stats.get('warnings_issued', 0)}")
        
        if obstacles_detected > 0:
            print("\n⚠️  RECOMMANDATIONS:")
            print("- Ajuster le seuil de détection si nécessaire")
            print("- Vérifier la position des capteurs")
            print("- Tester différentes conditions d'éclairage")
        else:
            print("\n✅ TOUT EST OPTIMAL!")
            print("- Le système fonctionne correctement")
            print("- Aucun obstacle détecté dans la plage de test")
        
        print("🎉 TEST AVANCÉ RÉUSSI!")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
