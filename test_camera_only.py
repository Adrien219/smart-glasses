# test_camera_only.py
import cv2

print("📷 Test caméra seule")
cap = cv2.VideoCapture(0)

if cap.isOpened():
    print("✅ Caméra OK")
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Caméra Test', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("❌ Erreur lecture frame")
            break
else:
    print("❌ Caméra inaccessible")

cap.release()
cv2.destroyAllWindows()
print("✅ Test terminé")