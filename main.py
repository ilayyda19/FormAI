import cv2 as cv
import numpy as np
import time

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

consecutive_gestures = 0
previous_command = None
CONFIRMATION_THRESHOLD = 10
last_command_time = 0
is_paused = False
active_action = "None"

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
        
        current_command = gesture_analyzer.get_gesture(hand_landmarks)
        frame = hand_sensor.draw_landmarks(frame)

        if current_command and current_command != "unknown": 
            
            if current_command == previous_command:
                consecutive_gestures += 1
            else:
                consecutive_gestures = 1
                previous_command = current_command

            if consecutive_gestures >= CONFIRMATION_THRESHOLD and (time.time() - last_command_time) > 2.0:
                active_action = current_command
                last_command_time = time.time()
                consecutive_gestures = 0

                if active_action == "FIST":
                    is_paused = not is_paused
                    print("System Status Changed:", "PAUSED" if is_paused else "RUNNING")
                elif active_action == "PEACE":
                    print("Counter Reset!")
                    
        else:
            consecutive_gestures = 0
            previous_command = None
            
        cv.putText(frame, f"Detected: {current_command}", (30, 40), 
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        cv.putText(frame, f"Action: {active_action}", (30, 80), 
                   cv.FONT_HERSHEY_SIMPLEX, 1, (230, 0, 160), 2)

    else:
        consecutive_gestures = 0
        previous_command = None

    status_color = (0, 0, 255) if is_paused else (0, 255, 0)
    cv.putText(frame, f"SYSTEM: {'PAUSED' if is_paused else 'ACTIVE'}", (30, 120), 
               cv.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

    cv.imshow('Sports Analysis - Live', frame)
    
    if cv.waitKey(1) == ord('q'):
        break

hand_sensor.close()
cap.release()
cv.destroyAllWindows()