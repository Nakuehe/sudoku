"""
Sudoku Game — Main Entry Point
Run this file to start the game.
Requires: pygame
Install: pip install pygame
"""
from gui import GameUI


def main():
    print("=" * 50)
    print("  SUDOKU — Modern Pygame Edition")
    print("=" * 50)
    print("\nControls:")
    print("  Click or Arrow Keys — Select cell")
    print("  1-9 — Place number")
    print("  N — Toggle Notes mode")
    print("  H — Use hint")
    print("  T — Tutorial")
    print("  Ctrl+Z / Ctrl+Y — Undo / Redo")
    print("  ESC — Pause / Save / Quit")
    print("\nStarting game...\n")

    try:
        ui = GameUI()
        ui.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()