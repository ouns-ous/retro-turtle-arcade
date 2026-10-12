"""Unit tests for Pong paddle AI controllers and trajectory prediction."""

import unittest
from retro_arcade.physics import Vector2D
from retro_arcade.ai import (
    create_ai,
    EasyAI,
    MediumAI,
    HardAI,
    ImpossibleAI,
    predict_ball_y,
)


class TestPaddleAI(unittest.TestCase):
    def test_factory(self):
        ai_easy = create_ai("easy", 30.0)
        self.assertIsInstance(ai_easy, EasyAI)

        ai_med = create_ai("medium", 30.0)
        self.assertIsInstance(ai_med, MediumAI)

        ai_hard = create_ai("hard", 30.0)
        self.assertIsInstance(ai_hard, HardAI)

        ai_imp = create_ai("impossible", 30.0)
        self.assertIsInstance(ai_imp, ImpossibleAI)

        ai_def = create_ai("unknown", 30.0)
        self.assertIsInstance(ai_def, MediumAI)

    def test_trajectory_prediction_straight(self):
        # Ball moving horizontally with vy = 0
        ball_pos = Vector2D(0.0, 50.0)
        ball_vel = Vector2D(10.0, 0.0)
        target_x = 200.0

        predicted_y = predict_ball_y(
            ball_pos=ball_pos,
            ball_vel=ball_vel,
            target_x=target_x,
            court_top=250.0,
            court_bottom=-250.0,
        )
        self.assertAlmostEqual(predicted_y, 50.0, places=1)

    def test_trajectory_prediction_with_wall_bounce(self):
        # Ball bouncing off the top wall
        ball_pos = Vector2D(0.0, 200.0)
        ball_vel = Vector2D(10.0, 10.0)
        target_x = 100.0

        predicted_y = predict_ball_y(
            ball_pos=ball_pos,
            ball_vel=ball_vel,
            target_x=target_x,
            court_top=250.0,
            court_bottom=-250.0,
        )
        # Without boundary, projected would be 200 + 10*(10) = 300
        # Wall is at 250, so bounced down by 50 => 200.0
        self.assertAlmostEqual(predicted_y, 200.0, places=1)

    def test_ai_movement_directions(self):
        ai = create_ai("hard", 30.0)
        # Ball approaching AI on the right, high up
        move_up = ai.calculate_move(
            paddle_y=0.0,
            ball_pos=Vector2D(100.0, 100.0),
            ball_vel=Vector2D(8.0, 2.0),
            court_top=250.0,
            court_bottom=-250.0,
            paddle_x=300.0,
        )
        self.assertGreater(move_up, 0.0)

        # Ball approaching AI low down
        move_down = ai.calculate_move(
            paddle_y=0.0,
            ball_pos=Vector2D(100.0, -100.0),
            ball_vel=Vector2D(8.0, -2.0),
            court_top=250.0,
            court_bottom=-250.0,
            paddle_x=300.0,
        )
        self.assertLess(move_down, 0.0)


if __name__ == "__main__":
    unittest.main()
