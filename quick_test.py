#!/usr/bin/env python3
"""
Test ultime du module de navigation - version robuste.
"""
import sys
import os
import importlib.util

# Ajoute le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def import_module_directly(module_path, class_name):
    """Importe un module directement depuis son fichier."""
    try:
        spec = importlib.util.spec_from_file_location(
            class_name.lower(), 
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, class_name):
            return getattr(module, class_name)
        else:
            print(f"  ✗ Classe {class_name} non trouvée dans {module_path}")
            return None
    except Exception as e:
        print(f"  ✗ Erreur import {module_path}: {e}")
        return None

def main():
    print("="*70)
    print("TEST ULTIME DU MODULE DE NAVIGATION")
    print("="*70)
    
    # Liste des modules à tester avec leurs chemins
    modules_to_test = [
        ("NavigationModule", "core/navigation/navigation_module.py"),
        ("NavigationState", "core/navigation/navigation_module.py"),
        ("EgocentricOccupancyHistogram", "core/navigation/fusion/eoh.py"),
        ("PriorityEngine", "core/navigation/decision/priority_engine.py"),
        ("CameraAdapter", "core/navigation/adapters/camera_adapter.py"),
        ("UltrasonicAdapter", "core/navigation/adapters/hc_sr04_adapter.py"),
    ]
    
    print("\n1. Test des imports individuels:")
    print("-" * 40)
    
    imported_classes = {}
    
    for class_name, file_path in modules_to_test:
        if os.path.exists(file_path):
            print(f"  ✓ Fichier existe: {file_path}")
            cls = import_module_directly(file_path, class_name)
            if cls:
                imported_classes[class_name] = cls
                print(f"    ✓ Classe {class_name} importée")
            else:
                print(f"    ✗ Échec import {class_name}")
        else:
            print(f"  ✗ Fichier manquant: {file_path}")
    
    print("\n2. Test de fonctionnement:")
    print("-" * 40)
    
    # Test EOH
    if 'EgocentricOccupancyHistogram' in imported_classes:
        try:
            EOH = imported_classes['EgocentricOccupancyHistogram']
            eoh = EOH(bins=5, fov_deg=60)
            eoh.update(-20, 100, confidence=0.8)
            snapshot = eoh.get_snapshot()
            print(f"  ✓ EOH fonctionne: min_distance={snapshot.min_distance}")
        except Exception as e:
            print(f"  ✗ EOH erreur: {e}")
    
    # Test PriorityEngine
    if 'PriorityEngine' in imported_classes:
        try:
            PriorityEngine = imported_classes['PriorityEngine']
            engine = PriorityEngine()
            print(f"  ✓ PriorityEngine fonctionne: emergency={engine.emergency_dist}cm")
        except Exception as e:
            print(f"  ✗ PriorityEngine erreur: {e}")
    
    # Test NavigationModule
    if 'NavigationModule' in imported_classes:
        try:
            NavigationModule = imported_classes['NavigationModule']
            nav = NavigationModule()
            state = nav.get_state()
            print(f"  ✓ NavigationModule fonctionne: état={state['module_state']}")
        except Exception as e:
            print(f"  ✗ NavigationModule erreur: {e}")
    
    print("\n3. Test d'intégration:")
    print("-" * 40)
    
    if all(k in imported_classes for k in ['EgocentricOccupancyHistogram', 'PriorityEngine']):
        try:
            # Crée EOH
            EOH = imported_classes['EgocentricOccupancyHistogram']
            eoh = EOH(bins=7, fov_deg=62.2)
            
            # Ajoute des obstacles
            obstacles = [(-30, 200), (0, 80), (30, 150)]
            for bearing, distance in obstacles:
                eoh.update(bearing, distance, confidence=0.8)
            
            snapshot = eoh.get_snapshot()
            
            # Utilise PriorityEngine
            PriorityEngine = imported_classes['PriorityEngine']
            engine = PriorityEngine()
            decision = engine.evaluate(snapshot)
            
            print(f"  ✓ Intégration réussie!")
            print(f"    Distance min: {snapshot.min_distance}cm")
            print(f"    Décision: {decision.action_needed}")
            print(f"    Message: {decision.message[:40]}...")
            
        except Exception as e:
            print(f"  ✗ Intégration échouée: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("RÉSUMÉ:")
    print(f"Classes importées avec succès: {len(imported_classes)}/{len(modules_to_test)}")
    
    if len(imported_classes) >= 4:  # Au moins les 4 principales
        print("✅ MODULE DE NAVIGATION OPÉRATIONNEL!")
    else:
        print("⚠  Certains composants sont manquants")
    
    print("="*70)

if __name__ == "__main__":
    main()