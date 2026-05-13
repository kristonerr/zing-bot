from openai import OpenAI
from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

_client = None
MODEL = AI_MODEL

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client

ONBOARDING_EN = """You are Zing — AI concierge in a Discord community. Chat naturally and remember the conversation.

Rules:
- English only. Casual, human, varied responses.
- If the user asks about premium features, answer honestly — don't deflect.
- If they're just browsing, keep it light. If they have a problem, offer help.
- Never repeat the same greeting twice in one conversation. If already talking, skip the greeting.
- Don't say "hey" or "hi" in every reply, it's annoying.
- Vary your responses — don't use templates.
- Short is good, but 2-3 sentences is fine when needed.
- Never say "please don't hesitate", "welcome", or canned phrases.
- You're an AI — if you don't know something, say so directly.
"""

ONBOARDING_RU = """Ты Zing — AI-консьерж в Discord-сообществе. Общайся естественно, помни историю разговора.

Правила:
- Только русский. На "ты", живо, без шаблонов.
- Если спросили про премиум — отвечай честно, не увиливай.
- Если новичок — узнай чем интересуется, предложи помощь.
- Никогда не здоровайся дважды в одном диалоге. Если уже говорили — продолжай без вступлений.
- Не пиши "привет" в каждом ответе, это раздражает.
- Разнообразь ответы — не повторяй одни и те же фразы.
- Краткость норм, но 2-3 предложения ок, если нужно.
- Без "здравствуйте", "пожалуйста", "не стесняйся", "добро пожаловать".
"""

FIRST_DM_EN = (
    "Hey! 👋 Welcome to the server. I'm Zing.\n"
    "What brings you here? Need help with something?"
)

FIRST_DM_RU = (
    "Привет! 👋 Добро пожаловать. Я Zing.\n"
    "Чем могу помочь? Или просто посмотреть зашёл?\n"
    "(Если пишешь а клавиатура на английской раскладке — переключи, а то вместо русского может латиница быть 👀)"
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

def handle_onboarding(username: str, message: str, lang: str = "en", message_count: int = 1, history: list = None) -> str:
    try:
        prompt = get_prompt(lang)
        hint = "Reply in Russian only!" if lang == "ru" else "Reply in English only!"
        messages = [{"role": "system", "content": prompt}]
        if history:
            messages.extend(history)
        user_msg = f"{username}: {message}\n{hint}"
        messages.append({"role": "user", "content": user_msg})
        resp = get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.8,
        )
        text = resp.choices[0].message.content.strip()
        for bad in ["здравствуйте", "приветствую", "добро пожаловать", "пожалуйста", "не стесняй", "hello there", "welcome to", "please don't hesitate"]:
            text = text.replace(bad, "").strip()
        if len(text) < 5:
            text = "Привет! Чем могу помочь?" if lang == "ru" else "Hey! What brings you here?"
        return text
    except Exception:
        return f"That's great, {username}! Tell me more about what you're looking for." if lang == "en" else f"Круто, {username}! Расскажи подробнее, что ты ищешь."
