# 🕹️ Retro Turtle Arcade

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-Zero%20(Stdlib)-success.svg)](requirements.txt)
[![Tests](https://img.shields.io/badge/tests-Passing%20(100%25)-brightgreen.svg)](tests/)

A modular, feature-packed retro arcade suite and 2D physics engine built entirely using **Python's standard library** (`turtle` & `tkinter`). No external packages or heavyweight game engines needed!

---

## 🌟 Highlights

- **3 Complete Classic Arcade Games**:
  - **Retro Pong Arena**: 1-Player vs predictive AI (4 difficulty tiers) or 2-Player local co-op/versus, dynamic ball speed curves, angle reflections based on paddle impact offsets, and dynamic power-ups (Paddle Expand, Speed Burst, Slow-Mo).
  - **Neon Cyber Snake**: Direction-buffered responsive input (no accidental self-kills), special fruits (Golden Apple, Speed Berry), dynamic combo multipliers, and wall wrap-around toggle.
  - **Quantum Breakout**: Multi-row colored bricks with armor hit points, paddle deflection physics, falling lives system, and victory sequence.
- **Interactive Arcade Cabinet Hub**:
  - Animated neon menu launcher with keyboard navigation (`Up/Down`, `W/S`, `Enter`).
  - Seamless in-game return to menu (`ESC`) without restarting Python.
- **Custom 2D Physics & Collision Engine**:
  - 2D Vector mathematics (`Vector2D`), Axis-Aligned Bounding Boxes (`AABB`), circle-box intersection detection, and reflection physics.
  - Predictive raycasting AI with boundary folding calculation for impossible bounce anticipation.
- **Persistent High Scores & Hall of Fame**:
  - Automatically records statistics and scores in `scores.json`.
  - Formatted CLI ASCII leaderboard viewer (`--leaderboard`).
- **Threaded Non-Blocking Audio**:
  - Retro sound effects (hit, bounce, score, pickup, brick break) powered by `winsound` in background threads.
- **Zero External Dependencies**:
  - Pure standard library. Clones and runs instantly on any machine with Python 3.10+.
- **Headless Simulation Harness**:
  - Run benchmarks and tests headlessly without opening any GUI window.

---

## 📐 Architecture Overview

```
retro-turtle-arcade/
├── main.py                     # Root executable script
├── requirements.txt            # Zero external dependencies (Stdlib only)
├── LICENSE                     # MIT License
├── README.md                   # Complete documentation
├── retro_arcade/               # Core game engine package
│   ├── __init__.py             # Exports and version info
│   ├── config.py               # Themes, window settings, and game constants
│   ├── physics.py              # Vector2D, AABB, raycasting, reflection math
│   ├── ai.py                   # Multi-tier paddle AI (Easy, Med, Hard, Impossible)
│   ├── scoreboard.py           # Persistent JSON high scores & statistics
│   ├── audio.py                # Non-blocking threaded audio synthesizer
│   ├── engine.py               # Master screen manager and 60 FPS tick loop
│   ├── menu.py                 # Interactive retro arcade cabinet menu
│   ├── cli.py                  # CLI argument parser and headless runner
│   └── games/                  # Game implementations
│       ├── __init__.py
│       ├── base.py             # Abstract BaseGame and GameState lifecycle
│       ├── pong.py             # Retro Pong game
│       ├── snake.py            # Neon Cyber Snake game
│       └── breakout.py         # Quantum Breakout game
└── tests/                      # Comprehensive unit test suite
    ├── __init__.py
    ├── test_physics.py         # Math and collision unit tests
    ├── test_ai.py              # AI controller and raycast tests
    ├── test_scoreboard.py      # Score persistence and formatting tests
    ├── test_games.py           # Headless Pong, Snake, Breakout lifecycle tests
    └── test_cli.py             # Argument parsing tests
```

---

## 🎮 Controls

### Global Controls
| Action | Keybinding |
| :--- | :--- |
| **Pause / Resume** | `P` |
| **Restart Game** | `R` |
| **Return to Menu** | `ESC` |

### Retro Pong
| Player | Up | Down |
| :--- | :--- | :--- |
| **Player 1 (Left)** | `W` | `S` |
| **Player 2 (Right)** | `Up Arrow` | `Down Arrow` |

### Neon Cyber Snake
| Action | Keybinding |
| :--- | :--- |
| **Directional Movement** | `Arrow Keys` or `W, A, S, D` |

### Quantum Breakout
| Action | Keybinding |
| :--- | :--- |
| **Paddle Movement** | `Left / Right Arrows` or `A / D` |
| **Launch Ball** | `Spacebar` |

---

## 🚀 Quick Start

### 1. Launch the Arcade Cabinet Menu
```bash
python main.py
```

### 2. Directly Launch Specific Games
```bash
# Launch Pong in 1-Player mode vs Hard AI
python main.py --game pong --mode 1p --difficulty hard

# Launch Pong in 2-Player local versus
python main.py --game pong --mode 2p

# Launch Neon Cyber Snake
python main.py --game snake

# Launch Quantum Breakout
python main.py --game breakout
```

### 3. Customize Themes & Audio
```bash
# Launch Synthwave 80s theme without audio
python main.py --theme synthwave --mute

# Available themes: neon, synthwave, matrix, retro
python main.py --theme matrix
```

### 4. View Hall of Fame Leaderboard
```bash
python main.py --leaderboard
```

### 5. Headless Simulation & Benchmark
Verify physics and game rules headlessly without opening a GUI window:
```bash
python main.py --headless-sim pong --sim-steps 500
python main.py --headless-sim snake --sim-steps 300
python main.py --headless-sim breakout --sim-steps 400
```

---

## 🧪 Testing

Run the full automated test suite using Python's built-in `unittest`:

```bash
python -m unittest discover tests
```

All tests execute in headless mode, making them ideal for continuous integration (CI) pipelines.

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
