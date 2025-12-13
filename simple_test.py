#!/usr/bin/env python3
"""
Test simplifié pour vérifier l'installation.
"""
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Teste les imports de base."""
    modules_to_test = [
        ("core.navigation", "NavigationModule"),
        ("core.navigation.fusion.eoh", "EgocentricOccupancyHistogram"),
        ("core.navigation.decision.priority_engine", "PriorityEngine"),
    ]
    
    print("Test des imports...")
    for module_path, class_name in modules_to_test:
        try:
            # Import dynamique
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_path}.{class_name} importé avec succès")
        except ImportError as e:
            print(f"✗ Erreur import {module_path}.{class_name}: {e}")
            return False
        except AttributeError as e:
            print(f"✗ Classe {class_name} non trouvée dans {module_path}: {e}")
            return False
    
    return True

def test_basic_functionality():
    """Teste les fonctionnalités de base."""
    print("\nTest des fonctionnalités de base...")
    
    try:
        from core.navigation.fusion.eoh import EgocentricOccupancyHistogram
        
        # Test EOH
        eoh = EgocentricOccupancyHistogram(bins=5, fov_deg=60)
        eoh.update(-20, 100, confidence=0.8)
        eoh.update(0, 50, confidence=0.9)
        eoh.update(20, 150, confidence=0.7)
        
        snapshot = eoh.get_snapshot()
        print(f"✓ EOH fonctionne: min_distance={snapshot.min_distance}")
        
        # Test PriorityEngine
        from core.navigation.decision.priority_engine import PriorityEngine
        
        engine = PriorityEngine()
        decision = engine.evaluate(snapshot)
        print(f"✓ PriorityEngine fonctionne: action_needed={decision.action_needed}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur fonctionnalités: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale."""
    print("="*60)
    print("Test simplifié du module de navigation")
    print("="*60)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Les imports ont échoué")
        return False
    
    # Test 2: Fonctionnalités de base
    if not test_basic_functionality():
        print("\n❌ Les tests de fonctionnalités ont échoué")
        return False
    
    print("\n" + "="*60)
    print("✅ Tous les tests ont réussi!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)