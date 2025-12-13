import sys
import os

# Ajoute le répertoire courant
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("TEST FINAL DU MODULE DE NAVIGATION")
print("=" * 60)

# Test 1: Vérifie la structure
print("\n1. Vérification de la structure:")
required_files = [
    "core/__init__.py",
    "core/navigation/__init__.py", 
    "core/navigation/navigation_module.py",
    "core/navigation/fusion/eoh.py",
    "core/navigation/decision/priority_engine.py",
]

missing = []
for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MANQUANT")
        missing.append(file)

if missing:
    print(f"\n❌ {len(missing)} fichiers manquants!")
    sys.exit(1)

# Test 2: Importation de base
print("\n2. Test d'importation de base:")
try:
    import core.navigation
    print("✓ core.navigation importé")
    
    # Vérifie les attributs
    if hasattr(core.navigation, 'NavigationModule'):
        print("✓ NavigationModule disponible")
    if hasattr(core.navigation, 'NavigationState'):
        print("✓ NavigationState disponible")
        
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test EOH simple
print("\n3. Test EOH simple:")
try:
    from core.navigation.fusion.eoh import EgocentricOccupancyHistogram
    
    eoh = EgocentricOccupancyHistogram(bins=5, fov_deg=60)
    eoh.update(-20, 100, confidence=0.8)
    eoh.update(0, 50, confidence=0.9)
    snapshot = eoh.get_snapshot()
    
    print(f"✓ EOH créé et testé")
    print(f"  Min distance: {snapshot.min_distance}")
    print(f"  Bins: {len(snapshot.bins)}")
    
except Exception as e:
    print(f"✗ Erreur EOH: {e}")

# Test 4: Test PriorityEngine
print("\n4. Test PriorityEngine:")
try:
    from core.navigation.decision.priority_engine import PriorityEngine
    
    engine = PriorityEngine()
    print(f"✓ PriorityEngine créé")
    print(f"  Emergency dist: {engine.emergency_dist}cm")
    
except Exception as e:
    print(f"✗ Erreur PriorityEngine: {e}")

# Test 5: Test NavigationModule minimal
print("\n5. Test NavigationModule minimal:")
try:
    from core.navigation import NavigationModule
    
    # Crée une config minimaliste
    class MinimalConfig:
        def __init__(self):
            self.config = {
                'camera': {'fov_deg': 62.2, 'width': 320, 'height': 240, 'fps': 5},
                'ultrasonic': {'trig_pin': 23, 'echo_pin': 24, 'sample_rate_hz': 10},
                'system': {'debug_mode': True}
            }
    
    nav = NavigationModule()
    print("✓ NavigationModule instancié")
    
    # Essaie quelques méthodes
    state = nav.get_state()
    print(f"  État initial: {state['module_state']}")
    
except Exception as e:
    print(f"✗ Erreur NavigationModule: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ TEST TERMINÉ - Vérifiez les résultats ci-dessus")
print("=" * 60)