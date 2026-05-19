
import threading
import queue
import time

import pyttsx3


class AudioFeedback:

    DEFAULT_RATE   = 170
    DEFAULT_VOLUME = 0.93
    COOLDOWN       = 3.5    

    def __init__(self, lang: str = "tr"):
        self.lang    = lang
        self._muted  = False
        self._q: queue.Queue[str | None] = queue.Queue()
        self._history: dict[str, float]  = {}
        self._engine: pyttsx3.Engine | None = None
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    

    def say(self, msg: str, bypass_cooldown: bool = False):
        if self._muted:
            return
        now = time.time()
        if not bypass_cooldown and now - self._history.get(msg, 0) < self.COOLDOWN:
            return
        self._history[msg] = now
        self._q.put(msg)

    def mute(self):   self._muted = True
    def unmute(self): self._muted = False

    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        return self._muted

    def close(self):
        self._q.put(None)

   

    def on_rep(self, n: int):
        m = {"tr": f"Tekrar {n}", "en": f"Rep {n}"}
        self.say(m[self.lang], bypass_cooldown=True)

    def on_good_form(self):
        m = {"tr": "Harika gidiyor!", "en": "Looking good!"}
        self.say(m[self.lang])

    def on_session_start(self):
        m = {"tr": "Hazir olunca basliyoruz.", "en": "Ready when you are."}
        self.say(m[self.lang], bypass_cooldown=True)

    def on_session_end(self, total: int):
        m = {
            "tr": f"Antrenman bitti. {total} tekrar tamamlandi.",
            "en": f"Done! {total} reps completed.",
        }
        self.say(m[self.lang], bypass_cooldown=True)

    def warn(self, text: str):
        self.say(text)

    def error(self, text: str):
        self.say(text)

  

    def _loop(self):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate",   self.DEFAULT_RATE)
        self._engine.setProperty("volume", self.DEFAULT_VOLUME)
        self._pick_voice()

        while True:
            item = self._q.get()
            if item is None:
                break
            if not self._muted:
                try:
                    self._engine.say(item)
                    self._engine.runAndWait()
                except Exception:
                    pass

    def _pick_voice(self):
        if not self._engine:
            return
        voices = self._engine.getProperty("voices") or []
        lookup = {"tr": "turkish", "en": "english"}
        target = lookup.get(self.lang, "english")
        for v in voices:
            name = (v.name or "").lower()
            if target in name:
                self._engine.setProperty("voice", v.id)
                return
        if voices:
            self._engine.setProperty("voice", voices[0].id)
