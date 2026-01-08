import pygame
import random
from pygame.locals import *
from collections import namedtuple
from random import choice

pygame.init()
pygame.font.init()


class TetrisGame():
    def __init__(self):
        # GLOBALS VARS
        self.s_width = 800
        self.s_height = 700
        self.play_width = 300  # meaning 300 // 10 = 30 width per block
        self.play_height = 600  # meaning 600 // 20 = 30 height per block
        self.block_size = 30

        self.top_left_x = (self.s_width - self.play_width) // 2
        self.top_left_y = self.s_height - self.play_height
        self.PvAI_lost = False
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

        self.line_multipliers = {
            1: 1.0,
            2: 1.5,
            3: 2.0,
            4: 3.0
        }

    class Piece(object):
        def __init__(self, x, y, orientation, shape_colors, shapes):
            self.x = x
            self.y = y
            self.shape = orientation
            self.color = shape_colors[shapes.index(orientation)]
            self.rotation = 0

    def create_grid(self, locked_pos={}):
        grid = [[(0, 0, 0) for _ in range(10)] for _ in range(20)]

        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if (j, i) in locked_pos:
                    c = locked_pos[(j, i)]
                    grid[i][j] = c
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
        accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0, 0, 0)] for i in range(20)]
        accepted_pos = [j for sub in accepted_pos for j in sub]

        formatted = self.convert_shape_format(shape)

        for pos in formatted:
            # Check if the position is outside the grid horizontally
            if pos[0] < 0 or pos[0] >= 10:
                return False
            # Check if the position is outside the grid vertically
            if pos[1] >= 20:
                return False
            # Check if the position is occupied
            if pos not in accepted_pos and pos[1] > -1:
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
        self.screen.blit(surface, (0,0))

    def draw_grid(self, surface, grid):
        sx = self.top_left_x
        sy = self.top_left_y

        for i in range(len(grid)):
            pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * self.block_size),
                             (sx + self.play_width, sy + i * self.block_size))
            for j in range(len(grid[i])):
                pygame.draw.line(surface, (128, 128, 128), (sx + j * self.block_size, sy),
                                 (sx + j * self.block_size, sy + self.play_height))
        self.screen.blit(surface, (0, 0))
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
        self.screen.blit(surface, (0, 0))
    def update_score(self, nscore):
        score = self.max_score()

        with open('scores.txt', 'w') as f:
            if int(score) > nscore:
                f.write(str(score))
            else:
                f.write(str(nscore))

    # Max height of each column
    def aggregated_heights(self, grid):
        heights = [0] * 10  # Assuming a grid width of 10 columns

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

    def count_holes(self, grid):
        heights = [0] * 10  # Assuming a grid width of 10 columns
        lengths = self.aggregated_heights(grid)
        for col in range(10):
            row = 0
            # Continuously prints 0
            while row < lengths[col]:
                if grid[19-row][col] == (0, 0, 0):
                    heights[col] += 1
                row += 1
        return heights

    def max_score(self):
        try:
            with open('scores.txt', 'r') as f:
                lines = f.readlines()
                score = lines[0].strip()
        except (FileNotFoundError, IndexError):
            score = "0"
        return score

    # AI's actions

    # Dynamically change window screen size to make it adjustable
    def handle_resize(self, event):
        self.s_width, self.s_height = event.size
        self.block_size = min(self.s_width // 10, self.s_height // 20)
        self.play_width = self.block_size * 10
        self.play_height = self.block_size * 20
        self.top_left_x = (self.s_width - self.play_width) // 2
        self.top_left_y = self.s_height - self.play_height

    def draw_window(self, surface, grid, score=0, last_score=0):
        surface.fill((0, 0, 0))

        pygame.font.init()
        font = pygame.font.SysFont('comicsans', 60)
        label = font.render('Tetris', 1, (255, 255, 255))

        surface.blit(label, (self.top_left_x + self.play_width / 2 - (label.get_width() / 2), 30))

        # current score
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render('Score: ' + str(score), 1, (255, 255, 255))
        level_label = font.render('Level: ' + str(score), 1, (255, 255, 255))
        sx = self.top_left_x + self.play_width + 50
        sy = self.top_left_y + self.play_height / 2 - 100

        surface.blit(label, (sx + 20, sy + 160))
        surface.blit(level_label, (sx + 20, sy - 110))
        # last score
        label = font.render('High Score: ' + last_score, 1, (255, 255, 255))

        sx = self.top_left_x - 200
        sy = self.top_left_y + 200

        surface.blit(label, (sx - 20, sy + 160))

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
        max_speed = 0.1
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
                    level = score // speed_increase_interval
                    fall_speed *= (0.9 ** level)
                if fall_time / 1000 > fall_speed:
                    fall_time = 0
                    current_piece.y += 1
                    if not (self.valid_space(current_piece, grid)) and current_piece.y > 0:
                        current_piece.y -= 1
                        change_piece = True

                keys = pygame.key.get_pressed()
                current_time = pygame.time.get_ticks()
                if keys[pygame.K_UP] and (current_time - last_rotation_time) > rotation_delay:
                    self.rotate_piece(current_piece, grid)
                    last_rotation_time = current_time
                    if not (self.valid_space(current_piece, grid)):
                        current_piece.rotation -= 1

                if keys[pygame.K_LEFT] and (current_time - last_move_time) > move_delay:
                    self.left_once(current_piece, grid)
                    last_move_time = current_time

                if keys[pygame.K_RIGHT] and (current_time - last_move_time) > move_delay:
                    self.right_once(current_piece, grid)
                    last_move_time = current_time

                if keys[pygame.K_DOWN] and (current_time - last_move_time) > move_delay:
                    self.down_once(current_piece, grid)
                    last_move_time = current_time

                if keys[pygame.K_SPACE] and (current_time - last_move_time) > 2 * move_delay:
                    self.space_once(current_piece, grid)
                    last_move_time = current_time
                if keys[pygame.K_c] and can_hold:  # Press 'C' to hold
                    if hold_piece is None:
                        hold_piece = current_piece
                        current_piece = next_piece
                        next_piece = self.get_shape()
                    else:
                        hold_piece, current_piece = current_piece, hold_piece
                        current_piece.x = 5
                        current_piece.y = 0
                    can_hold = False

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
                    lines_cleared, score_increase = self.clear_rows(grid, locked_positions)
                    score += int(score_increase)

            self.draw_window(win, grid, score, last_score)
            self.draw_next_shape(next_piece, win)
            self.draw_hold_piece(hold_piece, win)
            if paused:
                self.draw_text_middle(win, "PAUSED", 80, (255, 255, 255))
            pygame.display.update()

            if self.check_lost(locked_positions):
                # Game over logic
                pygame.mixer.music.stop()

                pygame.mixer.music.stop()

                # Display "YOU LOST!" for 1 second
                self.draw_text_middle(win, "YOU LOST!", 80, (255, 255, 255))
                pygame.display.update()
                self.gameover_sound.play()
                pygame.time.delay(1000)  # Delay for 1 second (1000 milliseconds)

                # Switch to "PRESS ANY KEY TO EXIT"
                # Redraw the game screen to "erase" the "YOU LOST!" text
                self.draw_window(win, grid, score, last_score)  # Redraw the grid and UI
                self.draw_next_shape(next_piece, win)  # Redraw the next piece
                self.draw_hold_piece(hold_piece, win)  # Redraw the hold piece
                pygame.display.update()
                pygame.time.delay(1000)
                self.draw_text_middle(win, 'PRESS ANY KEY TO EXIT', 40, (255, 255, 255))
                pygame.display.update()
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
                # Wait for any key press to exit
                waiting_for_input = True
                while waiting_for_input:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                            waiting_for_input = False
                self.gameover_sound.stop()
                run = False
                self.update_score(score)


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






