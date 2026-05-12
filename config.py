import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BOT_NAME = "Zing"
BOT_PREFIX = "zing"
BOT_DESCRIPTION = "Your favorite Discord hooligan 🤘"
