"""Unit tests for persistent scoreboard and high score records."""

import unittest
import os
import tempfile
from retro_arcade.scoreboard import ScoreManager


class TestScoreManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.score_file = os.path.join(self.tmp_dir.name, "test_scores.json")
        self.mgr = ScoreManager(self.score_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_initial_structure(self):
        self.assertEqual(self.mgr.data["pong"]["player_wins"], 0)
        self.assertEqual(self.mgr.data["snake"]["high_score"], 0)
        self.assertEqual(self.mgr.data["breakout"]["high_score"], 0)

    def test_record_pong_result(self):
        self.mgr.record_pong_result("Player 1", 5, 3, 12)
        self.assertEqual(self.mgr.data["pong"]["player_wins"], 1)
        self.assertEqual(self.mgr.data["pong"]["high_rally"], 12)

        # Reload from disk
        reloaded = ScoreManager(self.score_file)
        self.assertEqual(reloaded.data["pong"]["player_wins"], 1)
        self.assertEqual(reloaded.data["pong"]["high_rally"], 12)

    def test_record_snake_score(self):
        is_high = self.mgr.record_snake_score("CyberAce", 150, 15)
        self.assertTrue(is_high)
        self.assertEqual(self.mgr.data["snake"]["high_score"], 150)
        self.assertEqual(self.mgr.data["snake"]["longest_length"], 15)

        # Lower score should not be new high
        is_high_lower = self.mgr.record_snake_score("CyberAce", 80, 8)
        self.assertFalse(is_high_lower)
        self.assertEqual(self.mgr.data["snake"]["high_score"], 150)

    def test_record_breakout_score(self):
        is_high = self.mgr.record_breakout_score("BrickMaster", 500, 25)
        self.assertTrue(is_high)
        self.assertEqual(self.mgr.data["breakout"]["high_score"], 500)
        self.assertEqual(self.mgr.data["breakout"]["max_bricks_cleared"], 25)

    def test_format_leaderboard_text(self):
        self.mgr.record_snake_score("PlayerOne", 120, 10)
        text = self.mgr.format_leaderboard_text()
        self.assertIn("RETRO TURTLE ARCADE - HALL OF FAME", text)
        self.assertIn("PlayerOne", text)
        self.assertIn("120", text)


if __name__ == "__main__":
    unittest.main()
