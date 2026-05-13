import cv2 as cv
import time

from src.core.pose_estimator      import PoseEstimator
from src.core.hand_landmarker     import HandLandmarker
from src.core.hand_gestures       import GestureAnalyz
from src.interaction.gesture_ctrl import GestureController
from src.interaction.hud          import HUD

print("Loading...")


exercises = ["SQUAT", "PUSH-UP", "LUNGE", "PLANK"]
current_ex_idx = 0

estimator          = PoseEstimator()
hand_sensor        = HandLandmarker()
gesture_analyzer   = GestureAnalyz()
gesture_controller = GestureController()
hud                = HUD()

show_skeleton = True

# Default HUD data
data = {
    "gesture":  "None",
    "action":   "None",
    "exercise": exercises[current_ex_idx],
    "system":   "ACTIVE",
    "color":    (0, 255, 0),
    "skeleton": True,
}

print("The camera is turning on...")
cap = cv.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame. Exiting...")
        break

    frame = cv.flip(frame, 1)

   
    estimator.process_frame(frame)
    if show_skeleton:
        frame = estimator.draw_landmarks(frame)

    
    hand_landmarks, handedness = hand_sensor.detect(frame)

    if hand_landmarks and handedness:
        current_command = gesture_analyzer.get_gesture(hand_landmarks)
        action = gesture_controller.update(current_command, hand_landmarks)

        if action == "NEXT_EXERCISE":
            current_ex_idx = (current_ex_idx + 1) % len(exercises)
        elif action == "PREV_EXERCISE":
            current_ex_idx = (current_ex_idx - 1) % len(exercises)
        elif action == "TOGGLE_SKELETON":
            show_skeleton = not show_skeleton

        data.update({
            "gesture":  current_command,
            "action":   gesture_controller.active_action,
            "exercise": exercises[current_ex_idx],
            "system":   "PAUSED" if gesture_controller.is_paused else "ACTIVE",
            "color":    (0, 0, 255) if gesture_controller.is_paused else (0, 255, 0),
            "skeleton": show_skeleton,
        })
    else:
       
        gesture_controller.clear_consecutive()
        data.update({
            "gesture":  "None",
            "exercise": exercises[current_ex_idx],
            "system":   "PAUSED" if gesture_controller.is_paused else "ACTIVE",
            "color":    (0, 0, 255) if gesture_controller.is_paused else (0, 255, 0),
            "skeleton": show_skeleton,
        })

    frame = hud.draw(frame, data)

    cv.imshow("Sports Analysis - Live", frame)
    if cv.waitKey(1) == ord("q"):
        break

hand_sensor.close()
cap.release()
cv.destroyAllWindows()