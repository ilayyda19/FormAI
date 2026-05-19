import time
from collections import deque


class GestureController:

    def __init__(self, confirmation_threshold=10, cooldown=2.0, history_size=5):
        self.confirmation_threshold = confirmation_threshold
        self.cooldown = cooldown

        
        self.consecutive_gestures = 0
        self.previous_command = None
        self.last_command_time = 0

        
        self.is_paused = False
        self.active_action = "None"

        self.history_size = 5
        self.x_history = deque(maxlen=5)
        self.swipe_threshold = 0.07

    def update(self, current_command, hand_landmarks=None):
        now = time.time()

       
        if current_command == "POINT" and hand_landmarks:
            wrist_x = hand_landmarks[0].x
            swipe_action = self._check_swipe(wrist_x)

            if swipe_action and (now - self.last_command_time) > self.cooldown:
                self.last_command_time = now
                self.active_action = swipe_action
                self.consecutive_gestures = 0
                return swipe_action
        else:
            self.x_history.clear()

        
        if not current_command or current_command == "unknown_gesture":
            self.consecutive_gestures = 0
            self.previous_command = None
            return None

        if current_command == self.previous_command:
            self.consecutive_gestures += 1
        else:
            self.consecutive_gestures = 1
            self.previous_command = current_command

        if (self.consecutive_gestures >= self.confirmation_threshold
                and (now - self.last_command_time) > self.cooldown):
            self.last_command_time = now
            self.consecutive_gestures = 0
            return self._execute_static(current_command)

        return None

    def _check_swipe(self, current_x):
        self.x_history.append(current_x)

        if len(self.x_history) < self.history_size:
            return None

        diff = self.x_history[-1] - self.x_history[0]

        if abs(diff) > self.swipe_threshold:
            direction = "NEXT_EXERCISE" if diff > 0 else "PREV_EXERCISE"
            self.x_history.clear()
            return direction

        return None

    def _execute_static(self, command):
        if command == "FIST":
            self.is_paused = not self.is_paused
            self.active_action = "PAUSED" if self.is_paused else "RUNNING"
            return "SYSTEM_STATUS_CHANGE"

        elif command == "PEACE":
            self.active_action = "TOGGLE_SKELETON"
            return "TOGGLE_SKELETON"

        return None

    def clear_consecutive(self):
        """Resets only the gesture counter — does not touch is_paused."""
        self.consecutive_gestures = 0
        self.previous_command = None
        self.x_history.clear()