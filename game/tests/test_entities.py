import unittest

from game.entities import Ship, circle_hits_rect


class EntityTests(unittest.TestCase):
    def test_ship_stays_inside_screen_after_movement(self) -> None:
        ship = Ship(x=10, y=500, width=60, height=48, speed=500)

        ship.move(direction=-1.0, dt=1.0, screen_width=960)
        self.assertEqual(ship.x, 0)
        ship.move(direction=1.0, dt=3.0, screen_width=960)
        self.assertEqual(ship.x, 900)

    def test_circle_rect_collision_detects_hit_and_near_miss(self) -> None:
        rect = (100, 100, 60, 48)

        self.assertTrue(circle_hits_rect(130, 100, 15, rect))
        self.assertFalse(circle_hits_rect(50, 50, 10, rect))
