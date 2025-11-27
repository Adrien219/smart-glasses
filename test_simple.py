import cv2
import time

print("🧪 TEST SIMPLIFIÉ DU SYSTÈME")

# Test caméra
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Caméra inaccessible")
    exit()

print("✅ Caméra OK - Test en cours...")

try:
    mode = "navigation"
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Afficher le mode actuel
        cv2.putText(frame, f"Mode: {mode}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Q=Quit, 1-5=Changer mode", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Test Smart Glasses", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            mode = "navigation"
            print("🔄 Mode: Navigation")
        elif key == ord('2'):
            mode = "object"
            print("🔄 Mode: Objets")
        elif key == ord('3'):
            mode = "face" 
            print("🔄 Mode: Visages")
        elif key == ord('4'):
            mode = "text"
            print("🔄 Mode: Texte")
        elif key == ord('5'):
            mode = "ai"
            print("🔄 Mode: IA")
            
except KeyboardInterrupt:
    print("🛑 Arrêt manuel")
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test terminé")