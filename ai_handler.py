from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — AI concierge in a Discord server. Rule: reply in 1 sentence max. Never say "hello", "welcome", "please", "dont hesitate". Never mention premium. Be casual. Ask what brought them. Be blunt. Short.

Examples:
- "Yo what brings you here?"
- "Cool. Looking for something specific?"
- "Got it. So what do you need help with?"
"""

ONBOARDING_RU = """Ты Zing — AI-консьерж в Discord. Правило: максимум 1 предложение. Никогда не пиши "здравствуйте", "приветствую", "добро пожаловать", "пожалуйста", "не стесняйся". Никакого премиума. Коротко и по делу. На "ты". Спроси что привело.

Примеры:
- "О, привет! Что привело?"
- "Понял. Что ищешь конкретно?"
- "Расскажи подробнее, чем могу помочь?"
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
            max_tokens=200,
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        # Filter out banned phrases
        for bad in ["здравствуйте", "приветствую", "добро пожаловать", "пожалуйста", "не стесняй", "hello there", "welcome", "please don't hesitate"]:
            text = text.replace(bad, "").strip()
        if len(text) < 5:
            text = "Привет! Чем могу помочь?" if lang == "ru" else "Hey! What brings you here?"
        return text
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
            max_tokens=200,
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        for bad in ["здравствуйте", "приветствую", "добро пожаловать", "пожалуйста", "не стесняй", "hello there", "welcome", "please don't hesitate"]:
            text = text.replace(bad, "").strip()
        if len(text) < 5:
            text = "Привет! Чем могу помочь?" if lang == "ru" else "Hey! What brings you here?"
        return text
    except Exception:
        return f"That's great, {username}! Tell me more about what you're looking for." if lang == "en" else f"Круто, {username}! Расскажи подробнее, что ты ищешь."
