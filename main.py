import os
import threading
from bot import bot
from server import start_server

if __name__ == "__main__":
    print("Starting Zing...")
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    bot.run(os.getenv("DISCORD_TOKEN"))
