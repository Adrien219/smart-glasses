# Crée ce fichier: test_final.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Test Final - Navigation Module ===")

try:
    # Test 1: Vérifie que EOH existe
    from core.navigation.fusion.eoh import EgocentricOccupancyHistogram
    print("✓ 1. EOH importé")
    
    # Test 2: Vérifie que NavigationModule existe
    from core.navigation.navigation_module import NavigationModule
    print("✓ 2. NavigationModule importé")
    
    # Test 3: Crée une instance
    nav = NavigationModule()
    print(f"✓ 3. Instance créée, état: {nav.state}")
    
    # Test 4: Méthodes de base
    nav.start()
    print(f"✓ 4. Module démarré")
    
    state = nav.get_state()
    print(f"✓ 5. État récupéré: {state}")
    
    nav.stop()
    print("✓ 6. Module arrêté")
    
    print("\n" + "="*40)
    print("✅ TOUS LES TESTS ONT RÉUSSI !")
    print("="*40)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    
    # Aide au débogage
    print("\n📂 Fichiers trouvés dans core/navigation/:")
    for root, dirs, files in os.walk("core/navigation"):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), "core/navigation")
                print(f"  - {rel_path}")