# main.py
"""
Hand Control + YOLOv8 Obstacle Detection + Pinch Gestures
Usage: python main.py
"""
import sys
import time
import json
import cv2
from collections import deque
from hand_module import HandDetector, Gesture
import pyttsx3
import threading
import queue
import traceback
from ultralytics import YOLO
import numpy as np

# ----------------- VoiceAssistant thread-safe -----------------
class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def speak(self, text):
        self.queue.put(text)

    def _run(self):
        while True:
            text = self.queue.get()
            if text is None:
                break
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS thread error: {e}")
            self.queue.task_done()

# ----------------- Config -----------------
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SMOOTH_N = 10
ACTION_COOLDOWN = 1.5
OBSTACLE_COOLDOWN = 5.5

# ----------------- YOLOv8 -----------------
yolo_model = YOLO("yolov8n.pt")

def detect_obstacles(frame):
    results = yolo_model(frame)
    obstacles = []
    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy()
        confidences = r.boxes.conf.cpu().numpy()
        for box, cls_id, conf in zip(boxes, classes, confidences):
            if conf < 0.5:
                continue
            obstacles.append({
                "box": box.astype(int),
                "class_id": int(cls_id),
                "confidence": float(conf)
            })
    return obstacles

# ----------------- Action performer -----------------
def perform_action(action_name, va):
    print(f">>> ACTION: {action_name}")
    tts_map = {
        "volume_up": "Volume augmenté",
        "volume_down": "Volume diminué",
        "play_pause": "Lecture ou pause",
        "lock_system": "Système verrouillé",
        "select": "Sélection effectuée",
        "take_photo": "Photo prise",
        "open_menu": "Menu principal",
        "next": "Suivant",
        "previous": "Précédent",
        "announce_obstacle": "Obstacle détecté devant",
        "sos": "Alerte d'urgence envoyée",
        "stop_system": "Arrêt complet du système",
        "help": "Aide vocale activée"
    }
    spoken = tts_map.get(action_name, action_name.replace("_", " "))
    try:
        va.speak(spoken)
    except Exception as e:
        print(f"Error during TTS: {e}")

# ----------------- Pinch detection -----------------
def detect_pinch(lmList):
    """Retourne le doigt pincé avec le pouce, None sinon"""
    if not lmList:
        return None
    thumb_tip = lmList[4][1:3]  # x,y
    finger_tips = {
        "index": lmList[8][1:3],
        "middle": lmList[12][1:3],
        "ring": lmList[16][1:3],
        "pinky": lmList[20][1:3]
    }
    for finger, tip in finger_tips.items():
        distance = ((thumb_tip[0]-tip[0])**2 + (thumb_tip[1]-tip[1])**2)**0.5
        if distance < 40:  # seuil ajustable
            return finger
    return None

# ----------------- Main loop -----------------
def main():
    try:
        va = VoiceAssistant()
        va.speak("Initialisation du module de commandes par la main et détection d'obstacles.")

        detector = HandDetector(max_hands=1, detection_conf=0.75, track_conf=0.7)
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            va.speak("Caméra introuvable. Vérifiez la connexion.")
            print("❌ Unable to open camera.")
            return

        gesture_window = deque(maxlen=SMOOTH_N)
        last_triggered = {}
        last_obstacle_alert = 0

        va.speak("Module prêt. Montrez une main pour commencer.")

        while True:
            ok, img = cap.read()
            if not ok:
                print("⚠️ Frame not received")
                break

            h, w, _ = img.shape

            # ---------- Hand detection ----------
            try:
                img = detector.findHands(img, draw=True)
                lmList = detector.findPosition(img, draw=False)
            except Exception as e:
                print(f"MediaPipe error: {e}")
                lmList = []

            # ---------- Gesture recognition ----------
            gesture = detector.recognizeGesture(lmList)
            motion = detector.detect_motion()

            # ---------- Smoothing ----------
            gesture_window.append(gesture.name if gesture else "NONE")
            majority = max(set(gesture_window), key=lambda g: gesture_window.count(g))
            current_gesture = None if majority == "NONE" else Gesture[majority]

            # ---------- Detect pinch ----------
            pinch_finger = detect_pinch(lmList)
            action_to_fire = None
            now = time.time()

            # Priorité: pinch > swipe > gesture
            if pinch_finger:
                action_to_fire = CONFIG.get("pinch", {}).get(pinch_finger)
            elif motion:
                swipe = motion.get("swipe")
                action_to_fire = CONFIG.get("swipe", {}).get(swipe)
            if not action_to_fire and current_gesture:
                action_to_fire = CONFIG.get("gestures", {}).get(current_gesture.name)

            # ---------- Apply cooldown ----------
            if action_to_fire:
                last_t = last_triggered.get(action_to_fire, 0)
                if now - last_t > ACTION_COOLDOWN:
                    perform_action(action_to_fire, va)
                    last_triggered[action_to_fire] = now

            # ---------- YOLO obstacle detection ----------
            obstacles = detect_obstacles(img)
            if obstacles and (now - last_obstacle_alert > OBSTACLE_COOLDOWN):
                va.speak("Obstacle détecté devant")
                last_obstacle_alert = now

            # ---------- Overlay ----------
            for obj in obstacles:
                x1, y1, x2, y2 = obj['box']
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(img, f"Obj:{obj['class_id']}", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            label = majority if not pinch_finger else f"Pinch-{pinch_finger}"
            cv2.putText(img, f"Gesture: {label}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            if motion:
                swipe = motion.get("swipe")
                if swipe:
                    cv2.putText(img, f"Swipe: {swipe}", (10,70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
            if action_to_fire:
                cv2.putText(img, f"Action: {action_to_fire}", (10,110),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

            cv2.imshow("Hand Control + YOLOv8 + Pinch", img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                va.speak("Arrêt du module")
                break
            if key == ord('c'):
                gesture_window.clear()
                va.speak("Calibrage terminé")

        cap.release()
        cv2.destroyAllWindows()

    except Exception:
        print("=== Exception in main loop ===")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
