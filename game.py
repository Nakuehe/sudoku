"""
Sudoku Generator, Validator, and Persistence Module
Handles puzzle generation, validation, difficulty levels,
save/load state, leaderboards, and player statistics.
"""
import json
import os
import random
import time

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".sudoku_saves")
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
STATS_FILE = os.path.join(SAVE_DIR, "stats.json")
LEADERBOARD_FILE = os.path.join(SAVE_DIR, "leaderboard.json")


def _ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# GENERATOR
# ---------------------------------------------------------------------------
class SudokuGenerator:
    """Generate valid 9x9 Sudoku puzzles with varying difficulty levels."""

    def __init__(self):
        self.size = 9
        self.box_size = 3

    def create_solved_grid(self):
        grid = [[0] * self.size for _ in range(self.size)]
        self._fill_diagonal_boxes(grid)
        self._solve_grid(grid)
        return grid

    def _fill_diagonal_boxes(self, grid):
        for box in range(self.box_size):
            row = box * self.box_size
            col = box * self.box_size
            nums = list(range(1, self.size + 1))
            random.shuffle(nums)
            for i in range(self.box_size):
                for j in range(self.box_size):
                    grid[row + i][col + j] = nums.pop()

    def _is_valid(self, grid, row, col, num):
        for i in range(self.size):
            if grid[row][i] == num or grid[i][col] == num:
                return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if grid[br + i][bc + j] == num:
                    return False
        return True

    def _find_empty(self, grid):
        for r in range(self.size):
            for c in range(self.size):
                if grid[r][c] == 0:
                    return (r, c)
        return None

    def _solve_grid(self, grid):
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
        copy = [row[:] for row in puzzle]
        return self._count_solutions(copy, limit=2) == 1

    def generate_puzzle(self, difficulty='medium'):
        targets = {
            'easy': (30, 35), 'medium': (40, 46),
            'hard': (50, 55), 'expert': (52, 58),
        }
        lo, hi = targets.get(difficulty, (40, 46))
        target = random.randint(lo, hi)

        while True:
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
            if removed >= lo:
                return solved, puzzle


# ---------------------------------------------------------------------------
# VALIDATOR
# ---------------------------------------------------------------------------
class SudokuValidator:
    """Validate Sudoku grids and assist with solving."""

    def __init__(self):
        self.size = 9

    def is_valid_placement(self, grid, row, col, num):
        for i in range(self.size):
            if grid[row][i] == num or grid[i][col] == num:
                return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if grid[br + i][bc + j] == num:
                    return False
        return True

    def is_valid(self, grid):
        return self._check_rows(grid) and self._check_cols(grid) and self._check_boxes(grid)

    def _check_rows(self, grid):
        for row in grid:
            if sorted(row) != list(range(1, self.size + 1)):
                return False
        return True

    def _check_cols(self, grid):
        for col in range(self.size):
            nums = [grid[r][col] for r in range(self.size)]
            if sorted(nums) != list(range(1, self.size + 1)):
                return False
        return True

    def _check_boxes(self, grid):
        for br in range(3):
            for bc in range(3):
                box = [grid[br * 3 + i][bc * 3 + j] for i in range(3) for j in range(3)]
                if sorted(box) != list(range(1, self.size + 1)):
                    return False
        return True

    def is_solved(self, grid):
        for row in grid:
            if 0 in row:
                return False
        return self.is_valid(grid)

    def has_conflict(self, grid, row, col):
        val = grid[row][col]
        if val == 0:
            return False
        grid[row][col] = 0
        conflict = not self.is_valid_placement(grid, row, col, val)
        grid[row][col] = val
        return conflict

    def _find_valid_candidates(self, grid, row, col):
        return [n for n in range(1, self.size + 1) if self.is_valid_placement(grid, row, col, n)]

    def get_best_hint(self, puzzle, solved_grid=None):
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
            with open(SAVE_FILE, 'w') as f:
                json.dump(state_dict, f, indent=2)
            return True
        except (IOError, OSError):
            return False

    @staticmethod
    def load_game():
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None

    @staticmethod
    def delete_save():
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)


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
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save(data):
        _ensure_save_dir()
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def add_entry(cls, difficulty, elapsed):
        data = cls._load()
        entries = data.get(difficulty, [])
        entries.append({
            'time': round(elapsed, 2),
            'date': time.strftime('%Y-%m-%d %H:%M'),
        })
        entries.sort(key=lambda e: e['time'])
        data[difficulty] = entries[:cls.MAX_ENTRIES]
        cls._save(data)

    @classmethod
    def get_entries(cls, difficulty):
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
            return {'games_played': 0, 'games_won': 0, 'total_time': 0.0,
                    'hints_used': 0, 'per_difficulty': {}}
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {'games_played': 0, 'games_won': 0, 'total_time': 0.0,
                    'hints_used': 0, 'per_difficulty': {}}

    @staticmethod
    def _save(data):
        _ensure_save_dir()
        with open(STATS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def record_game_start(cls):
        data = cls._load()
        data['games_played'] = data.get('games_played', 0) + 1
        cls._save(data)

    @classmethod
    def record_game_win(cls, difficulty, elapsed, hints_used):
        data = cls._load()
        data['games_won'] = data.get('games_won', 0) + 1
        data['total_time'] = data.get('total_time', 0.0) + elapsed
        data['hints_used'] = data.get('hints_used', 0) + hints_used

        per = data.get('per_difficulty', {})
        d = per.get(difficulty, {'played': 0, 'won': 0, 'best_time': None})
        d['won'] = d.get('won', 0) + 1
        bt = d.get('best_time')
        if bt is None or elapsed < bt:
            d['best_time'] = round(elapsed, 2)
        per[difficulty] = d
        data['per_difficulty'] = per
        cls._save(data)

    @classmethod
    def get_stats(cls):
        return cls._load()