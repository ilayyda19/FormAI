from datetime import datetime, timedelta

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


class WorkoutHistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)

        self.history = history

        self.setWindowTitle("Workout History")
        self.resize(600, 680)
        self.setStyleSheet(self._style())

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title = QLabel("Workout History")
        title.setObjectName("HistoryTitle")

        subtitle = QLabel("All completed exercise records")
        subtitle.setObjectName("HistorySubtitle")

        total_count, week_count, success_rate = self._calculate_stats()

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        stats_layout.addWidget(self.create_history_stat_card(str(total_count), "TOTAL"))
        stats_layout.addWidget(self.create_history_stat_card(str(week_count), "THIS WEEK"))
        stats_layout.addWidget(self.create_history_stat_card(f"{success_rate}%", "SUCCESS RATE"))

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

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

        def refresh_history_cards(filter_name="all"):
            clear_history_cards()

            filtered_history = [
                record
                for record in self.history
                if self.record_matches_filter(record, filter_name)
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
                count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                content_layout.addWidget(count_label)

                for record in reversed(filtered_history):
                    content_layout.addWidget(self.create_history_card(record))

            content_layout.addStretch()

        filter_buttons = {
            "All": "all",
            "This Week": "week",
            "This Month": "month",
        }

        for label, filter_name in filter_buttons.items():
            button = QPushButton(label)
            button.setObjectName("HistoryFilterButton")
            button.clicked.connect(
                lambda checked=False, name=filter_name: refresh_history_cards(name)
            )
            filter_layout.addWidget(button)

        filter_layout.addStretch()

        refresh_history_cards("all")
        scroll_area.setWidget(content)

        close_button = QPushButton("CLOSE")
        close_button.clicked.connect(self.accept)

        button_row = QHBoxLayout()
        button_row.addWidget(close_button)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(stats_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(scroll_area)
        layout.addLayout(button_row)

    def create_history_stat_card(self, value, label):
        card = QFrame()
        card.setObjectName("HistoryStatCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        value_label = QLabel(str(value))
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

    def record_matches_filter(self, record, filter_name):
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

    def _calculate_stats(self):
        total_count = len(self.history)
        today = datetime.now().date()
        week_start = today - timedelta(days=6)
        week_count = 0
        completed_count = 0

        for record in self.history:
            reps = int(record.get("reps") or 0)
            elapsed = int(record.get("elapsed_seconds") or 0)
            target_value = int(record.get("target_value") or 0)
            target_type = record.get("target_type", "reps")

            current_value = elapsed if target_type == "seconds" else reps

            if target_value > 0 and current_value >= target_value:
                completed_count += 1

            date_text = record.get("date")
            if not date_text:
                continue

            try:
                record_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                continue

            if week_start <= record_date <= today:
                week_count += 1

        success_rate = int((completed_count / total_count) * 100) if total_count else 0

        return total_count, week_count, success_rate

    def _style(self):
        return """
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
                padding: 8px;
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
        """