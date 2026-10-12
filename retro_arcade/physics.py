"""2D Vector math and collision physics engine for arcade games."""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple, Optional


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, val))


@dataclass(frozen=True)
class Vector2D:
    """Immutable 2D Vector with arithmetic operations."""
    x: float
    y: float

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2D:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector2D:
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Vector2D by zero.")
        return Vector2D(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2D:
        return Vector2D(-self.x, -self.y)

    @property
    def magnitude_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.magnitude_squared)

    def normalized(self) -> Vector2D:
        mag = self.magnitude
        if mag == 0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / mag, self.y / mag)

    def dot(self, other: Vector2D) -> float:
        return self.x * other.x + self.y * other.y

    def distance_to(self, other: Vector2D) -> float:
        return (self - other).magnitude

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class AABB:
    """Axis-Aligned Bounding Box for rectangular collision detection."""
    center_x: float
    center_y: float
    half_width: float
    half_height: float

    @property
    def min_x(self) -> float:
        return self.center_x - self.half_width

    @property
    def max_x(self) -> float:
        return self.center_x + self.half_width

    @property
    def min_y(self) -> float:
        return self.center_y - self.half_height

    @property
    def max_y(self) -> float:
        return self.center_y + self.half_height

    @property
    def width(self) -> float:
        return self.half_width * 2

    @property
    def height(self) -> float:
        return self.half_height * 2

    def contains_point(self, pt: Vector2D) -> bool:
        return (
            self.min_x <= pt.x <= self.max_x
            and self.min_y <= pt.y <= self.max_y
        )

    def overlaps(self, other: AABB) -> bool:
        if abs(self.center_x - other.center_x) > (self.half_width + other.half_width):
            return False
        if abs(self.center_y - other.center_y) > (self.half_height + other.half_height):
            return False
        return True


def check_aabb_collision(a: AABB, b: AABB) -> bool:
    """Check if two AABBs overlap."""
    return a.overlaps(b)


def check_circle_aabb_collision(
    circle_center: Vector2D, radius: float, box: AABB
) -> Tuple[bool, Optional[Vector2D]]:
    """
    Test collision between circle and AABB.
    Returns (collided, normal_vector_of_impact).
    """
    closest_x = clamp(circle_center.x, box.min_x, box.max_x)
    closest_y = clamp(circle_center.y, box.min_y, box.max_y)

    diff_x = circle_center.x - closest_x
    diff_y = circle_center.y - closest_y

    dist_sq = diff_x * diff_x + diff_y * diff_y
    if dist_sq <= radius * radius:
        dist = math.sqrt(dist_sq)
        if dist > 0.0001:
            normal = Vector2D(diff_x / dist, diff_y / dist)
        else:
            # Circle center is inside box; pick normal based on closest edge
            dist_to_left = abs(circle_center.x - box.min_x)
            dist_to_right = abs(box.max_x - circle_center.x)
            dist_to_bottom = abs(circle_center.y - box.min_y)
            dist_to_top = abs(box.max_y - circle_center.y)
            min_dist = min(dist_to_left, dist_to_right, dist_to_bottom, dist_to_top)
            if min_dist == dist_to_left:
                normal = Vector2D(-1.0, 0.0)
            elif min_dist == dist_to_right:
                normal = Vector2D(1.0, 0.0)
            elif min_dist == dist_to_bottom:
                normal = Vector2D(0.0, -1.0)
            else:
                normal = Vector2D(0.0, 1.0)
        return True, normal

    return False, None


def reflect_velocity(vel: Vector2D, normal: Vector2D) -> Vector2D:
    """
    Reflect velocity vector across surface normal: v' = v - 2(v . n)n
    """
    n = normal.normalized()
    dot = vel.dot(n)
    return vel - (2.0 * dot) * n


def calculate_paddle_bounce(
    ball_pos: Vector2D,
    ball_vel: Vector2D,
    paddle_box: AABB,
    is_left_paddle: bool,
    max_bounce_angle_deg: float = 65.0,
) -> Vector2D:
    """
    Calculate realistic Pong paddle bounce where angle varies based on
    where on the paddle the ball hits (center vs edges).
    """
    # Relative intersect y: -1.0 (bottom edge) to +1.0 (top edge)
    offset_y = (ball_pos.y - paddle_box.center_y) / max(paddle_box.half_height, 1.0)
    offset_y = clamp(offset_y, -1.0, 1.0)

    bounce_angle_rad = offset_y * math.radians(max_bounce_angle_deg)
    speed = ball_vel.magnitude

    dir_x = math.cos(bounce_angle_rad)
    dir_y = math.sin(bounce_angle_rad)

    if not is_left_paddle:
        dir_x = -abs(dir_x)
    else:
        dir_x = abs(dir_x)

    new_vel = Vector2D(dir_x, dir_y).normalized() * speed
    return new_vel
