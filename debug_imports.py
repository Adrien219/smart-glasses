import sys
import os

print("DEBUG: Python path et imports")
print("=" * 60)

# 1. Ajoute le répertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
print(f"1. Current dir ajouté: {current_dir}")

# 2. Essaie d'importer directement
print("\n2. Test d'importation directe:")
try:
    # Essaie d'importer core
    import core
    print("✓ core importé")
except ImportError as e:
    print(f"✗ Erreur import core: {e}")
    
    # Vérifie si le fichier existe
    core_init = os.path.join(current_dir, "core", "__init__.py")
    if os.path.exists(core_init):
        print(f"  Fichier trouvé: {core_init}")
    else:
        print(f"  Fichier MANQUANT: {core_init}")
        print("  Création du fichier...")
        with open(core_init, 'w') as f:
            f.write("# Core package\n")
        print("  Fichier créé!")

# 3. Essaie d'importer navigation_module directement
print("\n3. Test d'importation navigation_module:")
try:
    # Chemin vers le fichier
    nav_path = os.path.join(current_dir, "core", "navigation", "navigation_module.py")
    if os.path.exists(nav_path):
        print(f"✓ Fichier trouvé: {nav_path}")
        
        # Import avec importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location("navigation_module", nav_path)
        nav_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nav_module)
        print("✓ navigation_module chargé avec importlib")
        
        # Essaie de créer une instance
        NavigationModule = getattr(nav_module, 'NavigationModule', None)
        if NavigationModule:
            print("✓ Classe NavigationModule trouvée")
            # Essaie de créer une instance avec config minimaliste
            test_config = {
                'camera': {'fov_deg': 62.2, 'width': 320, 'height': 240, 'fps': 5},
                'ultrasonic': {'trig_pin': 23, 'echo_pin': 24, 'sample_rate_hz': 10},
                'system': {'debug_mode': True}
            }
            try:
                nav = NavigationModule()
                print("✓ Instance NavigationModule créée")
            except Exception as e:
                print(f"✗ Erreur création instance: {e}")
        else:
            print("✗ Classe NavigationModule non trouvée")
    else:
        print(f"✗ Fichier non trouvé: {nav_path}")
        
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# 4. Test simple d'EOH
print("\n4. Test d'EOH simple:")
try:
    eoh_path = os.path.join(current_dir, "core", "navigation", "fusion", "eoh.py")
    if os.path.exists(eoh_path):
        print(f"✓ Fichier eoh.py trouvé")
        
        # Exécute le code directement
        with open(eoh_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Crée un namespace
        namespace = {'np': __import__('numpy')}
        exec(code, namespace)
        
        # Essaie de créer une instance
        EOH = namespace.get('EgocentricOccupancyHistogram')
        if EOH:
            eoh = EOH(bins=5, fov_deg=60)
            eoh.update(-20, 100, confidence=0.8)
            snapshot = eoh.get_snapshot()
            print(f"✓ EOH testé: min_distance = {snapshot.min_distance}")
        else:
            print("✗ Classe EOH non trouvée")
    else:
        print(f"✗ Fichier eoh.py non trouvé: {eoh_path}")
        
except Exception as e:
    print(f"✗ Erreur test EOH: {e}")

print("\n" + "=" * 60)
print("DEBUG terminé")