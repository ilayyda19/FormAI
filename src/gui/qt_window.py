import sys
import time
import cv2 as cv


from pathlib import Path
from datetime import datetime

from src.core.hand_gestures import GestureAnalyz
from src.core.hand_landmarker import HandLandmarker
from src.core.pose_estimator import PoseEstimator
from src.exercises.movements import EXERCISE_REGISTRY, get_exercise
from src.interaction.feedback_engine import FeedbackEngine
from src.interaction.gesture_ctrl import GestureController
from src.services.workout_history_manager import WorkoutHistoryManager
from src.gui.workout_history_dialog import WorkoutHistoryDialog
from src.gui.settings_dialog import SettingsDialog

from src.interaction.voice_command import VoiceCommandListener
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from src.gui.progress_ring import ProgressRing
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)


DEFAULT_TARGETS = {
    "squat": {"type": "reps", "value": 12},
    "bicep_curl": {"type": "reps", "value": 12},
    "shoulder_press": {"type": "reps", "value": 10},
    "lateral_raise": {"type": "reps", "value": 12},
    "lunge": {"type": "reps", "value": 10},
    "tricep_extension": {"type": "reps", "value": 12},
    "push_up": {"type": "reps", "value": 10},
    "deadlift": {"type": "reps", "value": 8},
    "plank": {"type": "seconds", "value": 30},
    "bent_over_row": {"type": "reps", "value": 12},
    "calf_raise": {"type": "reps", "value": 15},
    "front_raise": {"type": "reps", "value": 12},
}

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "datas"
HISTORY_FILE = DATA_DIR / "workout_history.json"


class QtAppWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FormAI")
        self.resize(1180, 720)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel#Title {
                color: #22c55e;
                font-size: 30px;
                font-weight: 700;
            }

            QLabel#CameraView {
                background-color: #111111;
                border: 1px solid #3e3e42;
                border-radius: 10px;
                color: #858585;
                font-size: 28px;
            }
                           
            QLabel#CameraSubtitleLabel {
                background-color: rgba(30, 30, 30, 190);
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 14px;
                padding: 8px 14px;
                font-size: 28px;
                font-weight: 600;
            }

            QFrame#CameraExerciseCard {
                background-color: rgba(30, 30, 30, 185);
                border: 1px solid #3e3e42;
                border-radius: 12px;
            }

            QLabel#CameraExerciseImage {
                background-color: transparent;
                border: none;
            }

            QLabel#CameraExerciseName {
                background-color: transparent;
                color: #d4d4d4;
                font-size: 13px;
                font-weight: 800;
            }

            QLabel#CameraExerciseState {
                background-color: transparent;
                color: #22c55e;
                font-size: 11px;
                font-weight: 700;
            }
                           
            QLabel#CameraStatusPill {
                background-color: rgba(30, 30, 30, 185);
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 9px;
                padding: 7px 12px;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#CountdownOverlay {
                background-color: rgba(30, 30, 30, 150);
                color: #22c55e;
                font-size: 96px;
                font-weight: 800;
                border-radius: 10px;
            }

            QLabel#MessageOverlay {
                background-color: rgba(30, 30, 30, 180);
                color: #22c55e;
                font-size: 42px;
                font-weight: 800;
                border-radius: 10px;
            }

            QFrame#SidePanel {
                background-color: #252526;
                border-left: 1px solid #3e3e42;
            }

            QFrame#Card {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 10px;
            }

            QLabel#FeedbackLabel {
                background-color: transparent;
                color: #d4d4d4;
                font-weight: 600;
            }

            QPushButton#FullscreenButton {
                background-color: rgba(30, 30, 30, 180);
                border: 1px solid #3e3e42;
                border-radius: 23px;
                color: #d4d4d4;
                font-size: 22px;
                font-weight: 700;
                padding: 0px;
            }

            QPushButton#FullscreenButton:hover {
                background-color: rgba(20, 83, 45, 210);
                border: 1px solid #22c55e;
            }

            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 12px 16px;
                color: #d4d4d4;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #14532d;
            }

            QPushButton:pressed {
                background-color: #166534;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.camera_label = QLabel("CAMERA")
        self.camera_label.setObjectName("CameraView")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.camera_label.setScaledContents(False)

        self.countdown_label = QLabel("")
        self.countdown_label.setObjectName("CountdownOverlay")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.hide()

        self.message_label = QLabel("")
        self.message_label.setObjectName("MessageOverlay")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()

        self.camera_container = QFrame()
        self.camera_stack = QStackedLayout(self.camera_container)
        self.camera_stack.setStackingMode(QStackedLayout.StackAll)
        self.camera_stack.setContentsMargins(0, 0, 0, 0)
        self.camera_stack.addWidget(self.camera_label)
        self.camera_stack.addWidget(self.countdown_label)
        self.camera_stack.addWidget(self.message_label)

        self.camera_exercise_card = QFrame(self.camera_container)
        self.camera_exercise_card.setObjectName("CameraExerciseCard")
        self.camera_exercise_card.setFixedSize(150, 170)
        self.camera_exercise_card.hide()

        camera_card_layout = QVBoxLayout(self.camera_exercise_card)
        camera_card_layout.setContentsMargins(10, 10, 10, 10)
        camera_card_layout.setSpacing(6)

        self.camera_exercise_image_label = QLabel()
        self.camera_exercise_image_label.setObjectName("CameraExerciseImage")
        self.camera_exercise_image_label.setFixedSize(130, 95)
        self.camera_exercise_image_label.setAlignment(Qt.AlignCenter)
        self.camera_exercise_image_label.setScaledContents(False)

        self.camera_exercise_name_label = QLabel("SQUAT")
        self.camera_exercise_name_label.setObjectName("CameraExerciseName")
        self.camera_exercise_name_label.setAlignment(Qt.AlignCenter)
        self.camera_exercise_name_label.setWordWrap(True)

        self.camera_exercise_state_label = QLabel("IDLE")
        self.camera_exercise_state_label.setObjectName("CameraExerciseState")
        self.camera_exercise_state_label.setAlignment(Qt.AlignCenter)

        camera_card_layout.addWidget(self.camera_exercise_image_label)
        camera_card_layout.addWidget(self.camera_exercise_name_label)
        camera_card_layout.addWidget(self.camera_exercise_state_label)

        self.fullscreen_button = QPushButton("⛶", self.camera_container)
        self.fullscreen_button.setObjectName("FullscreenButton")
        self.fullscreen_button.setFixedSize(46, 46)
        self.fullscreen_button.setToolTip("Fullscreen")
        self.fullscreen_button.raise_()

        self.camera_gesture_label = QLabel("Gesture  None", self.camera_container)
        self.camera_gesture_label.setObjectName("CameraStatusPill")
        self.camera_gesture_label.hide()

        self.camera_phase_label = QLabel("Phase  REST", self.camera_container)
        self.camera_phase_label.setObjectName("CameraStatusPill")
        self.camera_phase_label.hide()

        self.camera_subtitle_label = QLabel("", self.camera_container)
        self.camera_subtitle_label.setObjectName("CameraSubtitleLabel")
        self.camera_subtitle_label.setAlignment(Qt.AlignCenter)
        self.camera_subtitle_label.setWordWrap(True)
        self.camera_subtitle_label.hide()

        self.last_subtitle_text = ""
        self.last_subtitle_time = 0.0
        self.feedback_priority_until = 0.0

        self.subtitle_hide_timer = QTimer(self)
        self.subtitle_hide_timer.setSingleShot(True)
        self.subtitle_hide_timer.timeout.connect(self.clear_camera_subtitle)

        self.is_fullscreen_mode = False

        self.side_panel = QFrame()
        self.side_panel.setObjectName("SidePanel")
        self.side_panel.setFixedWidth(340)

        side_layout = QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(24, 24, 24, 24)
        side_layout.setSpacing(18)

        title = QLabel("FormAI")
        title.setObjectName("Title")

        data_card = QFrame()
        data_card.setObjectName("Card")

        self.data_layout = QVBoxLayout(data_card)
        self.data_layout.setContentsMargins(18, 18, 18, 18)
        self.data_layout.setSpacing(10)

        self.progress_ring = ProgressRing()
        self.progress_ring_in_camera = False

        self.exercise_label = QLabel("Exercise: SQUAT")
        self.reps_label = QLabel("Reps: 0")
        self.target_label = QLabel("Target: 12 reps")
        self.status_label = QLabel("System: IDLE")
        self.gesture_status_label = QLabel("Gestures: ON")
        self.feedback_label = QLabel("Feedback: Ready")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)

        self.data_layout.addWidget(self.progress_ring, alignment=Qt.AlignCenter)
        self.data_layout.addWidget(self.exercise_label)
        self.data_layout.addWidget(self.reps_label)
        self.data_layout.addWidget(self.target_label)
        self.data_layout.addWidget(self.status_label)
        self.data_layout.addWidget(self.gesture_status_label)
        self.data_layout.addWidget(self.feedback_label)

        self.start_button = QPushButton("START")
        self.choose_button = QPushButton("CHOOSE EXERCISE")
        self.history_button = QPushButton("WORKOUT HISTORY")
        self.settings_button = QPushButton("⚙  SETTINGS")

        side_layout.addWidget(title)
        side_layout.addWidget(data_card)
        side_layout.addSpacing(16)
        side_layout.addWidget(self.start_button)
        side_layout.addWidget(self.choose_button)
        side_layout.addWidget(self.history_button)
        side_layout.addStretch()
        side_layout.addWidget(self.settings_button)

        root.addWidget(self.camera_container, stretch=1)
        root.addWidget(self.side_panel)

        self.pose_estimator = PoseEstimator()
        self.show_skeleton = False

        self.hand_sensor = HandLandmarker()
        self.gesture_analyzer = GestureAnalyz()
        self.gesture_controller = GestureController()

        self.app_settings = {
            "voice_feedback":    True,
            "subtitle_feedback": True,
            "hand_gestures":     True,
            "voice_commands": True,
        }


        self.feedback = FeedbackEngine(lang="en")
        self.feedback.on_message = self.on_feedback_message
        self.feedback.on_rep = self.on_feedback_rep
        self.feedback.start()

        self.pending_voice_command = None
        self.voice_listener = VoiceCommandListener(lang="en-US")
        self.voice_listener.on_command = self.queue_voice_command
        self.voice_listener.on_status = self.on_voice_status

        if self.voice_listener.available and self.app_settings.get("voice_commands", True):
            self.voice_listener.start()

        self.exercise_keys = list(EXERCISE_REGISTRY.keys())
        self.current_ex_idx = 0
        self.current_exercise = get_exercise(self.exercise_keys[self.current_ex_idx])

        self.exercise_images = self.load_exercise_images(BASE_DIR / "assets" / "exercises")
        print("Loaded exercise images:", list(self.exercise_images.keys()))

        self.exercise_targets = {
            key: target.copy()
            for key, target in DEFAULT_TARGETS.items()
        }
        self.history_manager = WorkoutHistoryManager(HISTORY_FILE)

    
        self.workout_state = "idle"
        self.countdown_start_time = None
        self.countdown_seconds = 3
        self.workout_started_at = None
        self.workout_saved = False
        self.workout_feedback_announced = False

        self.reps = 0
        self.phase = "rest"
        self.elapsed_seconds = 0
        self.last_gesture = "None"

        self.frame_index = 0
        self.hand_detection_interval = 3

        self.target_type = "reps"
        self.target_value = 12
        self.update_current_target()
        self.update_progress_ring()

        self.cap = cv.VideoCapture(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_frame)
        self.timer.start(30)

        self.start_button.clicked.connect(self.on_start_stop_clicked)
        self.choose_button.clicked.connect(self.open_exercise_dialog)
        self.history_button.clicked.connect(self.open_history_dialog)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen_mode)

        QTimer.singleShot(0, self.position_fullscreen_button)

   

    def open_settings_dialog(self):
        dialog = SettingsDialog(
            settings=self.app_settings,
            feedback=self.feedback,
            on_feedback_message=self.on_feedback_message,
            camera_subtitle_label=self.camera_subtitle_label,
            gesture_controller=self.gesture_controller,
            gesture_status_label=self.gesture_status_label,
            voice_listener=self.voice_listener,
            parent=self,
        )

        dialog.exec()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_fullscreen_button()
        self.position_camera_overlays()
        self.position_camera_subtitle()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.is_fullscreen_mode:
            self.toggle_fullscreen_mode()
            return

        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen_mode()
            return

        super().keyPressEvent(event)

    def position_fullscreen_button(self):
        if not hasattr(self, "fullscreen_button"):
            return

        margin = 18
        x = self.camera_container.width() - self.fullscreen_button.width() - margin
        y = self.camera_container.height() - self.fullscreen_button.height() - margin

        self.fullscreen_button.move(max(0, x), max(0, y))
        self.fullscreen_button.raise_()
        self.fullscreen_button.show()

    def position_camera_overlays(self):
        if not hasattr(self, "camera_exercise_card"):
            return

        status_labels = [
            self.camera_gesture_label,
            self.camera_phase_label,
        ]

        if not self.is_fullscreen_mode:
            self.camera_exercise_card.hide()
            for label in status_labels:
                label.hide()
            return

        margin = 18

        status_y = margin
        for label in status_labels:
            label.adjustSize()
            label.move(margin, status_y)
            label.show()
            label.raise_()
            status_y += label.height() + 8

        self.camera_exercise_card.show()
        self.camera_exercise_card.move(margin, status_y + 8)
        self.camera_exercise_card.raise_()

        for label in status_labels:
            label.raise_()

        if self.progress_ring_in_camera:
            x = self.camera_container.width() - self.progress_ring.width() - margin
            y = margin
            self.progress_ring.move(max(0, x), y)
            self.progress_ring.raise_()
            self.progress_ring.show()

    def position_camera_subtitle(self):
        if not hasattr(self, "camera_subtitle_label"):
            return

        subtitle_on = self.app_settings.get("subtitle_feedback", True)
        has_text = bool(self.camera_subtitle_label.text().strip())

        if not subtitle_on or not has_text:
            self.camera_subtitle_label.hide()
            return

        margin = 18
        max_width = min(680, max(260, self.camera_container.width() - 160))

        self.camera_subtitle_label.setFixedWidth(max_width)
        self.camera_subtitle_label.adjustSize()

        x = (self.camera_container.width() - self.camera_subtitle_label.width()) // 2
        y = self.camera_container.height() - self.camera_subtitle_label.height() - 84

        self.camera_subtitle_label.move(max(margin, x), max(margin, y))
        self.camera_subtitle_label.show()
        self.camera_subtitle_label.raise_()
        self.fullscreen_button.raise_()

    def clear_camera_subtitle(self):
        if not hasattr(self, "camera_subtitle_label"):
            return

        if hasattr(self, "subtitle_hide_timer") and self.subtitle_hide_timer.isActive():
            self.subtitle_hide_timer.stop()

        self.camera_subtitle_label.clear()
        self.camera_subtitle_label.hide()
        self.last_subtitle_text = ""
        self.last_subtitle_time = 0.0

    def update_camera_overlay_text(self):
        key = self.exercise_keys[self.current_ex_idx]
        exercise_name = key.replace("_", " ").upper()

        self.camera_exercise_name_label.setText(exercise_name)
        self.camera_exercise_state_label.setText(self.workout_state.upper())

        gesture_state = "ON" if self.gesture_controller.gestures_enabled else "OFF"
        self.camera_gesture_label.setText(f"Gestures  {gesture_state}")
        self.camera_phase_label.setText(f"Phase  {self.phase.upper()}")

        image = self.exercise_images.get(key)
        if image is None:
            self.camera_exercise_image_label.clear()
            return

        rgb_image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        q_image = QImage(
            rgb_image.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(q_image).scaled(
            self.camera_exercise_image_label.width(),
            self.camera_exercise_image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.camera_exercise_image_label.setPixmap(pixmap)

    def move_progress_ring_to_camera(self):
        if self.progress_ring_in_camera:
            return

        self.data_layout.removeWidget(self.progress_ring)
        self.progress_ring.setParent(self.camera_container)
        self.progress_ring_in_camera = True
        self.progress_ring.show()
        self.progress_ring.raise_()
        self.position_camera_overlays()

    def move_progress_ring_to_panel(self):
        if not self.progress_ring_in_camera:
            return

        self.progress_ring.hide()
        self.progress_ring.setParent(None)
        self.data_layout.insertWidget(0, self.progress_ring, 0, Qt.AlignCenter)
        self.progress_ring_in_camera = False
        self.progress_ring.show()


    def get_current_exercise_key(self):
        return self.exercise_keys[self.current_ex_idx]

    def get_current_target(self):
        key = self.get_current_exercise_key()
        return self.exercise_targets.get(key, {"type": "reps", "value": 10})

    def update_current_target(self):
        target = self.get_current_target()
        self.target_type = target["type"]
        self.target_value = int(target["value"])

        unit = "sec" if self.target_type == "seconds" else "reps"
        self.target_label.setText(f"Target: {self.target_value} {unit}")

    def update_progress_ring(self):
        target_value = max(1, int(self.target_value))

        if self.target_type == "seconds":
            current_value = self.elapsed_seconds
            target_text = f"/{self.target_value}s"
        else:
            current_value = self.reps
            target_text = f"/{self.target_value}"

        progress = min(current_value / target_value, 1.0)
        self.progress_ring.set_progress(progress, current_value, target_text)


    def on_feedback_message(self, text, color):
        self.feedback_label.setText(f"Feedback: {text}")

        if not self.app_settings.get("subtitle_feedback", True):
            self.clear_camera_subtitle()
            return
        
        now = time.time()

        is_warning = color == "#F39C12"
        is_error = color == "#E74C3C"
        is_ok = color == "#2ECC71"

        if is_warning or is_error:
            self.feedback_priority_until = now + 2.5

        if is_ok and now < self.feedback_priority_until:
            return
        
        same_text = text == self.last_subtitle_text

        if same_text and now - self.last_subtitle_time < 0.8 and self.camera_subtitle_label.isVisible():
            self.subtitle_hide_timer.start(2200)
            return

        self.subtitle_hide_timer.stop()
        self.camera_subtitle_label.setText(text)
        self.position_camera_subtitle()

        self.last_subtitle_text = text
        self.last_subtitle_time = now

    
        self.subtitle_hide_timer.start(2200)

    
    def on_feedback_rep(self, n):
        self.reps = n
        self.reps_label.setText(f"Reps: {self.reps}")

    def queue_voice_command(self, command):
        self.pending_voice_command = command


    def on_voice_status(self, text):
        try:
            self.feedback_label.setText(text)
        except RuntimeError:
            pass


    def process_pending_voice_command(self):
        command = self.pending_voice_command
        self.pending_voice_command = None

        if not command:
            return

        self.handle_voice_command(command)


    def handle_voice_command(self, command):
        if command == "START":
            self.start_countdown()

        elif command == "PAUSE":
            if self.workout_state == "running":
                self.workout_state = "paused"
                self.status_label.setText("System: PAUSED")

        elif command == "RESUME":
            if self.workout_state == "paused":
                self.workout_state = "running"
                self.status_label.setText("System: RUNNING")

        elif command in ("STOP", "RESET"):
             self.cancel_workout()

        elif command.startswith("EXERCISE:"):
            key = command.split(":", 1)[1]
            if key in self.exercise_keys:
                index = self.exercise_keys.index(key)
                self.select_exercise(index)

    
    def on_start_stop_clicked(self):
        if self.workout_state in ("running", "paused", "countdown"):
            self.cancel_workout()
        else:
            self.start_countdown()
    def cancel_workout(self):
        self.workout_state = "idle"
        self.countdown_start_time = None
        self.workout_started_at = None
        self.workout_saved = False
        self.workout_feedback_announced = False
        self.gesture_controller.is_paused = False

        self.reps = 0
        self.phase = "rest"
        self.elapsed_seconds = 0

        self.message_label.hide()
        self.countdown_label.hide()

        self.clear_camera_subtitle()

        self.reps_label.setText("Reps: 0")
        self.status_label.setText("System: IDLE")
        self.feedback_label.setText("Feedback: Ready")

        self.update_current_target()
        self.update_progress_ring()
        self.update_start_button_text()

    def update_start_button_text(self):
        if self.workout_state in ("running", "paused", "countdown"):
            self.start_button.setText("CANCEL")
        else:
            self.start_button.setText("START")



    def start_countdown(self):
        if self.workout_state in ("countdown", "running", "paused"):
        
            return

        self.current_exercise = get_exercise(self.exercise_keys[self.current_ex_idx])
        self.reps = 0
        self.phase = "rest"
        self.elapsed_seconds = 0
        self.workout_started_at = None
        self.workout_saved = False
        self.workout_feedback_announced = False
        self.gesture_controller.is_paused = False

        self.update_current_target()
        self.update_progress_ring()
        self.feedback.set_target(self.target_value)

        self.reps_label.setText("Reps: 0")
        self.status_label.setText("System: COUNTDOWN")
        self.feedback_label.setText("Feedback: Ready")
        self.clear_camera_subtitle()
        self.message_label.hide()

        self.workout_state = "countdown"
        self.countdown_start_time = time.time()
        self.update_start_button_text()

    def update_countdown(self):
        if self.workout_state != "countdown" or self.countdown_start_time is None:
            self.countdown_label.hide()
            return

        elapsed = time.time() - self.countdown_start_time
        remaining = self.countdown_seconds - int(elapsed)

        if remaining > 0:
            self.countdown_label.setText(str(remaining))
            self.countdown_label.show()
            self.countdown_label.raise_()
            return

        if elapsed < self.countdown_seconds + 0.7:
            self.countdown_label.setText("GO")
            self.countdown_label.show()
            self.countdown_label.raise_()
            return

        self.countdown_label.hide()
        self.workout_state = "running"
        self.countdown_start_time = None
        self.status_label.setText("System: RUNNING")
        self.update_start_button_text()

    def finish_workout(self):
        if self.workout_state == "finished":
            return

        self.workout_state = "finished"
        self.status_label.setText("System: FINISHED")
        self.update_start_button_text()

        if not self.workout_saved:
            self.save_workout_record()
            self.workout_saved = True

        if not self.workout_feedback_announced:
            self.feedback.stop(self.reps)
            self.workout_feedback_announced = True

        if self.target_type == "seconds":
            text = f"TARGET COMPLETED\n{self.elapsed_seconds} / {self.target_value} SEC"
        else:
            text = f"TARGET COMPLETED\n{self.reps} / {self.target_value} REPS"

        self.message_label.setText(text)
        self.message_label.show()
        self.message_label.raise_()
        self.position_camera_overlays()
        self.position_fullscreen_button()
        QTimer.singleShot(5000, self.message_label.hide)


    def load_workout_history(self):
        return self.history_manager.load()


    def save_workout_record(self):

        now = datetime.now()
        exercise_key = self.get_current_exercise_key()
        target = self.get_current_target()

        record = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "exercise_key": exercise_key,
            "exercise": exercise_key.replace("_", " ").upper(),
            "target_type": target["type"],
            "target_value": target["value"],
            "reps": self.reps,
            "elapsed_seconds": self.elapsed_seconds,
            "status": "completed",
        }

        self.history_manager.append(record)

    def open_exercise_dialog(self):
        if self.workout_state in ("countdown", "running"):
            return

        targets_snapshot = {
            key: target.copy()
            for key, target in self.exercise_targets.items()
        }

        dialog = QDialog(self)
        dialog.setWindowTitle("Choose Exercise")
        dialog.resize(430, 520)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }

            QLabel {
                color: #d4d4d4;
            }

            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }

            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
            }

            QListWidget::item:selected {
                background-color: #14532d;
                color: #ffffff;
            }

            QSpinBox, QComboBox {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 8px 14px;
                color: #d4d4d4;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #14532d;
            }
        """)

        layout = QVBoxLayout(dialog)

        exercise_list = QListWidget()
        for key in self.exercise_keys:
            exercise_list.addItem(key.replace("_", " ").upper())

        exercise_list.setCurrentRow(self.current_ex_idx)

        form = QFormLayout()

        target_type_box = QComboBox()
        target_type_box.addItems(["reps", "seconds"])

        target_value_box = QSpinBox()
        target_value_box.setRange(1, 300)

        def load_target_for_row(row):
            if row < 0 or row >= len(self.exercise_keys):
                return

            key = self.exercise_keys[row]
            target = self.exercise_targets.get(key, {"type": "reps", "value": 10})

            target_type_box.setCurrentText(target["type"])
            target_value_box.setValue(int(target["value"]))

        def save_target_for_row(row):
            if row < 0 or row >= len(self.exercise_keys):
                return

            key = self.exercise_keys[row]
            self.exercise_targets[key] = {
                "type": target_type_box.currentText(),
                "value": target_value_box.value(),
            }

        def on_row_changed(new_row):
            old_row = getattr(dialog, "last_row", self.current_ex_idx)
            save_target_for_row(old_row)
            load_target_for_row(new_row)
            dialog.last_row = new_row

        dialog.last_row = self.current_ex_idx
        exercise_list.currentRowChanged.connect(on_row_changed)

        load_target_for_row(self.current_ex_idx)

        form.addRow("Target type", target_type_box)
        form.addRow("Target value", target_value_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )

        layout.addWidget(exercise_list)
        layout.addLayout(form)
        layout.addWidget(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_row = exercise_list.currentRow()
            save_target_for_row(selected_row)
            keep_state = self.workout_state == "paused"
            self.select_exercise(selected_row, keep_state=keep_state)
        else:
            self.exercise_targets = targets_snapshot
            self.update_current_target()
            self.update_progress_ring()

    def select_exercise(self, index, keep_state=False):
        if index < 0 or index >= len(self.exercise_keys):
            return

        if self.workout_state in ("countdown", "running"):
            return

        previous_state = self.workout_state

        self.current_ex_idx = index
        self.current_exercise = get_exercise(self.exercise_keys[self.current_ex_idx])

        self.reps = 0
        self.phase = "rest"
        self.elapsed_seconds = 0
        self.workout_started_at = None
        self.workout_saved = False

        if keep_state:
            self.workout_state = previous_state
        else:
            self.workout_state = "idle"

        self.message_label.hide()
        self.countdown_label.hide()

        exercise_name = self.exercise_keys[self.current_ex_idx].replace("_", " ").upper()

        self.exercise_label.setText(f"Exercise: {exercise_name}")
        self.reps_label.setText("Reps: 0")

        if self.workout_state == "paused":
            self.status_label.setText("System: PAUSED")
        else:
            self.status_label.setText(f"System: {self.workout_state.upper()}")

        self.feedback_label.setText("Feedback: Ready")
        self.clear_camera_subtitle()
        self.update_current_target()
        self.update_progress_ring()
        self.update_start_button_text()


    def open_history_dialog(self):
        history = self.load_workout_history()
        dialog = WorkoutHistoryDialog(history, self)
        dialog.exec()


    def load_exercise_images(self, folder):
        images = {}

        for key in self.exercise_keys:
            path = str(folder / f"{key}.png")
            img = cv.imread(path, cv.IMREAD_COLOR)

            if img is not None:
                images[key] = self.crop_white_border(img)
            else:
                print("Image not found:", path)

        return images

    def crop_white_border(self, image):
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        _, mask = cv.threshold(gray, 245, 255, cv.THRESH_BINARY_INV)

        if cv.countNonZero(mask) == 0:
            return image

        x, y, w, h = cv.boundingRect(mask)

        pad = 18
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(image.shape[1], x + w + pad)
        y2 = min(image.shape[0], y + h + pad)

        if x1 >= x2 or y1 >= y2:
            return image

        return image[y1:y2, x1:x2]


    def draw_filmstrip_selector(self, frame, exercise_options, selected_index):
        if not exercise_options:
            return

        h, w = frame.shape[:2]

        band_h = 230
        y1 = int(h * 0.30)
        y2 = y1 + band_h

        overlay = frame.copy()
        cv.rectangle(overlay, (0, y1), (w, y2), (30, 30, 30), -1)
        cv.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

        center_x = w // 2
        center_y = y1 + band_h // 2 + 4

        offsets = [-2, -1, 0, 1, 2]

        small_w, small_h = 170, 116
        big_w, big_h = 285, 165
        gap = 30

        for offset in offsets:
            idx = (selected_index + offset) % len(exercise_options)
            key = exercise_options[idx]
            name = key.replace("_", " ").upper()
            selected = offset == 0

            card_w = big_w if selected else small_w
            card_h = big_h if selected else small_h

            x_center = center_x + offset * (small_w + gap)

            if offset < 0:
                x_center -= 46
            elif offset > 0:
                x_center += 46

            x1 = int(x_center - card_w // 2)
            y_card1 = int(center_y - card_h // 2)
            x2 = x1 + card_w
            y_card2 = y_card1 + card_h

            bg = (245, 247, 250) if selected else (225, 228, 232)
            border = (34, 197, 94) if selected else (150, 155, 160)
            text = (30, 30, 30) if selected else (70, 70, 70)

            cv.rectangle(frame, (x1, y_card1), (x2, y_card2), bg, -1)
            cv.rectangle(frame, (x1, y_card1), (x2, y_card2), border, 2 if selected else 1)

            if selected:
                cv.rectangle(frame, (x1, y_card1), (x1 + 7, y_card2), border, -1)

            image = self.exercise_images.get(key)
            if image is not None:
                self.draw_card_image(frame, image, x1, y_card1, x2, y_card2, selected)

            scale = 0.50 if selected else 0.36
            thick = 2 if selected else 1
            lines = self.wrap_text(name, card_w - 20, scale, thick)
            visible_lines = lines[:2]
            text_y = y_card2 - (28 if len(visible_lines) == 2 else 16)

            for i, line in enumerate(visible_lines):
                (tw, _), _ = cv.getTextSize(line, cv.FONT_HERSHEY_SIMPLEX, scale, thick)
                tx = x1 + max(10, (card_w - tw) // 2)
                self.draw_cv_text(
                    frame,
                    line,
                    (tx, text_y + i * 18),
                    color=text,
                    scale=scale,
                    thick=thick,
                )

        hint = "POINT MOVE TO BROWSE  /  HOLD TO SELECT"
        (tw, _), _ = cv.getTextSize(hint, cv.FONT_HERSHEY_SIMPLEX, 0.52, 1)
        self.draw_cv_text(
            frame,
            hint,
            (max(24, (w - tw) // 2), y2 + 34),
            color=(212, 212, 212),
            scale=0.52,
            thick=1,
        )

    def draw_card_image(self, frame, image, x1, y1, x2, y2, selected):
        pad_x = 14 if selected else 10
        pad_y = 12 if selected else 10
        label_space = 42 if selected else 32

        area_x1 = x1 + pad_x
        area_y1 = y1 + pad_y
        area_x2 = x2 - pad_x
        area_y2 = y2 - label_space

        area_w = max(1, area_x2 - area_x1)
        area_h = max(1, area_y2 - area_y1)

        img_h, img_w = image.shape[:2]
        scale = min(area_w / img_w, area_h / img_h)

        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))

        resized = cv.resize(image, (new_w, new_h), interpolation=cv.INTER_AREA)

        px = area_x1 + (area_w - new_w) // 2
        py = area_y1 + (area_h - new_h) // 2

        frame_h, frame_w = frame.shape[:2]
        dst_x1 = max(0, px)
        dst_y1 = max(0, py)
        dst_x2 = min(frame_w, px + new_w)
        dst_y2 = min(frame_h, py + new_h)

        if dst_x1 >= dst_x2 or dst_y1 >= dst_y2:
            return

        src_x1 = dst_x1 - px
        src_y1 = dst_y1 - py
        src_x2 = src_x1 + (dst_x2 - dst_x1)
        src_y2 = src_y1 + (dst_y2 - dst_y1)

        frame[dst_y1:dst_y2, dst_x1:dst_x2] = resized[src_y1:src_y2, src_x1:src_x2]

    def wrap_text(self, text, max_width, scale, thick):
        words = str(text).split()
        if not words:
            return []

        lines = []
        current = ""

        for word in words:
            candidate = word if not current else f"{current} {word}"
            (width, _), _ = cv.getTextSize(candidate, cv.FONT_HERSHEY_SIMPLEX, scale, thick)

            if width <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def draw_cv_text(self, frame, text, pos, color=(212, 212, 212), scale=0.55, thick=1):
        cv.putText(
            frame,
            str(text),
            pos,
            cv.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thick,
            cv.LINE_AA,
        )


    def toggle_fullscreen_mode(self):
        if self.is_fullscreen_mode:
            self.is_fullscreen_mode = False
            self.move_progress_ring_to_panel()
            self.camera_exercise_card.hide()
            self.side_panel.show()
            self.showNormal()
            self.fullscreen_button.setToolTip("Fullscreen")
        else:
            self.is_fullscreen_mode = True
            self.side_panel.hide()
            self.move_progress_ring_to_camera()
            self.showFullScreen()
            self.fullscreen_button.setToolTip("Exit fullscreen")

        QTimer.singleShot(0, self.position_fullscreen_button)
        QTimer.singleShot(0, self.position_camera_overlays)
        QTimer.singleShot(0, self.position_camera_subtitle)


    def update_camera_frame(self):
        if not self.cap.isOpened():
            return
        
        self.process_pending_voice_command()

        ret, frame = self.cap.read()
        if not ret:
            return
        
        self.frame_index += 1

        frame = cv.flip(frame, 1)

        landmarks, angles = self.pose_estimator.process_frame(
            frame,
            draw_angles=self.show_skeleton,
        )

        if angles and self.workout_state == "running":
            
            if self.workout_started_at is None:
                self.workout_started_at = time.time()

            self.elapsed_seconds = int(time.time() - self.workout_started_at)

            result = self.current_exercise.analyze(angles)
            self.feedback.process(result)

            self.reps = result.rep_count
            self.phase = result.phase.value

            exercise_name = self.exercise_keys[self.current_ex_idx].replace("_", " ").upper()

            self.exercise_label.setText(f"Exercise: {exercise_name}")
            self.reps_label.setText(f"Reps: {self.reps}")
            self.update_current_target()
            self.status_label.setText(f"Phase: {self.phase.upper()}")

            if self.target_type == "reps" and self.reps >= self.target_value:
                self.finish_workout()

            elif self.target_type == "seconds" and self.elapsed_seconds >= self.target_value:
                self.finish_workout()

        if self.show_skeleton:
            drawn_frame = self.pose_estimator.draw_landmarks(frame)
            if drawn_frame is not None:
                frame = drawn_frame


        interval = 1 if self.gesture_controller.selector_active else self.hand_detection_interval

        if self.frame_index % interval == 0:
            hand_landmarks, handedness = self.hand_sensor.detect(frame)

            if hand_landmarks and handedness:
                current_command = self.gesture_analyzer.get_gesture(hand_landmarks)
                self.last_gesture = current_command

                action = self.gesture_controller.update(
                    current_command,
                    hand_landmarks,
                    exercise_count=len(self.exercise_keys),
                )

                if action == "SELECT_EXERCISE":
                    keep_state = self.workout_state == "paused"
                    self.select_exercise(
                        self.gesture_controller.selector_index,
                        keep_state=keep_state,
                    )

                elif action == "SYSTEM_STATUS_CHANGE":
                    if self.workout_state in ("running", "paused"):
                        if self.gesture_controller.is_paused:
                            self.workout_state = "paused"
                            self.status_label.setText("System: PAUSED")
                        else:
                            self.workout_state = "running"
                            self.status_label.setText("System: RUNNING")
                    else:
                        self.gesture_controller.is_paused = False

                elif action == "TOGGLE_SKELETON":
                    self.show_skeleton = not self.show_skeleton

                elif action == "TOGGLE_GESTURES":
                    new_state = self.gesture_controller.gestures_enabled
                    self.app_settings["hand_gestures"] = new_state
                    state = "ON" if new_state else "OFF"
                    self.gesture_status_label.setText(f"Gestures: {state}")

                elif action == "START_WORKOUT":
                    if self.workout_state in ("idle", "finished"):
                        self.start_countdown()

            else:
                self.last_gesture = "None"
                self.gesture_controller.clear_consecutive()

        if self.gesture_controller.selector_active:
            self.message_label.hide()
            self.draw_filmstrip_selector(
                frame,
                self.exercise_keys,
                self.gesture_controller.selector_index,
            )
        

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        h, w, ch = frame.shape
        bytes_per_line = ch * w

        image = QImage(
            frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(image).scaled(
            self.camera_label.width(),
            self.camera_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.camera_label.setPixmap(pixmap)
        self.update_countdown()
        self.update_progress_ring()

        if self.is_fullscreen_mode:
            self.update_camera_overlay_text()

    

    def closeEvent(self, event):
        if hasattr(self, "timer"):
            self.timer.stop()

        if hasattr(self, "voice_listener"):
            self.voice_listener.stop()

        if hasattr(self, "feedback"):
            if not self.workout_feedback_announced:
                self.feedback.stop(self.reps)
            self.feedback.close()

        if hasattr(self, "hand_sensor"):
            self.hand_sensor.close()

        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()

        event.accept()


def run_qt_app():
    app = QApplication(sys.argv)
    window = QtAppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_qt_app()
