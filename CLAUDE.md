# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

### File Structure
- **`game.py`**: Core game logic - generates and validates Sudoku puzzles, provides hints
  - `SudokuGenerator`: Creates valid 9x9 Sudoku grids using backtracking; applies "dig-and-verify" approach to remove cells while ensuring unique solution
  - `SudokuValidator`: Validates complete grids (row/col/box checks), solves puzzles via backtracking, provides hint suggestions using MRV heuristic
  
- **`gui.py`**: Pygame-based GUI with screens for menu (difficulty selection), game board (with conflict highlighting), HUD (timer/hints/buttons), and win overlay

- **`main.py`**: Entry point that initializes `GameUI` and runs the pygame event loop

### Key Design Patterns

1. **Generator uses diagonal-box initialization** to create solved grids efficiently, then fills remaining 3x3 boxes independently for randomness before solving via randomized backtracking (`_solve_grid`). The deterministic variant (`_solve_grid_det`) is used only for uniqueness verification.

2. **Unique-solution guarantee**: `generate_puzzle()` removes cells one-by-one in random order, but after each removal calls `_has_unique_solution()` which counts solutions (with early exit at limit=2). If removing a cell creates multiple solutions, it restores that cell.

3. **Hint system prioritizes solved_grid**: `get_best_hint(puzzle, solved_grid)` with `solved_grid` passed returns values from the ground-truth solution (100% correct). Without `solved_grid`, falls back to MRV heuristic finding empty cell with fewest valid candidates.

4. **Conflict detection via temporary grid modification**: `has_conflict()` temporarily sets cell to 0, checks validity placement, restores original value. This avoids nested loop conflicts and is O(1) per call.

### Grid Representation
- Values: 0 = empty/unfilled, 1-9 = filled cells
- Rows/columns are `list[list[int]]` of size 9x9
- Cell coordinates: `(row, col)` where row=0..8 (top to bottom), col=0..8 (left to right)
- 3x3 boxes indexed by `(box_row, box_col)` where each is 0..2

## Commands

### Running the Game
```bash
python main.py
# or directly
python gui.py
```

**Controls:**
- `1-9`: Enter number in selected cell
- `Backspace/Delete`: Clear cell (if not a given)
- `H` / click Hint button: Request hint (max 5, cooldown ~4s)
- `N`: New game (back to menu)
- `R`: Restart current game
- `T`: Toggle tutorial overlay
- `C`: Close tutorial overlay
- Escape: Return to main menu

### Running Tests
```bash
# All tests with verbose output
python -m pytest test_game.py -v

# Run single test file
python -m unittest test_game

# Run specific test class
python -m pytest test_game.py::TestSudokuGenerator -v

# Run with coverage
python -m pytest test_game.py --cov=game --cov-report=html
```

### Difficulty Levels (empty cells removed from solved grid)
| Level   | Empty Cell Range | Description                    |
|---------|------------------|--------------------------------|
| easy    | 30-35            | Great for beginners            |
| medium  | 40-46            | Balanced challenge             |
| hard    | 50-55            | For seasoned players           |
| expert  | 52-58            | Extreme challenge              |

### Test Coverage Summary
The test suite (`test_game.py`) covers:
- Puzzle generation for all difficulty levels
- Sudoku rule validation (rows, columns, boxes)
- Puzzle solving correctness
- Hint system behavior with and without solved_grid
- Conflict detection (row/column/box conflicts)
- Integration between Generator and Validator

## Important Notes

### Randomness Considerations
- All generation uses `random.shuffle()` which can produce different grids each run
- Tests that compare difficulty levels should generate multiple samples or use fixed random seed
- The `_is_valid` method checks row, column, and box constraints; placing same value twice in same box fails check

### State Management in GUI
- `GameBoard.cells_given` marks cells as immutable (cannot be erased)
- `GameBoard.cells_conflict` tracks which user-input cells violate Sudoku rules
- Conflict highlighting updates whenever puzzle changes via `board.update_conflicts()`

### Module Dependencies
- Main dependencies: `pygame`, `sys`, `time`, `random`
- Tests depend on: `pytest` (in `requirements_test.txt`)
