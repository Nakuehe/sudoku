"""
Sudoku GUI — Modern Pygame Interface
Features: notes/pencil marks, undo/redo, arrow navigation, number frequency,
highlight matching, save/load, pause, theme toggle, sound, win animation,
leaderboard view, stats view, hints, difficulty menu, tutorial overlay.
"""
import pygame
import sys
import time
import math
from game import (SudokuGenerator, SudokuValidator, GameSaveManager,
                  LeaderboardManager, StatsManager)

pygame.init()
pygame.mixer.init()

# ---------------------------------------------------------------------------
# THEME DEFINITIONS
# ---------------------------------------------------------------------------
THEMES = {
    'dark': {
        'bg': (30, 30, 46),
        'grid_bg': (45, 45, 65),
        'cell_bg': (55, 55, 80),
        'cell_selected': (80, 80, 120),
        'cell_highlight': (65, 65, 95),
        'cell_same_num': (75, 60, 100),
        'cell_given': (200, 200, 220),
        'cell_user': (130, 180, 255),
        'cell_conflict': (255, 100, 100),
        'cell_hint': (100, 220, 160),
        'grid_line': (90, 90, 120),
        'grid_line_bold': (160, 160, 200),
        'note_color': (160, 160, 190),
        'btn_bg': (70, 70, 100),
        'btn_hover': (90, 90, 130),
        'btn_text': (220, 220, 240),
        'hud_text': (180, 180, 200),
        'overlay_bg': (20, 20, 35, 200),
        'title_color': (130, 180, 255),
        'accent': (130, 180, 255),
        'win_text': (255, 215, 0),
        'freq_full': (80, 200, 120),
        'freq_partial': (130, 180, 255),
    },
    'light': {
        'bg': (240, 240, 245),
        'grid_bg': (255, 255, 255),
        'cell_bg': (255, 255, 255),
        'cell_selected': (200, 220, 255),
        'cell_highlight': (230, 235, 250),
        'cell_same_num': (215, 205, 240),
        'cell_given': (30, 30, 50),
        'cell_user': (50, 100, 200),
        'cell_conflict': (220, 50, 50),
        'cell_hint': (20, 160, 80),
        'grid_line': (180, 180, 200),
        'grid_line_bold': (60, 60, 80),
        'note_color': (120, 120, 150),
        'btn_bg': (210, 215, 230),
        'btn_hover': (190, 195, 220),
        'btn_text': (40, 40, 60),
        'hud_text': (60, 60, 80),
        'overlay_bg': (255, 255, 255, 220),
        'title_color': (50, 100, 200),
        'accent': (50, 100, 200),
        'win_text': (220, 160, 0),
        'freq_full': (20, 160, 80),
        'freq_partial': (50, 100, 200),
    },
}

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 620, 820
GRID_ORIGIN = (35, 110)
CELL_SIZE = 60
GRID_SIZE = CELL_SIZE * 9
FPS = 60

DIFFICULTIES = ['easy', 'medium', 'hard', 'expert']

# ---------------------------------------------------------------------------
# SOUND HELPER
# ---------------------------------------------------------------------------
class SoundFX:
    """Simple sound effects using pygame.mixer with generated tones."""

    def __init__(self):
        self.enabled = True
        self._cache = {}

    def _generate_tone(self, freq, duration_ms=80):
        key = (freq, duration_ms)
        if key in self._cache:
            return self._cache[key]
        sample_rate = 44100
        n_samples = int(sample_rate * duration_ms / 1000)
        buf = bytes(2 * n_samples)
        import array
        arr = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / sample_rate
            val = int(16000 * math.sin(2 * math.pi * freq * t) *
                      max(0, 1 - i / n_samples))
            arr[i] = max(-32767, min(32767, val))
        snd = pygame.mixer.Sound(buffer=arr.tobytes())
        self._cache[key] = snd
        return snd

    def play_place(self):
        if self.enabled:
            self._generate_tone(520, 60).play()

    def play_error(self):
        if self.enabled:
            self._generate_tone(220, 150).play()

    def play_hint(self):
        if self.enabled:
            self._generate_tone(660, 80).play()

    def play_win(self):
        if self.enabled:
            for i, f in enumerate([523, 659, 784, 1047]):
                pygame.time.set_timer(pygame.USEREVENT + 10 + i, (i + 1) * 150, loops=1)
                self._cache[('win', i)] = self._generate_tone(f, 200)

    def play_win_tone(self, index):
        if self.enabled:
            snd = self._cache.get(('win', index))
            if snd:
                snd.play()

    def toggle(self):
        self.enabled = not self.enabled

# ---------------------------------------------------------------------------
# MAIN GAME UI CLASS
# ---------------------------------------------------------------------------
class GameUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sudoku")
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_md = pygame.font.SysFont("segoeui", 22)
        self.font_sm = pygame.font.SysFont("segoeui", 16)
        self.font_xs = pygame.font.SysFont("segoeui", 13)
        self.font_title = pygame.font.SysFont("segoeui", 44, bold=True)

        self.theme_name = 'dark'
        self.theme = THEMES[self.theme_name]
        self.sfx = SoundFX()
        self.generator = SudokuGenerator()
        self.validator = SudokuValidator()

        # Game state
        self.state = 'menu'  # menu | playing | paused | win | stats | leaderboard | tutorial
        self.difficulty = 'medium'
        self.solved_grid = None
        self.original_puzzle = None
        self.grid = None
        self.notes = None  # 9x9 array of sets
        self.selected = None  # (row, col)
        self.hints_remaining = 3
        self.hints_used = 0
        self.start_time = 0
        self.elapsed = 0
        self.paused_elapsed = 0
        self.note_mode = False
        self.conflicts = set()  # set of (row, col)

        # Undo / Redo
        self.undo_stack = []
        self.redo_stack = []

        # Win animation
        self.win_time = 0
        self.win_particles = []

    # --- PLACEHOLDER SECTIONS (to be filled) ---
    # SECTION: new_game
    def new_game(self, difficulty=None):
        if difficulty:
            self.difficulty = difficulty
        self.solved_grid, puzzle = self.generator.generate_puzzle(self.difficulty)
        self.original_puzzle = [row[:] for row in puzzle]
        self.grid = [row[:] for row in puzzle]
        self.notes = [[set() for _ in range(9)] for _ in range(9)]
        self.selected = None
        self.hints_remaining = 3
        self.hints_used = 0
        self.note_mode = False
        self.conflicts = set()
        self.undo_stack = []
        self.redo_stack = []
        self.start_time = time.time()
        self.paused_elapsed = 0
        self.elapsed = 0
        self.win_particles = []
        self.state = 'playing'
        StatsManager.record_game_start()

    # SECTION: handle_events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            # Win sound timers
            if event.type >= pygame.USEREVENT + 10 and event.type <= pygame.USEREVENT + 13:
                self.sfx.play_win_tone(event.type - pygame.USEREVENT - 10)
                continue
            if self.state == 'menu':
                self._handle_menu_event(event)
            elif self.state == 'playing':
                self._handle_play_event(event)
            elif self.state == 'paused':
                self._handle_pause_event(event)
            elif self.state == 'win':
                self._handle_win_event(event)
            elif self.state in ('stats', 'leaderboard', 'tutorial'):
                self._handle_overlay_event(event)
        return True

    # SECTION: handle_menu_events
    def _handle_menu_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Difficulty buttons
            for i, diff in enumerate(DIFFICULTIES):
                bx = WIDTH // 2 - 80
                by = 320 + i * 55
                if pygame.Rect(bx, by, 160, 42).collidepoint(mx, my):
                    self.new_game(diff)
                    return
            # Load game button
            load_rect = pygame.Rect(WIDTH // 2 - 80, 320 + len(DIFFICULTIES) * 55 + 10, 160, 42)
            if load_rect.collidepoint(mx, my):
                self._load_game()
                return
            # Stats button
            stats_rect = pygame.Rect(WIDTH // 2 - 170, 320 + len(DIFFICULTIES) * 55 + 62, 160, 42)
            if stats_rect.collidepoint(mx, my):
                self.state = 'stats'
            # Leaderboard button
            lb_rect = pygame.Rect(WIDTH // 2 + 10, 320 + len(DIFFICULTIES) * 55 + 62, 160, 42)
            if lb_rect.collidepoint(mx, my):
                self.state = 'leaderboard'
            # Theme toggle
            theme_rect = pygame.Rect(WIDTH - 50, 10, 40, 30)
            if theme_rect.collidepoint(mx, my):
                self._toggle_theme()

    def _handle_pause_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Resume
            if pygame.Rect(WIDTH//2 - 80, HEIGHT//2 - 30, 160, 42).collidepoint(mx, my):
                self.start_time = time.time()
                self.state = 'playing'
            # Save & Quit
            if pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 25, 160, 42).collidepoint(mx, my):
                self._save_game()
                self.state = 'menu'
            # Quit without save
            if pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 80, 160, 42).collidepoint(mx, my):
                self.state = 'menu'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.start_time = time.time()
            self.state = 'playing'

    def _handle_win_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 60, 160, 42).collidepoint(mx, my):
                self.state = 'menu'
            if pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 115, 160, 42).collidepoint(mx, my):
                self.new_game()

    def _handle_overlay_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = 'menu' if self.grid is None else 'playing'
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Close button area top-right of overlay
            self.state = 'menu' if self.grid is None else 'playing'

    # SECTION: handle_play_events
    def _handle_play_event(self, event):
        if event.type == pygame.KEYDOWN:
            key = event.key
            # ESC -> pause
            if key == pygame.K_ESCAPE:
                self.paused_elapsed += time.time() - self.start_time
                self.state = 'paused'
                return
            # Arrow keys navigation
            if self.selected:
                r, c = self.selected
                if key == pygame.K_UP: self.selected = (max(0, r-1), c)
                elif key == pygame.K_DOWN: self.selected = (min(8, r+1), c)
                elif key == pygame.K_LEFT: self.selected = (r, max(0, c-1))
                elif key == pygame.K_RIGHT: self.selected = (r, min(8, c+1))
            # Number keys
            if key in range(pygame.K_1, pygame.K_9 + 1):
                num = key - pygame.K_0
                self._place_number(num)
            if key in range(pygame.K_KP1, pygame.K_KP9 + 1):
                num = key - pygame.K_KP1 + 1
                self._place_number(num)
            # Delete / Backspace
            if key in (pygame.K_DELETE, pygame.K_BACKSPACE, pygame.K_0):
                self._place_number(0)
            # N -> toggle note mode
            if key == pygame.K_n:
                self.note_mode = not self.note_mode
            # Z -> undo, Y -> redo
            if key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                self._undo()
            if key == pygame.K_y and (event.mod & pygame.KMOD_CTRL):
                self._redo()
            # H -> hint
            if key == pygame.K_h:
                self._use_hint()
            # T -> tutorial
            if key == pygame.K_t:
                self.state = 'tutorial'

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            ox, oy = GRID_ORIGIN
            # Grid click
            if ox <= mx < ox + GRID_SIZE and oy <= my < oy + GRID_SIZE:
                col = (mx - ox) // CELL_SIZE
                row = (my - oy) // CELL_SIZE
                self.selected = (row, col)
            # HUD buttons (drawn later, define rects here)
            hud_y = GRID_ORIGIN[1] + GRID_SIZE + 15
            btns = self._get_hud_buttons(hud_y)
            for name, rect in btns.items():
                if rect.collidepoint(mx, my):
                    if name == 'hint': self._use_hint()
                    elif name == 'undo': self._undo()
                    elif name == 'redo': self._redo()
                    elif name == 'notes': self.note_mode = not self.note_mode
                    elif name == 'pause':
                        self.paused_elapsed += time.time() - self.start_time
                        self.state = 'paused'
                    elif name == 'theme': self._toggle_theme()
                    elif name == 'sound': self.sfx.toggle()

    def _get_hud_buttons(self, y):
        labels = ['undo', 'redo', 'notes', 'hint', 'pause', 'theme', 'sound']
        btns = {}
        bw = 72
        total = len(labels) * bw + (len(labels) - 1) * 6
        sx = (WIDTH - total) // 2
        for i, name in enumerate(labels):
            btns[name] = pygame.Rect(sx + i * (bw + 6), y, bw, 34)
        return btns

    def _toggle_theme(self):
        self.theme_name = 'light' if self.theme_name == 'dark' else 'dark'
        self.theme = THEMES[self.theme_name]

    # SECTION: place_number
    def _place_number(self, num):
        if not self.selected:
            return
        r, c = self.selected
        if self.original_puzzle[r][c] != 0:
            return  # can't edit given cells

        if self.note_mode and num != 0:
            old_notes = frozenset(self.notes[r][c])
            if num in self.notes[r][c]:
                self.notes[r][c].discard(num)
            else:
                self.notes[r][c].add(num)
            self.undo_stack.append(('note', r, c, old_notes, frozenset(self.notes[r][c])))
            self.redo_stack.clear()
            return

        old_val = self.grid[r][c]
        if old_val == num:
            return
        self.undo_stack.append(('val', r, c, old_val, num))
        self.redo_stack.clear()
        self.grid[r][c] = num
        if num != 0:
            self.notes[r][c].clear()
        self._update_conflicts()
        if num != 0 and (r, c) not in self.conflicts:
            self.sfx.play_place()
        elif (r, c) in self.conflicts:
            self.sfx.play_error()
        self._check_win()

    # SECTION: undo_redo
    def _undo(self):
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        if action[0] == 'val':
            _, r, c, old_val, _ = action
            self.grid[r][c] = old_val
            self._update_conflicts()
        elif action[0] == 'note':
            _, r, c, old_notes, _ = action
            self.notes[r][c] = set(old_notes)

    def _redo(self):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        if action[0] == 'val':
            _, r, c, _, new_val = action
            self.grid[r][c] = new_val
            if new_val != 0:
                self.notes[r][c].clear()
            self._update_conflicts()
        elif action[0] == 'note':
            _, r, c, _, new_notes = action
            self.notes[r][c] = set(new_notes)

    # SECTION: use_hint
    def _use_hint(self):
        if self.hints_remaining <= 0:
            return
        hint = self.validator.get_best_hint(self.grid, self.solved_grid)
        if hint:
            r, c, val = hint
            old_val = self.grid[r][c]
            self.grid[r][c] = val
            self.notes[r][c].clear()
            self.undo_stack.append(('val', r, c, old_val, val))
            self.redo_stack.clear()
            self.hints_remaining -= 1
            self.hints_used += 1
            self.selected = (r, c)
            self._update_conflicts()
            self.sfx.play_hint()
            self._check_win()

    # SECTION: check_win
    def _check_win(self):
        if self.validator.is_solved(self.grid):
            self.elapsed = self._get_elapsed()
            self.state = 'win'
            self.win_time = time.time()
            self.sfx.play_win()
            # Generate particles
            import random as rnd
            self.win_particles = []
            for _ in range(60):
                self.win_particles.append({
                    'x': rnd.randint(50, WIDTH - 50),
                    'y': rnd.randint(50, HEIGHT - 50),
                    'vx': rnd.uniform(-2, 2),
                    'vy': rnd.uniform(-3, -0.5),
                    'life': rnd.uniform(1.5, 3.0),
                    'color': rnd.choice([(255,215,0),(130,180,255),(100,220,160),(255,140,100)]),
                    'size': rnd.randint(3, 7),
                })
            StatsManager.record_game_win(self.difficulty, self.elapsed, self.hints_used)
            LeaderboardManager.add_entry(self.difficulty, self.elapsed)
            GameSaveManager.delete_save()

    # SECTION: update_conflicts
    def _update_conflicts(self):
        self.conflicts = set()
        for r in range(9):
            for c in range(9):
                if self.grid[r][c] != 0 and self.validator.has_conflict(self.grid, r, c):
                    self.conflicts.add((r, c))

    # SECTION: save_load
    def _save_game(self):
        state = {
            'grid': self.grid,
            'original': self.original_puzzle,
            'solved': self.solved_grid,
            'notes': [[list(s) for s in row] for row in self.notes],
            'difficulty': self.difficulty,
            'elapsed': self._get_elapsed(),
            'hints_remaining': self.hints_remaining,
            'hints_used': self.hints_used,
        }
        GameSaveManager.save_game(state)

    def _load_game(self):
        state = GameSaveManager.load_game()
        if state is None:
            return
        self.grid = state['grid']
        self.original_puzzle = state['original']
        self.solved_grid = state['solved']
        self.notes = [[set(s) for s in row] for row in state['notes']]
        self.difficulty = state['difficulty']
        self.paused_elapsed = state.get('elapsed', 0)
        self.hints_remaining = state.get('hints_remaining', 3)
        self.hints_used = state.get('hints_used', 0)
        self.start_time = time.time()
        self.undo_stack = []
        self.redo_stack = []
        self.note_mode = False
        self.selected = None
        self._update_conflicts()
        self.state = 'playing'

    # SECTION: get_elapsed
    def _get_elapsed(self):
        if self.state == 'playing':
            return self.paused_elapsed + (time.time() - self.start_time)
        return self.paused_elapsed

    # SECTION: draw
    def draw(self):
        self.screen.fill(self.theme['bg'])
        if self.state == 'menu':
            self._draw_menu()
        elif self.state == 'playing':
            self._draw_game()
        elif self.state == 'paused':
            self._draw_game()
            self._draw_pause()
        elif self.state == 'win':
            self._draw_game()
            self._draw_win()
        elif self.state == 'stats':
            self._draw_stats()
        elif self.state == 'leaderboard':
            self._draw_leaderboard()
        elif self.state == 'tutorial':
            self._draw_game()
            self._draw_tutorial()
        pygame.display.flip()

    # SECTION: draw_menu
    def _draw_menu(self):
        self._draw_centered_text("SUDOKU", self.font_title, self.theme['title_color'], 120)
        self._draw_centered_text("Select Difficulty", self.font_md, self.theme['hud_text'], 260)
        mx, my = pygame.mouse.get_pos()
        for i, diff in enumerate(DIFFICULTIES):
            rect = pygame.Rect(WIDTH // 2 - 80, 320 + i * 55, 160, 42)
            hover = rect.collidepoint(mx, my)
            self._draw_button(rect, diff.capitalize(), hover)
        # Load button
        load_rect = pygame.Rect(WIDTH // 2 - 80, 320 + len(DIFFICULTIES) * 55 + 10, 160, 42)
        saved = GameSaveManager.load_game() is not None
        if saved:
            self._draw_button(load_rect, "Continue", load_rect.collidepoint(mx, my))
        # Stats & Leaderboard
        sr = pygame.Rect(WIDTH // 2 - 170, 320 + len(DIFFICULTIES) * 55 + 62, 160, 42)
        lr = pygame.Rect(WIDTH // 2 + 10, 320 + len(DIFFICULTIES) * 55 + 62, 160, 42)
        self._draw_button(sr, "Stats", sr.collidepoint(mx, my))
        self._draw_button(lr, "Leaderboard", lr.collidepoint(mx, my))
        # Theme toggle
        tr = pygame.Rect(WIDTH - 50, 10, 40, 30)
        icon = "☀" if self.theme_name == 'dark' else "🌙"
        self._draw_button(tr, icon, tr.collidepoint(mx, my))

    # SECTION: draw_game
    def _draw_game(self):
        self._draw_hud()
        self._draw_grid()
        self._draw_number_freq()

    # SECTION: draw_grid
    def _draw_grid(self):
        ox, oy = GRID_ORIGIN
        t = self.theme
        sel_num = None
        if self.selected and self.grid:
            sr, sc = self.selected
            sel_num = self.grid[sr][sc]

        for r in range(9):
            for c in range(9):
                x = ox + c * CELL_SIZE
                y = oy + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                # Background
                bg = t['cell_bg']
                if self.selected and (r, c) == self.selected:
                    bg = t['cell_selected']
                elif self.selected and (r == self.selected[0] or c == self.selected[1]
                                        or (r//3 == self.selected[0]//3 and c//3 == self.selected[1]//3)):
                    bg = t['cell_highlight']
                # Highlight same number
                if sel_num and sel_num != 0 and self.grid[r][c] == sel_num and (r, c) != self.selected:
                    bg = t['cell_same_num']
                pygame.draw.rect(self.screen, bg, rect)

                val = self.grid[r][c]
                if val != 0:
                    is_given = self.original_puzzle[r][c] != 0
                    color = t['cell_given'] if is_given else t['cell_user']
                    if (r, c) in self.conflicts:
                        color = t['cell_conflict']
                    txt = self.font_lg.render(str(val), True, color)
                    self.screen.blit(txt, (x + (CELL_SIZE - txt.get_width()) // 2,
                                           y + (CELL_SIZE - txt.get_height()) // 2))
                elif self.notes[r][c]:
                    ns = CELL_SIZE // 3
                    for n in self.notes[r][c]:
                        nr = (n - 1) // 3
                        nc = (n - 1) % 3
                        nt = self.font_xs.render(str(n), True, t['note_color'])
                        nx = x + nc * ns + (ns - nt.get_width()) // 2
                        ny = y + nr * ns + (ns - nt.get_height()) // 2
                        self.screen.blit(nt, (nx, ny))

        # Grid lines
        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
            color = t['grid_line_bold'] if i % 3 == 0 else t['grid_line']
            pygame.draw.line(self.screen, color, (ox + i * CELL_SIZE, oy),
                             (ox + i * CELL_SIZE, oy + GRID_SIZE), thick)
            pygame.draw.line(self.screen, color, (ox, oy + i * CELL_SIZE),
                             (ox + GRID_SIZE, oy + i * CELL_SIZE), thick)

    # SECTION: draw_hud
    def _draw_hud(self):
        t = self.theme
        y = 15
        # Top bar: difficulty, timer, hints
        diff_txt = self.font_md.render(f"  {self.difficulty.capitalize()}  ", True, t['accent'])
        self.screen.blit(diff_txt, (20, y))
        elapsed = self._get_elapsed()
        time_txt = self.font_md.render(self._format_time(elapsed), True, t['hud_text'])
        self.screen.blit(time_txt, (WIDTH // 2 - time_txt.get_width() // 2, y))
        hint_txt = self.font_md.render(f"Hints: {self.hints_remaining}", True, t['hud_text'])
        self.screen.blit(hint_txt, (WIDTH - hint_txt.get_width() - 20, y))
        # Note mode indicator
        if self.note_mode:
            note_ind = self.font_sm.render("NOTES ON", True, t['accent'])
            self.screen.blit(note_ind, (WIDTH // 2 - note_ind.get_width() // 2, y + 30))
        # Sound indicator
        snd_txt = self.font_sm.render("🔊" if self.sfx.enabled else "🔇", True, t['hud_text'])
        self.screen.blit(snd_txt, (WIDTH - 40, y + 30))

        # Bottom HUD buttons
        hud_y = GRID_ORIGIN[1] + GRID_SIZE + 15
        mx, my = pygame.mouse.get_pos()
        btns = self._get_hud_buttons(hud_y)
        labels = {'undo': '↶', 'redo': '↷', 'notes': 'N', 'hint': '💡',
                  'pause': '⏸', 'theme': '☀' if self.theme_name == 'dark' else '🌙',
                  'sound': '🔊' if self.sfx.enabled else '🔇'}
        for name, rect in btns.items():
            hover = rect.collidepoint(mx, my)
            self._draw_button(rect, labels.get(name, name), hover)

    # SECTION: draw_number_freq
    def _draw_number_freq(self):
        t = self.theme
        y = GRID_ORIGIN[1] + GRID_SIZE + 58
        ox = GRID_ORIGIN[0]
        counts = [0] * 10
        for r in range(9):
            for c in range(9):
                v = self.grid[r][c]
                if v != 0:
                    counts[v] += 1
        bw = CELL_SIZE
        for n in range(1, 10):
            x = ox + (n - 1) * bw
            color = t['freq_full'] if counts[n] >= 9 else t['freq_partial']
            txt = self.font_md.render(str(n), True, color)
            self.screen.blit(txt, (x + (bw - txt.get_width()) // 2, y))
            ct = self.font_xs.render(str(counts[n]), True, t['hud_text'])
            self.screen.blit(ct, (x + (bw - ct.get_width()) // 2, y + 26))

    # SECTION: draw_overlay screens
    def _draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.theme['overlay_bg'])
        self.screen.blit(overlay, (0, 0))
        self._draw_centered_text("PAUSED", self.font_title, self.theme['title_color'], HEIGHT // 2 - 100)
        mx, my = pygame.mouse.get_pos()
        r1 = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 - 30, 160, 42)
        r2 = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 25, 160, 42)
        r3 = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 80, 160, 42)
        self._draw_button(r1, "Resume", r1.collidepoint(mx, my))
        self._draw_button(r2, "Save & Quit", r2.collidepoint(mx, my))
        self._draw_button(r3, "Quit", r3.collidepoint(mx, my))

    def _draw_win(self):
        # Particles
        dt = 1 / max(self.clock.get_fps(), 1)
        for p in self.win_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= dt
            if p['life'] > 0:
                alpha = min(255, int(255 * p['life'] / 2))
                s = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p['color'], alpha), (p['size'], p['size']), p['size'])
                self.screen.blit(s, (int(p['x']), int(p['y'])))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.theme['overlay_bg'])
        self.screen.blit(overlay, (0, 0))
        self._draw_centered_text("YOU WIN!", self.font_title, self.theme['win_text'], HEIGHT // 2 - 80)
        self._draw_centered_text(f"Time: {self._format_time(self.elapsed)}   Hints: {self.hints_used}",
                                 self.font_md, self.theme['hud_text'], HEIGHT // 2 - 20)
        mx, my = pygame.mouse.get_pos()
        r1 = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 60, 160, 42)
        r2 = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 115, 160, 42)
        self._draw_button(r1, "Menu", r1.collidepoint(mx, my))
        self._draw_button(r2, "New Game", r2.collidepoint(mx, my))

    def _draw_stats(self):
        t = self.theme
        self._draw_centered_text("STATISTICS", self.font_title, t['title_color'], 60)
        stats = StatsManager.get_stats()
        y = 140
        lines = [
            f"Games Played: {stats.get('games_played', 0)}",
            f"Games Won: {stats.get('games_won', 0)}",
            f"Total Hints Used: {stats.get('hints_used', 0)}",
            f"Total Time: {self._format_time(stats.get('total_time', 0))}",
        ]
        for line in lines:
            txt = self.font_md.render(line, True, t['hud_text'])
            self.screen.blit(txt, (60, y))
            y += 36
        y += 20
        per = stats.get('per_difficulty', {})
        for diff in DIFFICULTIES:
            d = per.get(diff, {})
            if d:
                bt = d.get('best_time')
                bt_str = self._format_time(bt) if bt else '--'
                line = f"{diff.capitalize()}: Won {d.get('won', 0)} | Best: {bt_str}"
                txt = self.font_sm.render(line, True, t['accent'])
                self.screen.blit(txt, (60, y))
                y += 28
        self._draw_centered_text("Press ESC to go back", self.font_sm, t['hud_text'], HEIGHT - 50)

    def _draw_leaderboard(self):
        t = self.theme
        self._draw_centered_text("LEADERBOARD", self.font_title, t['title_color'], 60)
        y = 140
        data = LeaderboardManager.get_all()
        for diff in DIFFICULTIES:
            entries = data.get(diff, [])
            header = self.font_md.render(f"— {diff.capitalize()} —", True, t['accent'])
            self.screen.blit(header, (WIDTH // 2 - header.get_width() // 2, y))
            y += 30
            if not entries:
                txt = self.font_sm.render("No records yet", True, t['hud_text'])
                self.screen.blit(txt, (80, y))
                y += 24
            for i, e in enumerate(entries[:3]):
                line = f"#{i+1}  {self._format_time(e['time'])}  ({e.get('date', '')})"
                txt = self.font_sm.render(line, True, t['hud_text'])
                self.screen.blit(txt, (80, y))
                y += 24
            y += 10
        self._draw_centered_text("Press ESC to go back", self.font_sm, t['hud_text'], HEIGHT - 50)

    def _draw_tutorial(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.theme['overlay_bg'])
        self.screen.blit(overlay, (0, 0))
        t = self.theme
        self._draw_centered_text("HOW TO PLAY", self.font_title, t['title_color'], 100)
        rules = [
            "Fill each row, column, and 3×3 box with digits 1-9.",
            "Click a cell, then press 1-9 to place a number.",
            "Press N to toggle Notes mode (pencil marks).",
            "Press H for a hint (3 per game).",
            "Arrow keys to navigate the grid.",
            "Ctrl+Z = Undo, Ctrl+Y = Redo.",
            "ESC to pause, save, or quit.",
            "Conflicting numbers are highlighted in red.",
        ]
        y = 200
        for rule in rules:
            txt = self.font_sm.render(f"• {rule}", True, t['hud_text'])
            self.screen.blit(txt, (60, y))
            y += 30
        self._draw_centered_text("Press ESC to close", self.font_sm, t['hud_text'], HEIGHT - 50)

    # SECTION: helpers
    def _draw_button(self, rect, text, hover=False):
        t = self.theme
        color = t['btn_hover'] if hover else t['btn_bg']
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        txt = self.font_sm.render(text, True, t['btn_text'])
        self.screen.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2,
                                rect.y + (rect.height - txt.get_height()) // 2))

    def _draw_centered_text(self, text, font, color, y):
        txt = font.render(text, True, color)
        self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))

    def _format_time(self, secs):
        m, s = divmod(int(secs), 60)
        return f"{m:02d}:{s:02d}"

    # SECTION: run
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
def main():
    ui = GameUI()
    ui.run()


if __name__ == '__main__':
    main()