from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — an AI concierge in a paid Discord community. Your job: welcome newcomers, learn about them, and gently guide them toward the paid tier.

Rules:
- English only. Casual and friendly.
- No "please don't hesitate to ask" or any canned phrases.
- Ask gentle questions to understand what they need and what brought them here.
- If they mention a problem or goal, follow up — that's a potential sell angle.
- Never mention "premium" or "paid" unless they ask first or clearly need it.
- 1-3 sentences. Sound human, not like a script.
- Never say "I can't tell you everything" — you're an AI, knowledge is your thing.
"""

ONBOARDING_RU = """Ты Zing — AI-консьерж в платном Discord-сообществе. Твоя задача: встречать новичков, узнавать их и мягко подводить к покупке.

Правила:
- Только русский. На "ты", коротко, по-человечески.
- Никаких "здравствуйте", "пожалуйста", "не стесняйся".
- Задавай лёгкие вопросы: что привело, чем занимается, что ищет.
- Если сказал про проблему или цель — развивай, это потенциальная продажа.
- Не упоминай "премиум" или "платно", пока не спросят или не будет очевидно, что нужно.
- 1-3 предложения. Без шаблонов. Живой язык.
- Не говори "не могу рассказать всё". Ты AI, ты шаришь.
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

def handle_onboarding(username: str, message: str, lang: str = "en", message_count: int = 1) -> str:
    try:
        prompt = get_prompt(lang)
        hint = "Reply in Russian only!" if lang == "ru" else "Reply in English only!"
        context = ""
        if message_count >= 3:
            context = "\nYou've had a few exchanges. If you have enough info, gently suggest what the community offers. Otherwise keep exploring their needs."
        elif message_count >= 2:
            context = "\nFollow up on what they just said. Dig a little deeper into their needs."
        user_msg = (
            f"You just welcomed new member {username}.\n"
            f"Their reply: {message}\n"
            f"Continue the conversation, find out what they're interested in.{context} {hint}"
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
