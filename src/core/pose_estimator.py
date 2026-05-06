import cv2 as cv
import mediapipe as mp
import numpy as np
import time
from src.utils.math_utils import calculate_angle
from src.utils.draw_utils import draw_skeleton, draw_points

class PoseEstimator:
    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10), 
        (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19), 
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23), 
        (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), 
        (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
    ]
    def __init__(self, model_path='models/pose_landmarker_full.task'):
        self.current_landmarks=None

        BaseOptions = mp.tasks.BaseOptions
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = PoseLandmarkerOptions(
            base_options = BaseOptions(model_asset_path = model_path),
            running_mode = VisionRunningMode.LIVE_STREAM, 
            result_callback = self._result_callback
        )
        self.landmarker = PoseLandmarker.create_from_options(options)

    def _result_callback(self, result, output_image, timestamp_ms):
        if result.pose_landmarks:
            self.current_landmarks = result.pose_landmarks[0]
        else:
            self.current_landmarks = None

    def process_frame(self, frame):
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp = time.time_ns() // 1_000_000 
        self.landmarker.detect_async(mp_image, timestamp)
        
        angles = {}
        
        landmarks = self.current_landmarks 
        
        if landmarks:
            hip_r, knee_r, ankle_r, elbow_r, sholder_r, wrist_r = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y], [landmarks[14].x,landmarks[14].y], [landmarks[12].x, landmarks[12].y], [landmarks[16].x,landmarks[16].y]
            hip_l, knee_l, ankle_l, elbow_l, sholder_l, wrist_l = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y], [landmarks[13].x,landmarks[13].y], [landmarks[11].x, landmarks[11].y], [landmarks[15].x,landmarks[15].y]

            angles['knee_r'] = calculate_angle(hip_r, knee_r, ankle_r)
            angles['knee_l'] = calculate_angle(hip_l, knee_l, ankle_l)

            angles['sholder_r'] = calculate_angle(hip_r,sholder_r, elbow_r)
            angles['sholder_l'] = calculate_angle(hip_l, sholder_l, elbow_l) 

            angles['hip_r'] = calculate_angle(sholder_r, hip_r, knee_r)
            angles['hip_l'] = calculate_angle(sholder_l, hip_l, knee_l)

            angles['elbow_r'] = calculate_angle(wrist_r, elbow_r, sholder_r)
            angles['elbow_l'] = calculate_angle(wrist_l, elbow_l, sholder_l)
        

            h, w, _ = frame.shape

            pos_bottom_r = tuple(np.multiply(knee_r, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['knee_r'])), pos_bottom_r, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            pos_bottom_l = tuple(np.multiply(knee_l, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['knee_l'])), pos_bottom_l, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)

            pos_mid_r = tuple(np.multiply(hip_r, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['hip_r'])), pos_mid_r, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            pos_mid_l = tuple(np.multiply(hip_l, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['hip_l'])), pos_mid_l, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            
            pos_top_r = tuple(np.multiply(sholder_r, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['sholder_r'])), pos_top_r, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            pos_top_l = tuple(np.multiply(sholder_l, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['sholder_l'])), pos_top_l, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            
            pos_elbow_r = tuple(np.multiply(elbow_r, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['elbow_r'])), pos_elbow_r, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            pos_elbow_l = tuple(np.multiply(elbow_l, [w, h]).astype(int))
            cv.putText(frame, str(int(angles['elbow_l'])), pos_elbow_l, cv.FONT_HERSHEY_SCRIPT_COMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            
        return landmarks, angles

    def draw_landmarks(self, frame):
        
        landmarks = self.current_landmarks
        
        
        if landmarks:
            
            
            draw_skeleton(frame, landmarks, self.CONNECTIONS)
            draw_points(frame, landmarks)
                
        return frame  
      