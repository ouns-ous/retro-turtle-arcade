"""Unit tests for 2D Vector math and collision physics."""

import unittest
import math
from retro_arcade.physics import (
    Vector2D,
    AABB,
    clamp,
    check_aabb_collision,
    check_circle_aabb_collision,
    reflect_velocity,
    calculate_paddle_bounce,
)


class TestVector2D(unittest.TestCase):
    def test_arithmetic(self):
        v1 = Vector2D(3.0, 4.0)
        v2 = Vector2D(1.0, 2.0)

        # Addition
        v_add = v1 + v2
        self.assertEqual(v_add, Vector2D(4.0, 6.0))

        # Subtraction
        v_sub = v1 - v2
        self.assertEqual(v_sub, Vector2D(2.0, 2.0))

        # Multiplication
        v_mul = v1 * 2.0
        self.assertEqual(v_mul, Vector2D(6.0, 8.0))
        self.assertEqual(2.0 * v1, Vector2D(6.0, 8.0))

        # Division
        v_div = v1 / 2.0
        self.assertEqual(v_div, Vector2D(1.5, 2.0))

        # Negation
        self.assertEqual(-v1, Vector2D(-3.0, -4.0))

    def test_division_by_zero(self):
        v = Vector2D(1.0, 1.0)
        with self.assertRaises(ZeroDivisionError):
            _ = v / 0.0

    def test_magnitude_and_normalized(self):
        v = Vector2D(3.0, 4.0)
        self.assertEqual(v.magnitude_squared, 25.0)
        self.assertEqual(v.magnitude, 5.0)

        v_norm = v.normalized()
        self.assertAlmostEqual(v_norm.x, 0.6)
        self.assertAlmostEqual(v_norm.y, 0.8)
        self.assertAlmostEqual(v_norm.magnitude, 1.0)

        v_zero = Vector2D(0.0, 0.0).normalized()
        self.assertEqual(v_zero, Vector2D(0.0, 0.0))

    def test_dot_and_distance(self):
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        self.assertEqual(v1.dot(v2), 0.0)

        v3 = Vector2D(3.0, 4.0)
        v4 = Vector2D(0.0, 0.0)
        self.assertEqual(v3.distance_to(v4), 5.0)


class TestCollisionPhysics(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(5.0, 0.0, 10.0), 5.0)
        self.assertEqual(clamp(-5.0, 0.0, 10.0), 0.0)
        self.assertEqual(clamp(15.0, 0.0, 10.0), 10.0)

    def test_aabb_overlap(self):
        box1 = AABB(center_x=0.0, center_y=0.0, half_width=10.0, half_height=10.0)
        box2 = AABB(center_x=15.0, center_y=0.0, half_width=10.0, half_height=10.0)
        box3 = AABB(center_x=30.0, center_y=0.0, half_width=10.0, half_height=10.0)

        self.assertTrue(check_aabb_collision(box1, box2))
        self.assertFalse(check_aabb_collision(box1, box3))
        self.assertTrue(box1.contains_point(Vector2D(5.0, 5.0)))
        self.assertFalse(box1.contains_point(Vector2D(15.0, 5.0)))

    def test_circle_aabb_collision(self):
        box = AABB(center_x=0.0, center_y=0.0, half_width=20.0, half_height=20.0)
        # Hits top edge
        hit, normal = check_circle_aabb_collision(Vector2D(0.0, 25.0), radius=10.0, box=box)
        self.assertTrue(hit)
        self.assertIsNotNone(normal)
        self.assertAlmostEqual(normal.y, 1.0, places=3)

        # Far away miss
        miss, _ = check_circle_aabb_collision(Vector2D(50.0, 50.0), radius=5.0, box=box)
        self.assertFalse(miss)

    def test_reflect_velocity(self):
        vel = Vector2D(10.0, -10.0)
        normal = Vector2D(0.0, 1.0)  # Horizontal surface facing up
        reflected = reflect_velocity(vel, normal)
        self.assertAlmostEqual(reflected.x, 10.0)
        self.assertAlmostEqual(reflected.y, 10.0)

    def test_paddle_bounce_angular_deflection(self):
        paddle = AABB(center_x=-300.0, center_y=0.0, half_width=10.0, half_height=50.0)
        ball_vel = Vector2D(-6.0, 0.0)

        # Hit dead center
        bounce_center = calculate_paddle_bounce(
            ball_pos=Vector2D(-290.0, 0.0),
            ball_vel=ball_vel,
            paddle_box=paddle,
            is_left_paddle=True,
        )
        self.assertGreater(bounce_center.x, 0.0)
        self.assertAlmostEqual(bounce_center.y, 0.0, places=3)

        # Hit top edge
        bounce_top = calculate_paddle_bounce(
            ball_pos=Vector2D(-290.0, 45.0),
            ball_vel=ball_vel,
            paddle_box=paddle,
            is_left_paddle=True,
        )
        self.assertGreater(bounce_top.x, 0.0)
        self.assertGreater(bounce_top.y, 0.0)


if __name__ == "__main__":
    unittest.main()
