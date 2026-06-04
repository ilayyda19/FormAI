import threading
import queue
import time
import traceback

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class AudioFeedback:
    DEFAULT_RATE = 165
    DEFAULT_VOLUME = 0.90
    COOLDOWN = 8.0
    MIN_GAP_BETWEEN_MESSAGES = 3.0

    def __init__(self, lang: str = "en"):
        self.lang = lang
        self._muted = False
        self._q: queue.Queue[str | None] = queue.Queue()
        self._history: dict[str, float] = {}
        self._engine = None
        self._available = pyttsx3 is not None

        if self._available:
            self._t = threading.Thread(target=self._loop, daemon=True)
            self._t.start()

    @property
    def muted(self) -> bool:
        return self._muted

    def say(self, msg: str, bypass_cooldown: bool = False):
        if self._muted or not self._available or not msg:
            return

        msg = self._shorten(msg)
        now = time.time()

        if not bypass_cooldown:
            last_same = self._history.get(msg, 0.0)
            if now - last_same < self.COOLDOWN:
                return

            last_any = self._history.get("__last_any__", 0.0)
            if now - last_any < self.MIN_GAP_BETWEEN_MESSAGES:
                return

        self._history[msg] = now
        self._history["__last_any__"] = now
        self._q.put(msg)

    def mute(self):
        self._muted = True

    def unmute(self):
        self._muted = False

    def set_enabled(self, enabled: bool):
        self._muted = not enabled

    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        return self._muted

    def close(self):
        if self._available:
            self._q.put(None)
        self._stop_engine()

    def on_rep(self, n: int):
        self.say(f"Rep {n}", bypass_cooldown=True)

    def on_good_form(self):
        self.say("Good form.")

    def on_session_start(self):
        self.say("Ready.", bypass_cooldown=True)

    def on_session_end(self, total: int):
        self.say(f"Workout complete. {total} reps completed.", bypass_cooldown=True)

    def warn(self, text: str):
        self.say(text)

    def error(self, text: str):
        self.say(text)

    def _loop(self):
        while True:
            item = self._q.get()

            if item is None:
                break

            if self._muted:
                continue

            self._speak_item(item)

        self._stop_engine()

    def _speak_item(self, item: str):
        for attempt in range(2):
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", self.DEFAULT_RATE)
                self._engine.setProperty("volume", self.DEFAULT_VOLUME)
                self._pick_voice()
                self._engine.say(item)
                self._engine.runAndWait()
                return
            except Exception:
                print(f"[AudioFeedback] say() failed for '{item}' (attempt {attempt + 1}):")
                traceback.print_exc()
            finally:
                self._stop_engine()

            time.sleep(0.15)

    def _stop_engine(self):
        if not self._engine:
            return

        try:
            self._engine.stop()
        except Exception:
            pass
        finally:
            self._engine = None

    def _pick_voice(self):
        if not self._engine:
            return

        voices = self._engine.getProperty("voices") or []

        for voice in voices:
            name = (voice.name or "").lower()

            if "english" in name or "zira" in name or "david" in name:
                self._engine.setProperty("voice", voice.id)
                return

        if voices:
            self._engine.setProperty("voice", voices[0].id)

    def _shorten(self, text: str) -> str:
        shortcuts = {
            "Keep your chest up and avoid folding forward.": "Chest up.",
            "Do not squat too deep. Keep the movement controlled.": "Control depth.",
            "Go a little lower for a full squat.": "Go lower.",
            "Try to keep both knees moving evenly.": "Move knees evenly.",
            "Keep your upper body upright.": "Stay upright.",
            "Bring your back knee closer to the ground.": "Back knee lower.",
            "Do not bend your front knee too much.": "Control front knee.",
            "Keep your elbows stable, do not use your shoulders!": "Keep elbows stable.",
            "Squeeze more at the top and hold!": "Squeeze at the top.",
            "Do not hyperextend your lower back, keep your torso upright!": "Keep torso upright.",
            "Extend your arms fully!": "Extend arms.",
            "Slightly bend your elbows, do not keep them completely locked or overly bent.": "Soft elbows.",
            "Do not go too high, stop at shoulder level!": "Stop at shoulder level.",
            "Keep your upper arm vertical, your elbows shouldn't move forward/backward!": "Keep upper arms still.",
            "Extend your arm fully!": "Extend arm.",
            "Do not raise your hips, maintain a straight body line!": "Keep body straight.",
            "Your hips are sagging too low!": "Lift hips.",
            "Keep your elbows close to your torso (tucked in).": "Elbows close.",
            "Knees are bent too much, make sure you are engaging your hamstrings.": "Less knee bend.",
            "Shoulders should not pass the bar line, keep your back flat!": "Keep back flat.",
            "You might be leaning down too low, please check.": "Do not go too low.",
            "Your hips are too high! Flatten your body.": "Hips down.",
            "Your hips are too low, do not let your lower back sag.": "Hips up.",
            "Shoulders should be directly above your elbows.": "Align shoulders.",
            "Keep your torso bent forward, do not stand up straight!": "Stay bent forward.",
            "Drive your elbows back and squeeze your shoulder blades.": "Drive elbows back.",
            "Keep your body upright, do not lean forward!": "Stay upright.",
            "Keep your arms stable, do not swing them.": "Keep arms stable.",
            "Arms should be nearly straight, do not bend them too much.": "Keep arms straighter.",
            "Do not raise your arms above shoulder level, risk of strain!": "Do not raise too high.",
        }

        return shortcuts.get(text, text)