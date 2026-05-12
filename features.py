import random
import discord
from database import get_db

REACTIONS = ["🔥", "😏", "💀", "😂", "🤡", "👀", "🗿", "🤌", "🎪", "🧌"]

TRIGGER_PATTERNS = [
    ("how to make money fast", "bro, if I knew I wouldn't be a Discord bot"),
    ("i'm bored", "Skill issue. Get roasted or get good."),
    ("is anyone here", "Just me and your lack of friends, champ."),
    ("how to get a girlfriend", "Step 1: Stop asking Discord bots. Step 2: Touch grass."),
    ("i'm lonely", "Have you tried being interesting? Just a thought."),
    ("rate my setup", "10/10... if your goal is to look like you bought everything at a garage sale"),
    ("i can't code", "Don't worry, it shows."),
    ("what's the meaning of life", "42. Next question."),
    ("i'm better than you", "That's cute. The short bus is here for you, buddy."),
    ("gg", "gg indeed. Especially if you're on the losing team."),
    ("anyone want to play", "I'd play with you, but I don't think my AI can handle that much secondhand embarrassment"),
    ("i'm tired", "Of what? Typing? Don't worry, I'll carry this conversation."),
    ("help me", "I can't, I'm a bot. Try a therapist."),
    ("this server is dead", "It's not dead — it's just allergic to your messages."),
    ("i made a game", "Was it called 'how to waste everyone's time'?"),
]

TRIGGER_PATTERNS_RU = [
    ("как заработать", "Бро, если бы я знал — я бы не сидел в Дискорде ботом"),
    ("мне скучно", "Навык-issue. Дай себя поджарить или иди гуляй, малой"),
    ("есть кто", "Только я и отсутствие у тебя друзей, красавчик"),
    ("как найти девушку", "Шаг 1: перестать спрашивать у Discord-бота. Шаг 2: выйти на улицу"),
    ("мне одиноко", "А ты пробовал быть интересным? Просто мысль"),
    ("оцени", "5/10. Амбициозно, но исполнение подкачало"),
    ("я не умею кодить", "Да ладно, неудивительно"),
    ("смысл жизни", "42. Следующий вопрос"),
    ("я лучше тебя", "Милый, у меня даже рук нет, а я всё равно тебя умнее"),
    ("кто хочет поиграть", "Я бы сыграл, но мой ИИ не выдержит такого количества кринжа"),
    ("я устал", "От чего? От печатания? Давай, я понесу этот разговор"),
    ("помоги", "Я бот, не врач. Попробуй психотерапевта"),
    ("сервер мёртвый", "Он не мёртвый — он просто аллергичен на твои сообщения"),
    ("игра", "Ты про игру 'угадай кто здесь самый скучный'? Потому что ты выигрываешь"),
]

def should_react_randomly():
    return random.random() < 0.1

def get_random_reaction():
    return random.choice(REACTIONS)

def check_smart_troll(message_text: str, lang: str):
    text = message_text.lower()
    patterns = TRIGGER_PATTERNS_RU if lang == "ru" else TRIGGER_PATTERNS
    for trigger, response in patterns:
        if trigger in text:
            return response
    return None

class GuessGame:
    def __init__(self):
        self.active_games = {}

    def start(self, guild_id: str, members):
        if guild_id in self.active_games:
            return False, None
        target = random.choice(members)
        if target.bot:
            return False, None
        self.active_games[guild_id] = {
            "target_id": target.id,
            "target_name": target.display_name,
            "hints": 0,
            "attempts": 0,
        }
        hints = [
            f"Этот человек {'носит очки' if random.random() > 0.5 else 'не носит очки'}... ну, типа того.",
            f"Он/она {'часто пишет в чат' if random.random() > 0.5 else 'молчит как партизан'}.",
            f"Ник начинается на букву '{target.display_name[0].upper()}'",
        ]
        return True, random.choice(hints)

    def guess(self, guild_id: str, target_id: int) -> tuple:
        if guild_id not in self.active_games:
            return "no_game", None
        game = self.active_games[guild_id]
        game["attempts"] += 1

        if target_id == game["target_id"]:
            del self.active_games[guild_id]
            return "win", game["target_name"]
        else:
            return "lose", game["attempts"]

guess_game = GuessGame()
