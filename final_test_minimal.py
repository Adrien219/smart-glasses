#!/usr/bin/env python3
import sys
import time
import logging
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO)

print("🧪 TEST FINAL - Version Minimaliste")
print("=" * 60)

try:
    from core.navigation.navigation_module import NavigationModule
    
    # 1. Initialisation
    print("1. Initialisation...")
    nav = NavigationModule()
    print("✅ Instance créée")
    
    # 2. Test Arduino
    print("\n2. Test Arduino...")
    result = nav.test_arduino_connection()
    print(f"   {result['status']}: {result['message']}")
    
    # 3. Démarrage
    print("\n3. Démarrage système...")
    nav.start()
    print("✅ Système démarré")
    
    # 4. Boucle de démonstration (5 secondes)
    print("\n4. Démonstration (5 secondes)...")
    print("   Surveillance des données Arduino:")
    
    start_time = time.time()
    while time.time() - start_time < 5:
        state = nav.get_state()
        arduino_status = state['arduino_status']['connection_status']
        
        sensor_data = nav.get_sensor_data()
        distance = sensor_data['ultrasonic']['last_reading']
        light = sensor_data['light']['level']
        
        if distance:
            print(f"   📏 {distance['distance']:.1f} cm | 💡 {light} | 🔌 {arduino_status}", end='\r')
        
        time.sleep(0.5)
    
    # 5. Arrêt
    print("\n\n5. Arrêt...")
    nav.stop()
    print("✅ Système arrêté")
    
    print("\n🎉 TEST RÉUSSI!")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
