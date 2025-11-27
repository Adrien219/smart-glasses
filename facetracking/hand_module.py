# hand_module.py
"""
Hand Detection Module using MediaPipe
"""

import cv2
import mediapipe as mp
from enum import Enum

# ---------------- Gestures ----------------
class Gesture(Enum):
    OPEN = 1
    FIST = 2
    POINT = 3
    V_SIGN = 4
    NONE = 5

# ---------------- HandDetector ----------------
class HandDetector:
    def __init__(self, max_hands=1, detection_conf=0.65, track_conf=0.6):
        self.max_hands = max_hands
        self.detection_conf = detection_conf
        self.track_conf = track_conf

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_conf,
            min_tracking_confidence=self.track_conf
        )
        self.mpDraw = mp.solutions.drawing_utils

        self.lmList = []
        self.results = None

        # Pour le calcul du mouvement
        self.prev_lm = None

    # ---------------- findHands ----------------
    def findHands(self, img, draw=True):
        """
        img: image BGR
        draw: dessiner landmarks et connections
        Retourne l'image avec ou sans dessin
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img  # Toujours BGR pour affichage OpenCV

    # ---------------- findPosition ----------------
    def findPosition(self, img, handNo=0, draw=False):
        """
        Retourne la liste des landmarks [(id, x, y), ...] pour la main handNo
        img: image BGR
        """
        self.lmList = []
        h, w, c = img.shape

        if self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                for id, lm in enumerate(myHand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lmList.append((id, cx, cy))
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
                        # Afficher l'id du landmark
                        cv2.putText(img, str(id), (cx+2, cy+2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0), 1)
        return self.lmList

    # ---------------- recognizeGesture ----------------
    def recognizeGesture(self, lmList):
        """
        Retourne une Gesture basée sur landmarks
        lmList: [(id, x, y), ...]
        """
        if not lmList or len(lmList) == 0:
            return Gesture.NONE

        # Exemple simple de détection (OPEN ou FIST)
        tips = [4, 8, 12, 16, 20]  # doigts : pouce, index, majeur, annulaire, auriculaire
        open_fingers = 0

        # Compter combien de doigts sont ouverts
        for tip in tips:
            _, x, y = lmList[tip]
            # Si y du tip < y du PIP (landmark avant), doigt ouvert
            if tip != 4:  # sauf pouce
                if lmList[tip][2] < lmList[tip-2][2]:
                    open_fingers += 1
            else:
                # pouce : comparaison sur x
                if lmList[tip][1] > lmList[tip-1][1]:
                    open_fingers += 1

        if open_fingers == 5:
            return Gesture.OPEN
        elif open_fingers == 0:
            return Gesture.FIST
        elif open_fingers == 2:
            return Gesture.V_SIGN
        elif open_fingers == 1:
            return Gesture.POINT
        else:
            return Gesture.NONE

    # ---------------- detect_motion ----------------
    def detect_motion(self):
        """
        Détecte les mouvements basiques (swipe) entre frames
        Retourne dict: {"swipe": "left/right/up/down"} ou None
        """
        if not self.lmList:
            return None

        motion = {}
        if self.prev_lm:
            # comparer le centre de la main
            cx_prev = sum([x for _, x, _ in self.prev_lm]) / len(self.prev_lm)
            cy_prev = sum([y for _, _, y in self.prev_lm]) / len(self.prev_lm)
            cx_curr = sum([x for _, x, _ in self.lmList]) / len(self.lmList)
            cy_curr = sum([y for _, _, y in self.lmList]) / len(self.lmList)

            dx = cx_curr - cx_prev
            dy = cy_curr - cy_prev

            threshold = 20  # pixels
            if abs(dx) > abs(dy) and abs(dx) > threshold:
                motion["swipe"] = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) and abs(dy) > threshold:
                motion["swipe"] = "down" if dy > 0 else "up"

        self.prev_lm = self.lmList.copy()
        return motion
