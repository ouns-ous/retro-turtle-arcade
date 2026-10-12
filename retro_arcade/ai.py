"""AI Controllers for Pong paddle with predictive physics calculation."""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import Optional
from .physics import Vector2D, clamp


class BaseAI(ABC):
    """Abstract Base Class for Pong paddle AI controllers."""

    def __init__(self, paddle_speed: float):
        self.paddle_speed = paddle_speed

    @abstractmethod
    def calculate_move(
        self,
        paddle_y: float,
        ball_pos: Vector2D,
        ball_vel: Vector2D,
        court_top: float,
        court_bottom: float,
        paddle_x: float,
    ) -> float:
        """
        Calculates vertical paddle movement offset (-paddle_speed to +paddle_speed).
        """
        pass


class EasyAI(BaseAI):
    """Slow reaction with intentional jitter; only tracks when ball is nearby."""

    def __init__(self, paddle_speed: float):
        super().__init__(paddle_speed * 0.65)
        self.jitter_frames = 0
        self.jitter_offset = 0.0

    def calculate_move(
        self,
        paddle_y: float,
        ball_pos: Vector2D,
        ball_vel: Vector2D,
        court_top: float,
        court_bottom: float,
        paddle_x: float,
    ) -> float:
        # If ball is moving away from AI, stay near center
        if ball_vel.x < 0:
            target_y = 0.0
        else:
            self.jitter_frames += 1
            if self.jitter_frames > 15:
                self.jitter_offset = random.uniform(-40.0, 40.0)
                self.jitter_frames = 0
            target_y = ball_pos.y + self.jitter_offset

        diff = target_y - paddle_y
        if abs(diff) < 10.0:
            return 0.0
        move = self.paddle_speed if diff > 0 else -self.paddle_speed
        return move


class MediumAI(BaseAI):
    """Reactive tracking with standard speed and deadband smoothing."""

    def __init__(self, paddle_speed: float):
        super().__init__(paddle_speed * 0.85)

    def calculate_move(
        self,
        paddle_y: float,
        ball_pos: Vector2D,
        ball_vel: Vector2D,
        court_top: float,
        court_bottom: float,
        paddle_x: float,
    ) -> float:
        if ball_vel.x < 0:
            target_y = 0.0
        else:
            target_y = ball_pos.y

        diff = target_y - paddle_y
        if abs(diff) < 8.0:
            return 0.0
        move = self.paddle_speed if diff > 0 else -self.paddle_speed
        return move


class HardAI(BaseAI):
    """Predictive AI that calculates future ball bounce trajectory."""

    def __init__(self, paddle_speed: float):
        super().__init__(paddle_speed * 1.05)

    def calculate_move(
        self,
        paddle_y: float,
        ball_pos: Vector2D,
        ball_vel: Vector2D,
        court_top: float,
        court_bottom: float,
        paddle_x: float,
    ) -> float:
        if ball_vel.x <= 0:
            target_y = 0.0
        else:
            # Raycast ball trajectory to paddle_x
            target_y = predict_ball_y(
                ball_pos, ball_vel, paddle_x, court_top, court_bottom
            )

        diff = target_y - paddle_y
        if abs(diff) < 5.0:
            return 0.0
        move = self.paddle_speed if diff > 0 else -self.paddle_speed
        return move


class ImpossibleAI(BaseAI):
    """Perfect prediction with tactical edge deflection aiming."""

    def __init__(self, paddle_speed: float):
        super().__init__(paddle_speed * 1.25)

    def calculate_move(
        self,
        paddle_y: float,
        ball_pos: Vector2D,
        ball_vel: Vector2D,
        court_top: float,
        court_bottom: float,
        paddle_x: float,
    ) -> float:
        if ball_vel.x <= 0:
            target_y = 0.0
        else:
            pred_y = predict_ball_y(
                ball_pos, ball_vel, paddle_x, court_top, court_bottom
            )
            # Offset slightly to intentionally hit with paddle edge to create sharp angles
            target_y = pred_y + (15.0 if pred_y > 0 else -15.0)

        diff = target_y - paddle_y
        if abs(diff) < 3.0:
            return 0.0
        move = self.paddle_speed if diff > 0 else -self.paddle_speed
        return move


def predict_ball_y(
    ball_pos: Vector2D,
    ball_vel: Vector2D,
    target_x: float,
    court_top: float,
    court_bottom: float,
) -> float:
    """Simulates future ball wall bounces until reaching target_x."""
    if ball_vel.x <= 0:
        return ball_pos.y

    curr_x = ball_pos.x
    curr_y = ball_pos.y
    vx = ball_vel.x
    vy = ball_vel.y

    # Calculate time to reach target_x
    dx = target_x - curr_x
    if dx <= 0:
        return curr_y

    time_total = dx / vx
    court_height = court_top - court_bottom

    # Fast analytic reflection calculation
    # Project unconstrained y
    projected_y = curr_y + vy * time_total

    # Fold back into [court_bottom, court_top]
    rel_y = projected_y - court_bottom
    period = 2 * court_height
    mod_y = rel_y % period

    if mod_y < 0:
        mod_y += period

    if mod_y <= court_height:
        final_y = court_bottom + mod_y
    else:
        final_y = court_top - (mod_y - court_height)

    return clamp(final_y, court_bottom + 10.0, court_top - 10.0)


def create_ai(difficulty: str, paddle_speed: float) -> BaseAI:
    """Factory creating configured AI controller."""
    diff = difficulty.lower()
    if diff == "easy":
        return EasyAI(paddle_speed)
    elif diff == "hard":
        return HardAI(paddle_speed)
    elif diff == "impossible":
        return ImpossibleAI(paddle_speed)
    else:
        return MediumAI(paddle_speed)
