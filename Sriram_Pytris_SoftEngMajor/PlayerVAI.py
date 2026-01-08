import pygame
import os
import multiprocessing
from multiprocessing import *
from TetrisCopyCopy import TetrisGame as PlayerGame
from AiTetrisCopyCopy import AITetrisGame as AI_1_Game
from AITetrisCopyCopy2 import AITetrisGame as AI_2_Game



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


def run_tetris_game(game_class, pos_info, conn, title, exit_event, start_event, play_music=False):
    x, y, width, height = pos_info
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)

    game = game_class(screen)
    conn.send("ready")

    # Wait for synchronized start signal
    start_event.wait()
    # Wait for start signal
    start_event.wait()

    try:
        if play_music:
            try:
                """Get the absolute path to a resource file, works in dev and PyInstaller."""
                base_path = os.path.dirname(os.path.abspath(__file__))
                music_path = os.path.join(base_path, "Original Tetris theme (Tetris Soundtrack).mp3")
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)
            except pygame.error as e:
                print(f"Error loading music: {e}")

        game.main(screen)
    finally:
        exit_event.set()


def run_single_player_game():
    pygame.init()

    try:
        screen = pygame.display.set_mode((800, 700))
        pygame.display.set_caption("Single Player Tetris")
        game = PlayerGame(screen)


        try:
            # Set the volume to what's necessary
            try:
                with open("volume.txt", "r") as f:
                    for i in f:
                        pygame.mixer.music.set_volume(round(float(i),0) / 100)
            except FileNotFoundError as e:
                print(f"File error: {e}")
        except pygame.error as e:
            print(f"Error: {e}")

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
        args=(AI_1_Game, positions['player1'], child_conn_ai1, "AI 1 Tetris", exit_event, start_event, True)
    )

    ai2_process = Process(
        target=run_tetris_game,
        args=(AI_2_Game, positions['player2'], child_conn_ai2, "AI 2 Tetris", exit_event, start_event, False)
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
        args=(PlayerGame, positions['player1'], child_conn_player, "Player Tetris", exit_event, start_event, True)
    )

    ai_process = Process(
        target=run_tetris_game,
        args=(AI_1_Game, positions['player2'], child_conn_ai, "AI Tetris", exit_event, start_event, False)
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


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont('Arial', 32)
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=10)

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


def show_settings():
    # Create settings window without changing main display
    settings_screen = pygame.display.set_mode((400, 300))  # Increased height for volume controls
    pygame.display.set_caption("Settings")

    font = pygame.font.SysFont('Arial', 30)
    title = font.render("SETTINGS", True, (255, 255, 255))

    # Volume control variables
    current_volume = pygame.mixer.music.get_volume() * 100  # Convert to percentage
    volume_changed = False

    # Volume label
    volume_label = font.render(f"Volume: {int(current_volume)}%", True, (255, 255, 255))

    # Volume control buttons
    increase_vol_button = Button(300, 100, 40, 40, "+", (100, 100, 100), (150, 150, 150))
    decrease_vol_button = Button(50, 100, 40, 40, "-", (100, 100, 100), (150, 150, 150))

    back_button = Button(100, 200, 200, 40, "BACK", (100, 100, 100), (150, 150, 150))

    clock = pygame.time.Clock()
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        settings_screen.fill((0, 0, 50))

        # Draw settings content
        settings_screen.blit(title, (200 - title.get_width() // 2, 30))

        # Draw volume controls
        settings_screen.blit(volume_label, (200 - volume_label.get_width() // 2, 110))
        increase_vol_button.draw(settings_screen)
        decrease_vol_button.draw(settings_screen)

        back_button.draw(settings_screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.rect.collidepoint(mouse_pos):
                    running = False
                # Handle volume adjustments
                if increase_vol_button.rect.collidepoint(mouse_pos):
                    current_volume = min(100, current_volume + 10)
                    volume_changed = True
                elif decrease_vol_button.rect.collidepoint(mouse_pos):
                    current_volume = max(0, current_volume - 10)
                    volume_changed = True

        # Update volume if changed
        if volume_changed:
            pygame.mixer.music.set_volume(current_volume / 100)
            volume_label = font.render(f"Volume: {int(current_volume)}%", True, (255, 255, 255))
            volume_changed = False
            with open("volume.txt", "w") as f:
                f.write(str(current_volume))
                f.close()

        clock.tick(60)


def show_mode_selection():
    screen = pygame.display.set_mode((600, 500))
    pygame.display.set_caption("Tetris Mode Selection")

    font = pygame.font.SysFont('Arial', 40)
    title = font.render("SELECT GAME MODE", True, (255, 255, 255))

    # Create buttons
    buttons = [
        Button(150, 150, 300, 60, "Single Player", (50, 50, 150), (70, 70, 200)),
        Button(150, 250, 300, 60, "AI vs AI", (150, 50, 50), (200, 70, 70)),
        Button(150, 350, 300, 60, "Player vs AI", (150, 150, 50), (200, 200, 70))
    ]

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 50))

        # Draw title
        screen.blit(title, (300 - title.get_width() // 2, 50))

        # Draw buttons and check hover
        for button in buttons:
            button.check_hover(mouse_pos)
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.rect.collidepoint(mouse_pos):
                        pygame.display.quit()  # Close the mode selection window
                        return i  # Return the index of the selected mode

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
    if os.path.exists('player1_lost.txt'):
        os.remove('player1_lost.txt')
    if os.path.exists("AI1_lost.txt"):
        os.remove("AI1_lost.txt")
    if os.path.exists("AI2_lost.txt"):
        os.remove("AI2_lost.txt")
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
                continue  # Go back to main menu if mode selection is cancelled

            if selected_mode == 0:
                run_single_player_game()
            elif selected_mode == 1:

                run_ai_vs_ai_game()
            elif selected_mode == 2:

                run_player_vs_ai_game()




if __name__ == "__main__":
    multiprocessing.freeze_support()  # MUST BE HERE for PyInstaller
    main()