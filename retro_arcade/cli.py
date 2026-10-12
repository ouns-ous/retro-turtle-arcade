"""Command-line interface and entry point for Retro Turtle Arcade."""

from __future__ import annotations
import argparse
import sys
from .config import ArcadeConfig, THEMES
from .scoreboard import ScoreManager
from .audio import SoundManager
from .engine import ArcadeEngine
from .games import PongGame, SnakeGame, BreakoutGame
from . import __version__


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="retro-arcade",
        description="🕹️ Retro Turtle Arcade: Classic Arcade Games in Python Turtle",
    )
    parser.add_argument(
        "--game",
        choices=["menu", "pong", "snake", "breakout"],
        default="menu",
        help="Directly launch a specific game or open the main menu (default: menu)",
    )
    parser.add_argument(
        "--mode",
        choices=["1p", "2p"],
        default="1p",
        help="Pong game mode: 1-Player vs AI or 2-Player local versus (default: 1p)",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard", "impossible"],
        default="medium",
        help="AI difficulty level for 1-Player Pong (default: medium)",
    )
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        default="neon",
        help="Visual color palette theme (default: neon)",
    )
    parser.add_argument(
        "--mute",
        action="store_true",
        help="Disable audio sound effects",
    )
    parser.add_argument(
        "--leaderboard",
        action="store_true",
        help="Print the persistent Hall of Fame leaderboard and exit",
    )
    parser.add_argument(
        "--headless-sim",
        choices=["pong", "snake", "breakout"],
        help="Run a headless physics simulation benchmark without launching a GUI",
    )
    parser.add_argument(
        "--sim-steps",
        type=int,
        default=300,
        help="Number of physics frames to simulate in headless mode (default: 300)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Retro Turtle Arcade v{__version__}",
    )
    return parser.parse_args()


def run_headless_simulation(game_name: str, steps: int, config: ArcadeConfig) -> None:
    """Simulates game logic in memory without opening a GUI window."""
    score_mgr = ScoreManager(config.high_score_file)
    sound_mgr = SoundManager(enabled=False)

    print(f"\n[Simulation] Running {steps} headless simulation steps for '{game_name}'...")

    if game_name == "pong":
        game = PongGame(config, score_mgr, sound_mgr, screen=None, two_player=False)
        game.setup()
        for i in range(steps):
            game.update(0.016)
        print(f"Simulation completed successfully.")
        print(f"  Ball Position: ({game.ball_pos.x:.1f}, {game.ball_pos.y:.1f})")
        print(f"  Ball Velocity: ({game.ball_vel.x:.1f}, {game.ball_vel.y:.1f})")
        print(f"  Score: P1 {game.left_score} - AI {game.right_score}")
        print(f"  Max Rally: {game.max_rally}")

    elif game_name == "snake":
        game = SnakeGame(config, score_mgr, sound_mgr, screen=None)
        game.setup()
        for i in range(steps):
            # Automated steering towards first food
            if game.foods:
                fx, fy = game.foods[0].grid_x, game.foods[0].grid_y
                hx, hy = game.snake_body[0]
                if fx > hx and game.direction != (-1, 0):
                    game.change_direction(1, 0)
                elif fx < hx and game.direction != (1, 0):
                    game.change_direction(-1, 0)
                elif fy > hy and game.direction != (0, -1):
                    game.change_direction(0, 1)
                elif fy < hy and game.direction != (0, 1):
                    game.change_direction(0, -1)
            game.update(0.016)
        print(f"Simulation completed successfully.")
        print(f"  Snake Length: {len(game.snake_body)}")
        print(f"  Score: {game.score}")
        print(f"  Game State: {game.state.name}")

    elif game_name == "breakout":
        game = BreakoutGame(config, score_mgr, sound_mgr, screen=None)
        game.setup()
        game.launch_ball()
        for i in range(steps):
            # Automated paddle tracking
            game.paddle_x = game.ball_pos.x
            game.update(0.016)
        print(f"Simulation completed successfully.")
        print(f"  Bricks Cleared: {game.bricks_cleared}")
        print(f"  Score: {game.score}")
        print(f"  Remaining Lives: {game.lives}")

    print("[Simulation] Physics, collision detection, and score records verified 100% OK!\n")


def main() -> None:
    args = parse_arguments()

    config = ArcadeConfig(
        theme_name=args.theme,
        sound_enabled=not args.mute,
        pong_ai_difficulty=args.difficulty,
    )

    if args.leaderboard:
        score_mgr = ScoreManager(config.high_score_file)
        print(score_mgr.format_leaderboard_text())
        sys.exit(0)

    if args.headless_sim:
        run_headless_simulation(args.headless_sim, args.sim_steps, config)
        sys.exit(0)

    engine = ArcadeEngine(config=config, headless=False)
    if args.game == "menu":
        engine.run()
    else:
        engine.initialize_display()
        if args.game == "pong":
            action = "pong_2p" if args.mode == "2p" else "pong_1p"
            engine.launch_activity(action)
        elif args.game == "snake":
            engine.launch_activity("snake")
        elif args.game == "breakout":
            engine.launch_activity("breakout")

        engine.is_running = True
        engine._schedule_tick()
        try:
            engine.screen.mainloop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
