import cv2 as cv
import numpy as np


def draw_skeleton(frame, landmarks, connections, color=(255, 160, 0), thickness=3):
    for start_idx, end_idx in connections:
        start = landmarks[start_idx]
        end = landmarks[end_idx]

        start_point = (int(start.x * frame.shape[1]), int(start.y * frame.shape[0]))
        end_point = (int(end.x * frame.shape[1]), int(end.y * frame.shape[0]))

        cv.line(frame, start_point, end_point, color, thickness)

def draw_points(frame, landmarks, color=(255, 255, 255), radius=5):
    for landmark in landmarks:
        x = int(landmark.x * frame.shape[1])
        y = int(landmark.y * frame.shape[0])
        cv.circle(frame, (x, y), radius, color, -1)

def draw_angle_text(frame, text, position, color=(255, 255, 255)):
    cv.putText(frame, str(int(text)), position, 
               cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 3, cv.LINE_AA)

def draw_info_text(frame, text, position, color=(0, 255, 255), scale=1):
    cv.putText(frame, text, position,
               cv.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv.LINE_AA)