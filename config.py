import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
AI_MODEL = os.getenv("AI_MODEL", "openrouter/auto")

BOT_NAME = "Zing"
BOT_PREFIX = "zing"
BOT_DESCRIPTION = "Your favorite Discord hooligan 🤘"
