"""Retro Pong Game with AI opponents and power-up system."""

from __future__ import annotations
import math
import random
from typing import Optional, List, Dict, Any
from .base import BaseGame, GameState
from ..config import ArcadeConfig
from ..scoreboard import ScoreManager
from ..audio import SoundManager
from ..physics import Vector2D, AABB, check_circle_aabb_collision, calculate_paddle_bounce, clamp
from ..ai import create_ai, BaseAI


class PowerUp:
    def __init__(self, pos: Vector2D, kind: str):
        self.pos = pos
        self.kind = kind  # "expand", "slowmo", "speed"
        self.radius = 12.0
        self.duration = 10.0  # seconds active
        self.collected = False

    @property
    def aabb(self) -> AABB:
        return AABB(self.pos.x, self.pos.y, self.radius, self.radius)


class PongGame(BaseGame):
    """Classic Retro Pong with modern arcade dynamics."""

    def __init__(
        self,
        config: ArcadeConfig,
        scoreboard: ScoreManager,
        sound: SoundManager,
        screen: Optional[Any] = None,
        two_player: bool = False,
        ai_difficulty: Optional[str] = None,
    ):
        super().__init__(config, scoreboard, sound, screen)
        self.two_player = two_player
        self.ai_difficulty = ai_difficulty or config.pong_ai_difficulty
        self.ai: Optional[BaseAI] = None if two_player else create_ai(self.ai_difficulty, config.pong_paddle_speed)

        # Court bounds
        self.court_half_w = (config.window_width - 80) / 2
        self.court_half_h = (config.window_height - 100) / 2
        self.paddle_offset_x = self.court_half_w - 30

        # Paddle dimensions
        self.base_paddle_half_w = 8.0
        self.base_paddle_half_h = 45.0
        self.left_paddle_half_h = self.base_paddle_half_h
        self.right_paddle_half_h = self.base_paddle_half_h

        # Paddle positions
        self.left_paddle_y = 0.0
        self.right_paddle_y = 0.0
        self.left_move_intent = 0.0
        self.right_move_intent = 0.0

        # Ball state
        self.ball_radius = 8.0
        self.ball_pos = Vector2D(0.0, 0.0)
        self.ball_vel = Vector2D(0.0, 0.0)
        self.current_rally = 0
        self.max_rally = 0

        # Scores
        self.left_score = 0
        self.right_score = 0
        self.winner = ""

        # Powerups
        self.active_powerups: List[PowerUp] = []
        self.powerup_timer = 0.0
        self.left_power_duration = 0.0
        self.right_power_duration = 0.0

        # Turtle visuals
        self.t_left_paddle = None
        self.t_right_paddle = None
        self.t_ball = None
        self.t_hud = None
        self.t_court = None
        self.t_powerups = []

    @property
    def left_paddle_box(self) -> AABB:
        return AABB(-self.paddle_offset_x, self.left_paddle_y, self.base_paddle_half_w, self.left_paddle_half_h)

    @property
    def right_paddle_box(self) -> AABB:
        return AABB(self.paddle_offset_x, self.right_paddle_y, self.base_paddle_half_w, self.right_paddle_half_h)

    def setup(self) -> None:
        self.reset()
        if not self.is_headless:
            import turtle

            # Court border and centerline turtle
            self.t_court = turtle.RawTurtle(self.screen)
            self.t_court.hideturtle()
            self.t_court.speed(0)
            self.draw_court_decorations()

            # Left paddle
            self.t_left_paddle = turtle.RawTurtle(self.screen)
            self.t_left_paddle.speed(0)
            self.t_left_paddle.shape("square")
            self.t_left_paddle.color(self.config.theme.primary)
            self.t_left_paddle.penup()
            self.t_left_paddle.shapesize(stretch_wid=self.left_paddle_half_h / 10, stretch_len=self.base_paddle_half_w / 10)

            # Right paddle
            self.t_right_paddle = turtle.RawTurtle(self.screen)
            self.t_right_paddle.speed(0)
            self.t_right_paddle.shape("square")
            self.t_right_paddle.color(self.config.theme.secondary)
            self.t_right_paddle.penup()
            self.t_right_paddle.shapesize(stretch_wid=self.right_paddle_half_h / 10, stretch_len=self.base_paddle_half_w / 10)

            # Ball turtle
            self.t_ball = turtle.RawTurtle(self.screen)
            self.t_ball.speed(0)
            self.t_ball.shape("circle")
            self.t_ball.color(self.config.theme.accent)
            self.t_ball.penup()
            self.t_ball.shapesize(stretch_wid=self.ball_radius / 10, stretch_len=self.ball_radius / 10)

            # HUD
            self.t_hud = turtle.RawTurtle(self.screen)
            self.t_hud.hideturtle()
            self.t_hud.speed(0)
            self.t_hud.penup()

            self.bind_keys()
            self.render()

    def draw_court_decorations(self) -> None:
        if self.is_headless or not self.t_court:
            return
        theme = self.config.theme
        self.t_court.clear()
        self.t_court.penup()
        self.t_court.color(theme.border_color)
        self.t_court.width(3)

        # Outer bounding court
        x0, y0 = -self.court_half_w, -self.court_half_h
        x1, y1 = self.court_half_w, self.court_half_h
        self.t_court.goto(x0, y0)
        self.t_court.pendown()
        for x, y in [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
            self.t_court.goto(x, y)
        self.t_court.penup()

        # Dashed center line
        self.t_court.goto(0, -self.court_half_h)
        self.t_court.setheading(90)
        dash_len = 15
        gap_len = 10
        cur_y = -self.court_half_h
        while cur_y < self.court_half_h:
            self.t_court.pendown()
            self.t_court.forward(dash_len)
            self.t_court.penup()
            self.t_court.forward(gap_len)
            cur_y += dash_len + gap_len

    def bind_keys(self) -> None:
        if self.is_headless or not self.screen:
            return
        self.screen.listen()
        # Player 1 controls (W/S)
        self.screen.onkeypress(lambda: self.set_left_intent(1.0), "w")
        self.screen.onkeypress(lambda: self.set_left_intent(1.0), "W")
        self.screen.onkeyrelease(lambda: self.set_left_intent(0.0), "w")
        self.screen.onkeyrelease(lambda: self.set_left_intent(0.0), "W")

        self.screen.onkeypress(lambda: self.set_left_intent(-1.0), "s")
        self.screen.onkeypress(lambda: self.set_left_intent(-1.0), "S")
        self.screen.onkeyrelease(lambda: self.set_left_intent(0.0), "s")
        self.screen.onkeyrelease(lambda: self.set_left_intent(0.0), "S")

        # Player 2 controls (Up/Down) if in 2-player mode
        if self.two_player:
            self.screen.onkeypress(lambda: self.set_right_intent(1.0), "Up")
            self.screen.onkeyrelease(lambda: self.set_right_intent(0.0), "Up")
            self.screen.onkeypress(lambda: self.set_right_intent(-1.0), "Down")
            self.screen.onkeyrelease(lambda: self.set_right_intent(0.0), "Down")

        self.screen.onkeypress(self.toggle_pause, "p")
        self.screen.onkeypress(self.toggle_pause, "P")
        self.screen.onkeypress(self.reset, "r")
        self.screen.onkeypress(self.reset, "R")

    def set_left_intent(self, val: float) -> None:
        self.left_move_intent = val

    def set_right_intent(self, val: float) -> None:
        self.right_move_intent = val

    def reset(self) -> None:
        self.left_score = 0
        self.right_score = 0
        self.current_rally = 0
        self.max_rally = 0
        self.left_paddle_y = 0.0
        self.right_paddle_y = 0.0
        self.left_paddle_half_h = self.base_paddle_half_h
        self.right_paddle_half_h = self.base_paddle_half_h
        self.active_powerups.clear()
        self.powerup_timer = 0.0
        self.winner = ""
        self.state = GameState.PLAYING
        self.launch_ball(serve_to_left=random.choice([True, False]))

    def launch_ball(self, serve_to_left: bool) -> None:
        self.ball_pos = Vector2D(0.0, 0.0)
        speed = self.config.pong_ball_base_speed
        angle_rad = random.uniform(-math.radians(35), math.radians(35))
        vx = math.cos(angle_rad) * speed * (-1.0 if serve_to_left else 1.0)
        vy = math.sin(angle_rad) * speed
        self.ball_vel = Vector2D(vx, vy)
        self.current_rally = 0

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        # 1. Update Paddles
        paddle_step = self.config.pong_paddle_speed
        # Left paddle
        self.left_paddle_y += self.left_move_intent * paddle_step
        max_y = self.court_half_h - self.left_paddle_half_h
        self.left_paddle_y = clamp(self.left_paddle_y, -max_y, max_y)

        # Right paddle (AI or Player 2)
        if self.two_player:
            self.right_paddle_y += self.right_move_intent * paddle_step
        elif self.ai:
            ai_move = self.ai.calculate_move(
                self.right_paddle_y,
                self.ball_pos,
                self.ball_vel,
                self.court_half_h,
                -self.court_half_h,
                self.paddle_offset_x,
            )
            self.right_paddle_y += ai_move

        max_y_r = self.court_half_h - self.right_paddle_half_h
        self.right_paddle_y = clamp(self.right_paddle_y, -max_y_r, max_y_r)

        # 2. Advance Ball
        self.ball_pos = self.ball_pos + self.ball_vel

        # 3. Top / Bottom Wall Collision
        if self.ball_pos.y + self.ball_radius >= self.court_half_h:
            self.ball_pos = Vector2D(self.ball_pos.x, self.court_half_h - self.ball_radius)
            self.ball_vel = Vector2D(self.ball_vel.x, -abs(self.ball_vel.y))
            self.sound.play("bounce")
        elif self.ball_pos.y - self.ball_radius <= -self.court_half_h:
            self.ball_pos = Vector2D(self.ball_pos.x, -self.court_half_h + self.ball_radius)
            self.ball_vel = Vector2D(self.ball_vel.x, abs(self.ball_vel.y))
            self.sound.play("bounce")

        # 4. Paddle Collisions
        # Left Paddle
        if self.ball_vel.x < 0:
            collided, _ = check_circle_aabb_collision(self.ball_pos, self.ball_radius, self.left_paddle_box)
            if collided:
                self.ball_pos = Vector2D(self.left_paddle_box.max_x + self.ball_radius, self.ball_pos.y)
                cur_speed = min(self.ball_vel.magnitude + self.config.pong_ball_speed_increment, self.config.pong_ball_max_speed)
                temp_vel = self.ball_vel.normalized() * cur_speed
                self.ball_vel = calculate_paddle_bounce(self.ball_pos, temp_vel, self.left_paddle_box, is_left_paddle=True)
                self.current_rally += 1
                self.max_rally = max(self.max_rally, self.current_rally)
                self.sound.play("hit")

        # Right Paddle
        if self.ball_vel.x > 0:
            collided, _ = check_circle_aabb_collision(self.ball_pos, self.ball_radius, self.right_paddle_box)
            if collided:
                self.ball_pos = Vector2D(self.right_paddle_box.min_x - self.ball_radius, self.ball_pos.y)
                cur_speed = min(self.ball_vel.magnitude + self.config.pong_ball_speed_increment, self.config.pong_ball_max_speed)
                temp_vel = self.ball_vel.normalized() * cur_speed
                self.ball_vel = calculate_paddle_bounce(self.ball_pos, temp_vel, self.right_paddle_box, is_left_paddle=False)
                self.current_rally += 1
                self.max_rally = max(self.max_rally, self.current_rally)
                self.sound.play("hit")

        # 5. Goal Scoring Check
        if self.ball_pos.x < -self.court_half_w - 20:
            # Right player scored
            self.right_score += 1
            self.sound.play("score")
            self.check_win_condition(serve_to_left=True)
        elif self.ball_pos.x > self.court_half_w + 20:
            # Left player scored
            self.left_score += 1
            self.sound.play("score")
            self.check_win_condition(serve_to_left=False)

        # 6. Spawn and Update Power-ups
        self.powerup_timer += dt
        if self.powerup_timer >= 12.0 and len(self.active_powerups) < 2:
            self.powerup_timer = 0.0
            spawn_x = random.uniform(-self.court_half_w * 0.5, self.court_half_w * 0.5)
            spawn_y = random.uniform(-self.court_half_h * 0.7, self.court_half_h * 0.7)
            kind = random.choice(["expand", "slowmo", "speed"])
            self.active_powerups.append(PowerUp(Vector2D(spawn_x, spawn_y), kind))

        # Check Power-up collection by ball
        for p in list(self.active_powerups):
            if self.ball_pos.distance_to(p.pos) <= (self.ball_radius + p.radius):
                self.apply_powerup(p)
                self.active_powerups.remove(p)
                self.sound.play("powerup")

    def apply_powerup(self, p: PowerUp) -> None:
        last_hit_left = self.ball_vel.x > 0
        if p.kind == "expand":
            if last_hit_left:
                self.left_paddle_half_h = self.base_paddle_half_h * 1.5
            else:
                self.right_paddle_half_h = self.base_paddle_half_h * 1.5
        elif p.kind == "slowmo":
            self.ball_vel = self.ball_vel.normalized() * self.config.pong_ball_base_speed
        elif p.kind == "speed":
            self.ball_vel = self.ball_vel.normalized() * min(self.ball_vel.magnitude * 1.3, self.config.pong_ball_max_speed)

    def check_win_condition(self, serve_to_left: bool) -> None:
        target = self.config.pong_winning_score
        if self.left_score >= target:
            self.winner = "Player 1 (Left)"
            self.state = GameState.VICTORY
            self.sound.play("game_over")
            self.scoreboard.record_pong_result(self.winner, self.left_score, self.right_score, self.max_rally)
        elif self.right_score >= target:
            self.winner = "Player 2" if self.two_player else f"AI ({self.ai_difficulty.capitalize()})"
            self.state = GameState.GAME_OVER
            self.sound.play("game_over")
            self.scoreboard.record_pong_result(self.winner, self.left_score, self.right_score, self.max_rally)
        else:
            self.launch_ball(serve_to_left)

    def render(self) -> None:
        if self.is_headless:
            return

        # Paddle positions & sizes
        self.t_left_paddle.goto(-self.paddle_offset_x, self.left_paddle_y)
        self.t_left_paddle.shapesize(stretch_wid=self.left_paddle_half_h / 10, stretch_len=self.base_paddle_half_w / 10)

        self.t_right_paddle.goto(self.paddle_offset_x, self.right_paddle_y)
        self.t_right_paddle.shapesize(stretch_wid=self.right_paddle_half_h / 10, stretch_len=self.base_paddle_half_w / 10)

        # Ball position
        self.t_ball.goto(self.ball_pos.x, self.ball_pos.y)

        # Render HUD
        self.t_hud.clear()
        theme = self.config.theme
        self.t_hud.color(theme.text_color)
        hud_y = self.court_half_h + 15

        p2_title = "Player 2" if self.two_player else f"AI [{self.ai_difficulty.upper()}]"
        self.t_hud.goto(0, hud_y)
        hud_text = f"P1: {self.left_score}   |   Rally: {self.current_rally} (Max: {self.max_rally})   |   {p2_title}: {self.right_score}"
        self.t_hud.write(hud_text, align="center", font=("Courier", 13, "bold"))

        # Overlay banners
        if self.state == GameState.PAUSED:
            self.t_hud.goto(0, 0)
            self.t_hud.color(theme.warning_color)
            self.t_hud.write("PAUSED\nPress [P] to Resume", align="center", font=("Courier", 22, "bold"))
        elif self.state in (GameState.VICTORY, GameState.GAME_OVER):
            self.t_hud.goto(0, 30)
            self.t_hud.color(theme.primary if self.state == GameState.VICTORY else theme.warning_color)
            self.t_hud.write(f"VICTORY: {self.winner}!\nPress [R] to Play Again", align="center", font=("Courier", 20, "bold"))

        self.screen.update()

    def cleanup(self) -> None:
        if self.is_headless or not self.screen:
            return
        for t in [self.t_left_paddle, self.t_right_paddle, self.t_ball, self.t_hud, self.t_court]:
            if t:
                t.clear()
                t.hideturtle()
        self.active_powerups.clear()
