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
font = pygame.font.SysFont("consolas", 20)
clock = pygame.time.Clock()
spotify_cache = None
spotify_cover = None
spotify_timer = 0

CHAT_X = 20
CHAT_Y = 150
CHAT_WIDTH = 500
LINE_HEIGHT = 22
MAX_CHAT_LINES = 20

SPOTIFY_COVER_SIZE = 100
SPOTIFY_X = 1150 - SPOTIFY_COVER_SIZE  # ~1150 to leave margin
SPOTIFY_Y = 20


chat_queue = Queue()
chat_log = []

MAX_LINES = 30

def render_chat():
    y = CHAT_Y
    for msg in chat_log[-MAX_CHAT_LINES:]:
        lines = wrap_text(msg, font, CHAT_WIDTH)
        for line in lines:
            text_surface = font.render(line, True, (255, 255, 255))
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
            lines.append(current_line.strip())
            current_line = word + ' '
    if current_line:
        lines.append(current_line.strip())

    return lines

def render_spotify():
    if spotify_cache:
        # Album cover
        if spotify_cover:
            screen.blit(spotify_cover, (SPOTIFY_X, SPOTIFY_Y))
        else:
            pygame.draw.rect(screen, (100, 100, 100),
                             pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE))

        # Song + Artist
        song_text = font.render(spotify_cache['song'], True, (255, 255, 255))
        artist_text = font.render(spotify_cache['artist'], True, (200, 200, 200))

        screen.blit(song_text, (SPOTIFY_X - 300, SPOTIFY_Y + 10))
        screen.blit(artist_text, (SPOTIFY_X - 300, SPOTIFY_Y + 40))


# Start handlers
threading.Thread(target=run_twitch, args=(chat_queue,), daemon=True).start()
threading.Thread(target=run_youtube, args=(chat_queue,), daemon=True).start()
threading.Thread(target=run_tiktok, args=(chat_queue,), daemon=True).start()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Poll Spotify every 3s
    if time.time() - spotify_timer > 3:
        spotify_cache = get_current_song()
        print("SPOTIFY CACHE:", spotify_cache)  # DEBUG LINE
        if spotify_cache:
            spotify_cover = load_album_cover(spotify_cache['cover_url'])
        spotify_timer = time.time()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: skip()
    if keys[pygame.K_LEFT]: previous()
    if keys[pygame.K_SPACE]: toggle_play()

    while not chat_queue.empty():
        chat_log.append(chat_queue.get())

    screen.fill((15, 15, 15))  # Always first

    render_spotify()
    render_chat()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
