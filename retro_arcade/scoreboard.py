"""Persistent high score and player statistics manager."""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from datetime import datetime


@dataclass
class ScoreEntry:
    player: str
    score: int
    date: str
    extra: str = ""


class ScoreManager:
    """Manages persistent scoreboards and statistics for all arcade games."""

    DEFAULT_DATA: Dict[str, Any] = {
        "pong": {
            "high_rally": 0,
            "player_wins": 0,
            "ai_wins": 0,
            "history": [],
        },
        "snake": {
            "high_score": 0,
            "longest_length": 3,
            "games_played": 0,
            "leaderboard": [],
        },
        "breakout": {
            "high_score": 0,
            "max_bricks_cleared": 0,
            "games_played": 0,
            "leaderboard": [],
        },
    }

    def __init__(self, filepath: str = "scores.json"):
        self.filepath = filepath
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            return json.loads(json.dumps(self.DEFAULT_DATA))
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                merged = json.loads(json.dumps(self.DEFAULT_DATA))
                for k, v in loaded.items():
                    if k in merged and isinstance(v, dict):
                        merged[k].update(v)
                    else:
                        merged[k] = v
                return merged
        except Exception:
            return json.loads(json.dumps(self.DEFAULT_DATA))

    def save(self) -> None:
        try:
            parent = os.path.dirname(self.filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[ScoreManager] Error saving scores: {e}")

    # Pong stats
    def record_pong_result(self, winner: str, left_score: int, right_score: int, max_rally: int) -> None:
        p_stats = self.data["pong"]
        if max_rally > p_stats.get("high_rally", 0):
            p_stats["high_rally"] = max_rally
        if "Left" in winner or "Player 1" in winner:
            p_stats["player_wins"] = p_stats.get("player_wins", 0) + 1
        else:
            p_stats["ai_wins"] = p_stats.get("ai_wins", 0) + 1

        history = p_stats.setdefault("history", [])
        history.append({
            "winner": winner,
            "score": f"{left_score}-{right_score}",
            "rally": max_rally,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        p_stats["history"] = history[-20:]  # Keep latest 20
        self.save()

    # Snake stats
    def record_snake_score(self, player: str, score: int, length: int) -> bool:
        """Records snake game. Returns True if new high score."""
        s_stats = self.data["snake"]
        s_stats["games_played"] = s_stats.get("games_played", 0) + 1
        is_new_high = score > s_stats.get("high_score", 0)
        if is_new_high:
            s_stats["high_score"] = score
        if length > s_stats.get("longest_length", 0):
            s_stats["longest_length"] = length

        leaderboard = s_stats.setdefault("leaderboard", [])
        leaderboard.append({
            "player": player,
            "score": score,
            "length": length,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        s_stats["leaderboard"] = leaderboard[:10]
        self.save()
        return is_new_high

    # Breakout stats
    def record_breakout_score(self, player: str, score: int, bricks_cleared: int) -> bool:
        """Records breakout game. Returns True if new high score."""
        b_stats = self.data["breakout"]
        b_stats["games_played"] = b_stats.get("games_played", 0) + 1
        is_new_high = score > b_stats.get("high_score", 0)
        if is_new_high:
            b_stats["high_score"] = score
        if bricks_cleared > b_stats.get("max_bricks_cleared", 0):
            b_stats["max_bricks_cleared"] = bricks_cleared

        leaderboard = b_stats.setdefault("leaderboard", [])
        leaderboard.append({
            "player": player,
            "score": score,
            "bricks": bricks_cleared,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        b_stats["leaderboard"] = leaderboard[:10]
        self.save()
        return is_new_high

    def format_leaderboard_text(self) -> str:
        """Generate formatted ASCII tables for console output."""
        lines = [
            "=" * 60,
            "              RETRO TURTLE ARCADE - HALL OF FAME",
            "=" * 60,
            "",
            "--- 1. PONG CHAMPIONSHIP ---",
            f"  Player Wins: {self.data['pong'].get('player_wins', 0)}  |  AI Wins: {self.data['pong'].get('ai_wins', 0)}",
            f"  All-Time Longest Rally: {self.data['pong'].get('high_rally', 0)} volleys",
            "",
            "--- 2. NEON SNAKE TOP SCORES ---",
            f"  High Score: {self.data['snake'].get('high_score', 0)} pts  |  Longest Length: {self.data['snake'].get('longest_length', 3)}",
        ]
        snake_board = self.data["snake"].get("leaderboard", [])
        if snake_board:
            lines.append("  Rank | Player         | Score  | Length | Date")
            lines.append("  " + "-" * 52)
            for idx, entry in enumerate(snake_board[:5], 1):
                p_name = entry.get("player", "Player")[:14].ljust(14)
                sc = str(entry.get("score", 0)).rjust(6)
                lg = str(entry.get("length", 0)).rjust(6)
                dt = entry.get("date", "")
                lines.append(f"  #{idx:<3} | {p_name} | {sc} | {lg} | {dt}")
        else:
            lines.append("  (No games recorded yet)")

        lines.extend([
            "",
            "--- 3. QUANTUM BREAKOUT TOP SCORES ---",
            f"  High Score: {self.data['breakout'].get('high_score', 0)} pts  |  Max Bricks: {self.data['breakout'].get('max_bricks_cleared', 0)}",
        ])
        breakout_board = self.data["breakout"].get("leaderboard", [])
        if breakout_board:
            lines.append("  Rank | Player         | Score  | Bricks | Date")
            lines.append("  " + "-" * 52)
            for idx, entry in enumerate(breakout_board[:5], 1):
                p_name = entry.get("player", "Player")[:14].ljust(14)
                sc = str(entry.get("score", 0)).rjust(6)
                bk = str(entry.get("bricks", 0)).rjust(6)
                dt = entry.get("date", "")
                lines.append(f"  #{idx:<3} | {p_name} | {sc} | {bk} | {dt}")
        else:
            lines.append("  (No games recorded yet)")

        lines.append("=" * 60)
        return "\n".join(lines)
