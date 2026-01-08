import pygame
import random
from pygame.locals import *
from collections import namedtuple
from random import choice
import numpy as np
from multiprocessing import Pool
import math
import copy
import os

pygame.init()
pygame.font.init()


class AITetrisGame():
    def __init__(self, screen):
        # GLOBALS VARS
        self.s_width = 800
        self.s_height = 700
        self.play_width = 300  # meaning 300 // 10 = 30 width per block
        self.play_height = 600  # meaning 600 // 20 = 30 height per block
        self.block_size = 30
        self.PvAI_lost = False
        self.top_left_x = (self.s_width - self.play_width) // 2
        self.top_left_y = self.s_height - self.play_height
        self.paused = False
        # SHAPE FORMATS
        self.four_S = [['.....',
                        '.....',
                        '..00.',
                        '.00..',
                        '.....'],
                       ['.....',
                        '..0..',
                        '..00.',
                        '...0.',
                        '.....']]

        self.four_Z = [['.....',
                        '.....',
                        '.00..',
                        '..00.',
                        '.....'],
                       ['.....',
                        '..0..',
                        '.00..',
                        '.0...',
                        '.....']]

        self.four_I = [['..0..',
                        '..0..',
                        '..0..',
                        '..0..',
                        '.....'],
                       ['.....',
                        '0000.',
                        '.....',
                        '.....',
                        '.....']]

        self.four_O = [['.....',
                        '.....',
                        '.00..',
                        '.00..',
                        '.....']]

        self.four_J = [['.....',
                        '.0...',
                        '.000.',
                        '.....',
                        '.....'],
                       ['.....',
                        '..00.',
                        '..0..',
                        '..0..',
                        '.....'],
                       ['.....',
                        '.....',
                        '.000.',
                        '...0.',
                        '.....'],
                       ['.....',
                        '..0..',
                        '..0..',
                        '.00..',
                        '.....']]

        self.four_L = [['.....',
                        '...0.',
                        '.000.',
                        '.....',
                        '.....'],
                       ['.....',
                        '..0..',
                        '..0..',
                        '..00.',
                        '.....'],
                       ['.....',
                        '.....',
                        '.000.',
                        '.0...',
                        '.....'],
                       ['.....',
                        '.00..',
                        '..0..',
                        '..0..',
                        '.....']]

        self.four_T = [['.....',
                        '..0..',
                        '.000.',
                        '.....',
                        '.....'],
                       ['.....',
                        '..0..',
                        '..00.',
                        '..0..',
                        '.....'],
                       ['.....',
                        '.....',
                        '.000.',
                        '..0..',
                        '.....'],
                       ['.....',
                        '..0..',
                        '.00..',
                        '..0..',
                        '.....']]

        self.three_I = [['.....',
                         '..0..',
                         '..0..',
                         '..0..',
                         '.....'],
                        ['.....',
                         '.....',
                         '.000.',
                         '.....',
                         '.....']]

        self.three_J = [['.....',
                         '...0.',
                         '..00.',
                         '.....',
                         '.....'],
                        ['.....',
                         '...0.',
                         '...00',
                         '.....',
                         '.....'],
                        ['.....',
                         '.....',
                         '...00',
                         '...0.',
                         '.....'],
                        ['.....',
                         '.....',
                         '..00.',
                         '...0.',
                         '.....']]

        self.two_I = [['.....',
                       '..0..',
                       '..0..',
                       '.....',
                       '.....'],
                      ['.....',
                       '..00.',
                       '.....',
                       '.....',
                       '.....']]
        self.locked_positions = {}
        self.loser_flag = 'AI2_lost.txt'
        self.death_message = "AI LOST!"
        self.ai_loser_flag = "AI1_lost.txt"
        self.shared_pause = 0
        self.shapes = [self.four_S, self.four_Z, self.four_I, self.four_O, self.four_J, self.four_L, self.four_T,
                       self.three_I, self.three_J, self.two_I]
        self.shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255),
                             (128, 0, 128),
                             (165, 82, 201), (213, 48, 50), (78, 87, 84)]
        self.screen = screen
        # Dictionary dictating what each move represents as a number.
        self.movement_dict = {'Rotate': 1, 'Left': 2, 'Down': 3, 'Right': 4, 'Space': 5, 'Hold': 6}
        self.w1, self.w2, self.w3, self.w4 = -2.1, - 3.6, 3.8, 0.3
        self.line_multipliers = {
            1: 1,
            2: 3,
            3: 6,
            4: 10
        }
        try:
            self.clear_sound = pygame.mixer.Sound("NES Tetris Sound Effect_ Tetris Clear [ZcOiC6VvftE].mp3")

            self.gameover_sound = pygame.mixer.Sound("Undertale OST_ 011 - Determination-[AudioTrimmer.com].mp3")
        except FileNotFoundError as e:
            print(f"Error loading sound effects: {e}")
            self.clear_sound = self.gameover_sound = None

    class Piece(object):
        def __init__(self, x, y, orientation, shape_colors, shapes):
            self.x = x
            self.y = y
            self.shape = orientation
            self.color = shape_colors[shapes.index(orientation)]
            self.rotation = 0

    def create_grid(self, locked_pos={}):
        grid = [[(0, 0, 0) for _ in range(10)] for _ in range(20)]  # 20 rows, 10 columns, 3 color channels (RGB)
        for (x, y), color in locked_pos.items():
            grid[y][x] = color  # Set the color for locked positions
        return grid

    def convert_shape_format(self, shape):
        positions = []
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    positions.append((shape.x + j - 2, shape.y + i - 4))
        return positions

    def valid_space(self, shape, grid):
        formatted = self.convert_shape_format(shape)
        for (x, y) in formatted:
            if x < 0 or x >= 10 or y >= 20:  # Check if the position is out of bounds
                return False
            if y >= 0 and not np.array_equal(grid[y][x], [0, 0, 0]):  # Check if the cell is occupied
                return False
        return True

    def check_lost(self, positions):
        for pos in positions:
            x, y = pos
            if y < 0:
                return True
        return False

    def get_shape(self):
        return self.Piece(5, 0, random.choice(self.shapes), self.shape_colors, self.shapes)

    def draw_text_middle(self, surface, text, size, color):
        font = pygame.font.SysFont("comicsans", size, bold=True)
        label = font.render(text, 1, color)

        surface.blit(label, (
            self.top_left_x + self.play_width / 2 - (label.get_width() / 2),
            self.top_left_y + self.play_height / 2 - label.get_height() / 2))

    def draw_grid(self, surface, grid):
        sx = self.top_left_x
        sy = self.top_left_y

        for i in range(len(grid)):
            pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * self.block_size),
                             (sx + self.play_width, sy + i * self.block_size))
            for j in range(len(grid[i])):
                pygame.draw.line(surface, (128, 128, 128), (sx + j * self.block_size, sy),
                                 (sx + j * self.block_size, sy + self.play_height))

    def clear_rows(self, grid, locked):
        inc = 0
        for i in range(len(grid) - 1, -1, -1):
            row = grid[i]
            if (0, 0, 0) not in row:
                inc += 1
                ind = i
                for j in range(len(row)):
                    try:
                        del locked[(j, i)]
                    except:
                        continue
        if inc > 0:
            self.clear_sound.play()  # Play the sound effect
            for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
                x, y = key
                if y < ind:
                    newKey = (x, y + inc)
                    locked[newKey] = locked.pop(key)

        # Calculate the score based on the number of lines cleared
        multiplier = self.line_multipliers.get(inc, 0.0)  # Default to 0.0 if inc is not in the dictionary
        score = inc * multiplier * 10  # Assuming base score is 10 per line
        return inc, score

    def draw_next_shape(self, shape, surface):
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render('Next Shape', 1, (255, 255, 255))

        sx = self.top_left_x + self.play_width + 50
        sy = self.top_left_y + self.play_height / 2 - 100
        format = shape.shape[shape.rotation % len(shape.shape)]

        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    pygame.draw.rect(surface, shape.color,
                                     (sx + j * self.block_size, sy + i * self.block_size, self.block_size,
                                      self.block_size), 0)

        surface.blit(label, (sx + 10, sy - 50))

    def update_score(self, nscore):
        score = self.max_score()

        with open('AI2_Score.txt', 'w') as f:
            if int(score) > nscore:
                f.write(str(score))
            else:
                f.write(str(nscore))

    def aggregated_heights(self, grid):
        heights = [0] * 10  # A grid width of 10 columns
        for col in range(10):
            for row in range(20):
                if grid[row][col] != (0, 0, 0):  # Check if the cell is filled
                    heights[col] = 20 - row  # Height is the distance from the bottom
                    break  # Stop at the first filled cell
        return heights

    def check_lines_cleared(self, grid):
        """Check how many lines would be cleared in the given grid state."""
        lines_cleared = 0
        for row in grid:
            if all(cell != (0, 0, 0) for cell in row):
                lines_cleared += 1
        return lines_cleared
        # AI Evaluation Functions

    def calculate_hole_depth(self, grid):
        """Calculate how deep holes are by counting blocks above them"""
        hole_depth = 0
        for col in range(10):
            # Track the highest block in this column
            highest_block = None
            for row in range(20):
                if grid[row][col] != (0, 0, 0):
                    highest_block = row
                    break

            # If column has blocks, check for holes below them
            if highest_block is not None:
                for row in range(highest_block, 20):
                    if grid[row][col] == (0, 0, 0):  # Found a hole
                        # Count how many blocks are above this hole
                        blocks_above = 0
                        for above_row in range(row):
                            if grid[above_row][col] != (0, 0, 0):
                                blocks_above += 1
                        hole_depth += blocks_above
        return hole_depth

    def evaluate_position(self, grid, piece_positions):
        temp_grid = [row.copy() for row in grid]

        # Place the piece in the temporary grid
        for (x, y) in piece_positions:
            if 0 <= y < 20 and 0 <= x < 10:
                temp_grid[y][x] = (100, 100, 100)  # Mark as occupied

        heights = self.aggregated_heights(temp_grid)
        max_height = max(heights)
        holes = self.count_holes(temp_grid)
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(9))
        lines_cleared = self.check_lines_cleared(temp_grid)
        tetris_potential = self.calculate_tetris_potential(temp_grid)
        overhang_penalty = self.calculate_overhang_penalty(temp_grid)

        # Improved weights
        score = (
                50 * lines_cleared -  # Prioritize line clears
                2 * max_height -  # Penalize high stacks
                5 * holes -  # Avoid holes
                1.5 * bumpiness -  # Smooth surface
                2 * overhang_penalty -  # No overhangs!
                1 * self.calculate_wells(heights)  # Reward good well setups
        )

        return score

    def count_column_transitions(self, grid):
        """Count vertical transitions between filled and empty cells"""
        transitions = 0
        for col in range(10):
            for row in range(19):
                if (grid[row][col] == (0, 0, 0)) != (grid[row + 1][col] == (0, 0, 0)):
                    transitions += 1
        return transitions

    def count_row_transitions(self, grid):
        """Count horizontal transitions between filled and empty cells"""
        transitions = 0
        for row in range(20):
            for col in range(9):
                if (grid[row][col] == (0, 0, 0)) != (grid[row][col + 1] == (0, 0, 0)):
                    transitions += 1
        return transitions

    def calculate_wells(self, heights):
        wells = 0
        for i in range(10):
            left = heights[i - 1] if i > 0 else float('inf')
            right = heights[i + 1] if i < 9 else float('inf')
            current = heights[i]
            if current < left and current < right:
                depth = min(left, right) - current
                if depth >= 3:
                    wells -= depth * 2
                else:
                    wells += depth * 0.5
        return wells

    def calculate_overhang_penalty(self, grid):
        penalty = 0
        for col in range(10):
            for row in range(19):  # Up to second-to-last row
                if grid[row][col] != (0, 0, 0) and grid[row + 1][col] == (0, 0, 0):
                    penalty += 1
        return penalty

    def get_ai_move(self, current_piece, grid, hold_piece=None):
        """More thorough move evaluation with better hold strategy"""
        best_score = float('-inf')
        best_actions = []
        original_piece = current_piece

        # Evaluate both current piece and hold piece
        pieces_to_try = [(current_piece, False)]
        if hold_piece is not None:
            pieces_to_try.append((hold_piece, True))

        for piece, use_hold in pieces_to_try:
            for rotation in range(len(piece.shape)):
                # Create a test piece for this rotation
                test_piece = self.Piece(piece.x, piece.y, piece.shape,
                                        self.shape_colors, self.shapes)
                test_piece.rotation = rotation

                # Try all possible x positions
                for x_offset in range(-5, 6):  # Wider range of x positions
                    test_piece.x = original_piece.x + x_offset

                    if not self.valid_space(test_piece, grid):
                        continue

                    # Find the lowest position
                    while self.valid_space(test_piece, grid):
                        test_piece.y += 1
                    test_piece.y -= 1

                    # Evaluate this position
                    piece_positions = self.convert_shape_format(test_piece)
                    score = self.evaluate_position(grid, piece_positions)

                    # Add small random factor to avoid getting stuck in local optima
                    score += random.uniform(-0.5, 0.5)

                    # If this is better than current best, update
                    if score > best_score:
                        best_score = score
                        actions = []

                        if use_hold:
                            actions.append(self.movement_dict['Hold'])

                        # Calculate needed rotations
                        rotation_diff = (rotation - original_piece.rotation) % len(piece.shape)
                        for _ in range(rotation_diff):
                            actions.append(self.movement_dict['Rotate'])

                        # Calculate needed horizontal moves
                        x_diff = test_piece.x - original_piece.x
                        if x_diff > 0:
                            actions.extend([self.movement_dict['Right']] * abs(x_diff))
                        elif x_diff < 0:
                            actions.extend([self.movement_dict['Left']] * abs(x_diff))

                        # Always hard drop at the end
                        actions.append(self.movement_dict['Space'])
                        best_actions = actions

        return best_actions if best_actions else []

    def rotate_piece(self, shape, grid):
        original_rotation = shape.rotation
        shape.rotation = (shape.rotation + 1) % len(shape.shape)
        if not self.valid_space(shape, grid):
            for offset in [1, -1, 2, -2]:
                shape.x += offset
                if self.valid_space(shape, grid):
                    break
            else:
                shape.rotation = original_rotation  # Revert
                shape.x -= offset

    def left_once(self, current_piece, grid):
        current_piece.x -= 1
        if not self.valid_space(current_piece, grid):
            current_piece.x += 1
        # Additional check - if piece is on ground, don't allow move
        current_piece.y += 1
        if not self.valid_space(current_piece, grid):
            current_piece.y -= 1
            return False  # Piece is on ground, can't move
        current_piece.y -= 1
        return True

    def right_once(self, current_piece, grid):
        current_piece.x += 1
        if not self.valid_space(current_piece, grid):
            current_piece.x -= 1
        # Additional check - if piece is on ground, don't allow move
        current_piece.y += 1
        if not self.valid_space(current_piece, grid):
            current_piece.y -= 1
            return False  # Piece is on ground, can't move
        current_piece.y -= 1
        return True

    def down_once(self, current_piece, grid):
        current_piece.y += 1
        if not self.valid_space(current_piece, grid):
            current_piece.y -= 1

    def space_once(self, current_piece, grid):
        while self.valid_space(current_piece, grid):
            current_piece.y += 1
        current_piece.y -= 1

    def count_holes(self, grid):
        holes = 0
        for col in range(10):
            block_found = False
            for row in range(20):
                if grid[row][col] != (0, 0, 0):
                    block_found = True
                elif block_found:
                    holes += 1
        return holes

    def calculate_tetris_potential(self, grid):
        """Calculate potential for future Tetris (4-line clears)"""
        potential = 0
        for col in range(10):
            # Check if column is mostly empty at top
            empty_top = 0
            for row in range(4):
                if grid[row][col] == (0, 0, 0):
                    empty_top += 1
            if empty_top >= 3:  # Column has room for I-piece
                potential += 1
        return potential

    def check_ai_stuck(self, grid, current_piece):
        """Check if the AI is stuck in a bad position"""
        # Count how many moves we have left before hitting something
        test_piece = copy.deepcopy(current_piece)
        moves_left = 0
        test_piece.x -= 1
        if self.valid_space(test_piece, grid):
            moves_left += 1
        test_piece.x += 2
        if self.valid_space(test_piece, grid):
            moves_left += 1

        # Check if we're in a position with no good moves
        if moves_left == 0 and not self.valid_space(test_piece, grid):
            return True
        return False

    def calculate_penalty(self, grid):
        heights_penalty = max(self.aggregated_heights(grid)) * -1
        return heights_penalty

    def max_score(self):
        try:
            with open('AI2_Score.txt', 'r') as f:
                lines = f.readlines()
                score = lines[0].strip()
        except (FileNotFoundError, IndexError):
            score = "0"
        return score

    def draw_dynamic_text_block(
            self,
            surface,
            label_text,
            value_text,
            x,
            y,
            label_font_size=30,
            value_font_size=30,
            label_font_name="comicsans",
            value_font_name="comicsans",
            color=(255, 255, 255),
            max_width=180,
            spacing=5,
            align='left',
            v_align='top'
    ):
        """
        General-purpose text block renderer with scaling, alignment, and vertical centering.

        :param surface: Pygame surface to draw on
        :param label_text: Top text (e.g. "Score:")
        :param value_text: Bottom text (e.g. "182700")
        :param x: Base X position
        :param y: Base Y position
        :param align: Horizontal alignment: 'left', 'center', 'right'
        :param v_align: Vertical alignment: 'top', 'middle', 'bottom'
        """
        # Render label
        label_font = pygame.font.SysFont(label_font_name, label_font_size)
        label_render = label_font.render(label_text, True, color)

        # Render value with scaling
        current_size = value_font_size
        value_font = pygame.font.SysFont(value_font_name, current_size)
        value_render = value_font.render(value_text, True, color)

        while value_render.get_width() > max_width and current_size > 12:
            current_size -= 2
            value_font = pygame.font.SysFont(value_font_name, current_size)
            value_render = value_font.render(value_text, True, color)

        # Combined height
        total_height = label_render.get_height() + spacing + value_render.get_height()

        # Determine top-left Y based on vertical alignment
        if v_align == 'middle':
            base_y = y - total_height // 2
        elif v_align == 'bottom':
            base_y = y - total_height
        else:  # 'top'
            base_y = y

        label_y = base_y
        value_y = base_y + label_render.get_height() + spacing

        # Determine X based on alignment
        if align == 'center':
            label_x = x - label_render.get_width() // 2
            value_x = x - value_render.get_width() // 2
        elif align == 'right':
            label_x = x - label_render.get_width()
            value_x = x - value_render.get_width()
        else:
            label_x = x
            value_x = x

        # Blit both
        surface.blit(label_render, (label_x, label_y))
        surface.blit(value_render, (value_x, value_y))

    def draw_window(self, surface, grid, score=0, last_score=0, initial_lines_cleared=0):
        surface.fill((0, 0, 0))  # Clear screen

        # --- Title ---
        # --- Title (auto-positioned above the Tetris board) ---
        title_font = pygame.font.SysFont("comicsans", 60)
        title_label = title_font.render("Tetris", True, (255, 255, 255))

        # Compute center above the board
        title_x = self.top_left_x + self.play_width // 2 - title_label.get_width() // 2

        # Place the title *just above* the playfield, with smart padding
        padding = max(10, self.block_size // 2)
        title_y = max(0, self.top_left_y - title_label.get_height() - padding)

        surface.blit(title_label, (title_x, title_y))

        # --- Dynamic Score ---
        sx_right = self.top_left_x + self.play_width + 50
        sy_right = self.top_left_y + self.play_height // 2 - 100
        self.draw_dynamic_text_block(
            surface,
            'Score:',
            str(score),
            sx_right + 10,
            sy_right + 160,
            label_font_size=30,
            value_font_size=30,
            align='left',
            max_width=180
        )

        # --- Dynamic Level ---
        level = str(initial_lines_cleared // 10)
        self.draw_dynamic_text_block(
            surface,
            'Level:',
            level,
            sx_right + 10,
            sy_right - 200,
            label_font_size=30,
            value_font_size=30,
            align='left',
            max_width=180
        )

        # --- Dynamic High Score ---
        sx_left = self.top_left_x - 200
        sy_left = self.top_left_y + 200
        self.draw_dynamic_text_block(
            surface,
            'High Score:',
            str(last_score),
            sx_left,
            sy_left + 160,
            label_font_size=30,
            value_font_size=30,
            align='left',
            max_width=180
        )

        # --- Tetris Grid ---
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                pygame.draw.rect(
                    surface,
                    grid[i][j],
                    (
                        self.top_left_x + j * self.block_size,
                        self.top_left_y + i * self.block_size,
                        self.block_size,
                        self.block_size
                    ),
                    0
                )

        # --- Border & Grid Lines ---
        pygame.draw.rect(
            surface,
            (255, 0, 0),
            (self.top_left_x, self.top_left_y, self.play_width, self.play_height),
            5
        )
        self.draw_grid(surface, grid)

    def draw_hold_piece(self, hold_piece, surface):
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render('Hold', 1, (255, 255, 255))

        sx = self.top_left_x - 200
        sy = self.top_left_y + 50

        surface.blit(label, (sx + 10, sy - 30))

        if hold_piece is not None:
            format = hold_piece.shape[hold_piece.rotation % len(hold_piece.shape)]
            for i, line in enumerate(format):
                row = list(line)
                for j, column in enumerate(row):
                    if column == '0':
                        pygame.draw.rect(surface, hold_piece.color,
                                         (sx + j * self.block_size, sy + i * self.block_size, self.block_size,
                                          self.block_size), 0)

    def main(self, win):
        pygame.init()
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("Original Tetris theme (Tetris Soundtrack).mp3")
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading music: {e}")
        if os.path.exists(self.loser_flag):
            os.remove(self.loser_flag)
        initial_lines_cleared = 0
        last_score = self.max_score()
        self.locked_positions = {}
        grid = self.create_grid(self.locked_positions)
        change_piece = False
        run = True
        paused = False
        current_piece = self.get_shape()
        next_piece = self.get_shape()
        clock = pygame.time.Clock()
        hold_piece = None
        can_hold = True
        fall_time = 0
        initial_fall_speed = 0.2
        fall_speed = initial_fall_speed
        speed_increase_interval = 100
        max_speed = 0.05
        rotation_delay = 200
        move_delay = 150
        last_rotation_time = pygame.time.get_ticks()
        last_move_time = pygame.time.get_ticks()
        level_time = 0
        score = 0
        iterations = 0
        ai_enabled = True  # Add this to control AI
        ai_move_delay = 300  # Milliseconds between AI moves
        last_ai_move_time = pygame.time.get_ticks()
        ai_thinking_time = 0
        max_ai_thinking_time = 150  # Max milliseconds allowed for AI to think
        ai_move_queue = []
        while run:
            grid = self.create_grid(self.locked_positions)
            clock.tick(120)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.display.quit()
                    return


            if not paused:
                fall_time += clock.get_rawtime()
                level_time += clock.get_rawtime()
                fall_speed = initial_fall_speed
                if score >= speed_increase_interval:
                    if initial_lines_cleared % 10 == 0 and initial_lines_cleared != 0:
                        fall_speed *= 0.9

                if fall_time / 1000 > fall_speed:
                    fall_time = 0
                    current_piece.y += 1
                    if not (self.valid_space(current_piece, grid)) and current_piece.y > 0:
                        current_piece.y -= 1
                        change_piece = True

                if iterations == 0:
                    if can_hold:  # Hold piece
                        if hold_piece is None:
                            hold_piece = current_piece
                            current_piece = next_piece
                            next_piece = self.get_shape()
                        else:
                            hold_piece, current_piece = current_piece, hold_piece
                            current_piece.x = 5
                            current_piece.y = 0
                        can_hold = False
                current_time = pygame.time.get_ticks()
                # AI movement (when enabled)
                if not change_piece:

                    if ai_enabled and (current_time - last_ai_move_time) > ai_move_delay:
                        if not ai_move_queue:
                            ai_move_queue = self.get_ai_move(current_piece, grid, hold_piece)

                        if ai_move_queue:
                            action = ai_move_queue.pop(0)

                            if action == self.movement_dict['Rotate']:
                                self.rotate_piece(current_piece, grid)
                            elif action == self.movement_dict['Left']:
                                self.left_once(current_piece, grid)
                            elif action == self.movement_dict['Right']:
                                self.right_once(current_piece, grid)
                            elif action == self.movement_dict['Space']:
                                self.space_once(current_piece, grid)
                            elif action == self.movement_dict['Hold'] and can_hold:
                                if hold_piece is None:
                                    hold_piece = current_piece
                                    current_piece = next_piece
                                    next_piece = self.get_shape()
                                else:
                                    hold_piece, current_piece = current_piece, hold_piece
                                    current_piece.x = 5
                                    current_piece.y = 0
                                can_hold = False

                            last_ai_move_time = current_time
                shape_pos = self.convert_shape_format(current_piece)
                for i in range(len(shape_pos)):
                    x, y = shape_pos[i]
                    if y > -1:
                        grid[y][x] = current_piece.color

                if change_piece:
                    for pos in shape_pos:
                        p = (pos[0], pos[1])
                        self.locked_positions[p] = current_piece.color
                    current_piece = next_piece
                    next_piece = self.get_shape()
                    change_piece = False
                    can_hold = True

                    # Clear rows and update the score
                    new_lines_cleared, score_increase = self.clear_rows(grid, self.locked_positions)
                    initial_lines_cleared += new_lines_cleared
                    if initial_lines_cleared % 10 == 0 and initial_lines_cleared != 0:
                        rotation_delay *= 0.99
                        move_delay *= 0.99
                    score += int(score_increase)

            self.draw_window(win, grid, score, last_score, initial_lines_cleared)
            self.draw_next_shape(next_piece, win)
            self.draw_hold_piece(hold_piece, win)
            pygame.display.update()
            iterations += 1
            if self.check_lost(self.locked_positions):
                # Game over logic
                with open(self.loser_flag, "w") as f:
                    f.write("lost")
                pygame.mixer.music.stop()

                pygame.mixer.music.stop()

                # Display "YOU LOST!" for 1 second
                pygame.mixer.Sound.play(self.gameover_sound)
                self.draw_text_middle(win, self.death_message, 80, (255, 255, 255))
                pygame.display.update()
                pygame.time.delay(1000)  # Delay for 1 second (1000 milliseconds)

                # Switch to "PRESS ANY KEY TO EXIT"
                # Redraw the game screen to "erase" the "YOU LOST!" text
                self.draw_window(win, grid, score, last_score)  # Redraw the grid and UI
                self.draw_next_shape(next_piece, win)  # Redraw the next piece
                self.draw_hold_piece(hold_piece, win)  # Redraw the hold piece
                pygame.display.update()
                pygame.time.delay(1000)
                self.draw_text_middle(win, 'PRESS ESC KEY TO EXIT', 40, (255, 255, 255))
                pygame.display.update()
                self.locked_positions = {}
                grid = self.create_grid(self.locked_positions)
                current_piece = self.get_shape()
                next_piece = self.get_shape()
                self.update_score(score)
                score = 0
                level = 1
                iterations = 0
                fall_time = 0
                fall_speed = 0.2
                hold_piece = None
                can_hold = True
                rotation_delay = 240
                move_delay = 200
                ai_move_delay = 300
                # Wait for any key press to exit
                waiting_for_input = True
                while waiting_for_input:
                    for event in pygame.event.get():
                        match event.type:
                            case pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    waiting_for_input = False

                            case pygame.QUIT:
                                waiting_for_input = False
                            case _:
                                pass
                if os.path.exists(self.loser_flag):
                    os.remove(self.loser_flag)
                run = False

                self.update_score(score)
            if os.path.exists(self.ai_loser_flag):
                pygame.mixer.music.stop()

                pygame.mixer.music.stop()

                # Display "YOU LOST!" for 1 second

                self.draw_text_middle(win, "YOU WIN!", 80, (255, 255, 255))
                pygame.display.update()
                pygame.time.delay(1000)  # Delay for 1 second (1000 milliseconds)

                # Switch to "PRESS ANY KEY TO EXIT"
                # Redraw the game screen to "erase" the "YOU LOST!" text
                self.draw_window(win, grid, score, last_score)  # Redraw the grid and UI
                self.draw_next_shape(next_piece, win)  # Redraw the next piece
                self.draw_hold_piece(hold_piece, win)  # Redraw the hold piece
                pygame.display.update()
                pygame.time.delay(1000)
                self.draw_text_middle(win, 'PRESS ESC KEY TO EXIT', 40, (255, 255, 255))
                pygame.display.update()
                self.locked_positions = {}
                grid = self.create_grid(self.locked_positions)
                current_piece = self.get_shape()
                next_piece = self.get_shape()
                self.update_score(score)
                score = 0
                level = 1
                fall_time = 0
                fall_speed = 0.2
                hold_piece = None
                can_hold = True
                rotation_delay = 240
                move_delay = 200
                ai_move_delay = 300  # Reset AI move timing
                # Wait for any key press to exit
                waiting_for_input = True
                while waiting_for_input:
                    for event in pygame.event.get():
                        match event.type:
                            case pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    waiting_for_input = False

                            case pygame.QUIT:
                                waiting_for_input = False
                            case _:
                                pass
                run = False
                self.update_score(score)
        if os.path.exists(self.loser_flag):
            os.remove(self.loser_flag)

    def main_menu(self, win):
        run = True
        while run:
            win.fill((0, 0, 0))
            self.draw_text_middle(win, 'Press Any Key To Play', 60, (255, 255, 255))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN:
                    self.main(win)

        pygame.display.quit()










