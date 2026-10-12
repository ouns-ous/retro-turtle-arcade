"""Abstract base class and lifecycle states for arcade games."""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Any
from ..config import ArcadeConfig
from ..scoreboard import ScoreManager
from ..audio import SoundManager


class GameState(Enum):
    READY = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class BaseGame(ABC):
    """
    Abstract game harness supporting both Turtle visual rendering
    and headless simulation mode for test suites and headless benchmarks.
    """

    def __init__(
        self,
        config: ArcadeConfig,
        scoreboard: ScoreManager,
        sound: SoundManager,
        screen: Optional[Any] = None,
    ):
        self.config = config
        self.scoreboard = scoreboard
        self.sound = sound
        self.screen = screen
        self.state: GameState = GameState.READY
        self.is_headless = screen is None

    @abstractmethod
    def setup(self) -> None:
        """Initialize game entities, turtles, and keybindings."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset game variables to starting state."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance game physics and state by dt seconds."""
        pass

    @abstractmethod
    def render(self) -> None:
        """Draw or refresh current visual representation on screen."""
        pass

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            if not self.is_headless:
                self.render()
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            if not self.is_headless:
                self.render()

    @abstractmethod
    def cleanup(self) -> None:
        """Clear turtles and remove key listeners."""
        pass
