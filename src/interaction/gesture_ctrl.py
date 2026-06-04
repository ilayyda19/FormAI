import time
from collections import deque


class GestureController:

    def __init__(self, confirmation_threshold=10, cooldown=2.0, history_size=10):
        self.confirmation_threshold = confirmation_threshold
        self.cooldown = cooldown

        self.consecutive_gestures = 0
        self.previous_command = None
        self.last_command_time = 0.0

        self.is_paused = False
        self.active_action = "None"

        self.gestures_enabled = True
        self.selector_active = False
        self.selector_index = 0

        self.history_size = history_size
        self.point_x_history = deque(maxlen=history_size)
        self.point_stable_since = None
        self.point_seen_since = None

        self.selector_open_hold = 0.6
        self.selector_select_hold = 1.8
        self.selector_reopen_delay = 1.0
        self.selector_locked_until = 0.0

        self.swipe_cooldown = 0.95
        self.last_action_time = 0.0
        self.swipe_threshold = 0.18

    def update(self, current_command, hand_landmarks=None, exercise_count=0):
        now = time.time()

        if not current_command or current_command == "unknown_gesture":
            self.clear_consecutive()
            return None

        if not self.gestures_enabled and current_command != "PEACE":
            self.active_action = "GESTURES_OFF"
            self.clear_consecutive()
            return None

        if current_command == "POINT" and hand_landmarks:
            return self._handle_point(hand_landmarks, exercise_count, now)

        self._clear_point_tracking()


        if self.selector_active:
            self.active_action = "SELECTOR_ACTIVE"
            self.consecutive_gestures = 0
            self.previous_command = None
            return None

        if current_command == self.previous_command:
            self.consecutive_gestures += 1
        else:
            self.consecutive_gestures = 1
            self.previous_command = current_command

        if (
            self.consecutive_gestures >= self.confirmation_threshold
            and now - self.last_command_time > self.cooldown
        ):
            self.last_command_time = now
            self.consecutive_gestures = 0
            return self._execute_static(current_command)

        return None

    def _handle_point(self, hand_landmarks, exercise_count, now):
        if now < self.selector_locked_until:
            return None

        point_x = hand_landmarks[8].x

        if self.point_seen_since is None:
            self.point_seen_since = now

        if not self.selector_active:
            if now - self.point_seen_since >= self.selector_open_hold:
                self.selector_active = True
                self.active_action = "OPEN_SELECTOR"
                self.point_x_history.clear()
                self.point_stable_since = now
                return "OPEN_SELECTOR"

            return None

        swipe_action = self._check_selector_swipe(point_x, exercise_count)
        if swipe_action:
            self.active_action = swipe_action
            self.point_stable_since = None
            return swipe_action

        if self.point_stable_since is None:
            self.point_stable_since = now

        if now - self.point_stable_since >= self.selector_select_hold:
            self.selector_active = False
            self.active_action = "SELECT_EXERCISE"
            self.selector_locked_until = now + self.selector_reopen_delay
            self._clear_point_tracking()
            return "SELECT_EXERCISE"

        return None

    def _check_selector_swipe(self, current_x, exercise_count):
        now = time.time()
        self.point_x_history.append(current_x)

        if len(self.point_x_history) < self.history_size:
            return None

        diff = self.point_x_history[-1] - self.point_x_history[0]

        if abs(diff) <= self.swipe_threshold:
            return None

        if now - self.last_action_time < self.swipe_cooldown:
            return None

        self.last_action_time = now
        self.point_x_history.clear()

        if exercise_count <= 0:
            return None

        if diff > 0:
            self.selector_index = (self.selector_index - 1) % exercise_count
            return "PREV_EXERCISE_PREVIEW"

        self.selector_index = (self.selector_index + 1) % exercise_count
        return "NEXT_EXERCISE_PREVIEW"

    def _execute_static(self, command):
        if command == "FIST":
            self.is_paused = not self.is_paused
            self.active_action = "PAUSED" if self.is_paused else "RUNNING"
            return "SYSTEM_STATUS_CHANGE"

        if command == "PEACE":
            self.gestures_enabled = not self.gestures_enabled
            self.active_action = "GESTURES_ON" if self.gestures_enabled else "GESTURES_OFF"

            if not self.gestures_enabled:
                self.selector_active = False
                self._clear_point_tracking()

            return "TOGGLE_GESTURES"

        if command == "OPEN HAND":
            self.active_action = "TOGGLE_SKELETON"
            return "TOGGLE_SKELETON"
        
        if command == "THUMBS":
            self.active_action = "START_WORKOUT"
            return "START_WORKOUT"

        return None

    def _clear_point_tracking(self):
        self.point_seen_since = None
        self.point_stable_since = None
        self.point_x_history.clear()

    def clear_consecutive(self):
        self.consecutive_gestures = 0
        self.previous_command = None
        self._clear_point_tracking()