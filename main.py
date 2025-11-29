import time
import pygame
import threading
import requests
import io
import hashlib

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
BG_COLOR = (245, 245, 250)
TEXT_COLOR = (20, 20, 30)
SECONDARY_TEXT = (80, 80, 90)
CHAT_BG = (255, 255, 255)
BORDER_COLOR = (200, 200, 210)

# Fonts
font = pygame.font.SysFont("segoeui", 28)
small_font = pygame.font.SysFont("segoeui", 22)
title_font = pygame.font.SysFont("segoeui", 32, bold=True)
huge_font = pygame.font.SysFont("segoeui", 48, bold=True)
large_font = pygame.font.SysFont("segoeui", 36)

clock = pygame.time.Clock()
spotify_cache = None
spotify_cover = None
spotify_timer = 0
previous_song = None

# Song change overlay
song_overlay_active = False
song_overlay_start = 0
OVERLAY_DURATION = 3  # seconds
large_album_cover = None

CHAT_X = 30
CHAT_Y = 180
CHAT_WIDTH = 600
LINE_HEIGHT = 35
MAX_CHAT_LINES = 15

SPOTIFY_COVER_SIZE = 120
SPOTIFY_X = 1120 - SPOTIFY_COVER_SIZE
SPOTIFY_Y = 30

chat_queue = Queue()
chat_log = []

# Emote cache
emote_cache = {}
user_colors = {}

def get_user_color(username):
    """Generate consistent color for each user"""
    if username not in user_colors:
        hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
        # Generate pleasant colors (avoid too dark or too light)
        hue = hash_val % 360
        # Convert HSV to RGB for nice varied colors
        c = 0.6  # saturation
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = 0.4  # brightness offset
        
        if hue < 60:
            r, g, b = c, x, 0
        elif hue < 120:
            r, g, b = x, c, 0
        elif hue < 180:
            r, g, b = 0, c, x
        elif hue < 240:
            r, g, b = 0, x, c
        elif hue < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        # Ensure values are in valid range 0-255
        r = max(0, min(255, int((r + m) * 255)))
        g = max(0, min(255, int((g + m) * 255)))
        b = max(0, min(255, int((b + m) * 255)))
        
        user_colors[username] = (r, g, b)
    
    return user_colors[username]

def load_emote(emote_name):
    """Load Twitch emote from cache or download"""
    if emote_name in emote_cache:
        return emote_cache[emote_name]
    
    # Try to load common Twitch global emotes
    emote_urls = {
        'Kappa': 'https://static-cdn.jtvnw.net/emoticons/v2/25/default/dark/1.0',
        'PogChamp': 'https://static-cdn.jtvnw.net/emoticons/v2/305954156/default/dark/1.0',
        'LUL': 'https://static-cdn.jtvnw.net/emoticons/v2/425618/default/dark/1.0',
        '4Head': 'https://static-cdn.jtvnw.net/emoticons/v2/354/default/dark/1.0',
        'ResidentSleeper': 'https://static-cdn.jtvnw.net/emoticons/v2/245/default/dark/1.0',
        'Kreygasm': 'https://static-cdn.jtvnw.net/emoticons/v2/41/default/dark/1.0',
    }
    
    if emote_name in emote_urls:
        try:
            response = requests.get(emote_urls[emote_name], timeout=2)
            image_bytes = io.BytesIO(response.content)
            emote_img = pygame.image.load(image_bytes)
            emote_img = pygame.transform.scale(emote_img, (28, 28))
            emote_cache[emote_name] = emote_img
            return emote_img
        except:
            pass
    
    return None

def render_chat_message(message, x, y, max_width, message_font):
    """Render chat message with colored username and emotes"""
    if '[Twitch]' in message:
        # Parse: [Twitch] username: message
        parts = message.split(':', 2)
        if len(parts) >= 2:
            username = parts[0].replace('[Twitch]', '').strip()
            text = parts[1].strip() if len(parts) > 1 else ''
            
            # Render platform tag
            platform_surface = small_font.render('[Twitch]', True, (145, 70, 255))
            screen.blit(platform_surface, (x, y))
            x += platform_surface.get_width() + 5
            
            # Render colored username
            user_color = get_user_color(username)
            username_surface = message_font.render(username + ':', True, user_color)
            screen.blit(username_surface, (x, y))
            x += username_surface.get_width() + 8
            
            # Render message with emotes
            words = text.split(' ')
            for word in words:
                emote = load_emote(word)
                if emote:
                    screen.blit(emote, (x, y + 2))
                    x += 30
                else:
                    word_surface = message_font.render(word + ' ', True, TEXT_COLOR)
                    if x + word_surface.get_width() > max_width + CHAT_X:
                        return y + LINE_HEIGHT  # Next line
                    screen.blit(word_surface, (x, y))
                    x += word_surface.get_width()
            
            return y + LINE_HEIGHT
    else:
        # Regular rendering for other platforms
        text_surface = message_font.render(message, True, TEXT_COLOR)
        screen.blit(text_surface, (x, y))
        return y + LINE_HEIGHT

def render_chat():
    chat_height = MAX_CHAT_LINES * LINE_HEIGHT + 40
    pygame.draw.rect(screen, CHAT_BG, pygame.Rect(CHAT_X - 10, CHAT_Y - 50, CHAT_WIDTH + 20, chat_height), border_radius=10)
    pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(CHAT_X - 10, CHAT_Y - 50, CHAT_WIDTH + 20, chat_height), 2, border_radius=10)
    
    title_surface = title_font.render("Live Chat", True, TEXT_COLOR)
    screen.blit(title_surface, (CHAT_X, CHAT_Y - 40))
    
    y = CHAT_Y + 10
    for msg in chat_log[-MAX_CHAT_LINES:]:
        y = render_chat_message(msg, CHAT_X, y, CHAT_WIDTH, font)

def truncate_text(text, font, max_width):
    """Truncate text to fit width with ellipsis"""
    if font.size(text)[0] <= max_width:
        return text
    
    while len(text) > 0 and font.size(text + '...')[0] > max_width:
        text = text[:-1]
    
    return text + '...' if text else ''

def render_spotify():
    if spotify_cache:
        container_width = 400
        container_height = 160
        container_x = SPOTIFY_X - 320
        pygame.draw.rect(screen, CHAT_BG, pygame.Rect(container_x, SPOTIFY_Y - 10, container_width, container_height), border_radius=10)
        pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(container_x, SPOTIFY_Y - 10, container_width, container_height), 2, border_radius=10)
        
        if spotify_cover:
            screen.blit(spotify_cover, (SPOTIFY_X, SPOTIFY_Y))
            pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE), 2)
        else:
            pygame.draw.rect(screen, (220, 220, 220), pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE))
            pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(SPOTIFY_X, SPOTIFY_Y, SPOTIFY_COVER_SIZE, SPOTIFY_COVER_SIZE), 2)

        # Truncate song and artist to fit
        max_text_width = 280
        song_truncated = truncate_text(spotify_cache['song'], font, max_text_width)
        artist_truncated = truncate_text(spotify_cache['artist'], small_font, max_text_width)
        
        song_text = font.render(song_truncated, True, TEXT_COLOR)
        artist_text = small_font.render(artist_truncated, True, SECONDARY_TEXT)
        
        status = "▶ Playing" if spotify_cache.get('playing') else "⏸ Paused"
        status_text = small_font.render(status, True, SECONDARY_TEXT)

        screen.blit(song_text, (SPOTIFY_X - 290, SPOTIFY_Y + 15))
        screen.blit(artist_text, (SPOTIFY_X - 290, SPOTIFY_Y + 55))
        screen.blit(status_text, (SPOTIFY_X - 290, SPOTIFY_Y + 90))

def render_song_overlay():
    """Full screen overlay when song changes"""
    if not spotify_cache or not large_album_cover:
        return
    
    # Semi-transparent dark overlay
    overlay = pygame.Surface((1280, 720))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(220)
    screen.blit(overlay, (0, 0))
    
    # Large album cover centered
    cover_size = 300
    cover_x = 640 - cover_size // 2
    cover_y = 150
    screen.blit(large_album_cover, (cover_x, cover_y))
    
    # Song info below
    song_surface = huge_font.render(spotify_cache['song'], True, (255, 255, 255))
    artist_surface = large_font.render(spotify_cache['artist'], True, (200, 200, 200))
    album_surface = small_font.render(f"Album: {spotify_cache.get('album', 'Unknown')}", True, (150, 150, 150))
    
    # Center text
    screen.blit(song_surface, (640 - song_surface.get_width() // 2, cover_y + cover_size + 30))
    screen.blit(artist_surface, (640 - artist_surface.get_width() // 2, cover_y + cover_size + 85))
    screen.blit(album_surface, (640 - album_surface.get_width() // 2, cover_y + cover_size + 125))

def check_song_change():
    global previous_song, song_overlay_active, song_overlay_start, large_album_cover
    
    if spotify_cache:
        current_song = spotify_cache['song']
        if previous_song and previous_song != current_song:
            # Song changed!
            song_overlay_active = True
            song_overlay_start = time.time()
            
            # Load large album cover
            if spotify_cache.get('cover_url'):
                try:
                    response = requests.get(spotify_cache['cover_url'])
                    image_bytes = io.BytesIO(response.content)
                    large_album_cover = pygame.image.load(image_bytes)
                    large_album_cover = pygame.transform.scale(large_album_cover, (300, 300))
                except:
                    large_album_cover = None
        
        previous_song = current_song

# Start handlers
threading.Thread(target=run_twitch, args=(chat_queue,), daemon=True).start()
# threading.Thread(target=run_youtube, args=(chat_queue,), daemon=True).start()
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
        if spotify_cache:
            spotify_cover = load_album_cover(spotify_cache['cover_url'])
            check_song_change()
        spotify_timer = time.time()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: 
        skip()
        time.sleep(0.3)  # Debounce
    if keys[pygame.K_LEFT]: 
        previous()
        time.sleep(0.3)
    if keys[pygame.K_SPACE]: 
        toggle_play()
        time.sleep(0.3)

    while not chat_queue.empty():
        chat_log.append(chat_queue.get())

    screen.fill(BG_COLOR)

    # Check if overlay should still be shown
    if song_overlay_active:
        if time.time() - song_overlay_start < OVERLAY_DURATION:
            render_song_overlay()
        else:
            song_overlay_active = False
    else:
        render_spotify()
        render_chat()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()