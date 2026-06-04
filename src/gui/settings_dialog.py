from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings,
        feedback,
        on_feedback_message,
        camera_subtitle_label,
        gesture_controller,
        gesture_status_label,
        voice_listener=None,
        parent=None,
    ):
        super().__init__(parent)

        self.settings = settings
        self.feedback = feedback
        self.on_feedback_message = on_feedback_message
        self.camera_subtitle_label = camera_subtitle_label
        self.gesture_controller = gesture_controller
        self.gesture_status_label = gesture_status_label
        self.voice_listener = voice_listener

        self.setWindowTitle("Settings")
        self.resize(520, 720)
        self.setStyleSheet(self._style())

        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 20)
        outer.setSpacing(14)

        title = QLabel("Settings")
        title.setObjectName("STitle")
        outer.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content = QWidget()
        main = QVBoxLayout(content)
        main.setContentsMargins(0, 0, 8, 0)
        main.setSpacing(14)

        rows = [
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

            (
                "voice_commands",      
                "🎙️",
                "Voice Commands",
                "Control training with spoken words.",
            ),
        ]

        for key, icon, label_text, sub_text in rows:
            main.addWidget(self._create_setting_row(key, icon, label_text, sub_text))

        self._add_section_title(main, "Gesture Guide")

        gestures = [
            ("✊", "Fist",       "Pause / Resume workout"),
            ("☝️", "Point",      "Open exercise selector · Hold to confirm · Swipe to browse"),
            ("✌️", "Peace",      "Enable / Disable gestures"),
            ("🖐️", "Open Hand",  "Toggle skeleton overlay"),
            ("👍", "Thumbs Up",  "Start workout"),
        ]

        for icon, name, description in gestures:
            main.addWidget(self._create_guide_row(icon, name, description))

        self._add_section_title(main, "Voice Commands")

        commands = [
            ("🎙️", "\"start\"",           "Start the workout"),
            ("🎙️", "\"pause\"",           "Pause the workout"),
            ("🎙️", "\"resume\"",          "Resume the workout"),
            ("🎙️", "\"stop\"",            "Stop the workout"),
            ("🎙️", "\"squat\"",           "Switch to Squat"),
            ("🎙️", "\"push up\"",         "Switch to Push Up"),
            ("🎙️", "\"bicep curl\"",      "Switch to Bicep Curl"),
        ]

        for icon, command, description in commands:
            main.addWidget(self._create_guide_row(command, "Voice", description))

        main.addStretch()

        scroll_area.setWidget(content)
        outer.addWidget(scroll_area, stretch=1)

        done_row = QHBoxLayout()
        done_button = QPushButton("DONE")
        done_button.clicked.connect(self.accept)

        done_row.addStretch()
        done_row.addWidget(done_button)
        outer.addLayout(done_row)

    def _create_setting_row(self, key, icon, label_text, sub_text):
        row = QFrame()
        row.setObjectName("SRow")

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(16, 12, 16, 12)
        row_layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            "color: #22c55e;"
            "font-size: 11px;"
            "font-weight: 800;"
            "background: transparent;"
            "border: none;"
        )
        icon_label.setFixedWidth(54)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        label = QLabel(label_text)
        label.setStyleSheet(
            "font-weight: 700;"
            "font-size: 13px;"
            "background: transparent;"
            "border: none;"
        )

        subtitle = QLabel(sub_text)
        subtitle.setObjectName("SSub")
        subtitle.setWordWrap(True)

        text_column.addWidget(label)
        text_column.addWidget(subtitle)

        active = self.settings.get(key, True)
        toggle = QPushButton("ON" if active else "OFF")
        toggle.setCursor(Qt.PointingHandCursor)
        toggle.setStyleSheet(self._toggle_style(active))
        toggle.clicked.connect(
            lambda checked=False, setting_key=key, button=toggle:
            self._on_toggle(setting_key, button)
        )

        row_layout.addWidget(icon_label)
        row_layout.addLayout(text_column, stretch=1)
        row_layout.addWidget(toggle)

        return row

    def _add_section_title(self, layout, text):
        title = QLabel(text)
        title.setStyleSheet(
            "color: #858585;"
            "font-size: 11px;"
            "font-weight: 700;"
            "letter-spacing: 1px;"
            "background: transparent;"
            "border: none;"
            "margin-top: 6px;"
        )
        layout.addWidget(title)

    def _create_guide_row(self, left_text, name, description):
        row = QFrame()
        row.setObjectName("SRow")

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 10, 14, 10)
        row_layout.setSpacing(12)

        left_label = QLabel(left_text)
        left_label.setStyleSheet(
            "color: #22c55e;"
            "font-weight: 800;"
            "font-size: 11px;"
            "background: transparent;"
            "border: none;"
        )
        left_label.setFixedWidth(78)

        name_label = QLabel(name)
        name_label.setStyleSheet(
            "font-weight: 700;"
            "font-size: 12px;"
            "background: transparent;"
            "border: none;"
        )
        name_label.setFixedWidth(88)

        description_label = QLabel(description)
        description_label.setObjectName("SSub")
        description_label.setWordWrap(True)

        row_layout.addWidget(left_label)
        row_layout.addWidget(name_label)
        row_layout.addWidget(description_label, stretch=1)

        return row

    def _on_toggle(self, key, button):
        new_value = not self.settings.get(key, True)
        self.settings[key] = new_value

        button.setText("ON" if new_value else "OFF")
        button.setStyleSheet(self._toggle_style(new_value))

        self._apply_settings_now()

    def _apply_settings_now(self):
        voice_on = self.settings.get("voice_feedback", True)

        if hasattr(self.feedback, "voice_enabled"):
            self.feedback.voice_enabled = voice_on
        elif hasattr(self.feedback, "_audio"):
            if voice_on:
                self.feedback._audio.unmute()
            else:
                self.feedback._audio.mute()

        self.feedback.on_message = self.on_feedback_message


        subtitle_on = self.settings.get("subtitle_feedback", True)
        window = self.parent()
        if not subtitle_on:
            if hasattr(window, "clear_camera_subtitle"):
                window.clear_camera_subtitle()
            else:
                self.camera_subtitle_label.clear()
                self.camera_subtitle_label.hide()
        
        else:
            if self.camera_subtitle_label.text().strip():
                if hasattr(window, "position_camera_subtitle"):
                    window.position_camera_subtitle()
                else:
                    self.camera_subtitle_label.show()

        gestures_on = self.settings.get("hand_gestures", True)
        self.gesture_controller.gestures_enabled = gestures_on

        state = "ON" if gestures_on else "OFF"
        self.gesture_status_label.setText(f"Gestures: {state}")

        voice_commands_on = self.settings.get("voice_commands", True)

        if self.voice_listener is not None:
            if voice_commands_on:
                available = getattr(self.voice_listener, "available", False)
                running = getattr(self.voice_listener, "_running", False)

                if available and not running:
                    self.voice_listener.start()
            else:
                self.voice_listener.stop()

    def _toggle_style(self, active):
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

    def _style(self):
        return """
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
                font-size: 22px;
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

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea QWidget {
                background-color: transparent;
            }

            QScrollBar:vertical {
                background: #1e1e1e;
                width: 10px;
                margin: 4px 0px 4px 0px;
            }

            QScrollBar::handle:vertical {
                background: #3e3e42;
                border-radius: 5px;
                min-height: 28px;
            }

            QScrollBar::handle:hover {
                background: #22c55e;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
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
        """
