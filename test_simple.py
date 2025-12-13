#!/usr/bin/env python3
"""
Test simplifié du module de navigation.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Test du module de navigation...")
print("=" * 60)

try:
    from core.navigation import NavigationModule
    
    print("1. Création de l'instance...")
    nav = NavigationModule()
    
    print("2. Démarrage...")
    nav.start()
    
    print("3. Test pendant 10 secondes...")
    for i in range(10):
        state = nav.get_state()
        if state:
            print(f"  [{i+1}/10] État: {state.get('module_state', 'N/A')}")
        else:
            print(f"  [{i+1}/10] État: None (démarrage en cours)")
        time.sleep(1)
    
    print("4. Arrêt...")
    nav.stop()
    
    print("\n✅ Test réussi!")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()