import cv2 as cv
import numpy as np
from src.core.pose_estimator import PoseEstimator 

print("Yapay zeka modeli yükleniyor...")
estimator = PoseEstimator()
print("Kamera açılıyor...")

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
    

    cv.imshow('Sports Analysis - Live', frame)
    
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()