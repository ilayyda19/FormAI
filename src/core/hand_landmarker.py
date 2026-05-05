import cv2 as cv
import mediapipe as mp
import time
import numpy as np
from src.utils.draw_utils import draw_skeleton, draw_points

class HandLandmarker:

    CONNECTIONS = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),(0,17)
    ]

    def __init__(self, model_path='models/hand_landmarker.task'):
        self.current_landmarks = None
        self.current_handedness = None
        self._timestamp = 0

        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            num_hands=1,
            result_callback=self._result_callback
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def _result_callback(self, result, output_image, timestamp_ms):
        if result.hand_landmarks:
            self.current_landmarks = result.hand_landmarks[0]

            raw_handedness = result.handedness[0][0].category_name

            if raw_handedness == "Right":
                self.current_handedness = "Left"
            else:
                self.current_handedness = "Right"
        else:
            self.current_landmarks = None
            self.current_handedness = None

    def detect(self, frame):
        self._timestamp = int(time.time() * 1000)
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.landmarker.detect_async(mp_image, self._timestamp)
        return self.current_landmarks, self.current_handedness
    
    def draw_landmarks(self, frame):
        landmarks = self.current_landmarks
        
        if landmarks:
        
           draw_skeleton(frame, self.current_landmarks, self.CONNECTIONS, color=(95, 0, 240))
           draw_points(frame, self.current_landmarks)
                
        return frame

    def close(self):
        self.landmarker.close()