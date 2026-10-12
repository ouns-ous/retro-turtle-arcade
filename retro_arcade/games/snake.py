"""Neon Cyber Snake game with special fruits and combo multiplier."""

from __future__ import annotations
import random
from typing import Optional, List, Tuple, Any
from .base import BaseGame, GameState
from ..config import ArcadeConfig
from ..scoreboard import ScoreManager
from ..audio import SoundManager
from ..physics import Vector2D


class FoodItem:
    def __init__(self, grid_x: int, grid_y: int, kind: str = "normal", lifetime: float = 12.0):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.kind = kind  # "normal", "golden", "speed"
        self.lifetime = lifetime
        self.age = 0.0

    @property
    def points(self) -> int:
        if self.kind == "golden":
            return 30
        elif self.kind == "speed":
            return 20
        return 10


class SnakeGame(BaseGame):
    """Neon Cyber Snake with smooth controls and responsive mechanics."""

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
        self.grid_size = config.snake_grid_size
        self.cols = int((config.window_width - 80) // self.grid_size)
        self.rows = int((config.window_height - 100) // self.grid_size)
        self.half_cols = self.cols // 2
        self.half_rows = self.rows // 2

        # State
        self.snake_body: List[Tuple[int, int]] = []
        self.direction: Tuple[int, int] = (1, 0)
        self.pending_direction: Tuple[int, int] = (1, 0)
        self.foods: List[FoodItem] = []
        self.score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.step_interval = self.config.snake_initial_speed_ms / 1000.0
        self.time_since_step = 0.0

        # Turtles
        self.t_snake = None
        self.t_food = None
        self.t_hud = None
        self.t_border = None

    def setup(self) -> None:
        self.reset()
        if not self.is_headless:
            import turtle

            # Border
            self.t_border = turtle.RawTurtle(self.screen)
            self.t_border.hideturtle()
            self.t_border.speed(0)
            self.draw_border()

            # Snake segment renderer
            self.t_snake = turtle.RawTurtle(self.screen)
            self.t_snake.hideturtle()
            self.t_snake.speed(0)

            # Food renderer
            self.t_food = turtle.RawTurtle(self.screen)
            self.t_food.hideturtle()
            self.t_food.speed(0)

            # HUD
            self.t_hud = turtle.RawTurtle(self.screen)
            self.t_hud.hideturtle()
            self.t_hud.speed(0)

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

        min_x = -self.half_cols * self.grid_size
        max_x = self.half_cols * self.grid_size
        min_y = -self.half_rows * self.grid_size
        max_y = self.half_rows * self.grid_size

        self.t_border.goto(min_x, min_y)
        self.t_border.pendown()
        for x, y in [(max_x, min_y), (max_x, max_y), (min_x, max_y), (min_x, min_y)]:
            self.t_border.goto(x, y)
        self.t_border.penup()

    def bind_keys(self) -> None:
        if self.is_headless or not self.screen:
            return
        self.screen.listen()
        # Arrow keys and WASD
        self.screen.onkeypress(lambda: self.change_direction(0, 1), "Up")
        self.screen.onkeypress(lambda: self.change_direction(0, 1), "w")
        self.screen.onkeypress(lambda: self.change_direction(0, 1), "W")

        self.screen.onkeypress(lambda: self.change_direction(0, -1), "Down")
        self.screen.onkeypress(lambda: self.change_direction(0, -1), "s")
        self.screen.onkeypress(lambda: self.change_direction(0, -1), "S")

        self.screen.onkeypress(lambda: self.change_direction(-1, 0), "Left")
        self.screen.onkeypress(lambda: self.change_direction(-1, 0), "a")
        self.screen.onkeypress(lambda: self.change_direction(-1, 0), "A")

        self.screen.onkeypress(lambda: self.change_direction(1, 0), "Right")
        self.screen.onkeypress(lambda: self.change_direction(1, 0), "d")
        self.screen.onkeypress(lambda: self.change_direction(1, 0), "D")

        self.screen.onkeypress(self.toggle_pause, "p")
        self.screen.onkeypress(self.toggle_pause, "P")
        self.screen.onkeypress(self.reset, "r")
        self.screen.onkeypress(self.reset, "R")

    def change_direction(self, dx: int, dy: int) -> None:
        # Prevent 180-degree reversing into own neck
        cur_dx, cur_dy = self.direction
        if (dx == -cur_dx and dx != 0) or (dy == -cur_dy and dy != 0):
            return
        self.pending_direction = (dx, dy)

    def reset(self) -> None:
        start_x, start_y = 0, 0
        self.snake_body = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.direction = (1, 0)
        self.pending_direction = (1, 0)
        self.score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.step_interval = self.config.snake_initial_speed_ms / 1000.0
        self.time_since_step = 0.0
        self.foods.clear()
        self.spawn_food("normal")
        self.state = GameState.PLAYING

    def spawn_food(self, kind: str = "normal") -> None:
        occupied = set(self.snake_body) | {(f.grid_x, f.grid_y) for f in self.foods}
        available = []
        for gx in range(-self.half_cols + 1, self.half_cols):
            for gy in range(-self.half_rows + 1, self.half_rows):
                if (gx, gy) not in occupied:
                    available.append((gx, gy))

        if available:
            gx, gy = random.choice(available)
            lifetime = 10.0 if kind == "golden" else 15.0
            self.foods.append(FoodItem(gx, gy, kind=kind, lifetime=lifetime))

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        # Update combo timer
        if self.combo > 1:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 1

        # Age foods
        for f in list(self.foods):
            if f.kind != "normal":
                f.age += dt
                if f.age >= f.lifetime:
                    self.foods.remove(f)

        # Ensure at least 1 normal food is active
        has_normal = any(f.kind == "normal" for f in self.foods)
        if not has_normal:
            self.spawn_food("normal")

        # Step accumulator
        self.time_since_step += dt
        if self.time_since_step < self.step_interval:
            return

        self.time_since_step = 0.0
        self.step()

    def step(self) -> None:
        self.direction = self.pending_direction
        cur_head_x, cur_head_y = self.snake_body[0]
        dx, dy = self.direction
        new_head_x = cur_head_x + dx
        new_head_y = cur_head_y + dy

        # Wall Collision or Wrap
        if self.config.snake_wrap_walls:
            if new_head_x >= self.half_cols:
                new_head_x = -self.half_cols + 1
            elif new_head_x <= -self.half_cols:
                new_head_x = self.half_cols - 1
            if new_head_y >= self.half_rows:
                new_head_y = -self.half_rows + 1
            elif new_head_y <= -self.half_rows:
                new_head_y = self.half_rows - 1
        else:
            if (
                new_head_x >= self.half_cols
                or new_head_x <= -self.half_cols
                or new_head_y >= self.half_rows
                or new_head_y <= -self.half_rows
            ):
                self.game_over()
                return

        # Self collision (excluding tail if it moves)
        if (new_head_x, new_head_y) in self.snake_body[:-1]:
            self.game_over()
            return

        new_head = (new_head_x, new_head_y)
        self.snake_body.insert(0, new_head)

        # Check food collision
        eaten_food = None
        for f in self.foods:
            if f.grid_x == new_head_x and f.grid_y == new_head_y:
                eaten_food = f
                break

        if eaten_food:
            self.foods.remove(eaten_food)
            self.score += eaten_food.points * self.combo
            self.combo = min(self.combo + 1, 5)
            self.combo_timer = 5.0
            self.sound.play("pickup")

            # Gradually increase speed
            self.step_interval = max(
                self.config.snake_min_speed_ms / 1000.0,
                self.step_interval - (self.config.snake_speed_decrement_ms / 1000.0),
            )

            # Spawn next normal food
            self.spawn_food("normal")

            # Chance to spawn bonus food
            if random.random() < 0.35 and len(self.foods) < 3:
                kind = random.choice(["golden", "speed"])
                self.spawn_food(kind)
        else:
            # Did not eat: pop tail
            self.snake_body.pop()

    def game_over(self) -> None:
        self.state = GameState.GAME_OVER
        self.sound.play("game_over")
        self.scoreboard.record_snake_score(self.player_name, self.score, len(self.snake_body))

    def render(self) -> None:
        if self.is_headless:
            return

        theme = self.config.theme

        # Draw Foods
        self.t_food.clear()
        self.t_food.penup()
        for f in self.foods:
            px = f.grid_x * self.grid_size
            py = f.grid_y * self.grid_size
            if f.kind == "golden":
                self.t_food.color(theme.accent)
            elif f.kind == "speed":
                self.t_food.color(theme.secondary)
            else:
                self.t_food.color(theme.primary)

            self.t_food.goto(px, py)
            self.t_food.dot(self.grid_size - 2)

        # Draw Snake
        self.t_snake.clear()
        self.t_snake.penup()
        for i, (gx, gy) in enumerate(self.snake_body):
            px = gx * self.grid_size
            py = gy * self.grid_size
            self.t_snake.goto(px, py)
            if i == 0:
                self.t_snake.color(theme.primary)
                self.t_snake.dot(self.grid_size + 2)
            else:
                self.t_snake.color(theme.secondary if i % 2 == 0 else theme.primary)
                self.t_snake.dot(self.grid_size - 4)

        # Draw HUD
        self.t_hud.clear()
        self.t_hud.penup()
        self.t_hud.color(theme.text_color)
        hud_y = (self.half_rows * self.grid_size) + 15
        self.t_hud.goto(0, hud_y)
        combo_str = f" [Combo x{self.combo}]" if self.combo > 1 else ""
        hud_text = f"Score: {self.score}{combo_str}   |   Length: {len(self.snake_body)}   |   High: {self.scoreboard.data['snake'].get('high_score', 0)}"
        self.t_hud.write(hud_text, align="center", font=("Courier", 13, "bold"))

        if self.state == GameState.PAUSED:
            self.t_hud.goto(0, 0)
            self.t_hud.color(theme.warning_color)
            self.t_hud.write("PAUSED\nPress [P] to Resume", align="center", font=("Courier", 22, "bold"))
        elif self.state == GameState.GAME_OVER:
            self.t_hud.goto(0, 30)
            self.t_hud.color(theme.warning_color)
            self.t_hud.write(f"GAME OVER! Score: {self.score}\nPress [R] to Restart", align="center", font=("Courier", 20, "bold"))

        self.screen.update()

    def cleanup(self) -> None:
        if self.is_headless or not self.screen:
            return
        for t in [self.t_snake, self.t_food, self.t_hud, self.t_border]:
            if t:
                t.clear()
                t.hideturtle()
