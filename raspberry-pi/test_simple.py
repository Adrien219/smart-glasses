#!/usr/bin/env python3
# TEST SIMPLIFIÉ - Smart Glasses

import cv2
import requests
import time

def test_esp32_stream():
    """Test simple du stream ESP32"""
    print("📹 Test du stream ESP32...")
    
    try:
        esp32_ip = "10.231.158.139"
        stream_url = f"http://{esp32_ip}/stream"
        
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            print("❌ Impossible d'ouvrir le stream ESP32")
            return False
            
        # Essai de lecture de quelques frames
        for i in range(10):
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame {i+1} reçue - Taille: {frame.shape}")
                cv2.imshow('ESP32 Test', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print(f"❌ Erreur frame {i+1}")
                break
                
        cap.release()
        cv2.destroyAllWindows()
        return True
        
    except Exception as e:
        print(f"❌ Erreur stream: {e}")
        return False

def test_esp32_status():
    """Test du status ESP32"""
    print("📡 Test du status ESP32...")
    
    try:
        esp32_ip = "10.231.158.139"
        response = requests.get(f"http://{esp32_ip}/status", timeout=5)
        print(f"✅ Status ESP32:\n{response.text}")
        return True
    except Exception as e:
        print(f"❌ Erreur status: {e}")
        return False

def test_rpi_camera():
    """Test de la caméra Raspberry Pi"""
    print("📷 Test caméra RPi...")
    
    try:
        # Essaie différentes indexes de caméra
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Caméra {i} fonctionnelle - Taille: {frame.shape}")
                    cap.release()
                    return True
                cap.release()
                
        print("❌ Aucune caméra RPi détectée")
        return False
        
    except Exception as e:
        print(f"❌ Erreur caméra RPi: {e}")
        return False

if __name__ == "__main__":
    print("🔍 TEST SMART GLASSES - DÉBUT")
    
    # Tests individuels
    test_esp32_status()
    test_esp32_stream() 
    test_rpi_camera()
    
    print("🔍 TEST SMART GLASSES - TERMINÉ")