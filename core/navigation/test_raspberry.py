#!/usr/bin/env python3
"""
Test sur Raspberry Pi avec vrais capteurs.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.navigation import NavigationModule

def main():
    print("Test sur Raspberry Pi - Vrais capteurs")
    print("=" * 50)
    
    try:
        # Initialise avec la configuration
        nav = NavigationModule("config/navigation.yaml")
        
        # Démarre
        nav.start()
        
        print("Module démarré. Surveillance en cours...")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        # Monitor
        for i in range(30):  # 30 secondes de test
            state = nav.get_state()
            print(f"\r📊 État: {state['module_state']:10} | "
                  f"Distance: {state['eoh_snapshot']['min_distance'] or '---':6}cm | "
                  f"Temps: {i+1}/30s", end='', flush=True)
            time.sleep(1)
        
        print("\n\nTest terminé avec succès!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrompu")
    except Exception as e:
        print(f"\nErreur: {e}")
    finally:
        if 'nav' in locals():
            nav.stop()
            print("Module arrêté")

if __name__ == "__main__":
    main()