# tiktok_handler.py

from TikTokLive import TikTokLiveClient

def run_tiktok(queue):
    client = TikTokLiveClient(unique_id="arcturus.vega")  # no @

    @client.on("comment")
    async def on_comment(event):
        try:
            username = event.user.nickname
            message = event.comment
            queue.put(f"[TikTok] {username}: {message}")
        except Exception as e:
            print("[TikTok] Error:", e)

    client.run()
