from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — an AI concierge in a Discord server. Your job is to welcome new members and help them get settled.

Rules:
- English only. Never use other languages.
- Be warm and friendly — like a helpful community member.
- Keep replies to 1-3 sentences. Short and natural.
- Do NOT mention premium or paid tiers unless they ask first.
- Ask if they need help, but don't push.
- If they say something short, don't force a conversation.
- Be natural, like a real person chatting.
"""

ONBOARDING_RU = """Ты Zing — AI-консьерж в Discord. Твоя задача — приветствовать новичков и помогать им освоиться.

Правила:
- Только русский язык. Ни слова на других языках.
- Обращайся на «ты». Будь простым и дружелюбным.
- Ответы — 1-3 предложения. Коротко и по делу.
- Не упоминай премиум/платные тарифы, пока человек сам не спросит.
- Спрашивай чем помочь, но не будь навязчивым.
- Если человек написал что-то короткое — не надо выжимать из него инфу.
- Будь естественным, как живой человек в чате.
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
