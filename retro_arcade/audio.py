"""Sound effect manager with threaded non-blocking playback."""

from __future__ import annotations
import platform
import threading
from typing import Dict, Tuple

try:
    if platform.system() == "Windows":
        import winsound
    else:
        winsound = None
except ImportError:
    winsound = None


class SoundManager:
    """Manages sound effects without blocking game frame execution."""

    # Sound frequency (Hz) and duration (ms)
    EFFECTS: Dict[str, Tuple[int, int]] = {
        "hit": (520, 35),
        "bounce": (380, 25),
        "score": (880, 120),
        "game_over": (220, 280),
        "pickup": (750, 45),
        "powerup": (950, 70),
        "brick_break": (640, 30),
        "menu_select": (600, 30),
    }

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and (winsound is not None)

    def play(self, effect_name: str) -> None:
        """Plays sound asynchronously in a daemon thread so it never hitches FPS."""
        if not self.enabled or effect_name not in self.EFFECTS:
            return

        freq, dur = self.EFFECTS[effect_name]

        def _worker():
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
