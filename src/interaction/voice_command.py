# pyright: reportMissingImports=false, reportOptionalMemberAccess=false

import os
import re
import threading
import time
from difflib import SequenceMatcher
from typing import Callable, Optional, Any

try:
    import speech_recognition as sr  # type: ignore
except ImportError:
    sr = None


MIC_DEVICE_INDEX: Optional[int] = None


def _env_mic_index() -> Optional[int]:
    raw = os.getenv("FORMAI_MIC_INDEX", "").strip()

    if not raw:
        return MIC_DEVICE_INDEX

    try:
        return int(raw)
    except ValueError:
        return MIC_DEVICE_INDEX


COMMAND_ALIASES = {
    "START": [
        "start", "begin", "go", "lets go", "let us go", "başla", "basla",
    ],

    "PAUSE": [
        "pause", "hold", "wait", "mola", "duraklat",
    ],

    "RESUME": [
        "resume", "continue", "keep going", "devam", "devam et",
    ],

    "STOP": [
        "stop", "finish", "end workout", "bitir", "dur",
    ],

    "RESET": [
        "reset", "restart", "clear", "sifirla", "sıfırla",
    ],

    "EXERCISE:squat": [
        "squat", "squats", "squad", "skuat", "comelme", "çömelme",
    ],

    "EXERCISE:bicep_curl": [
        "bicep curl", "biceps curl", "bicep curls", "biceps curls",
        "bicep", "biceps", "curl", "arm curl",
        "bicep girl", "bicep carl", "biceps carl", "biceps girl",
        "biceps call", "bicep call",
        "baysip curl", "baysep curl", "bayseps curl", "baysips curl",
        "basic curl", "bike curl", "by step curl", "bay sip curl",
        "biseps curl", "bisep curl",
    ],

    "EXERCISE:push_up": [
        "push up", "push-up", "pushups", "push ups", "press up",
        "sinav", "şınav",
    ],

    "EXERCISE:deadlift": [
        "deadlift", "dead lift", "dedlift", "dead left",
    ],

    "EXERCISE:plank": [
        "plank", "pilank", "blank",
    ],

    "EXERCISE:lunge": [
        "lunge", "lunges", "lanj", "lanch",
    ],

    "EXERCISE:shoulder_press": [
        "shoulder press", "shoulders press", "sholder press",
        "shoulder", "overhead press",
    ],

    "EXERCISE:lateral_raise": [
        "lateral raise", "side raise", "lateral rice", "lateral rays",
    ],

    "EXERCISE:front_raise": [
        "front raise", "front rice", "front rays",
    ],

    "EXERCISE:tricep_extension": [
        "tricep extension", "triceps extension", "tricep", "triceps",
    ],

    "EXERCISE:bent_over_row": [
        "bent over row", "bent row", "row", "back row",
    ],

    "EXERCISE:calf_raise": [
        "calf raise", "calf raises", "calves raise", "calf rice",
    ],
}


_ALIAS_PAIRS: list[tuple[str, str]] = [
    (alias, command)
    for command, aliases in COMMAND_ALIASES.items()
    for alias in aliases
]


class VoiceCommandListener:
    def __init__(self, lang: str = "en-US", phrase_time_limit: int = 4):
        self.lang = lang
        self.phrase_time_limit = phrase_time_limit

        self.on_command: Optional[Callable[[str], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._recognizer: Any = None
        self._microphone: Any = None
        self._last_error_status = 0.0

        if sr is None:
            self._emit_status("Voice commands unavailable: SpeechRecognition is not installed.")
            return

        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.55
            self._recognizer.non_speaking_duration = 0.25

            mic_index = _env_mic_index()
            self._microphone = sr.Microphone(device_index=mic_index)

        except Exception as exc:
            self._recognizer = None
            self._microphone = None
            self._emit_status(f"Voice commands unavailable: microphone not found ({exc}).")

    @property
    def available(self) -> bool:
        return sr is not None and self._recognizer is not None and self._microphone is not None

    @staticmethod
    def list_microphones() -> list[str]:
        if sr is None:
            return []

        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def start(self):
        if self._running:
            return

        if not self.available:
            self._emit_status("Voice commands: OFF (no microphone)")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        self._emit_status("Voice commands: ON")

    def stop(self):
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _emit_status(self, text: str):
        print(text)

        if self.on_status:
            self.on_status(text)

    def _emit_command(self, command: str):
        print("Voice command:", command)

        if self.on_command:
            self.on_command(command)

    @staticmethod
    def _clean(text: str) -> str:
        text = text.lower().strip()

        replacements = {
            "ı": "i",
            "İ": "i",
            "ğ": "g",
            "ü": "u",
            "ş": "s",
            "ö": "o",
            "ç": "c",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _normalize_command(self, text: str) -> Optional[str]:
        cleaned = self._clean(text)

        if not cleaned:
            return None

        for alias, command in _ALIAS_PAIRS:
            clean_alias = self._clean(alias)

            if clean_alias and clean_alias in cleaned:
                return command

        best_command = None
        best_score = 0.0

        for alias, command in _ALIAS_PAIRS:
            clean_alias = self._clean(alias)
            score = SequenceMatcher(None, cleaned, clean_alias).ratio()

            if score > best_score:
                best_score = score
                best_command = command

        if best_score >= 0.72:
            return best_command

        return None

    def _listen_loop(self):
        if not self.available or sr is None:
            return

        recognizer = self._recognizer
        microphone = self._microphone

        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)

            while self._running:
                try:
                    with microphone as source:
                        audio = recognizer.listen(
                            source,
                            timeout=1.0,
                            phrase_time_limit=self.phrase_time_limit,
                        )

                    text = recognizer.recognize_google(
                        audio,
                        language=self.lang,
                    )

                    print("Heard:", text)

                    command = self._normalize_command(text)

                    if command:
                        self._emit_command(command)

                except sr.WaitTimeoutError:
                    continue

                except sr.UnknownValueError:
                    continue

                except sr.RequestError as exc:
                    now = time.time()

                    if now - self._last_error_status > 8.0:
                        self._last_error_status = now
                        self._emit_status(f"Voice recognition network error: {exc}")

                    time.sleep(1.0)

                except Exception as exc:
                    now = time.time()

                    if now - self._last_error_status > 5.0:
                        self._last_error_status = now
                        self._emit_status(f"Voice error: {exc}")

                    time.sleep(1.0)

        finally:
            self._running = False
            self._emit_status("Voice commands: OFF")