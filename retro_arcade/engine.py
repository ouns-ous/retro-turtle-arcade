"""Core game loop and screen harness for Retro Turtle Arcade."""

from __future__ import annotations
import sys
import time
from typing import Optional
from .config import ArcadeConfig
from .scoreboard import ScoreManager
from .audio import SoundManager
from .games import PongGame, SnakeGame, BreakoutGame
from .menu import ArcadeMenu


class ArcadeEngine:
    """Master runtime coordinator handling screen, event loops, and game transitions."""

    def __init__(self, config: Optional[ArcadeConfig] = None, headless: bool = False):
        self.config = config or ArcadeConfig()
        self.headless = headless
        self.scoreboard = ScoreManager(self.config.high_score_file)
        self.sound = SoundManager(self.config.sound_enabled)

        self.screen = None
        self.current_game = None
        self.menu = None
        self.is_running = False
        self.last_time = time.time()
        self.frame_interval_ms = max(10, int(1000 / self.config.fps))

    def initialize_display(self) -> None:
        """Configures Turtle canvas with double buffering and theme colors."""
        if self.headless:
            return

        import turtle
        self.screen = turtle.Screen()
        self.screen.title(f"{self.config.window_title} - [{self.config.theme.name}]")
        self.screen.setup(width=self.config.window_width, height=self.config.window_height)
        self.screen.bgcolor(self.config.theme.bg_color)
        self.screen.tracer(0)  # Double-buffering: only draw on explicit update

    def start_menu(self) -> None:
        """Displays arcade menu launcher."""
        if self.current_game:
            self.current_game.cleanup()
            self.current_game = None

        if self.headless:
            return

        self.menu = ArcadeMenu(
            config=self.config,
            sound=self.sound,
            scoreboard=self.scoreboard,
            screen=self.screen,
            on_select=self.launch_activity,
        )
        self.menu.setup()

    def launch_activity(self, action: str) -> None:
        """Launches the selected game or quits."""
        if action == "exit":
            self.stop()
            return

        if self.menu:
            self.menu.cleanup()
            self.menu = None

        if action == "pong_1p":
            self.current_game = PongGame(
                self.config, self.scoreboard, self.sound, self.screen, two_player=False
            )
        elif action == "pong_2p":
            self.current_game = PongGame(
                self.config, self.scoreboard, self.sound, self.screen, two_player=True
            )
        elif action == "snake":
            self.current_game = SnakeGame(
                self.config, self.scoreboard, self.sound, self.screen
            )
        elif action == "breakout":
            self.current_game = BreakoutGame(
                self.config, self.scoreboard, self.sound, self.screen
            )

        if self.current_game:
            self.current_game.setup()
            # Bind Escape to return to menu
            if self.screen:
                self.screen.onkeypress(self.return_to_menu, "Escape")

    def return_to_menu(self) -> None:
        """Exits active game back to main menu."""
        if self.current_game:
            self.current_game.cleanup()
            self.current_game = None
        self.start_menu()

    def run(self) -> None:
        """Enters the main application loop."""
        self.initialize_display()
        self.start_menu()
        self.is_running = True
        self.last_time = time.time()

        if not self.headless and self.screen:
            self._schedule_tick()
            try:
                self.screen.mainloop()
            except Exception:
                pass

    def _schedule_tick(self) -> None:
        if not self.is_running or not self.screen:
            return
        self._tick()
        self.screen.ontimer(self._schedule_tick, self.frame_interval_ms)

    def _tick(self) -> None:
        now = time.time()
        dt = min(now - self.last_time, 0.1)  # Clamp dt to avoid spiral of death
        self.last_time = now

        if self.current_game:
            self.current_game.update(dt)
            self.current_game.render()

    def stop(self) -> None:
        self.is_running = False
        if self.screen:
            try:
                self.screen.bye()
            except Exception:
                pass
        sys.exit(0)
