import random
import discord
from database import get_db

REACTIONS = ["🔥", "😏", "💀", "😂", "🤡", "👀", "🗿", "🤌", "🎪", "🧌"]

def should_react_randomly():
    return False  # disabled for now

def get_random_reaction():
    return random.choice(REACTIONS)

def check_smart_troll(message_text: str, lang: str):
    return None  # disabled for now

class GuessGame:
    def __init__(self):
        self.active_games = {}

    def start(self, guild_id: str, members):
        return False, None

    def guess(self, guild_id: str, target_id: int) -> tuple:
        return "no_game", None

guess_game = GuessGame()
