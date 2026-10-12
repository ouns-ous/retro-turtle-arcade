"""Configuration, themes, and game settings for Retro Turtle Arcade."""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Theme:
    """Color palette for game rendering."""
    name: str
    bg_color: str
    primary: str
    secondary: str
    accent: str
    text_color: str
    warning_color: str
    border_color: str


THEMES: Dict[str, Theme] = {
    "neon": Theme(
        name="Cyber Neon",
        bg_color="#0d1117",
        primary="#00ffcc",
        secondary="#ff007f",
        accent="#ffea00",
        text_color="#f0f6fc",
        warning_color="#ff4444",
        border_color="#30363d",
    ),
    "synthwave": Theme(
        name="Synthwave 80s",
        bg_color="#1a0b2e",
        primary="#f706cf",
        secondary="#05ffa1",
        accent="#ffbe0b",
        text_color="#ffffff",
        warning_color="#ff2a6d",
        border_color="#431c5d",
    ),
    "matrix": Theme(
        name="Matrix Terminal",
        bg_color="#051205",
        primary="#00ff41",
        secondary="#008f11",
        accent="#a8ffb2",
        text_color="#00ff41",
        warning_color="#ff5555",
        border_color="#003b00",
    ),
    "retro": Theme(
        name="Monochrome Classic",
        bg_color="#000000",
        primary="#ffffff",
        secondary="#aaaaaa",
        accent="#cccccc",
        text_color="#ffffff",
        warning_color="#ffffff",
        border_color="#555555",
    ),
}


@dataclass
class ArcadeConfig:
    """Arcade window and engine configurations."""
    window_width: int = 800
    window_height: int = 600
    window_title: str = "Retro Turtle Arcade"
    fps: int = 60
    theme_name: str = "neon"
    sound_enabled: bool = True
    high_score_file: str = "scores.json"

    # Pong settings
    pong_winning_score: int = 5
    pong_ball_base_speed: float = 6.0
    pong_ball_speed_increment: float = 0.35
    pong_ball_max_speed: float = 14.0
    pong_paddle_speed: float = 30.0
    pong_ai_difficulty: str = "medium"  # easy, medium, hard, impossible

    # Snake settings
    snake_grid_size: int = 20
    snake_initial_speed_ms: int = 100
    snake_speed_decrement_ms: int = 2
    snake_min_speed_ms: int = 40
    snake_wrap_walls: bool = False

    # Breakout settings
    breakout_brick_rows: int = 5
    breakout_brick_cols: int = 10
    breakout_lives: int = 3
    breakout_paddle_speed: float = 35.0

    @property
    def theme(self) -> Theme:
        return THEMES.get(self.theme_name, THEMES["neon"])
