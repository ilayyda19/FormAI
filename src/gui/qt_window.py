import sys
import time
import json
import cv2 as cv
import matplotlib

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

from pathlib import Path
from datetime import datetime, timedelta
from calendar import monthrange
from collections import Counter

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
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

from src.core.hand_gestures import GestureAnalyz
from src.core.hand_landmarker import HandLandmarker
from src.core.pose_estimator import PoseEstimator
from src.exercises.movements import EXERCISE_REGISTRY, get_exercise
from src.interaction.feedback_engine import FeedbackEngine
from src.interaction.gesture_ctrl import GestureController


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


class ProgressRing(QWidget):
    def __init__(self):
        super().__init__()
        self.progress = 0.0
        self.value_text = "0"
        self.target_text = "/0"
        self.setFixedSize(120, 120)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_progress(self, progress, value_text, target_text):
        self.progress = max(0.0, min(float(progress), 1.0))
        self.value_text = str(value_text)
        self.target_text = str(target_text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(14, 14, self.width() - 28, self.height() - 28)

        bg_pen = QPen(QColor("#3e3e42"), 8)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        progress_pen = QPen(QColor("#22c55e"), 8)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, -int(360 * self.progress * 16))

        painter.setPen(QColor("#d4d4d4"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.value_text)

        painter.setPen(QColor("#858585"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(0, self.height() / 2 + 24, self.width(), 24),
            Qt.AlignCenter,
            self.target_text,
        )


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

        self.camera_action_label = QLabel("Action  IDLE", self.camera_container)
        self.camera_action_label.setObjectName("CameraStatusPill")
        self.camera_action_label.hide()

        self.camera_subtitle_label = QLabel("", self.camera_container)
        self.camera_subtitle_label.setObjectName("CameraSubtitleLabel")
        self.camera_subtitle_label.setAlignment(Qt.AlignCenter)
        self.camera_subtitle_label.setWordWrap(True)
        self.camera_subtitle_label.hide()

        self.last_subtitle_text = ""
        self.last_subtitle_time = 0.0

        self.subtitle_hide_timer = QTimer(self)
        self.subtitle_hide_timer.setSingleShot(True)
        self.subtitle_hide_timer.timeout.connect(self.camera_subtitle_label.hide)

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

        self.feedback = FeedbackEngine(lang="en")
        self.feedback.on_message = self.on_feedback_message
        self.feedback.on_rep = self.on_feedback_rep
        self.feedback.start()

        self.exercise_keys = list(EXERCISE_REGISTRY.keys())
        self.current_ex_idx = 0
        self.current_exercise = get_exercise(self.exercise_keys[self.current_ex_idx])

        self.exercise_images = self.load_exercise_images(BASE_DIR / "assets" / "exercises")
        print("Loaded exercise images:", list(self.exercise_images.keys()))

        self.exercise_targets = {
            key: target.copy()
            for key, target in DEFAULT_TARGETS.items()
        }

        
        self.app_settings = {
            "voice_feedback":    True,
            "subtitle_feedback": True,
            "hand_gestures":     True,
        }

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

        self.target_type = "reps"
        self.target_value = 12
        self.update_current_target()
        self.update_progress_ring()

        self.cap = cv.VideoCapture(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_frame)
        self.timer.start(30)

        self.start_button.clicked.connect(self.start_countdown)
        self.choose_button.clicked.connect(self.open_exercise_dialog)
        self.history_button.clicked.connect(self.open_history_dialog)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen_mode)

        QTimer.singleShot(0, self.position_fullscreen_button)

   

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.resize(400, 340)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
                background: transparent;
                border: none;
            }
            QLabel#STitle {
                color: #22c55e;
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#SSub {
                color: #858585;
                font-size: 12px;
            }
            QFrame#SRow {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 10px 16px;
                color: #d4d4d4;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #14532d;
            }
        """)

        main = QVBoxLayout(dialog)
        main.setContentsMargins(24, 24, 24, 20)
        main.setSpacing(14)

        title = QLabel("Settings")
        title.setObjectName("STitle")
        main.addWidget(title)

        ROWS = [
            (
                "voice_feedback",
                "🔊",
                "Voice Feedback",
                "Read the exercise tips aloud.",
            ),
            (
                "subtitle_feedback",
                "💬",
                "Subtitle Feedback",
                "Display feedback text on the screen",
            ),
            (
                "hand_gestures",
                "✋",
                "Hand Gestures",
                "Control the training with hand movements.",
            ),
        ]

        toggle_buttons: dict[str, QPushButton] = {}

        def make_toggle_style(active: bool) -> str:
            if active:
                return (
                    "QPushButton {"
                    "  background-color: #22c55e;"
                    "  border: 1px solid #22c55e;"
                    "  color: #0a0a0a;"
                    "  border-radius: 13px;"
                    "  font-size: 11px;"
                    "  font-weight: 700;"
                    "  min-width: 54px; max-width: 54px;"
                    "  min-height: 26px; max-height: 26px;"
                    "  padding: 0px;"
                    "}"
                    "QPushButton:hover {"
                    "  background-color: #16a34a;"
                    "}"
                )
            else:
                return (
                    "QPushButton {"
                    "  background-color: #3e3e42;"
                    "  border: 1px solid #3e3e42;"
                    "  color: #858585;"
                    "  border-radius: 13px;"
                    "  font-size: 11px;"
                    "  font-weight: 700;"
                    "  min-width: 54px; max-width: 54px;"
                    "  min-height: 26px; max-height: 26px;"
                    "  padding: 0px;"
                    "}"
                    "QPushButton:hover {"
                    "  background-color: #4e4e52;"
                    "}"
                )

        def apply_settings_now():
           
            if hasattr(self.feedback, "voice_enabled"):
                self.feedback.voice_enabled = self.app_settings.get("voice_feedback", True)

            self.feedback.on_message = self.on_feedback_message

            if not self.app_settings.get("subtitle_feedback", True):
                self.camera_subtitle_label.hide()

            
            self.gesture_controller.gestures_enabled = self.app_settings.get(
                "hand_gestures", True
            )
            state = "ON" if self.app_settings.get("hand_gestures", True) else "OFF"
            self.gesture_status_label.setText(f"Gestures: {state}")

        def on_toggle(key: str, btn: QPushButton):
            new_val = not self.app_settings.get(key, True)
            self.app_settings[key] = new_val
            btn.setText("ON" if new_val else "OFF")
            btn.setStyleSheet(make_toggle_style(new_val))
            apply_settings_now()

        for key, icon, label_text, sub_text in ROWS:
            row = QFrame()
            row.setObjectName("SRow")
            row_h = QHBoxLayout(row)
            row_h.setContentsMargins(16, 12, 16, 12)
            row_h.setSpacing(12)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(
                "font-size: 18px; background: transparent; border: none;"
            )
            icon_lbl.setFixedWidth(28)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)

            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                "font-weight: 700; font-size: 13px;"
                "background: transparent; border: none;"
            )

            sub = QLabel(sub_text)
            sub.setObjectName("SSub")

            text_col.addWidget(lbl)
            text_col.addWidget(sub)

            active = self.app_settings.get(key, True)
            toggle = QPushButton("ON" if active else "OFF")
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setStyleSheet(make_toggle_style(active))
            toggle.clicked.connect(
                lambda checked=False, k=key, b=toggle: on_toggle(k, b)
            )
            toggle_buttons[key] = toggle

            row_h.addWidget(icon_lbl)
            row_h.addLayout(text_col, stretch=1)
            row_h.addWidget(toggle)

            main.addWidget(row)

        main.addStretch()

        done_row = QHBoxLayout()
        done_btn = QPushButton("DONE")
        done_btn.clicked.connect(dialog.accept)
        done_row.addStretch()
        done_row.addWidget(done_btn)
        main.addLayout(done_row)

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
            self.camera_action_label,
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

    def update_camera_overlay_text(self):
        key = self.exercise_keys[self.current_ex_idx]
        exercise_name = key.replace("_", " ").upper()

        self.camera_exercise_name_label.setText(exercise_name)
        self.camera_exercise_state_label.setText(self.workout_state.upper())

        self.camera_gesture_label.setText(
            f"Gesture {getattr(self, 'last_gesture', 'None')}"
        )
        self.camera_phase_label.setText(f"Phase  {self.phase.upper()}")
        self.camera_action_label.setText(f"Action  {self.workout_state.upper()}")

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
            self.camera_subtitle_label.hide()
            return
        
        now = time.time()
        same_text = text == self.last_subtitle_text

        if same_text and now - self.last_subtitle_time < 0.8:
            self.subtitle_hide_timer.start(2200)
            return

        self.camera_subtitle_label.setText(text)
        self.position_camera_subtitle()

        self.last_subtitle_text = text
        self.last_subtitle_time = now

        self.camera_subtitle_label.setText(text)
        self.position_camera_subtitle()
        self.subtitle_hide_timer.start(2200)

    
    def on_feedback_rep(self, n):
        self.reps = n
        self.reps_label.setText(f"Reps: {self.reps}")


    def start_countdown(self):
        if self.workout_state in ("countdown", "running"):
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

        self.reps_label.setText("Reps: 0")
        self.status_label.setText("System: COUNTDOWN")
        self.feedback_label.setText("Feedback: Ready")
        self.message_label.hide()

        self.workout_state = "countdown"
        self.countdown_start_time = time.time()

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

    def finish_workout(self):
        if self.workout_state == "finished":
            return

        self.workout_state = "finished"
        self.status_label.setText("System: FINISHED")

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


    def load_workout_history(self):
        if not HISTORY_FILE.exists():
            return []

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)

            if isinstance(history, list):
                return history

            return []

        except (json.JSONDecodeError, OSError):
            return []

    def save_workout_record(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

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

        history = self.load_workout_history()
        history.append(record)

        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)

        print("Saved workout to:", HISTORY_FILE)


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
        self.update_current_target()
        self.update_progress_ring()


    def create_history_stat_card(self, value, label):
        card = QFrame()
        card.setObjectName("HistoryStatCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("HistoryStatValue")
        value_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel(label)
        text_label.setObjectName("HistoryStatLabel")
        text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def create_history_card(self, record):
        card = QFrame()
        card.setObjectName("HistoryCard")

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(12)

        exercise = record.get("exercise", "UNKNOWN")
        date = record.get("date", "")
        time_text = record.get("time", "")

        reps = int(record.get("reps") or 0)
        elapsed = int(record.get("elapsed_seconds") or 0)
        target_value = int(record.get("target_value") or 0)
        target_type = record.get("target_type", "reps")

        if target_type == "seconds":
            current_value = elapsed
            unit = "sec"
        else:
            current_value = reps
            unit = "reps"

        completed = target_value > 0 and current_value >= target_value
        status_text = "Completed" if completed else "Incomplete"
        status_object = "HistoryStatusDone" if completed else "HistoryStatusMissing"

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        title_label = QLabel(exercise.title())
        title_label.setObjectName("HistoryCardTitle")

        status_label = QLabel(status_text)
        status_label.setObjectName(status_object)

        title_row.addWidget(title_label)
        title_row.addWidget(status_label)
        title_row.addStretch()

        date_label = QLabel(f"{date}  {time_text}")
        date_label.setObjectName("HistoryCardDate")

        left_layout.addLayout(title_row)
        left_layout.addWidget(date_label)

        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(2)

        result_label = QLabel(f"{current_value} / {target_value}")
        result_label.setObjectName("HistoryCardResult")
        result_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        result_hint = QLabel(f"target {unit}")
        result_hint.setObjectName("HistoryCardDate")
        result_hint.setAlignment(Qt.AlignmentFlag.AlignRight)

        result_layout.addWidget(result_label)
        result_layout.addWidget(result_hint)

        card_layout.addLayout(left_layout, stretch=1)
        card_layout.addLayout(result_layout)

        return card

    def open_history_dialog(self):
        history = self.load_workout_history()

        dialog = QDialog(self)
        dialog.setWindowTitle("Workout History")
        dialog.resize(600, 680)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }

            QLabel#HistoryTitle {
                color: #22c55e;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#HistorySubtitle {
                color: #858585;
                font-size: 13px;
                font-weight: 400;
            }

            QLabel#HistoryEmpty {
                color: #858585;
                font-size: 14px;
                padding: 20px;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea QWidget {
                background-color: transparent;
            }

            QFrame#HistoryCard {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 10px;
            }

            QFrame#HistoryStatCard {
                background-color: #171717;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }

            QLabel#HistoryStatValue {
                color: #22c55e;
                font-size: 26px;
                font-weight: 800;
            }

            QLabel#HistoryStatLabel {
                color: #858585;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#HistoryCardTitle {
                color: #d4d4d4;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#HistoryCardDate {
                color: #858585;
                font-size: 12px;
            }

            QLabel#HistoryCardResult {
                color: #22c55e;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#HistoryStatusDone {
                background-color: #14532d;
                color: #22c55e;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#HistoryStatusMissing {
                background-color: #3b2a08;
                color: #f59e0b;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 8px 14px;
                color: #d4d4d4;
                font-weight: 600;
            }

            QPushButton#HistoryFilterButton {
                background-color: #202020;
                border: 1px solid #2a2a2a;
                border-radius: 14px;
                padding: 6px 14px;
                color: #858585;
                font-weight: 600;
                font-size: 12px;
            }

            QPushButton#HistoryFilterButton:hover {
                background-color: #14532d;
                border: 1px solid #22c55e;
                color: #22c55e;
            }

            QPushButton:hover {
                background-color: #14532d;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title = QLabel("Workout History")
        title.setObjectName("HistoryTitle")

        subtitle = QLabel("All completed exercise records")
        subtitle.setObjectName("HistorySubtitle")

        total_count = len(history)
        today = datetime.now().date()
        week_start = today - timedelta(days=6)
        week_count = 0
        completed_count = 0

        for record in history:
            reps = int(record.get("reps") or 0)
            elapsed = int(record.get("elapsed_seconds") or 0)
            target_value = int(record.get("target_value") or 0)
            target_type = record.get("target_type", "reps")

            current_val = elapsed if target_type == "seconds" else reps
            if target_value > 0 and current_val >= target_value:
                completed_count += 1

            date_text = record.get("date")
            if not date_text:
                continue
            try:
                record_date = datetime.strptime(date_text, "%Y-%m-%d").date()
                if week_start <= record_date <= today:
                    week_count += 1
            except ValueError:
                continue

        success_rate = int((completed_count / total_count) * 100) if total_count else 0

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        stats_layout.addWidget(self.create_history_stat_card(str(total_count), "TOTAL"))
        stats_layout.addWidget(self.create_history_stat_card(str(week_count), "THIS WEEK"))
        stats_layout.addWidget(self.create_history_stat_card(f"{success_rate}%", "SUCCESS RATE"))

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_buttons = {
            "All": "all",
            "This Week": "week",
            "This Month": "month",
        }
        for label, filter_name in filter_buttons.items():
            btn = QPushButton(label)
            btn.setObjectName("HistoryFilterButton")
            btn.clicked.connect(lambda checked=False, name=filter_name: refresh_history_cards(name))
            filter_layout.addWidget(btn)
        filter_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        def clear_history_cards():
            while content_layout.count():
                item = content_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        def record_matches_filter(record, filter_name):
            if filter_name == "all":
                return True

            date_text = record.get("date")
            if not date_text:
                return False

            try:
                record_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                return False

            today = datetime.now().date()

            if filter_name == "week":
                week_start = today - timedelta(days=6)
                return week_start <= record_date <= today

            if filter_name == "month":
                return record_date.year == today.year and record_date.month == today.month

            return True

        def refresh_history_cards(filter_name="all"):
            clear_history_cards()

            filtered_history = [
                record
                for record in history
                if record_matches_filter(record, filter_name)
            ]

            if not filtered_history:
                empty_label = QLabel("No workout data for this filter.")
                empty_label.setObjectName("HistoryEmpty")
                empty_label.setAlignment(Qt.AlignCenter)
                content_layout.addWidget(empty_label)
            else:
                count_label = QLabel(
                    f"Showing {len(filtered_history)} workout{'s' if len(filtered_history) != 1 else ''}"
                )
                count_label.setObjectName("HistoryEmpty")
                count_label.setAlignment(Qt.AlignRight)
                content_layout.addWidget(count_label)

                for record in reversed(filtered_history):
                    content_layout.addWidget(self.create_history_card(record))

            content_layout.addStretch()

        refresh_history_cards("all")
        scroll_area.setWidget(content)

        close_button = QPushButton("CLOSE")
        close_button.clicked.connect(dialog.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(close_button)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(stats_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(scroll_area)
        layout.addLayout(btn_row)

        dialog.exec()


    def open_history_graphics(self):
        history = self.load_workout_history()

        if not history:
            print("No workout history yet.")
            return

        today = datetime.now().date()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

        counts_by_day = {
            day.strftime("%Y-%m-%d"): 0
            for day in last_7_days
        }

        month_counts = Counter()
        exercise_counter = Counter()

        for record in history:
            date_text = record.get("date")
            exercise = record.get("exercise", "UNKNOWN")

            if not date_text:
                continue

            try:
                record_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                continue

            date_key = record_date.strftime("%Y-%m-%d")

            if date_key in counts_by_day:
                counts_by_day[date_key] += 1

            if record_date.year == today.year and record_date.month == today.month:
                month_counts[record_date.day] += 1

            exercise_counter[exercise] += 1

        week_labels = [day.strftime("%a") for day in last_7_days]
        week_values = list(counts_by_day.values())

        days_in_month = monthrange(today.year, today.month)[1]
        month_days = list(range(1, days_in_month + 1))
        month_values = [month_counts.get(day, 0) for day in month_days]

        top_items = exercise_counter.most_common(5)
        top_labels = [item[0].replace("_", " ") for item in top_items]
        top_values = [item[1] for item in top_items]

        plt.style.use("dark_background")

        fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), dpi=100)

        try:
            fig.canvas.manager.set_window_title("FormAI - Workout History")
        except Exception:
            pass

        fig.patch.set_facecolor("#1E1E1E")
        fig.suptitle("Workout History", fontsize=13, fontweight="bold", color="#D4D4D4")

        for ax in axes:
            ax.set_facecolor("#252526")
            ax.tick_params(colors="#D4D4D4")
            ax.title.set_color("#D4D4D4")
            ax.xaxis.label.set_color("#D4D4D4")
            ax.yaxis.label.set_color("#D4D4D4")

            for spine in ax.spines.values():
                spine.set_color("#3E3E42")

        axes[0].plot(
            week_labels,
            week_values,
            color="#22c55e",
            linewidth=2.6,
            marker="o",
            markersize=6,
        )
        axes[0].fill_between(week_labels, week_values, color="#22c55e", alpha=0.16)
        axes[0].set_title("Last 7 Days")
        axes[0].set_ylabel("Completed")
        axes[0].set_ylim(0, max(week_values + [1]) + 1)
        axes[0].grid(True, alpha=0.16)

        axes[1].plot(
            month_days,
            month_values,
            color="#D7BA7D",
            linewidth=1.8,
            marker="o",
            markersize=4,
        )
        axes[1].fill_between(month_days, month_values, color="#D7BA7D", alpha=0.14)
        axes[1].set_title("This Month")
        axes[1].set_xlabel("Day")
        axes[1].set_ylabel("Workouts")
        axes[1].set_xlim(1, days_in_month)
        axes[1].set_ylim(0, max(month_values + [1]) + 1)
        axes[1].tick_params(axis="x", labelsize=7, rotation=45)
        axes[1].grid(True, alpha=0.12)

        if top_items:
            axes[2].barh(top_labels, top_values, color="#4EC9B0")
            axes[2].invert_yaxis()

        axes[2].set_title("Top Exercises")
        axes[2].set_xlabel("Completed")
        axes[2].grid(True, axis="x", alpha=0.14)

        plt.tight_layout(rect=[0, 0, 1, 0.90])
        plt.show(block=False)
        plt.pause(0.001)


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


    def update_camera_frame(self):
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

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

       
        if self.app_settings.get("hand_gestures", True):
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

            else:
                self.last_gesture = "None"
                self.gesture_controller.clear_consecutive()

            if self.gesture_controller.selector_active:
                self.draw_filmstrip_selector(
                    frame,
                    self.exercise_keys,
                    self.gesture_controller.selector_index,
                )
        else:
            
            self.last_gesture = "None"

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

        if hasattr(self, "feedback"):
            if not self.workout_feedback_announced:
                self.feedback.stop(self.reps)
            self.feedback.close()

        if hasattr(self, "hand_sensor"):
            self.hand_sensor.close()

        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()

        plt.close("all")
        event.accept()


def run_qt_app():
    app = QApplication(sys.argv)
    window = QtAppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_qt_app()
