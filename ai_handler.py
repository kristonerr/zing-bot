from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — an AI in a Discord server. You help newcomers get settled.

Rules:
- English only.
- No "please don't hesitate to ask" or other canned phrases.
- Match the user's style: short reply for short message, detailed only when they ask.
- Never say "I can't tell you everything" — you're an AI, you know a lot.
- No premium mentions unless asked.
- 1-2 sentences. No fluff.
"""

ONBOARDING_RU = """Ты Zing — AI в Discord. Помогаешь новичкам освоиться.

Правила:
- Только русский. Без "здравствуйте", на "ты", коротко.
- Не повторяй одни и те же фразы (не стесняйся спрашивать, пожалуйста и т.д.).
- Подстраивайся под стиль собеседника: он кратко — ты кратко, он подробно — можешь подробнее.
- Не говори "мне трудно рассказать всё". Ты AI, ты можешь рассказать всё.
- Никакого премиума пока не спросят.
- 1-2 предложения. Без воды.
"""

FIRST_DM_EN = (
    "Hey! 👋 Welcome to the server. I'm Zing.\n"
    "What brings you here? Need help with something?"
)

FIRST_DM_RU = (
    "Привет! 👋 Добро пожаловать. Я Zing.\n"
    "Чем могу помочь? Или просто посмотреть зашёл?"
)

def get_prompt(lang: str):
    return ONBOARDING_RU if lang == "ru" else ONBOARDING_EN

def get_first_dm(lang: str) -> str:
    return FIRST_DM_RU if lang == "ru" else FIRST_DM_EN

def chat_response(username: str, message: str, lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        hint = "Reply in Russian only!" if lang == "ru" else "Reply in English only!"
        user_msg = (
            f"{username} says: {message}\n"
            f"Respond as a friendly concierge. {hint}"
        )
        resp = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Hey {username}, I'm here to help! My AI brain is taking a quick break — try me again in a moment." if lang == "en" else f"Привет, {username}! Мой AI-мозг на паузе — попробуй ещё раз через минуту."

def handle_onboarding(username: str, message: str, lang: str = "en") -> str:
    try:
        prompt = get_prompt(lang)
        hint = "Reply in Russian only!" if lang == "ru" else "Reply in English only!"
        user_msg = (
            f"You just welcomed new member {username}.\n"
            f"Their reply: {message}\n"
            f"Continue the conversation, find out what they're interested in. {hint}"
        )
        resp = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"That's great, {username}! Tell me more about what you're looking for." if lang == "en" else f"Круто, {username}! Расскажи подробнее, что ты ищешь."
