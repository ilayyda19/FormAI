import json
from pathlib import Path


class WorkoutHistoryManager:
    def __init__(self, history_file: Path):
        self.history_file = history_file

    def load(self):
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as file:
                history = json.load(file)

            if isinstance(history, list):
                return history

            return []

        except (json.JSONDecodeError, OSError):
            return []

    def append(self, record):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        history = self.load()
        history.append(record)

        with open(self.history_file, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)