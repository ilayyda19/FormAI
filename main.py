import cv2 as cv
import numpy as np
from src.core.pose_estimator import PoseEstimator 
from src.core.hand_landmarker import HandLandmarker
from src.core.hand_gestures import GestureAnalyz


print("Loading...")
estimator = PoseEstimator()
hand_sensor = HandLandmarker()
gesture_analyzer = GestureAnalyz()

print("The camera is turning on...")

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    
    frame = cv.flip(frame, 1) 
   
    
    estimator.process_frame(frame)
    frame = estimator.draw_landmarks(frame)
    
    hand_landmarks, handedness = hand_sensor.detect(frame)

    if hand_landmarks and handedness:
        komut = gesture_analyzer.get_gesture(hand_landmarks, handedness)
        frame = hand_sensor.draw_landmarks(frame)

        cv.putText(frame, f"System promt: {komut} ({handedness})", (30, 50), 
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv.imshow('Sports Analysis - Live', frame)
    
    if cv.waitKey(1) == ord('q'):
        break

hand_sensor.close()
cap.release()
cv.destroyAllWindows()