import time
import pygame
import threading

from twitch_handler import run_twitch
from youtube_handler import run_youtube
from tiktok_handler import run_tiktok
from spotify_handler import get_current_song, skip, previous, toggle_play, load_album_cover
from queue import Queue

# Setup
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
pygame.display.set_caption("Unified Chat Display")

# Light mode colors
BG_COLOR = (245, 245, 250)  # Light gray background
TEXT_COLOR = (20, 20, 30)  # Dark text
SECONDARY_TEXT = (80, 80, 90)  # Gray text for artist names
CHAT_BG = (255, 255, 255)  # White chat background
BORDER_COLOR = (200, 200, 210)  # Subtle borders

# Bigger fonts for readability
font = pygame.font.SysFont("segoeui", 28)  # Larger main font
small_font = pygame.font.SysFont("segoeui", 22)  # For secondary info
title_font = pygame.font.SysFont("segoeui", 32, bold=True)  # For headers

clock = pygame.time.Clock()
spotify_cache = None
spotify_cover = None
spotify_timer = 0

CHAT_X = 30
CHAT_Y = 180
CHAT_WIDTH = 600
LINE_HEIGHT = 35  # Increased spacing
MAX_CHAT_LINES = 15

SPOTIFY_COVER_SIZE = 120
SPOTIFY_X = 1120 - SPOTIFY_COVER_SIZE
SPOTIFY_Y = 30

chat_queue = Queue()
chat_log = []

MAX_LINES = 30

def render_chat():
    # Draw chat container background
    chat_height = MAX_CHAT_LINES * LINE_HEIGHT + 40
    pygame.draw.rect(screen, CHAT_BG, pygame.Rect(CHAT_X - 10, CHAT_Y - 50, CHAT_WIDTH + 20, chat_height), border_radius=10)
    pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(CHAT_X - 10, CHAT_Y - 50, CHAT_WIDTH + 20, chat_height), 2, border_radius=10)
    
    # Title
    title_surface = title_font.render("Live Chat", True, TEXT_COLOR)
    screen.blit(title_surface, (CHAT_X, CHAT_Y - 40))
    
    # Chat messages
    y = CHAT_Y + 10
    for msg in chat_log[-MAX_CHAT_LINES:]:
        lines = wrap_text(msg, font, CHAT_WIDTH)
        for line in lines:
            text_surface = font.render(line, True, TEXT_COLOR)
            screen.blit(text_surface, (CHAT_X, y))
            y += LINE_HEIGHT


def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + ' '
    if current_line:
        lines.append(current_line.strip())

    return lines

def render_spotify():
    if spotify_cache:
        # Container background
        container_width = 400
        container_height = 160
        container_x = SPOTIFY_X - 320
        pygame.draw.rect(screen, CHAT_BG, pygame.Rect(container_x, SPOTIFY_Y - 10, container_width, container_height), border_radius=10)
        pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(container_x, SPOTIFY_Y - 10, container_width, container_height), 2, border_radius=10)
        
        # Album cover with border
        if spotify_cover:
            screen.blit(spotify_cover, (SPOTIFY_X, SPOTIFY_Y))
            pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE), 2)
        else:
            pygame.draw.rect(screen, (220, 220, 220), pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE))
            pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE), 2)

        # Song + Artist with better positioning
        song_text = font.render(spotify_cache['song'], True, TEXT_COLOR)
        artist_text = small_font.render(spotify_cache['artist'], True, SECONDARY_TEXT)
        
        # Playing status indicator
        status = "▶ Playing" if spotify_cache.get('playing') else "⏸ Paused"
        status_text = small_font.render(status, True, SECONDARY_TEXT)

        screen.blit(song_text, (SPOTIFY_X - 290, SPOTIFY_Y + 15))
        screen.blit(artist_text, (SPOTIFY_X - 290, SPOTIFY_Y + 55))
        screen.blit(status_text, (SPOTIFY_X - 290, SPOTIFY_Y + 90))


# Start handlers
threading.Thread(target=run_twitch, args=(chat_queue,), daemon=True).start()
# threading.Thread(target=run_youtube, args=(chat_queue,), daemon=True).start()
# threading.Thread(target=run_tiktok, args=(chat_queue,), daemon=True).start()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Poll Spotify every 3s
    if time.time() - spotify_timer > 3:
        spotify_cache = get_current_song()
        if spotify_cache:
            spotify_cover = load_album_cover(spotify_cache['cover_url'])
        spotify_timer = time.time()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: skip()
    if keys[pygame.K_LEFT]: previous()
    if keys[pygame.K_SPACE]: toggle_play()

    while not chat_queue.empty():
        chat_log.append(chat_queue.get())

    # Fill with light background
    screen.fill(BG_COLOR)

    render_spotify()
    render_chat()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()