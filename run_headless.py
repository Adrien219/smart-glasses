# run_headless.py - VERSION WINDOWS CORRIGÉE
import os
import sys
import time
import logging
import platform

# ==================== DÉTECTION DU SYSTÈME ====================
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# ==================== CONFIGURATION LOGGING ====================
if IS_WINDOWS:
    # Chemin dans le dossier temporaire utilisateur
    log_file = os.path.join(os.environ['TEMP'], 'smart_glasses.log')
else:
    log_file = "/tmp/smart_glasses.log"

# Configuration logging SIMPLIFIÉE - sans FileHandler pour l'instant
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]  # Uniquement console
)

print("=" * 60)
print("🚀 SMART GLASSES - MODE HEADLESS")
print(f"📋 Système détecté: {platform.system()}")
print("=" * 60)

def main():
    try:
        # ==================== IMPORT AVEC GESTION D'ERREURS ====================
        try:
            from main import SmartGlassesSystem
            print("✅ Import main réussi")
        except ImportError as e:
            print(f"❌ Erreur import: {e}")
            print(f"📁 Chemin Python: {sys.path}")
            return
        
        # ==================== INITIALISATION ====================
        print("Initialisation du système...")
        glasses = SmartGlassesSystem()
        
        # Force le mode headless
        glasses.headless_mode = True
        print("✅ Mode headless activé")
        
        # ==================== DÉMARRAGE ====================
        print("Démarrage de la boucle principale...")
        glasses.start()
        
    except KeyboardInterrupt:
        print("🛑 Arrêt demandé par l'utilisateur (Ctrl+C)")
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🧹 Nettoyage et arrêt du programme")
        try:
            if 'glasses' in locals():
                glasses.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()