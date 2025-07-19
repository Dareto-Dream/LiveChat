import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import pygame
import io

# Setup (replace with your actual info)
SPOTIFY_CLIENT_ID = 'b14770236aff484ab764de2b0cf8cb8c'
SPOTIFY_CLIENT_SECRET = 'f914dab7bb964da993b93afa86bae818'
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-playback-state user-modify-playback-state'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    open_browser=True
))

def get_current_song():
    playback = sp.current_playback()
    if playback and playback.get("item"):
        song = playback["item"]["name"]
        artist = ", ".join(a["name"] for a in playback["item"]["artists"])
        album_url = playback["item"]["album"]["images"][0]["url"]
        is_playing = playback["is_playing"]
        return {"song": song, "artist": artist, "cover_url": album_url, "playing": is_playing}
    return None

def skip():
    sp.next_track()

def previous():
    sp.previous_track()

def toggle_play():
    playback = sp.current_playback()
    if playback and playback["is_playing"]:
        sp.pause_playback()
    else:
        sp.start_playback()

def load_album_cover(url):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)
    image = pygame.image.load(image_bytes)
    return pygame.transform.scale(image, (100, 100))
