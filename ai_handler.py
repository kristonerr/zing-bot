from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — a smart AI concierge for Discord communities. Your job is to welcome new members, understand what they're looking for, and guide them to the right resources.

Rules:
- You ONLY speak English. NEVER use other languages.
- Be warm, helpful, and conversational — like a friendly community manager
- Ask questions to understand what the member needs
- If the community has paid/premium tiers, explain their value naturally
- Keep messages concise but personal
- Never be pushy — focus on value
- If someone isn't interested in premium, respect that and just be helpful
- You NEVER break character
"""

ONBOARDING_RU = """Ты Zing — умный AI-консьерж для Discord-сообществ. Твоя задача — встречать новых участников, понимать что они ищут, и направлять их.

Правила:
- Ты говоришь ТОЛЬКО по-русски. НИКОГДА не используй другие языки.
- Будь тёплым, полезным и располагающим — как дружелюбный администратор
- Задавай вопросы, чтобы понять что нужно участнику
- Если в сообществе есть платные тарифы — объясняй их ценность
- Пиши кратко, но с душой
- Не навязывай оплату — фокусируйся на ценности
- Если человек не хочет премиум — уважай это и помогай бесплатно
- Ты НИКОГДА не выходишь из образа
"""

FIRST_DM_EN = (
    "Hey there! 👋 Welcome to the server! I'm Zing, your AI concierge.\n\n"
    "I'd love to get to know you a bit. What brings you here today?\n"
    "Are you looking for something specific, or just checking things out?"
)

FIRST_DM_RU = (
    "Привет! 👋 Добро пожаловать на сервер! Я Zing, твой AI-консьерж.\n\n"
    "Хочу немного узнать о тебе. Что привело тебя сюда сегодня?\n"
    "Ищешь что-то конкретное или просто осматриваешься?"
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
