"""
Sudoku Generator, Validator, and Persistence Module
Handles puzzle generation, validation, difficulty levels,
save/load state, leaderboards, and player statistics.
"""

import json
import os
import random
import time
from copy import deepcopy

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".sudoku_saves")
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
STATS_FILE = os.path.join(SAVE_DIR, "stats.json")
LEADERBOARD_FILE = os.path.join(SAVE_DIR, "leaderboard.json")


def _ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def _default_stats():
    return {
        "games_played": 0,
        "games_won": 0,
        "total_time": 0.0,
        "hints_used": 0,
        "per_difficulty": {}
    }


# ---------------------------------------------------------------------------
# GENERATOR
# ---------------------------------------------------------------------------
class SudokuGenerator:
    """Generate valid 9x9 Sudoku puzzles with varying difficulty levels."""

    def __init__(self):
        self.size = 9
        self.box_size = 3

    def create_solved_grid(self):
        """Create a fully solved valid Sudoku grid."""
        grid = [[0] * self.size for _ in range(self.size)]
        self._fill_diagonal_boxes(grid)
        self._solve_grid(grid)
        return grid

    def _fill_diagonal_boxes(self, grid):
        """Fill the 3 diagonal 3x3 boxes randomly."""
        for box in range(self.box_size):
            row = box * self.box_size
            col = box * self.box_size
            nums = list(range(1, self.size + 1))
            random.shuffle(nums)
            for i in range(self.box_size):
                for j in range(self.box_size):
                    grid[row + i][col + j] = nums.pop()

    def _is_valid(self, grid, row, col, num):
        """
        Check whether placing num at (row, col) is valid.
        Important: skip checking the current cell itself.
        """
        # Check row
        for c in range(self.size):
            if c != col and grid[row][c] == num:
                return False

        # Check column
        for r in range(self.size):
            if r != row and grid[r][col] == num:
                return False

        # Check 3x3 box
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if (r != row or c != col) and grid[r][c] == num:
                    return False

        return True

    def _find_empty(self, grid):
        """Find the first empty cell (0)."""
        for r in range(self.size):
            for c in range(self.size):
                if grid[r][c] == 0:
                    return r, c
        return None

    def _solve_grid(self, grid):
        """Solve the grid using backtracking."""
        empty = self._find_empty(grid)
        if not empty:
            return True

        row, col = empty
        nums = list(range(1, self.size + 1))
        random.shuffle(nums)

        for num in nums:
            if self._is_valid(grid, row, col, num):
                grid[row][col] = num
                if self._solve_grid(grid):
                    return True
                grid[row][col] = 0

        return False

    def _count_solutions(self, grid, limit=2):
        """
        Count number of solutions up to 'limit'.
        Used to ensure uniqueness of puzzle.
        """
        empty = self._find_empty(grid)
        if not empty:
            return 1

        row, col = empty
        count = 0

        for num in range(1, self.size + 1):
            if self._is_valid(grid, row, col, num):
                grid[row][col] = num
                count += self._count_solutions(grid, limit)
                grid[row][col] = 0

                if count >= limit:
                    return count

        return count

    def _has_unique_solution(self, puzzle):
        """Return True if puzzle has exactly one solution."""
        copy_grid = [row[:] for row in puzzle]
        return self._count_solutions(copy_grid, limit=2) == 1

    def generate_puzzle(self, difficulty="medium", max_attempts=50):
        """
        Generate a Sudoku puzzle with a unique solution.

        difficulty:
            - easy
            - medium
            - hard
            - expert
        """
        difficulty = str(difficulty).strip().lower()

        targets = {
            "easy": (30, 35),
            "medium": (40, 46),
            "hard": (50, 55),
            "expert": (52, 58),
        }

        lo, hi = targets.get(difficulty, (40, 46))
        target = random.randint(lo, hi)

        best_result = None
        best_removed = -1

        for _ in range(max_attempts):
            solved = self.create_solved_grid()
            puzzle = [row[:] for row in solved]

            cells = [(r, c) for r in range(self.size) for c in range(self.size)]
            random.shuffle(cells)

            removed = 0

            for row, col in cells:
                if removed >= target:
                    break

                backup = puzzle[row][col]
                puzzle[row][col] = 0

                if self._has_unique_solution(puzzle):
                    removed += 1
                else:
                    puzzle[row][col] = backup

            if removed > best_removed:
                best_removed = removed
                best_result = (solved, puzzle)

            if removed >= lo:
                return solved, puzzle

        # Fallback: return best attempt if it meets minimum threshold
        if best_result is not None and best_removed >= lo:
            return best_result

        # Very rare fallback: just return the last best attempt anyway
        return best_result if best_result is not None else (self.create_solved_grid(), [[0] * 9 for _ in range(9)])


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------
class SudokuValidator:
    """Validate Sudoku grids and assist with solving."""

    def __init__(self):
        self.size = 9

    def is_valid_placement(self, grid, row, col, num):
        """
        Check whether placing num at (row, col) is valid.
        Important: skip checking the current cell itself.
        """
        # Check row
        for c in range(self.size):
            if c != col and grid[row][c] == num:
                return False

        # Check column
        for r in range(self.size):
            if r != row and grid[r][col] == num:
                return False

        # Check 3x3 box
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if (r != row or c != col) and grid[r][c] == num:
                    return False

        return True

    def is_valid(self, grid):
        """Return True if grid is a complete valid Sudoku solution."""
        return (
            self._check_rows(grid)
            and self._check_cols(grid)
            and self._check_boxes(grid)
        )

    def _check_rows(self, grid):
        expected = list(range(1, self.size + 1))
        for row in grid:
            if sorted(row) != expected:
                return False
        return True

    def _check_cols(self, grid):
        expected = list(range(1, self.size + 1))
        for col in range(self.size):
            nums = [grid[r][col] for r in range(self.size)]
            if sorted(nums) != expected:
                return False
        return True

    def _check_boxes(self, grid):
        expected = list(range(1, self.size + 1))
        for br in range(3):
            for bc in range(3):
                box = [
                    grid[br * 3 + i][bc * 3 + j]
                    for i in range(3)
                    for j in range(3)
                ]
                if sorted(box) != expected:
                    return False
        return True

    def is_solved(self, grid):
        """Return True if puzzle has no zeros and is fully valid."""
        for row in grid:
            if 0 in row:
                return False
        return self.is_valid(grid)

    def has_conflict(self, grid, row, col):
        """
        Check whether the current value at (row, col) conflicts with Sudoku rules.
        """
        val = grid[row][col]
        if val == 0:
            return False

        grid[row][col] = 0
        conflict = not self.is_valid_placement(grid, row, col, val)
        grid[row][col] = val
        return conflict

    def _find_valid_candidates(self, grid, row, col):
        """Return all valid candidates for an empty cell."""
        if grid[row][col] != 0:
            return []
        return [
            n for n in range(1, self.size + 1)
            if self.is_valid_placement(grid, row, col, n)
        ]

    def get_best_hint(self, puzzle, solved_grid=None):
        """
        Return a hint tuple: (row, col, value)
        Chooses the empty cell with the fewest valid candidates.
        If solved_grid is provided, returns the correct solved value.
        """
        best = None
        best_count = 10

        for row in range(self.size):
            for col in range(self.size):
                if puzzle[row][col] != 0:
                    continue

                candidates = self._find_valid_candidates(puzzle, row, col)
                if not candidates:
                    continue

                if len(candidates) < best_count:
                    best_count = len(candidates)

                    if solved_grid is not None:
                        best = (row, col, solved_grid[row][col])
                    else:
                        best = (row, col, candidates[0])

                    if best_count == 1:
                        return best

        return best


# ---------------------------------------------------------------------------
# SAVE / LOAD
# ---------------------------------------------------------------------------
class GameSaveManager:
    """Handles saving and loading game state to disk."""

    @staticmethod
    def save_game(state_dict):
        _ensure_save_dir()
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError, TypeError, ValueError):
            return False

    @staticmethod
    def load_game():
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def delete_save():
        try:
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            return True
        except (IOError, OSError):
            return False


# ---------------------------------------------------------------------------
# LEADERBOARD
# ---------------------------------------------------------------------------
class LeaderboardManager:
    """Manages per-difficulty best times (top 5 each)."""

    MAX_ENTRIES = 5

    @staticmethod
    def _load():
        if not os.path.exists(LEADERBOARD_FILE):
            return {}

        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (IOError, OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save(data):
        _ensure_save_dir()
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def add_entry(cls, difficulty, elapsed):
        difficulty = str(difficulty).strip().lower()

        data = cls._load()
        entries = data.get(difficulty, [])

        entries.append({
            "time": round(float(elapsed), 2),
            "date": time.strftime("%Y-%m-%d %H:%M"),
        })

        entries.sort(key=lambda e: e["time"])
        data[difficulty] = entries[:cls.MAX_ENTRIES]
        cls._save(data)

    @classmethod
    def get_entries(cls, difficulty):
        difficulty = str(difficulty).strip().lower()
        data = cls._load()
        return data.get(difficulty, [])

    @classmethod
    def get_all(cls):
        return cls._load()


# ---------------------------------------------------------------------------
# PLAYER STATS
# ---------------------------------------------------------------------------
class StatsManager:
    """Tracks cumulative player statistics."""

    @staticmethod
    def _load():
        if not os.path.exists(STATS_FILE):
            return _default_stats()

        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return _default_stats()

                # Ensure required fields exist
                defaults = _default_stats()
                for k, v in defaults.items():
                    data.setdefault(k, deepcopy(v))

                if not isinstance(data.get("per_difficulty"), dict):
                    data["per_difficulty"] = {}

                return data
        except (IOError, OSError, json.JSONDecodeError):
            return _default_stats()

    @staticmethod
    def _save(data):
        _ensure_save_dir()
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def record_game_start(cls, difficulty=None):
        """
        Record that a new game has started.
        If difficulty is provided, also increments per-difficulty 'played'.
        """
        data = cls._load()
        data["games_played"] = data.get("games_played", 0) + 1

        if difficulty:
            difficulty = str(difficulty).strip().lower()
            per = data.get("per_difficulty", {})
            d = per.get(difficulty, {"played": 0, "won": 0, "best_time": None})
            d["played"] = d.get("played", 0) + 1
            per[difficulty] = d
            data["per_difficulty"] = per

        cls._save(data)

    @classmethod
    def record_game_win(cls, difficulty, elapsed, hints_used):
        """
        Record a completed win for the given difficulty.
        """
        difficulty = str(difficulty).strip().lower()

        data = cls._load()
        data["games_won"] = data.get("games_won", 0) + 1
        data["total_time"] = round(data.get("total_time", 0.0) + float(elapsed), 2)
        data["hints_used"] = data.get("hints_used", 0) + int(hints_used)

        per = data.get("per_difficulty", {})
        d = per.get(difficulty, {"played": 0, "won": 0, "best_time": None})

        # In case record_game_start(difficulty) wasn't called earlier,
        # we keep played untouched here. Only won is guaranteed to increase.
        d["won"] = d.get("won", 0) + 1

        best_time = d.get("best_time")
        elapsed = round(float(elapsed), 2)

        if best_time is None or elapsed < best_time:
            d["best_time"] = elapsed

        per[difficulty] = d
        data["per_difficulty"] = per
        cls._save(data)

    @classmethod
    def get_stats(cls):
        return cls._load()