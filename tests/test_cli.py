"""Unit tests for command line parsing and configuration defaults."""

import unittest
from unittest.mock import patch
from retro_arcade.cli import parse_arguments


class TestCLI(unittest.TestCase):
    def test_default_arguments(self):
        with patch("sys.argv", ["retro-arcade"]):
            args = parse_arguments()
            self.assertEqual(args.game, "menu")
            self.assertEqual(args.mode, "1p")
            self.assertEqual(args.difficulty, "medium")
            self.assertEqual(args.theme, "neon")
            self.assertFalse(args.mute)
            self.assertFalse(args.leaderboard)

    def test_custom_game_and_flags(self):
        with patch("sys.argv", [
            "retro-arcade",
            "--game", "pong",
            "--mode", "2p",
            "--theme", "synthwave",
            "--mute",
        ]):
            args = parse_arguments()
            self.assertEqual(args.game, "pong")
            self.assertEqual(args.mode, "2p")
            self.assertEqual(args.theme, "synthwave")
            self.assertTrue(args.mute)


if __name__ == "__main__":
    unittest.main()
