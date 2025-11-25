import cv2
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Caméra non détectée")
else:
    print("✅ Caméra détectée")
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Test caméra", frame)
        cv2.waitKey(0)
    cap.release()
    cv2.destroyAllWindows()