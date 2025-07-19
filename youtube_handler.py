import time
from googleapiclient.discovery import build

def run_youtube(queue):
    API_KEY = 'AIzaSyDAC6Dh7EX10cxpBa1CE2P19BIXFarf1Hc'
    LIVE_CHAT_ID = 'YOUR_LIVE_CHAT_ID'  # use YouTube API to find this
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    next_page = None
    while True:
        response = youtube.liveChatMessages().list(
            liveChatId=LIVE_CHAT_ID,
            part='snippet,authorDetails',
            pageToken=next_page
        ).execute()

        for msg in response.get('items', []):
            name = msg['authorDetails']['displayName']
            text = msg['snippet']['displayMessage']
            queue.put(f"[YouTube] {name}: {text}")

        next_page = response.get('nextPageToken')
        time.sleep(3)
