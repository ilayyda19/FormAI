import time
from typing import Callable, Optional

from src.exercises.base_exercise import RepResult
from src.interaction.audio_feedback import AudioFeedback


SEV_COLOR = {
    "ok":      "#2ECC71",
    "warning": "#F39C12",
    "error":   "#E74C3C",
}

GOOD_FORM_GAP = 12.0  


class FeedbackEngine:
    

    def __init__(self, lang: str = "tr"):
        self._audio = AudioFeedback(lang=lang)
        self._lang  = lang
        self._last_good: float = 0.0

        self.on_message: Optional[Callable[[str, str], None]] = None
        self.on_rep:     Optional[Callable[[int], None]] = None

   
    def process(self, result: RepResult):
        if result.counted:
            self._audio.on_rep(result.rep_count)
            if self.on_rep:
                self.on_rep(result.rep_count)

        if result.errors:
            txt = result.errors[0]
            self._audio.error(txt)
            self._push(txt, SEV_COLOR["error"])

        elif result.warnings:
            txt = result.warnings[0]
            self._audio.warn(txt)
            self._push(txt, SEV_COLOR["warning"])

        else:
            now = time.time()
            if now - self._last_good >= GOOD_FORM_GAP:
                self._last_good = now
                self._audio.on_good_form()
            msgs = {"tr": "Form dogru ✓", "en": "Form correct ✓"}
            self._push(msgs[self._lang], SEV_COLOR["ok"])

    def start(self):
        self._audio.on_session_start()

    def stop(self, total_reps: int):
        self._audio.on_session_end(total_reps)

    def toggle_mute(self) -> bool:
        return self._audio.toggle_mute()

    def close(self):
        self._audio.close()



    def _push(self, text: str, color: str):
        if self.on_message:
            self.on_message(text, color)
