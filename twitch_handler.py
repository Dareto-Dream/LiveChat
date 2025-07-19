import socket

def run_twitch(queue):
    NICK = 'official_deltavortex'
    TOKEN = 'oauth:z1kajjkhicrp9y5l4509y5dsgmz6ji'
    CHANNEL = '#official_deltavortex'

    server = 'irc.chat.twitch.tv'
    port = 6667
    sock = socket.socket()
    sock.connect((server, port))
    sock.send(f"PASS {TOKEN}\n".encode())
    sock.send(f"NICK {NICK}\n".encode())
    sock.send(f"JOIN {CHANNEL}\n".encode())

    buffer = ""
    while True:
        buffer += sock.recv(2048).decode()
        lines = buffer.split("\r\n")
        buffer = lines.pop()
        for line in lines:
            if line.startswith("PING"):
                sock.send("PONG :tmi.twitch.tv\r\n".encode())
            elif "PRIVMSG" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    username = parts[1].split("!")[0]
                    msg = f"[Twitch] {username}: {parts[2]}"
                    queue.put(msg)
