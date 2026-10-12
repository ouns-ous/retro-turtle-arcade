"""Quantum Breakout brick-breaker game with multi-hit bricks and lives."""

from __future__ import annotations
import math
import random
from typing import Optional, List, Tuple, Any
from .base import BaseGame, GameState
from ..config import ArcadeConfig
from ..scoreboard import ScoreManager
from ..audio import SoundManager
from ..physics import (
    Vector2D,
    AABB,
    check_circle_aabb_collision,
    reflect_velocity,
    calculate_paddle_bounce,
    clamp,
)


class Brick:
    def __init__(self, box: AABB, max_health: int = 1, color_code: str = "#00ffcc"):
        self.box = box
        self.health = max_health
        self.max_health = max_health
        self.color_code = color_code

    @property
    def is_destroyed(self) -> bool:
        return self.health <= 0


class BreakoutGame(BaseGame):
    """Quantum Breakout with destructible bricks, deflection physics, and lives."""

    def __init__(
        self,
        config: ArcadeConfig,
        scoreboard: ScoreManager,
        sound: SoundManager,
        screen: Optional[Any] = None,
        player_name: str = "Player 1",
    ):
        super().__init__(config, scoreboard, sound, screen)
        self.player_name = player_name

        self.court_half_w = (config.window_width - 80) / 2
        self.court_half_h = (config.window_height - 100) / 2

        # Paddle
        self.paddle_y = -self.court_half_h + 35
        self.paddle_x = 0.0
        self.paddle_half_w = 48.0
        self.paddle_half_h = 7.0
        self.paddle_move_intent = 0.0

        # Ball
        self.ball_radius = 7.0
        self.ball_pos = Vector2D(0.0, self.paddle_y + 20)
        self.ball_vel = Vector2D(0.0, 0.0)
        self.ball_attached = True

        # Bricks
        self.bricks: List[Brick] = []
        self.score = 0
        self.lives = config.breakout_lives
        self.bricks_cleared = 0

        # Turtles
        self.t_paddle = None
        self.t_ball = None
        self.t_bricks = None
        self.t_hud = None
        self.t_border = None

    @property
    def paddle_box(self) -> AABB:
        return AABB(self.paddle_x, self.paddle_y, self.paddle_half_w, self.paddle_half_h)

    def setup(self) -> None:
        self.reset()
        if not self.is_headless:
            import turtle

            self.t_border = turtle.RawTurtle(self.screen)
            self.t_border.hideturtle()
            self.t_border.speed(0)
            self.draw_border()

            self.t_bricks = turtle.RawTurtle(self.screen)
            self.t_bricks.hideturtle()
            self.t_bricks.speed(0)

            self.t_paddle = turtle.RawTurtle(self.screen)
            self.t_paddle.speed(0)
            self.t_paddle.shape("square")
            self.t_paddle.color(self.config.theme.primary)
            self.t_paddle.penup()
            self.t_paddle.shapesize(stretch_wid=self.paddle_half_h / 10, stretch_len=self.paddle_half_w / 10)

            self.t_ball = turtle.RawTurtle(self.screen)
            self.t_ball.speed(0)
            self.t_ball.shape("circle")
            self.t_ball.color(self.config.theme.accent)
            self.t_ball.penup()
            self.t_ball.shapesize(stretch_wid=self.ball_radius / 10, stretch_len=self.ball_radius / 10)

            self.t_hud = turtle.RawTurtle(self.screen)
            self.t_hud.hideturtle()
            self.t_hud.speed(0)
            self.t_hud.penup()

            self.bind_keys()
            self.render()

    def draw_border(self) -> None:
        if self.is_headless or not self.t_border:
            return
        theme = self.config.theme
        self.t_border.clear()
        self.t_border.penup()
        self.t_border.color(theme.border_color)
        self.t_border.width(3)

        x0, y0 = -self.court_half_w, -self.court_half_h
        x1, y1 = self.court_half_w, self.court_half_h
        self.t_border.goto(x0, y0)
        self.t_border.pendown()
        # Open bottom or closed box (closed box has pit floor below paddle)
        for x, y in [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
            self.t_border.goto(x, y)
        self.t_border.penup()

    def bind_keys(self) -> None:
        if self.is_headless or not self.screen:
            return
        self.screen.listen()
        self.screen.onkeypress(lambda: self.set_paddle_intent(-1.0), "Left")
        self.screen.onkeypress(lambda: self.set_paddle_intent(-1.0), "a")
        self.screen.onkeypress(lambda: self.set_paddle_intent(-1.0), "A")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "Left")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "a")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "A")

        self.screen.onkeypress(lambda: self.set_paddle_intent(1.0), "Right")
        self.screen.onkeypress(lambda: self.set_paddle_intent(1.0), "d")
        self.screen.onkeypress(lambda: self.set_paddle_intent(1.0), "D")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "Right")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "d")
        self.screen.onkeyrelease(lambda: self.set_paddle_intent(0.0), "D")

        self.screen.onkeypress(self.launch_ball, "space")
        self.screen.onkeypress(self.toggle_pause, "p")
        self.screen.onkeypress(self.toggle_pause, "P")
        self.screen.onkeypress(self.reset, "r")
        self.screen.onkeypress(self.reset, "R")

    def set_paddle_intent(self, val: float) -> None:
        self.paddle_move_intent = val

    def reset(self) -> None:
        self.lives = self.config.breakout_lives
        self.score = 0
        self.bricks_cleared = 0
        self.paddle_x = 0.0
        self.reset_ball()
        self.build_bricks()
        self.state = GameState.PLAYING

    def reset_ball(self) -> None:
        self.ball_attached = True
        self.ball_pos = Vector2D(self.paddle_x, self.paddle_y + 18)
        self.ball_vel = Vector2D(0.0, 0.0)

    def launch_ball(self) -> None:
        if self.ball_attached and self.state == GameState.PLAYING:
            self.ball_attached = False
            speed = 7.0
            angle_rad = math.radians(random.uniform(60, 120))
            self.ball_vel = Vector2D(math.cos(angle_rad) * speed, math.sin(angle_rad) * speed)
            self.sound.play("bounce")

    def build_bricks(self) -> None:
        self.bricks.clear()
        theme = self.config.theme
        rows = self.config.breakout_brick_rows
        cols = self.config.breakout_brick_cols

        brick_w = (self.court_half_w * 2 - 40) / cols
        brick_h = 16.0
        start_x = -self.court_half_w + 20 + brick_w / 2
        start_y = self.court_half_h - 45

        row_colors = [theme.warning_color, theme.secondary, theme.accent, theme.primary, "#00b4d8"]

        for r in range(rows):
            y = start_y - r * (brick_h + 6)
            color = row_colors[r % len(row_colors)]
            hp = 2 if r == 0 else 1
            for c in range(cols):
                x = start_x + c * brick_w
                box = AABB(x, y, brick_w / 2 - 2, brick_h / 2)
                self.bricks.append(Brick(box, max_health=hp, color_code=color))

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        # 1. Update paddle
        self.paddle_x += self.paddle_move_intent * self.config.breakout_paddle_speed
        max_px = self.court_half_w - self.paddle_half_w
        self.paddle_x = clamp(self.paddle_x, -max_px, max_px)

        # If ball attached to paddle
        if self.ball_attached:
            self.ball_pos = Vector2D(self.paddle_x, self.paddle_y + 18)
            return

        # 2. Advance ball
        self.ball_pos = self.ball_pos + self.ball_vel

        # 3. Wall collisions (Left, Right, Top)
        if self.ball_pos.x + self.ball_radius >= self.court_half_w:
            self.ball_pos = Vector2D(self.court_half_w - self.ball_radius, self.ball_pos.y)
            self.ball_vel = Vector2D(-abs(self.ball_vel.x), self.ball_vel.y)
            self.sound.play("bounce")
        elif self.ball_pos.x - self.ball_radius <= -self.court_half_w:
            self.ball_pos = Vector2D(-self.court_half_w + self.ball_radius, self.ball_pos.y)
            self.ball_vel = Vector2D(abs(self.ball_vel.x), self.ball_vel.y)
            self.sound.play("bounce")

        if self.ball_pos.y + self.ball_radius >= self.court_half_h:
            self.ball_pos = Vector2D(self.ball_pos.x, self.court_half_h - self.ball_radius)
            self.ball_vel = Vector2D(self.ball_vel.x, -abs(self.ball_vel.y))
            self.sound.play("bounce")

        # 4. Paddle collision
        if self.ball_vel.y < 0:
            collided, normal = check_circle_aabb_collision(self.ball_pos, self.ball_radius, self.paddle_box)
            if collided:
                # Calculate angle deflection based on where ball hits paddle
                offset_x = (self.ball_pos.x - self.paddle_box.center_x) / max(self.paddle_box.half_width, 1.0)
                offset_x = clamp(offset_x, -0.9, 0.9)
                bounce_angle = math.radians(90.0 - (offset_x * 60.0))
                speed = min(self.ball_vel.magnitude * 1.02, 13.0)
                self.ball_vel = Vector2D(math.cos(bounce_angle) * speed, math.sin(bounce_angle) * speed)
                self.ball_pos = Vector2D(self.ball_pos.x, self.paddle_box.max_y + self.ball_radius)
                self.sound.play("hit")

        # 5. Brick collisions
        for brick in self.bricks:
            if brick.is_destroyed:
                continue
            collided, normal = check_circle_aabb_collision(self.ball_pos, self.ball_radius, brick.box)
            if collided and normal:
                self.ball_vel = reflect_velocity(self.ball_vel, normal)
                brick.health -= 1
                if brick.is_destroyed:
                    self.score += 20 * brick.max_health
                    self.bricks_cleared += 1
                    self.sound.play("brick_break")
                else:
                    self.score += 5
                    self.sound.play("hit")
                break

        # Check all bricks cleared (Victory)
        if all(b.is_destroyed for b in self.bricks):
            self.state = GameState.VICTORY
            self.sound.play("game_over")
            self.scoreboard.record_breakout_score(self.player_name, self.score, self.bricks_cleared)
            return

        # 6. Pit floor (Death)
        if self.ball_pos.y < -self.court_half_h - 10:
            self.lives -= 1
            self.sound.play("game_over")
            if self.lives <= 0:
                self.state = GameState.GAME_OVER
                self.scoreboard.record_breakout_score(self.player_name, self.score, self.bricks_cleared)
            else:
                self.reset_ball()

    def render(self) -> None:
        if self.is_headless:
            return

        theme = self.config.theme

        # Paddle
        self.t_paddle.goto(self.paddle_x, self.paddle_y)

        # Ball
        self.t_ball.goto(self.ball_pos.x, self.ball_pos.y)

        # Draw Bricks
        self.t_bricks.clear()
        self.t_bricks.penup()
        for b in self.bricks:
            if b.is_destroyed:
                continue
            self.t_bricks.color(b.color_code)
            self.t_bricks.goto(b.box.min_x, b.box.min_y)
            self.t_bricks.begin_fill()
            self.t_bricks.goto(b.box.max_x, b.box.min_y)
            self.t_bricks.goto(b.box.max_x, b.box.max_y)
            self.t_bricks.goto(b.box.min_x, b.box.max_y)
            self.t_bricks.goto(b.box.min_x, b.box.min_y)
            self.t_bricks.end_fill()

        # HUD
        self.t_hud.clear()
        self.t_hud.color(theme.text_color)
        hud_y = self.court_half_h + 15
        self.t_hud.goto(0, hud_y)
        hearts = "❤️ " * self.lives
        hud_text = f"Score: {self.score}   |   Lives: {hearts}  |   Bricks Left: {sum(1 for b in self.bricks if not b.is_destroyed)}"
        self.t_hud.write(hud_text, align="center", font=("Courier", 13, "bold"))

        if self.ball_attached and self.state == GameState.PLAYING:
            self.t_hud.goto(0, self.paddle_y + 40)
            self.t_hud.color(theme.accent)
            self.t_hud.write("PRESS [SPACE] TO LAUNCH BALL", align="center", font=("Courier", 12, "bold"))

        if self.state == GameState.PAUSED:
            self.t_hud.goto(0, 0)
            self.t_hud.color(theme.warning_color)
            self.t_hud.write("PAUSED\nPress [P] to Resume", align="center", font=("Courier", 22, "bold"))
        elif self.state == GameState.VICTORY:
            self.t_hud.goto(0, 20)
            self.t_hud.color(theme.primary)
            self.t_hud.write(f"VICTORY! All Bricks Cleared!\nFinal Score: {self.score}\nPress [R] to Play Again", align="center", font=("Courier", 18, "bold"))
        elif self.state == GameState.GAME_OVER:
            self.t_hud.goto(0, 20)
            self.t_hud.color(theme.warning_color)
            self.t_hud.write(f"GAME OVER! Score: {self.score}\nPress [R] to Retry", align="center", font=("Courier", 20, "bold"))

        self.screen.update()

    def cleanup(self) -> None:
        if self.is_headless or not self.screen:
            return
        for t in [self.t_paddle, self.t_ball, self.t_bricks, self.t_hud, self.t_border]:
            if t:
                t.clear()
                t.hideturtle()
