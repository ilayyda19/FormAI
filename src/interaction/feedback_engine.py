import time
from typing import Callable, Optional

from src.exercises.base_exercise import RepResult
from src.interaction.audio_feedback import AudioFeedback


SEV_COLOR = {
    "ok": "#2ECC71",
    "warning": "#F39C12",
    "error": "#E74C3C",
}

GOOD_FORM_GAP = 12.0
MESSAGE_MIN_GAP = 1.8
AUDIO_MIN_GAP = 7.0
AUDIO_STABLE_FRAMES = 6
STABLE_FRAMES_FOR_WARNING = 6
STABLE_FRAMES_FOR_ERROR = 5

AUDIO_SHORTCUTS: dict[str, str] = {
    "Keep your upper arm vertical, your elbows shouldn't move forward/backward!": "Keep elbows still!",
    "Keep your back straight!": "Straighten your back!",
    "Don't lock your knees!": "Soft knees!",
}


class FeedbackEngine:
    def __init__(self, lang: str = "en"):
        self._audio = AudioFeedback(lang=lang)
        self._lang = lang

        self._last_good: float = 0.0
        self._last_push_time: float = 0.0
        self._last_pushed_text: str = ""
        self._last_audio_time: float = 0.0
        self._last_audio_text: str = ""

        self._candidate_text: str = ""
        self._candidate_count: int = 0
        self._voice_enabled = True

        self.target_value: Optional[int] = None
        self._announced_milestones: set[int] = set()

        self.on_message: Optional[Callable[[str, str], None]] = None
        self.on_rep: Optional[Callable[[int], None]] = None

    @property
    def voice_enabled(self) -> bool:
        return self._voice_enabled

    @voice_enabled.setter
    def voice_enabled(self, enabled: bool):
        self._voice_enabled = bool(enabled)
        self._audio.set_enabled(self._voice_enabled)

    def set_target(self, target_value: int):
        self.target_value = max(1, int(target_value))
        self._announced_milestones = set()

    def process(self, result: RepResult):
        if result.counted:
            if self.on_rep:
                self.on_rep(result.rep_count)

            if self._should_announce_rep(result.rep_count):
                self._audio.on_rep(result.rep_count)

            return

        text = "Form correct ✓"
        severity = "ok"
        required_stability = 1

        if result.errors:
            text = result.errors[0]
            severity = "error"
            required_stability = STABLE_FRAMES_FOR_ERROR
        elif result.warnings:
            text = result.warnings[0]
            severity = "warning"
            required_stability = STABLE_FRAMES_FOR_WARNING

        if severity == "ok":
            now = time.time()
            if now - self._last_good >= GOOD_FORM_GAP:
                self._last_good = now
                self._audio.on_good_form()
                self._push(text, SEV_COLOR[severity], force=True)
            return

        stable_count = self._track_candidate(text)

        if stable_count >= AUDIO_STABLE_FRAMES:
            self._speak_feedback(text, severity)

        if stable_count >= required_stability:
            self._push(text, SEV_COLOR[severity])

    def start(self):
        self._audio.on_session_start()

    def stop(self, total_reps: int):
        self._audio.on_session_end(total_reps)

    def toggle_mute(self) -> bool:
        muted = self._audio.toggle_mute()
        self._voice_enabled = not muted
        return muted

    def close(self):
        self._audio.close()

    def _should_announce_rep(self, rep_count: int) -> bool:
        if rep_count <= 0 or not self.target_value:
            return False

        milestones = {
            max(1, round(self.target_value * 0.25)),
            max(1, round(self.target_value * 0.50)),
            max(1, round(self.target_value * 0.75)),
        }

        if rep_count in milestones and rep_count not in self._announced_milestones:
            self._announced_milestones.add(rep_count)
            return True

        return False

    def _track_candidate(self, text: str) -> int:
        if text == self._candidate_text:
            self._candidate_count = min(self._candidate_count + 1, 9999)
        else:
            self._candidate_text = text
            self._candidate_count = 1

        return self._candidate_count

    def _speak_feedback(self, text: str, severity: str):
        now = time.time()

        if text == self._last_audio_text and now - self._last_audio_time < AUDIO_MIN_GAP:
            return

        if text != self._last_audio_text and now - self._last_audio_time < 2.5:
            return

        self._last_audio_text = text
        self._last_audio_time = now

        audio_text = AUDIO_SHORTCUTS.get(text, text)

        if severity == "error":
            self._audio.error(audio_text)
        elif severity == "warning":
            self._audio.warn(audio_text)

    def _push(self, text: str, color: str, force: bool = False):
        now = time.time()

        if not force:
            if text == self._last_pushed_text and now - self._last_push_time < MESSAGE_MIN_GAP:
                return

            if now - self._last_push_time < MESSAGE_MIN_GAP:
                return

        self._last_pushed_text = text
        self._last_push_time = now

        if self.on_message:
            self.on_message(text, color)