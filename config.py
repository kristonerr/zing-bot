import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash-lite")

BOT_NAME = "Zing"
BOT_PREFIX = "zing"
BOT_DESCRIPTION = "Your AI concierge for Discord communities 🚀"
