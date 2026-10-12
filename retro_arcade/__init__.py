"""Retro Turtle Arcade

A modular, cross-platform arcade suite and physics playground
built entirely with Python's Turtle and Tkinter standard libraries.
"""

__version__ = "1.0.0"
__author__ = "ouns oussama"

from .config import Theme, ArcadeConfig
from .physics import Vector2D, AABB, check_aabb_collision, reflect_velocity
from .scoreboard import ScoreManager
from .audio import SoundManager

__all__ = [
    "Theme",
    "ArcadeConfig",
    "Vector2D",
    "AABB",
    "check_aabb_collision",
    "reflect_velocity",
    "ScoreManager",
    "SoundManager",
]
