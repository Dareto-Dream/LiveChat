import time
from queue import Queue
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']


def get_authenticated_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret_1033350218198-v48odn7v2murab79ru6p1kbv5cagmht1.apps.googleusercontent.com.json', SCOPES
    )
    creds = flow.run_local_server(port=8080)
    return build('youtube', 'v3', credentials=creds)


def get_live_chat_id(youtube):
    broadcasts = youtube.liveBroadcasts().list(
        part='snippet',
        broadcastStatus='active'
    ).execute()

    for item in broadcasts.get('items', []):
        return item['snippet']['liveChatId']

    print("[YouTube] No active broadcast found.")
    return None


def poll_chat(youtube, chat_id, queue: Queue):
    next_page_token = None

    while True:
        try:
            response = youtube.liveChatMessages().list(
                liveChatId=chat_id,
                part='snippet,authorDetails',
                pageToken=next_page_token
            ).execute()

            for msg in response.get("items", []):
                name = msg['authorDetails']['displayName']
                text = msg['snippet']['displayMessage']
                formatted = f"[YouTube] {name}: {text}"
                queue.put(formatted)

            next_page_token = response.get("nextPageToken")
            polling_interval = response.get("pollingIntervalMillis", 3000) / 1000.0
            time.sleep(polling_interval)

        except Exception as e:
            print(f"[YouTube] Error polling chat:", e)
            time.sleep(5)


def run_youtube(queue: Queue):
    youtube = get_authenticated_youtube()
    chat_id = get_live_chat_id(youtube)

    if chat_id:
        print("[YouTube] Connected. Polling chat...")
        poll_chat(youtube, chat_id, queue)
    else:
        print("[YouTube] Could not start chat polling.")
