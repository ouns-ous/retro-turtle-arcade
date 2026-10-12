"""Interactive Retro Arcade Cabinet Hub and Menu System."""

from __future__ import annotations
from typing import Optional, List, Callable, Any
from .config import ArcadeConfig
from .audio import SoundManager
from .scoreboard import ScoreManager


class ArcadeMenu:
    """Retro Arcade Main Menu rendered with Turtle."""

    MENU_ITEMS = [
        ("1. RETRO PONG (1P VS AI)", "pong_1p"),
        ("2. RETRO PONG (2P LOCAL)", "pong_2p"),
        ("3. NEON CYBER SNAKE", "snake"),
        ("4. QUANTUM BREAKOUT", "breakout"),
        ("5. HALL OF FAME (SCORES)", "leaderboard"),
        ("6. EXIT ARCADE", "exit"),
    ]

    def __init__(
        self,
        config: ArcadeConfig,
        sound: SoundManager,
        scoreboard: ScoreManager,
        screen: Optional[Any] = None,
        on_select: Optional[Callable[[str], None]] = None,
    ):
        self.config = config
        self.sound = sound
        self.scoreboard = scoreboard
        self.screen = screen
        self.on_select = on_select
        self.selected_index = 0
        self.showing_leaderboard = False

        self.t_menu = None

    def setup(self) -> None:
        if not self.screen:
            return
        import turtle

        self.t_menu = turtle.RawTurtle(self.screen)
        self.t_menu.hideturtle()
        self.t_menu.speed(0)

        self.bind_keys()
        self.render()

    def bind_keys(self) -> None:
        if not self.screen:
            return
        self.screen.listen()
        self.screen.onkeypress(self.move_up, "Up")
        self.screen.onkeypress(self.move_up, "w")
        self.screen.onkeypress(self.move_up, "W")

        self.screen.onkeypress(self.move_down, "Down")
        self.screen.onkeypress(self.move_down, "s")
        self.screen.onkeypress(self.move_down, "S")

        self.screen.onkeypress(self.activate_selection, "Return")
        self.screen.onkeypress(self.activate_selection, "space")
        self.screen.onkeypress(self.handle_back, "Escape")

    def move_up(self) -> None:
        if self.showing_leaderboard:
            return
        self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
        self.sound.play("menu_select")
        self.render()

    def move_down(self) -> None:
        if self.showing_leaderboard:
            return
        self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)
        self.sound.play("menu_select")
        self.render()

    def handle_back(self) -> None:
        if self.showing_leaderboard:
            self.showing_leaderboard = False
            self.sound.play("bounce")
            self.render()

    def activate_selection(self) -> None:
        if self.showing_leaderboard:
            self.showing_leaderboard = False
            self.render()
            return

        _, action = self.MENU_ITEMS[self.selected_index]
        self.sound.play("pickup")

        if action == "leaderboard":
            self.showing_leaderboard = True
            self.render()
            return

        if self.on_select:
            self.on_select(action)

    def render(self) -> None:
        if not self.t_menu or not self.screen:
            return

        theme = self.config.theme
        self.t_menu.clear()
        self.t_menu.penup()

        if self.showing_leaderboard:
            self.render_leaderboard()
            self.screen.update()
            return

        # Title
        self.t_menu.goto(0, 190)
        self.t_menu.color(theme.primary)
        self.t_menu.write("================================", align="center", font=("Courier", 14, "bold"))
        self.t_menu.goto(0, 160)
        self.t_menu.color(theme.accent)
        self.t_menu.write("RETRO TURTLE ARCADE", align="center", font=("Courier", 26, "bold"))
        self.t_menu.goto(0, 135)
        self.t_menu.color(theme.primary)
        self.t_menu.write("================================", align="center", font=("Courier", 14, "bold"))

        self.t_menu.goto(0, 105)
        self.t_menu.color(theme.secondary)
        self.t_menu.write("Select a game using [UP/DOWN] or [W/S] and press [ENTER]", align="center", font=("Courier", 11, "normal"))

        # Menu options
        start_y = 40
        spacing = 42
        for idx, (label, _) in enumerate(self.MENU_ITEMS):
            y = start_y - (idx * spacing)
            self.t_menu.goto(0, y)
            if idx == self.selected_index:
                self.t_menu.color(theme.accent)
                display_text = f"▶  {label}  ◀"
                font_weight = "bold"
            else:
                self.t_menu.color(theme.text_color)
                display_text = f"   {label}   "
                font_weight = "normal"
            self.t_menu.write(display_text, align="center", font=("Courier", 15, font_weight))

        # Footer
        self.t_menu.goto(0, -230)
        self.t_menu.color(theme.border_color)
        self.t_menu.write("Theme: " + theme.name + " | Built with Python Standard Library", align="center", font=("Courier", 10, "italic"))

        self.screen.update()

    def render_leaderboard(self) -> None:
        theme = self.config.theme
        self.t_menu.goto(0, 200)
        self.t_menu.color(theme.accent)
        self.t_menu.write("HALL OF FAME / HIGH SCORES", align="center", font=("Courier", 20, "bold"))

        self.t_menu.goto(0, 150)
        self.t_menu.color(theme.primary)
        pong_stats = self.scoreboard.data.get("pong", {})
        self.t_menu.write(
            f"Pong: Player Wins: {pong_stats.get('player_wins', 0)} | AI Wins: {pong_stats.get('ai_wins', 0)} | Best Rally: {pong_stats.get('high_rally', 0)}",
            align="center",
            font=("Courier", 12, "bold"),
        )

        self.t_menu.goto(0, 110)
        self.t_menu.color(theme.secondary)
        snake_stats = self.scoreboard.data.get("snake", {})
        self.t_menu.write(
            f"Snake High Score: {snake_stats.get('high_score', 0)} pts | Longest Snake: {snake_stats.get('longest_length', 3)}",
            align="center",
            font=("Courier", 12, "bold"),
        )

        self.t_menu.goto(0, 70)
        self.t_menu.color(theme.primary)
        bk_stats = self.scoreboard.data.get("breakout", {})
        self.t_menu.write(
            f"Breakout High Score: {bk_stats.get('high_score', 0)} pts | Max Bricks: {bk_stats.get('max_bricks_cleared', 0)}",
            align="center",
            font=("Courier", 12, "bold"),
        )

        self.t_menu.goto(0, -180)
        self.t_menu.color(theme.warning_color)
        self.t_menu.write("Press [SPACE] or [ESC] to Return to Menu", align="center", font=("Courier", 14, "bold"))

    def cleanup(self) -> None:
        if self.t_menu:
            self.t_menu.clear()
            self.t_menu.hideturtle()
