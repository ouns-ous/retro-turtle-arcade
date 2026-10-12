"""Unit tests for Pong, Snake, and Breakout game logic in headless mode."""

import unittest
import tempfile
import os
from retro_arcade.config import ArcadeConfig
from retro_arcade.scoreboard import ScoreManager
from retro_arcade.audio import SoundManager
from retro_arcade.games import PongGame, SnakeGame, BreakoutGame, GameState
from retro_arcade.physics import Vector2D


class TestHeadlessGames(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        score_file = os.path.join(self.tmp_dir.name, "scores.json")
        self.config = ArcadeConfig(high_score_file=score_file)
        self.scoreboard = ScoreManager(score_file)
        self.sound = SoundManager(enabled=False)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_pong_game_headless_lifecycle(self):
        game = PongGame(self.config, self.scoreboard, self.sound, screen=None, two_player=False)
        game.setup()
        self.assertEqual(game.state, GameState.PLAYING)
        self.assertEqual(game.left_score, 0)
        self.assertEqual(game.right_score, 0)

        # Move left paddle
        game.set_left_intent(1.0)
        game.update(0.016)
        self.assertGreater(game.left_paddle_y, 0.0)

        # Pause and resume
        game.toggle_pause()
        self.assertEqual(game.state, GameState.PAUSED)
        game.toggle_pause()
        self.assertEqual(game.state, GameState.PLAYING)

        # Scoring trigger
        game.ball_pos = Vector2D(game.court_half_w + 30, 0.0)
        game.update(0.016)
        self.assertEqual(game.left_score, 1)

        # Win condition trigger
        game.left_score = self.config.pong_winning_score - 1
        game.ball_pos = Vector2D(game.court_half_w + 30, 0.0)
        game.update(0.016)
        self.assertEqual(game.state, GameState.VICTORY)
        self.assertIn("Player 1", game.winner)

        game.cleanup()

    def test_snake_game_headless_lifecycle(self):
        game = SnakeGame(self.config, self.scoreboard, self.sound, screen=None)
        game.setup()
        self.assertEqual(game.state, GameState.PLAYING)
        self.assertEqual(len(game.snake_body), 3)

        # Advance snake
        initial_head = game.snake_body[0]
        # Run enough dt to trigger step
        game.update(game.step_interval + 0.01)
        new_head = game.snake_body[0]
        self.assertEqual(new_head, (initial_head[0] + 1, initial_head[1]))

        # Eat food
        food = game.foods[0]
        # Place head directly in front of food
        game.snake_body = [(food.grid_x - 1, food.grid_y), (food.grid_x - 2, food.grid_y)]
        game.direction = (1, 0)
        game.pending_direction = (1, 0)
        game.time_since_step = game.step_interval
        game.update(0.01)
        self.assertGreater(game.score, 0)
        self.assertEqual(game.snake_body[0], (food.grid_x, food.grid_y))

        # Wall collision
        game.config.snake_wrap_walls = False
        game.snake_body = [(game.half_cols - 1, 0), (game.half_cols - 2, 0)]
        game.direction = (1, 0)
        game.pending_direction = (1, 0)
        game.time_since_step = game.step_interval
        game.update(0.01)
        self.assertEqual(game.state, GameState.GAME_OVER)

        game.cleanup()

    def test_breakout_game_headless_lifecycle(self):
        game = BreakoutGame(self.config, self.scoreboard, self.sound, screen=None)
        game.setup()
        self.assertEqual(game.state, GameState.PLAYING)
        self.assertTrue(game.ball_attached)
        self.assertEqual(len(game.bricks), self.config.breakout_brick_rows * self.config.breakout_brick_cols)

        # Move paddle
        game.set_paddle_intent(1.0)
        game.update(0.016)
        self.assertGreater(game.paddle_x, 0.0)

        # Launch ball
        game.launch_ball()
        self.assertFalse(game.ball_attached)
        self.assertGreater(game.ball_vel.magnitude, 0.0)

        # Ball pit fall (Lose life)
        game.ball_pos = Vector2D(0.0, -game.court_half_h - 20)
        game.update(0.016)
        self.assertEqual(game.lives, self.config.breakout_lives - 1)
        self.assertTrue(game.ball_attached)

        game.cleanup()


if __name__ == "__main__":
    unittest.main()
