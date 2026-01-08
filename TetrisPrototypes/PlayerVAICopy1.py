import pygame
import sys
import os
import socket
import pickle
import threading
from pygame.locals import *
from multiprocessing import Process, Pipe, Event, Value
from TetrisCopyCopy import TetrisGame as PlayerGame
from MultiPlayerTetris import TetrisGame as MultiPlayerGame
from AiTetrisCopyCopy import AITetrisGame as AI_1_Game
from AITetrisCopyCopy2 import AITetrisGame as AI_2_Game

# Network Constants
PORT = 5555
BUFFER_SIZE = 4096
SYNC_INTERVAL = 100  # ms


class NetworkManager:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.is_host = False

    def host_game(self):
        try:
            self.socket.bind(('0.0.0.0', PORT))
            self.socket.listen(1)
            self.is_host = True
            print("Waiting for connection...")
            conn, addr = self.socket.accept()
            print("Connected to:", addr)
            self.connection = conn
            return True
        except Exception as e:
            print("Hosting failed:", e)
            return False

    def join_game(self, host_ip):
        try:
            self.socket.connect((host_ip, PORT))
            self.is_host = False
            self.connection = self.socket
            return True
        except Exception as e:
            print("Connection failed:", e)
            return False

    def send_data(self, data):
        try:
            serialized = pickle.dumps(data)
            self.connection.sendall(serialized)
            return True
        except Exception as e:
            print("Send failed:", e)
            return False

    def receive_data(self):
        try:
            data = self.connection.recv(BUFFER_SIZE)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print("Receive failed:", e)
            return None

    def close(self):
        if self.connection:
            self.connection.close()
        self.socket.close()


def get_current_game_state(game):
    """Extract all relevant game state for synchronization"""
    return {
        'locked_positions': dict(game.locked_positions),
        'score': game.score,
        'level': game.initial_lines_cleared // 10,
        'lines_cleared': game.initial_lines_cleared,
        'game_over': game.check_lost(game.locked_positions),
        'current_piece': {
            'x': game.current_piece.x,
            'y': game.current_piece.y,
            'rotation': game.current_piece.rotation,
            'shape_index': game.shapes.index(game.current_piece.shape),
            'color': game.current_piece.color
        },
        'next_piece': {
            'shape_index': game.shapes.index(game.next_piece.shape),
            'color': game.next_piece.color
        },
        'hold_piece': None if game.hold_piece is None else {
            'shape_index': game.shapes.index(game.hold_piece.shape),
            'color': game.hold_piece.color,
            'rotation': game.hold_piece.rotation
        },
        'fall_speed': game.fall_speed,
        'can_hold': game.can_hold,
        'grid': [[color for color in row] for row in game.create_grid(game.locked_positions)]
    }


def apply_game_state(game, state):
    """Apply received game state to local game"""
    game.locked_positions = {tuple(pos): color for pos, color in state['locked_positions'].items()}
    game.score = state['score']
    game.initial_lines_cleared = state['lines_cleared']

    # Update current piece
    cp = state['current_piece']
    game.current_piece = game.Piece(
        cp['x'], cp['y'],
        game.shapes[cp['shape_index']],
        game.shape_colors, game.shapes
    )
    game.current_piece.rotation = cp['rotation']
    game.current_piece.color = cp['color']

    # Update next piece
    np = state['next_piece']
    game.next_piece = game.Piece(
        5, 0, game.shapes[np['shape_index']],
        game.shape_colors, game.shapes
    )
    game.next_piece.color = np['color']

    # Update hold piece
    if state['hold_piece']:
        hp = state['hold_piece']
        game.hold_piece = game.Piece(
            5, 0, game.shapes[hp['shape_index']],
            game.shape_colors, game.shapes
        )
        game.hold_piece.rotation = hp['rotation']
        game.hold_piece.color = hp['color']
    else:
        game.hold_piece = None

    game.fall_speed = state['fall_speed']
    game.can_hold = state['can_hold']

def calculate_window_positions():
    """Calculate centered positions with equal gaps"""
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    window_width = 800
    window_height = 700
    gap = (screen_width - 2 * window_width) // 3  # Equal gaps on both sides and middle

    return {
        'player1': (gap, 100, window_width, window_height),
        'player2': (2 * gap + window_width, 100, window_width, window_height),
    }


def run_tetris_game(game_class, pos_info, conn, title, exit_event, start_event, play_music=False, player_num=1, ai_enabled=False):
    x, y, width, height = pos_info
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)

    game = game_class(screen)
    conn.send("ready")

    # Wait for synchronized start signal
    start_event.wait()

    try:
        if play_music:
            try:
                pygame.mixer.music.load("Original Tetris theme (Tetris Soundtrack).mp3")
                pygame.mixer.music.play(-1)
            except pygame.error as e:
                print(f"Error loading music: {e}")

        # Modify controls for player 2 if this is the second player
        if player_num == 2:
            game.movement_dict = {
                'Rotate': pygame.K_w,  # W for rotate
                'Left': pygame.K_a,  # A for left
                'Down': pygame.K_s,  # S for down
                'Right': pygame.K_d,  # D for right
                'Space': pygame.K_e,  # E for hard drop
                'Hold': pygame.K_q  # Q for hold
            }

        # Enable AI if this is an AI game
        if ai_enabled:
            game.ai_enabled = True

        game.main(screen)
    finally:
        if play_music:
            pygame.mixer.music.stop()
        exit_event.set()
def run_lan_game(network, is_host, is_player1):
    pygame.init()
    screen = pygame.display.set_mode((800, 700))
    pygame.display.set_caption(f"Tetris {'(Host)' if is_host else '(Client)'}")

    game_class = PlayerGame if is_player1 else MultiPlayerGame
    game = game_class(screen)

    clock = pygame.time.Clock()
    last_sync = pygame.time.get_ticks()
    input_queue = []

    def receive_thread():
        while True:
            data = network.receive_data()
            if data and 'state' in data:
                apply_game_state(game, data['state'])

    threading.Thread(target=receive_thread, daemon=True).start()

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if event.type == KEYDOWN:
                if event.key == K_p:
                    game.paused = not game.paused

                if not game.paused:
                    input_map = {
                        K_UP: 'rotate',
                        K_LEFT: 'left',
                        K_RIGHT: 'right',
                        K_DOWN: 'down',
                        K_SPACE: 'drop',
                        K_c: 'hold'
                    }
                    if event.key in input_map:
                        network.send_data({'input': input_map[event.key]})

        # Game logic
        if not game.paused:
            current_time = pygame.time.get_ticks()

            if is_host:
                # Host processes game logic
                game.fall_time += clock.get_rawtime()
                if game.fall_time / 1000 > game.fall_speed:
                    game.fall_time = 0
                    game.current_piece.y += 1
                    if not game.valid_space(game.current_piece, game.create_grid(game.locked_positions)):
                        game.current_piece.y -= 1
                        # Handle piece locking

                # Sync state periodically
                if current_time - last_sync > SYNC_INTERVAL:
                    network.send_data({'state': get_current_game_state(game)})
                    last_sync = current_time

            # Drawing
            grid = game.create_grid(game.locked_positions)
            game.draw_window(screen, grid, game.score, game.max_score())
            game.draw_next_shape(game.next_piece, screen)
            game.draw_hold_piece(game.hold_piece, screen)

            if game.paused:
                game.draw_text_middle(screen, "PAUSED", 80, (255, 255, 255))

        pygame.display.update()
        clock.tick(60)

    network.close()
    pygame.quit()

def run_single_player_game():
    pygame.init()

    try:
        screen = pygame.display.set_mode((800, 700))
        pygame.display.set_caption("Single Player Tetris")
        game = PlayerGame(screen)

        # Start music
        try:
            pygame.mixer.music.load("Original Tetris theme (Tetris Soundtrack).mp3")
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading music: {e}")

        game.main(screen)

    finally:
        # Ensure music stops and pygame quits properly
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.quit()


def run_ai_vs_ai_game():
    """Run an AI vs AI game showing both windows"""
    pygame.init()  # Reinitialize pygame for the game windows
    positions = calculate_window_positions()

    # Create pipes for synchronization
    parent_conn_ai1, child_conn_ai1 = Pipe()
    parent_conn_ai2, child_conn_ai2 = Pipe()
    start_event = Event()
    exit_event = Event()

    # Start both AI games with calculated positions
    # Only the first AI window will play music
    ai1_process = Process(
        target=run_tetris_game,
        args=(AI_1_Game, positions['player1'], child_conn_ai1, "AI 1 Tetris", exit_event, start_event, True, 1, True)
    )

    ai2_process = Process(
        target=run_tetris_game,
        args=(AI_2_Game, positions['player2'], child_conn_ai2, "AI 2 Tetris", exit_event, start_event, False, 2, True)
    )
    ai1_process.start()
    ai2_process.start()

    # Wait for initialization
    parent_conn_ai1.recv()
    parent_conn_ai2.recv()

    # Short delay for Pygame music to initialize properly
    pygame.time.delay(250)

    # Release both games to start in sync
    start_event.set()

    while ai1_process.is_alive() and ai2_process.is_alive():
        if exit_event.is_set():
            if ai1_process.is_alive():
                ai1_process.terminate()
            if ai2_process.is_alive():
                ai2_process.terminate()
            break

    ai1_process.join()
    ai2_process.join()


def run_player_vs_ai_game():
    """Run a Player vs AI game showing both windows"""
    pygame.init()
    positions = calculate_window_positions()

    # Create pipes for synchronization
    parent_conn_player, child_conn_player = Pipe()
    parent_conn_ai, child_conn_ai = Pipe()
    start_event = Event()
    exit_event = Event()

    # Start player and AI processes
    player_process = Process(
        target=run_tetris_game,
        args=(PlayerGame, positions['player1'], child_conn_player, "Player Tetris", exit_event, start_event, True, 1)
    )

    ai_process = Process(
        target=run_tetris_game,
        args=(AI_1_Game, positions['player2'], child_conn_ai, "AI Tetris", exit_event, start_event, False, 2, True)
    )
    player_process.start()
    ai_process.start()

    # Wait for initialization
    parent_conn_player.recv()
    parent_conn_ai.recv()

    # Short delay for Pygame music to initialize properly
    pygame.time.delay(250)

    # Release both games to start in sync
    start_event.set()

    while player_process.is_alive() and ai_process.is_alive():
        if exit_event.is_set():
            if player_process.is_alive():
                player_process.terminate()
            if ai_process.is_alive():
                ai_process.terminate()
            break

    player_process.join()
    ai_process.join()
def show_lan_menu():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("LAN Multiplayer")

    font = pygame.font.SysFont('Arial', 30)
    input_font = pygame.font.SysFont('Arial', 24)

    host_button = Button(150, 100, 300, 50, "Host Game", (50, 150, 50), (70, 200, 70))
    join_button = Button(150, 200, 300, 50, "Join Game", (50, 50, 150), (70, 70, 200))
    ip_input = ""
    active_input = False

    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill((0, 0, 50))

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if host_button.rect.collidepoint(mouse_pos):
                    network = NetworkManager()
                    if network.host_game():
                        run_lan_game(network, is_host=True, is_player1=True)
                        running = False
                elif join_button.rect.collidepoint(mouse_pos):
                    network = NetworkManager()
                    if network.join_game(ip_input):
                        run_lan_game(network, is_host=False, is_player1=False)
                        running = False

                # IP input handling
                if 150 <= mouse_pos[0] <= 450 and 300 <= mouse_pos[1] <= 330:
                    active_input = True
                else:
                    active_input = False

            if event.type == KEYDOWN and active_input:
                if event.key == K_BACKSPACE:
                    ip_input = ip_input[:-1]
                elif event.key == K_RETURN:
                    pass
                else:
                    ip_input += event.unicode

        # Draw UI
        host_button.draw(screen)
        join_button.draw(screen)

        # IP input box
        pygame.draw.rect(screen, (100, 100, 100) if not active_input else (150, 150, 150),
                         (150, 300, 300, 30))
        ip_text = input_font.render(ip_input, True, (255, 255, 255))
        screen.blit(ip_text, (160, 305))
        label = font.render("Enter Host IP:", True, (255, 255, 255))
        screen.blit(label, (150, 270))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def show_settings():
    # Create settings window without changing main display
    settings_screen = pygame.display.set_mode((400, 200))
    pygame.display.set_caption("Settings")

    font = pygame.font.SysFont('Arial', 30)
    title = font.render("SETTINGS", True, (255, 255, 255))

    back_button = Button(100, 100, 200, 40, "BACK", (100, 100, 100), (150, 150, 150))

    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        settings_screen.fill((0, 0, 50))

        # Draw settings content
        settings_screen.blit(title, (200 - title.get_width() // 2, 30))
        back_button.draw(settings_screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.rect.collidepoint(mouse_pos):
                    running = False

    # Settings window will close and control returns to main menu
    # Main menu will restore its own display
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.SysFont('Arial', 30)
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=10)

        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered


# ... (keep all other existing functions like run_single_player_game,
# run_ai_vs_ai_game, run_player_vs_ai_game, show_main_menu, etc.)

def show_mode_selection():
    screen = pygame.display.set_mode((600, 500))
    pygame.display.set_caption("Tetris Mode Selection")

    font = pygame.font.SysFont('Arial', 40)
    title = font.render("SELECT GAME MODE", True, (255, 255, 255))

    # Create buttons (removed original PvP option)
    buttons = [
        Button(150, 150, 300, 60, "Single Player", (50, 50, 150), (70, 70, 200)),
        Button(150, 250, 300, 60, "AI vs AI", (150, 50, 50), (200, 70, 70)),
        Button(150, 350, 300, 60, "Player vs AI", (150, 150, 50), (200, 200, 70)),
        Button(150, 450, 300, 60, "LAN Multiplayer", (50, 150, 50), (70, 200, 70))
    ]

    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 50))

        # Draw title
        screen.blit(title, (300 - title.get_width() // 2, 50))

        # Draw buttons
        for button in buttons:
            button.check_hover(mouse_pos)
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                return None

            if event.type == MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.rect.collidepoint(mouse_pos):
                        pygame.display.quit()
                        return i  # Return the selected mode index

    return None

def show_main_menu():
    # Initialize with main menu size
    pygame.init()
    screen = pygame.display.set_mode((600, 500))
    pygame.display.set_caption("Tetris Main Menu")

    font = pygame.font.SysFont('Arial', 60)
    title = font.render("PYTRIS", True, (255, 255, 255))

    # Create buttons
    play_button = Button(150, 200, 300, 60, "PLAY", (50, 150, 50), (70, 200, 70))
    settings_button = Button(150, 300, 300, 60, "SETTINGS", (100, 100, 100), (150, 150, 150))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 50))

        # Draw title
        screen.blit(title, (300 - title.get_width() // 2, 50))

        # Draw buttons
        play_button.draw(screen)
        settings_button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.rect.collidepoint(mouse_pos):
                    return "play"
                if settings_button.rect.collidepoint(mouse_pos):
                    # Store current display info before opening settings
                    original_display = pygame.display.get_surface()
                    show_settings()
                    # Restore main menu display
                    pygame.display.set_mode((600, 500))
                    # Redraw everything
                    continue

    return None
def main():
    pygame.init()
    pygame.mixer.init()

    while True:
        menu_result = show_main_menu()

        if menu_result is None:  # Window closed
            break

        if menu_result == "play":
            selected_mode = show_mode_selection()
            if selected_mode is None:
                continue

            if selected_mode == 0:
                run_single_player_game()
            elif selected_mode == 1:
                run_ai_vs_ai_game()
            elif selected_mode == 2:
                run_player_vs_ai_game()
            elif selected_mode == 3:
                show_lan_menu()


if __name__ == "__main__":
    main()