import cv2 as cv
import time

from src.core.pose_estimator      import PoseEstimator
from src.core.hand_landmarker     import HandLandmarker
from src.core.hand_gestures       import GestureAnalyz
from src.interaction.gesture_ctrl import GestureController
from src.interaction.hud          import HUD
from src.interaction.feedback_engine import FeedbackEngine
from src.exercises.movements      import get_exercise, EXERCISE_REGISTRY

print("Loading...")


EXERCISE_KEYS = list(EXERCISE_REGISTRY.keys())   
current_ex_idx = 0


estimator          = PoseEstimator()
hand_sensor        = HandLandmarker()
gesture_analyzer   = GestureAnalyz()
gesture_controller = GestureController()
hud                = HUD()
feedback           = FeedbackEngine(lang="tr")   


current_exercise = get_exercise(EXERCISE_KEYS[current_ex_idx])
feedback.start()

show_skeleton = True


data = {
    "gesture":  "None",
    "action":   "None",
    "exercise": EXERCISE_KEYS[current_ex_idx].replace("_", " ").upper(),
    "system":   "ACTIVE",
    "color":    (0, 255, 0),
    "skeleton": True,
    "reps":     0,
    "phase":    "rest",
    "feedback": "",
    "fb_color": "#2ECC71",
}


def _on_message(text: str, color: str):
    data["feedback"] = text
    data["fb_color"] = color

def _on_rep(n: int):
    data["reps"] = n

feedback.on_message = _on_message
feedback.on_rep     = _on_rep


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

  
    landmarks, angles = estimator.process_frame(frame)

    if show_skeleton:
        frame = estimator.draw_landmarks(frame)

   
    if not gesture_controller.is_paused and angles:
        result = current_exercise.analyze(angles)
        feedback.process(result)
        data["reps"]  = result.rep_count
        data["phase"] = result.phase.value

    
    hand_landmarks, handedness = hand_sensor.detect(frame)

    if hand_landmarks and handedness:
        current_command = gesture_analyzer.get_gesture(hand_landmarks)
        action = gesture_controller.update(current_command, hand_landmarks)

        if action == "NEXT_EXERCISE":
            current_ex_idx = (current_ex_idx + 1) % len(EXERCISE_KEYS)
            current_exercise = get_exercise(EXERCISE_KEYS[current_ex_idx])
            data["reps"] = 0
            data["phase"] = "rest"

        elif action == "PREV_EXERCISE":
            current_ex_idx = (current_ex_idx - 1) % len(EXERCISE_KEYS)
            current_exercise = get_exercise(EXERCISE_KEYS[current_ex_idx])
            data["reps"] = 0
            data["phase"] = "rest"

        elif action == "TOGGLE_SKELETON":
            show_skeleton = not show_skeleton

        data.update({
            "gesture":  current_command,
            "action":   gesture_controller.active_action,
            "exercise": EXERCISE_KEYS[current_ex_idx].replace("_", " ").upper(),
            "system":   "PAUSED" if gesture_controller.is_paused else "ACTIVE",
            "color":    (0, 0, 255) if gesture_controller.is_paused else (0, 255, 0),
            "skeleton": show_skeleton,
        })

    else:
        gesture_controller.clear_consecutive()
        data.update({
            "gesture":  "None",
            "exercise": EXERCISE_KEYS[current_ex_idx].replace("_", " ").upper(),
            "system":   "PAUSED" if gesture_controller.is_paused else "ACTIVE",
            "color":    (0, 0, 255) if gesture_controller.is_paused else (0, 255, 0),
            "skeleton": show_skeleton,
        })

    
    frame = hud.draw(frame, data)

    cv.imshow("Sports Analysis - Live", frame)
    if cv.waitKey(1) == ord("q"):
        break


feedback.stop(data["reps"])
feedback.close()
hand_sensor.close()
cap.release()
cv.destroyAllWindows()