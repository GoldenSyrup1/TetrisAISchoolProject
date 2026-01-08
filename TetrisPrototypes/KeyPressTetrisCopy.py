import pygame
import random
from pygame.locals import *
from collections import namedtuple
from random import choice
import numpy as np
from multiprocessing import Pool
import math
import copy

pygame.init()
pygame.font.init()
class AITetrisGame():
    def __init__(self):
        # GLOBALS VARS
        self.s_width = 800
        self.s_height = 700
        self.play_width = 300  # meaning 300 // 10 = 30 width per block
        self.play_height = 600  # meaning 600 // 20 = 30 height per block
        self.block_size = 30

        self.top_left_x = (self.s_width - self.play_width) // 2
        self.top_left_y = self.s_height - self.play_height

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

        self.shapes = [self.four_S, self.four_Z, self.four_I, self.four_O, self.four_J, self.four_L, self.four_T,
                       self.three_I, self.three_J, self.two_I]
        self.shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255),
                             (128, 0, 128),
                             (165, 82, 201), (213, 48, 50), (78, 87, 84)]
        self.screen = pygame.display.set_mode((800,700))
        # Dictionary dictating what each move represents as a number.
        self.movement_dict = {'Rotate': 1, 'Left': 2, 'Down': 3, 'Right': 4, 'Space': 5, 'Hold': 6}
        self.w1, self.w2, self.w3, self.w4 = -2.1, - 3.6, 3.8, 0.3
        self.line_multipliers = {
            1: 1,
            2: 3,
            3: 6,
            4: 10
        }

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
        self.screen.blit(surface,(0,0))
    def draw_grid(self, surface, grid):
        sx = self.top_left_x
        sy = self.top_left_y

        for i in range(len(grid)):
            pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * self.block_size),
                             (sx + self.play_width, sy + i * self.block_size))
            for j in range(len(grid[i])):
                pygame.draw.line(surface, (128, 128, 128), (sx + j * self.block_size, sy),
                                 (sx + j * self.block_size, sy + self.play_height))
        self.screen.blit(surface,(0,0))
    try:
        clear_sound = pygame.mixer.Sound("NES Tetris Sound Effect_ Tetris Clear [ZcOiC6VvftE].mp3")
        pause_sound = pygame.mixer.Sound("Super Mario Bros.-Pause Sound Effect.mp3")
        gameover_sound = pygame.mixer.Sound("Undertale OST_ 011 - Determination-[AudioTrimmer.com].mp3")
    except FileNotFoundError as e:
        print(f"Error loading sound effects: {e}")
        clear_sound = pause_sound = gameover_sound = None

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
        score = inc * multiplier * 100  # Assuming base score is 100 per line
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
        self.screen.blit(surface, (0, 0))
    def update_score(self, nscore):
        score = self.max_score()

        with open('PillarPenaltyScores.txt', 'w') as f:
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

    def rotate_piece(self, shape, grid):
        original_rotation = shape.rotation
        shape.rotation = (shape.rotation + 1) % len(shape.shape)
        if not self.valid_space(shape, grid):
            # Try shifting the piece left or right to make it fit
            shape.x += 1
            if not self.valid_space(shape, grid):
                shape.x -= 2
                if not self.valid_space(shape, grid):
                    shape.x += 1
                    shape.rotation = original_rotation

    def left_once(self, current_piece, grid):
        current_piece.x -= 1
        if not self.valid_space(current_piece, grid):
            current_piece.x += 1

    def right_once(self, current_piece, grid):
        current_piece.x += 1
        if not self.valid_space(current_piece, grid):
            current_piece.x -= 1

    def down_once(self, current_piece, grid):
        current_piece.y += 1
        if not self.valid_space(current_piece, grid):
            current_piece.y -= 1

    def space_once(self, current_piece, grid):
        while self.valid_space(current_piece, grid):
            current_piece.y += 1
        current_piece.y -= 1

    def calculate_hole_penalty(self, grid):
        """
        Calculates a penalty score based on:
        - The number of holes
        - The depth of holes
        - The height differences (pillar control)
        - Empty pillars (gaps between two high columns)

        :param grid: The Tetris grid.
        :return: A penalty score.
        """
        num_holes = 0
        hole_depth_penalty = 0
        column_heights = [0] * 10
        empty_pillar_penalty = 0

        for col in range(10):
            block_found = False
            hole_depth = 0

            for row in range(20):
                if grid[row][col] != (0, 0, 0):
                    block_found = True
                    if column_heights[col] == 0:
                        column_heights[col] = 20 - row
                    hole_depth = 0
                elif block_found:
                    num_holes += 1
                    hole_depth += 1
                    hole_depth_penalty += hole_depth

                    # Penalize height differences (pillar control)
        height_penalty = sum(abs(column_heights[i] - column_heights[i + 1]) for i in range(9))

        # **New Addition**: Penalize empty pillars
        for col in range(1, 9):  # Skip first & last column (no two neighbors)
            if column_heights[col] == 0:  # Check if it's an empty column
                left_height = column_heights[col - 1]
                right_height = column_heights[col + 1]

                if min(left_height, right_height) >= 3:  # Ensure it's surrounded by taller columns
                    empty_pillar_penalty += 5  # Assign penalty (adjust weight if necessary)

        penalty = (num_holes * -4) + (hole_depth_penalty * -2) + (height_penalty * -1) + (empty_pillar_penalty * -5) + (max(column_heights) * -1)
        return penalty
    def best_move(self, current_piece, grid, locked_positions):
        init_grid = grid
        best_score = float('-inf')
        best_position = None
        best_rotation = None

        for rotation in range(len(current_piece.shape)):  # Try all rotations
            temp_piece = self.Piece(current_piece.x, current_piece.y, current_piece.shape, self.shape_colors,
                                    self.shapes)
            temp_piece.rotation = rotation

            for move in range(-5, 6):  # Try moving left and right
                temp_piece.x = 5 + move  # Start from middle
                if not self.valid_space(temp_piece, grid):
                    continue
                self.space_once(temp_piece, grid)
                # Evaluate board after the move
                new_grid = self.create_grid(locked_positions)
                for pos in self.convert_shape_format(temp_piece):
                    x, y = pos
                    if y >= 0:
                        new_grid[y][x] = temp_piece.color
                score = self.calculate_hole_penalty(new_grid)
                if score > best_score:
                    best_score = score
                    best_position = (temp_piece.x, temp_piece.y)
                    best_rotation = rotation
        return best_position, best_rotation

    def max_score(self):
        try:
            with open('PillarPenaltyScores.txt', 'r') as f:
                lines = f.readlines()
                score = lines[0].strip()
        except (FileNotFoundError, IndexError):
            score = "0"
        return score

    # Dynamically change window screen size to make it adjustable
    def handle_resize(self, event):
        self.s_width, self.s_height = event.size
        self.block_size = min(self.s_width // 10, self.s_height // 20)
        self.play_width = self.block_size * 10
        self.play_height = self.block_size * 20
        self.top_left_x = (self.s_width - self.play_width) // 2
        self.top_left_y = self.s_height - self.play_height

    def draw_window(self, surface, grid, score=0, last_score=0, initial_lines_cleared=0):
        surface.fill((0, 0, 0))

        pygame.font.init()
        font = pygame.font.SysFont('comicsans', 60)
        label = font.render('Tetris', 1, (255, 255, 255))

        surface.blit(label, (self.top_left_x + self.play_width / 2 - (label.get_width() / 2), 30))

        # current score
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render('Score: ' + str(score), 1, (255, 255, 255))
        level_label = font.render('Level: ' + str(int((initial_lines_cleared / 10))), 1, (255, 255, 255))
        sx = self.top_left_x + self.play_width + 50
        sy = self.top_left_y + self.play_height / 2 - 100

        surface.blit(label, (sx + 10, sy + 160))
        surface.blit(level_label, (sx + 20, sy - 110))
        # last score
        label = font.render('High Score: ', 1, (255, 255, 255))
        score_label = font.render(f'{last_score}', 1, (255, 255, 255))

        sx = self.top_left_x - 200
        sy = self.top_left_y + 200

        surface.blit(label, (sx - 20, sy + 160))
        surface.blit(score_label, (sx, sy + 220))

        for i in range(len(grid)):
            for j in range(len(grid[i])):
                pygame.draw.rect(surface, grid[i][j],
                                 (self.top_left_x + j * self.block_size, self.top_left_y + i * self.block_size,
                                  self.block_size, self.block_size), 0)

        pygame.draw.rect(surface, (255, 0, 0), (self.top_left_x, self.top_left_y, self.play_width, self.play_height), 5)
        self.screen.blit(surface, (0, 0))
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
        self.screen.blit(surface, (0, 0))
    def main(self, win):
        pygame.init()
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("Original Tetris theme (Tetris Soundtrack).mp3")
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading music: {e}")
        initial_lines_cleared = 0
        last_score = self.max_score()
        locked_positions = {}
        grid = self.create_grid(locked_positions)
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

        while run:
            grid = self.create_grid(locked_positions)
            clock.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.display.quit()
                if event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # Press 'P' to pause
                        paused = not paused
                        if paused:
                            pygame.mixer.music.pause()
                            self.pause_sound.play()
                        else:
                            pygame.mixer.music.unpause()

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
                current_time = pygame.time.get_ticks()
                best_position, best_rotation = self.best_move(current_piece, grid, locked_positions)
                X, Y = best_position
                if current_piece.rotation == best_rotation:
                    pass
                else:
                    for i in range(best_rotation):
                        if current_time - last_rotation_time > rotation_delay:
                            self.rotate_piece(current_piece, grid)
                            if not self.valid_space(current_piece, grid):
                                current_piece.rotation -= 1
                            last_rotation_time = current_time
                if current_piece.x == X:
                    pass
                elif X < current_piece.x:
                    for i in range(abs(X - current_piece.x)):
                        if current_time - last_move_time > move_delay:
                            self.left_once(current_piece, grid)
                            last_move_time = current_time
                elif X > current_piece.x:
                    for i in range(abs(X - current_piece.x)):
                        if current_time - last_move_time > move_delay:
                            self.right_once(current_piece, grid)
                            last_move_time = current_time
                if Y < 7:
                    pass
                else:
                    if current_time - last_move_time > 2 * move_delay:
                        self.space_once(current_piece, grid)
                        last_move_time = current_time
                shape_pos = self.convert_shape_format(current_piece)
                for i in range(len(shape_pos)):
                    x, y = shape_pos[i]
                    if y > -1:
                        grid[y][x] = current_piece.color

                if change_piece:
                    for pos in shape_pos:
                        p = (pos[0], pos[1])
                        locked_positions[p] = current_piece.color
                    current_piece = next_piece
                    next_piece = self.get_shape()
                    change_piece = False
                    can_hold = True


                    # Clear rows and update the score
                    new_lines_cleared, score_increase = self.clear_rows(grid, locked_positions)
                    initial_lines_cleared += new_lines_cleared
                    if initial_lines_cleared % 10 == 0 and initial_lines_cleared != 0:
                        rotation_delay *= 0.99
                        move_delay *= 0.99
                    score += int(score_increase)
            self.draw_window(win, grid, score, last_score, initial_lines_cleared)
            self.draw_next_shape(next_piece, win)
            self.draw_hold_piece(hold_piece, win)
            if paused:
                self.draw_text_middle(win, "PAUSED", 80, (255, 255, 255))
            pygame.display.update()

            if self.check_lost(locked_positions):
                # Game over logic
                pygame.mixer.music.stop()
                locked_positions = {}
                grid = self.create_grid(locked_positions)
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
                self.draw_window(win, grid, score, self.max_score())
                self.draw_next_shape(next_piece, win)
                self.draw_hold_piece(hold_piece, win)
                pygame.display.update()
                self.draw_window(win, grid, score, last_score, initial_lines_cleared)  # Redraw the grid and UI
                self.draw_next_shape(next_piece, win)  # Redraw the next piece
                self.draw_hold_piece(hold_piece, win)  # Redraw the hold piece
                pygame.mixer.music.load('Original Tetris theme (Tetris Soundtrack).mp3')
                pygame.mixer.music.play(-1)
                pygame.display.update()
                self.update_score(score)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.mixer.music.stop()
                        run = False

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







