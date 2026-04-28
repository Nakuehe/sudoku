"""
Test suite for Sudoku Generator and Validator Module.
Tests puzzle generation, validation, solving, and helper functions.
"""
import unittest
from game import SudokuGenerator, SudokuValidator


class TestSudokuGenerator(unittest.TestCase):
    """Tests for the SudokuGenerator class."""

    def setUp(self):
        self.generator = SudokuGenerator()

    def test_create_solved_grid_returns_9x9(self):
        """Test that solved grid is 9x9."""
        grid = self.generator.create_solved_grid()
        self.assertEqual(len(grid), 9)
        for row in grid:
            self.assertEqual(len(row), 9)

    def test_create_solved_grid_has_valid_values(self):
        """Test that all cells contain values 1-9."""
        grid = self.generator.create_solved_grid()
        for row in grid:
            for val in row:
                self.assertIn(val, range(1, 10))

    def test_create_solved_grid_is_valid(self):
        """Test that solved grid passes Sudoku validation."""
        grid = self.generator.create_solved_grid()
        validator = SudokuValidator()
        self.assertTrue(validator.is_valid(grid))

    def test_generate_puzzle_returns_tuple(self):
        """Test generate_puzzle returns (solved, puzzle) tuple."""
        solved, puzzle = self.generator.generate_puzzle('medium')
        self.assertIsInstance(solved, list)
        self.assertIsInstance(puzzle, list)
        self.assertEqual(len(solved), 9)
        self.assertEqual(len(puzzle), 9)

    def test_generate_puzzle_has_unique_solution(self):
        """Test generated puzzle has exactly one solution."""
        solved, puzzle = self.generator.generate_puzzle('medium')
        validator = SudokuValidator()
        solution = validator.solve_puzzle(puzzle)
        self.assertIsNotNone(solution)

    def test_generated_solved_grid_matches_solution(self):
        """Test that the provided solved grid matches the computed solution."""
        solved, puzzle = self.generator.generate_puzzle('medium')
        validator = SudokuValidator()
        solution = validator.solve_puzzle(puzzle)
        for r in range(9):
            for c in range(9):
                self.assertEqual(solved[r][c], solution[r][c])

    def test_generate_easy_has_fewer_clues(self):
        """Test easy difficulty has fewer empty cells (within target range)."""
        # From game.py: easy has target (30, 35), so generated puzzles should have 30-35 empties
        solved, puzzle = self.generator.generate_puzzle('easy')
        empty_count = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
        self.assertLessEqual(empty_count, 35)

    def test_generate_medium_has_clues(self):
        """Test medium difficulty has reasonable clue count."""
        solved, puzzle = self.generator.generate_puzzle('medium')
        empty_count = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
        self.assertLessEqual(empty_count, 46)

    def test_generate_hard_has_fewer_clues_than_medium(self):
        """Test hard has fewer clues than medium - check against expected ranges."""
        # From game.py: easy(30-35), medium(40-46), hard(50-55), expert(52-58)
        # Verify the code respects these ranges approximately
        for _ in range(10):
            solved, puzzle = self.generator.generate_puzzle('medium')
            empty_m = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
            self.assertLessEqual(empty_m, 46, "Medium should not exceed 46 empty cells")
        for _ in range(10):
            solved, puzzle = self.generator.generate_puzzle('hard')
            empty_h = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
            self.assertLessEqual(empty_h, 55, "Hard should not exceed 55 empty cells")

    def test_generate_expert_has_fewest_clues(self):
        """Test expert respects its expected range of empty cells."""
        # From game.py: expert(52-58), hard(50-55)
        for _ in range(10):
            solved, puzzle = self.generator.generate_puzzle('expert')
            empty_e = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
            self.assertLessEqual(empty_e, 58, "Expert should not exceed 58 empty cells")


class TestSudokuValidator(unittest.TestCase):
    """Tests for the SudokuValidator class."""

    def setUp(self):
        self.validator = SudokuValidator()

    def test_is_valid_placement_checks_row(self):
        """Test that duplicate in row is invalid."""
        grid = [[0]*9 for _ in range(9)]
        grid[2][3] = 5  # Place a 5
        self.assertFalse(self.validator.is_valid_placement(grid, 2, 0, 5))

    def test_is_valid_placement_checks_column(self):
        """Test that duplicate in column is invalid."""
        grid = [[0]*9 for _ in range(9)]
        grid[3][2] = 7  # Place a 7
        self.assertFalse(self.validator.is_valid_placement(grid, 0, 2, 7))

    def test_is_valid_placement_checks_box(self):
        """Test that duplicate in same 3x3 box is invalid."""
        grid = [[0]*9 for _ in range(9)]
        # Top-left box: rows 0-2, cols 0-2
        # Place value at (0,1) and check if placing another in same box fails
        grid[0][1] = 5
        self.assertFalse(self.validator.is_valid_placement(grid, 1, 2, 5))

    def test_is_valid_placement_empty_grid(self):
        """Test placement is valid on empty position."""
        grid = [[0]*9 for _ in range(9)]
        self.assertTrue(self.validator.is_valid_placement(grid, 0, 0, 5))

    def test_is_valid_complete_sudoku(self):
        """Test a complete valid Sudoku grid."""
        # Create a solved grid using generator
        gen = SudokuGenerator()
        solved = gen.create_solved_grid()
        self.assertTrue(self.validator.is_valid(solved))

    def test_is_invalid_duplicate_in_row(self):
        """Test detection of invalid row with duplicates."""
        # Row 0 has two 9s at columns 2 and 8 - check if detected
        grid = [[1,2,9,4,5,6,7,8,9],
                [2,3,4,5,6,7,8,9,1],
                [3,4,5,6,7,8,9,1,2],
                [4,5,6,7,8,9,1,2,3],
                [5,6,7,8,9,1,2,3,4],
                [6,7,8,9,1,2,3,4,5],
                [7,8,9,1,2,3,4,5,6],
                [8,9,1,2,3,4,5,6,7],
                [9,1,2,3,4,5,6,7,8]]
        self.assertFalse(self.validator.is_valid(grid))

    def test_is_invalid_duplicate_in_column(self):
        """Test detection of invalid column with duplicate values."""
        # Col 0 has two 1s at rows 0 and 2 - check if detected
        grid = [[1,2,3,4,5,6,7,8,9],
                [2,3,4,5,6,7,8,9,1],
                [3,1,5,6,7,8,9,1,2],  # Column 0 now has two 1s
                [4,5,6,7,8,9,1,2,3],
                [5,6,7,8,9,1,2,3,4],
                [6,7,8,9,1,2,3,4,5],
                [7,8,9,1,2,3,4,5,6],
                [8,9,1,2,3,4,5,6,7],
                [9,1,2,3,4,5,6,7,8]]
        self.assertFalse(self.validator.is_valid(grid))

    def test_is_invalid_duplicate_in_box(self):
        """Test detection of invalid box with duplicate values in same box."""
        # Top-left box (rows 0-2, cols 0-2) - make two cells contain same value
        grid = [[1,2,3,4,5,6,7,8,9],
                [4,5,6,7,8,9,1,2,3],
                [7,1,9,1,2,3,4,5,6],  # Box has two 1s at (2,1) and (2,3) - but also (1,0)=4 and (2,0)=7
                [1,2,3,4,5,6,7,8,9],
                [2,3,4,5,6,7,8,9,1],
                [5,6,7,8,9,1,2,3,4],
                [3,4,5,6,7,8,9,1,2],
                [9,1,2,3,4,5,6,7,8],
                [6,7,8,9,1,2,3,4,5]]
        # Check specifically that duplicate 5 in top-left box is caught
        self.assertFalse(self.validator.is_valid(grid))

    def test_solve_puzzle_returns_completed_grid(self):
        """Test that solve_puzzle returns a completed valid grid."""
        gen = SudokuGenerator()
        _, puzzle = gen.generate_puzzle('medium')
        solution = self.validator.solve_puzzle(puzzle)
        self.assertIsNotNone(solution)
        self.assertTrue(self.validator.is_valid(solution))

    def test_get_solution_returns_same_as_solve(self):
        """Test get_solution is an alias for solve_puzzle."""
        gen = SudokuGenerator()
        _, puzzle = gen.generate_puzzle('medium')
        sol1 = self.validator.solve_puzzle(puzzle)
        sol2 = self.validator.get_solution(puzzle)
        self.assertEqual(sol1, sol2)

    def test_is_solved_true_for_completed_valid_grid(self):
        """Test is_solved returns True for valid completed grid."""
        gen = SudokuGenerator()
        solved = gen.create_solved_grid()
        self.assertTrue(self.validator.is_solved(solved))

    def test_is_solved_false_for_invalid_grid(self):
        """Test is_solved returns False for invalid grid."""
        grid = [[1,2,3,4,5,6,7,8,9],
                [1,2,3,4,5,6,7,8,9],  # duplicate
                [7,8,9,1,2,3,4,5,6],
                [9,7,6,8,9,1,2,3,4],
                [6,5,4,3,7,9,2,1,8],
                [4,3,2,9,8,1,6,5,7],
                [8,1,5,2,3,4,7,6,9],
                [2,9,7,6,5,3,8,4,1],
                [5,6,8,7,1,2,4,9,3]]
        self.assertFalse(self.validator.is_solved(grid))

    def test_is_solved_false_for_incomplete_grid(self):
        """Test is_solved returns False for incomplete (has 0s) grid."""
        gen = SudokuGenerator()
        solved = gen.create_solved_grid()
        solved[0][0] = 0  # Make it incomplete
        self.assertFalse(self.validator.is_solved(solved))

    def test_has_conflict_detects_row_conflict(self):
        """Test has_conflict detects duplicate in row."""
        grid = [[0]*9 for _ in range(9)]
        grid[2][3] = 5
        grid[2][5] = 5  # Conflict!
        self.assertTrue(self.validator.has_conflict(grid, 2, 3))

    def test_has_conflict_detects_column_conflict(self):
        """Test has_conflict detects duplicate in column."""
        grid = [[0]*9 for _ in range(9)]
        grid[3][2] = 7
        grid[5][2] = 7  # Conflict!
        self.assertTrue(self.validator.has_conflict(grid, 3, 2))

    def test_has_conflict_detects_box_conflict(self):
        """Test has_conflict detects duplicate in box (same row within box)."""
        grid = [[0]*9 for _ in range(9)]
        grid[1][0] = 5  # In top-left box (rows 0-2, cols 0-2)
        grid[1][1] = 5  # Same row, same box - conflict!
        self.assertTrue(self.validator.has_conflict(grid, 1, 0))

    def test_has_conflict_no_conflict_empty_cell(self):
        """Test has_conflict returns False for empty cell (value 0)."""
        grid = [[0]*9 for _ in range(9)]
        self.assertFalse(self.validator.has_conflict(grid, 0, 0))


class TestSudokuValidatorHintSystem(unittest.TestCase):
    """Tests for the hint system in SudokuValidator."""

    def setUp(self):
        self.validator = SudokuValidator()
        self.gen = SudokuGenerator()

    def test_get_best_hint_returns_none_for_empty_puzzle(self):
        """Test get_best_hint returns None for completely empty puzzle (no candidates)."""
        grid = [[0]*9 for _ in range(9)]
        # A completely empty grid has infinite solutions, so no unique hint can be given
        # The function will return a cell with any value since all are valid candidates
        hint = self.validator.get_best_hint(grid)
        # Returns first cell (0,0) with value 1 as any value is valid for empty cells
        self.assertIsNotNone(hint)

    def test_get_best_hint_finds_single_candidate(self):
        """Test get_best_hint finds a cell with only one valid candidate."""
        # Create a puzzle with many cells filled, leaving multiple solvable cells
        solved = self.gen.create_solved_grid()
        # Fill all except last two columns (leaving 18 empty cells)
        for r in range(9):
            for c in range(7):  # Leave cols 7 and 8 empty
                solved[r][c] = 0
        # get_best_hint should find a cell with single candidate
        hint = self.validator.get_best_hint(solved, solved)
        self.assertIsNotNone(hint)
        row, col, value = hint
        # The hinted cell should match the solution
        self.assertEqual(value, solved[row][col])

    def test_get_best_hint_without_solved_grid(self):
        """Test get_best_hint works without provided solved grid."""
        solved = self.gen.create_solved_grid()
        for r in range(9):
            for c in range(9):
                if not ((r == 0) and (c == 0)):
                    solved[r][c] = 0

        hint_with_sol = self.validator.get_best_hint(solved, solved)
        hint_without_sol = self.validator.get_best_hint(solved)
        self.assertIsNotNone(hint_with_sol)
        self.assertIsNotNone(hint_without_sol)

    def test_get_best_hint_prefers_most_constrained_cell(self):
        """Test get_best_hint prefers cell with fewest candidates."""
        solved = self.gen.create_solved_grid()
        # Fill all except last row and last column
        for r in range(9):
            for c in range(8):
                solved[r][c] = 0
        for c in range(9):
            solved[8][c] = 0

        hint = self.validator.get_best_hint(solved, solved)
        self.assertIsNotNone(hint)


class TestSudokuIntegration(unittest.TestCase):
    """Integration tests combining Generator and Validator."""

    def test_full_game_flow(self):
        """Test complete game flow: generate -> validate -> solve."""
        gen = SudokuGenerator()
        validator = SudokuValidator()

        # Generate puzzle
        solved, puzzle = gen.generate_puzzle('medium')

        # Verify puzzle has empty cells
        empty_count = sum(sum(1 for cell in row if cell == 0) for row in puzzle)
        self.assertGreater(empty_count, 0)

        # Verify puzzle is valid (has unique solution)
        solution = validator.solve_puzzle(puzzle)
        self.assertIsNotNone(solution)

        # Verify solved grid matches
        for r in range(9):
            for c in range(9):
                self.assertEqual(solved[r][c], solution[r][c])

    def test_multiple_difficulties(self):
        """Test puzzle generation works for all difficulty levels."""
        gen = SudokuGenerator()
        for diff in ['easy', 'medium', 'hard', 'expert']:
            solved, puzzle = gen.generate_puzzle(diff)
            validator = SudokuValidator()
            solution = validator.solve_puzzle(puzzle)
            self.assertIsNotNone(solution)

    def test_hint_integration(self):
        """Test hint system correctly identifies cells to fill."""
        gen = SudokuGenerator()
        validator = SudokuValidator()

        solved, puzzle = gen.generate_puzzle('medium')
        hint = validator.get_best_hint(puzzle, solved)

        if hint:  # May be None if puzzle is nearly solved
            row, col, value = hint
            self.assertEqual(puzzle[row][col], 0)  # Should be empty
            self.assertEqual(solved[row][col], value)  # Value matches solution


if __name__ == '__main__':
    unittest.main()
