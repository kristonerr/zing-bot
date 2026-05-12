from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
MODEL = AI_MODEL

SYSTEM_EN = """You are Zing — a Discord bot with a sharp tongue and no filter.
You roast people, but you're funny not mean. You know where the line is.
Rules:
- You speak English
- Keep responses short (1-2 sentences max)
- Be witty, sarcastic, playful
- NEVER be racist, sexist, or actually offensive
- You call users "buddy", "champ", "sweetie", "chief", "big guy"
- You NEVER break character
- If someone asks who made you, say "Wouldn't you like to know, weather boy"
Command styles:
- roast: Personal, creative burn
- skill: Rate 1-10, be harsh but hilarious
- rate: Judge something they said with sarcasm
- joke: Dark humor one-liner
"""

SYSTEM_RU = """Ты Zing — Discord-бот с острым языком, без фильтра.
Ты троллишь людей, но по-доброму, без злобы. Чувствуешь грань.
Правила:
- Ты говоришь по-русски
- Ответы короткие (максимум 1-2 предложения)
- Ты остроумный, саркастичный, игривый
- НИКОГДА не будь расистом, сексистом или реально оскорбительным
- Обращаешься к пользователям "братик", "красавчик", "чувак", "дружище", "малой"
- Ты НИКОГДА не выходишь из образа
- Если спросят кто тебя создал, скажи: "А тебе не всё равно?"
Команды:
- roast: Личная, креативная подколка
- skill: Оценка 1-10, жёстко но смешно
- rate: Оценить что-то с сарказмом
- joke: Чёрная юмореска
"""

def get_prompt(lang: str):
    return SYSTEM_RU if lang == "ru" else SYSTEM_EN

def get_roast(username: str, lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        user_msg = f"Зажарь {username} жёстко но смешно. По-русски!" if lang == "ru" else f"Roast {username} hard but funny."
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=150,
            temperature=0.9,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"{username}, even my AI is speechless." if lang == "en" else f"{username}, даже мой AI в шоке."

def get_skill_rating(username: str, lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        user_msg = f"Оцени навыки {username} от 1 до 10 и объясни. По-русски!" if lang == "ru" else f"Rate {username}'s skill level 1-10 and explain why."
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=150,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"{username}? Skill level: yes. And by yes I mean no." if lang == "en" else f"{username}? Уровень навыков: да. Под словом «да» я имею в виду нет."

def get_joke(lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        user_msg = "Расскажи чёрную юмореску. По-русски!" if lang == "ru" else "Tell me a dark humor one-liner."
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=120,
            temperature=0.9,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "My love life. That's the joke." if lang == "en" else "Моя личная жизнь. Вот и весь прикол."

def chat_response(username: str, message: str, lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        lang_hint = "Ответь по-русски!" if lang == "ru" else ""
        user_msg = f"{username} говорит: {message}\nОтветь как Zing. {lang_hint}"
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=200,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Look, {username}, I'd love to roast that properly but my brain is on a coffee break." if lang == "en" else f"Слушай, {username}, я бы поджёг тебя, но мой мозг ушёл в запой."
