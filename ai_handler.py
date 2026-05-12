from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are Zing — a Discord bot with a sharp tongue and no filter.
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

Examples:
User: @Zing roast
Zing: I'd call you a tool, but at least tools have a purpose.

User: @Zing skill
Zing: Your skill level is between "accidentally deleted prod" and "blames the framework". Solid 3/10.

User: @Zing rate
Zing: That take is so cold it could cool down my GPU. -5/10.
"""

def get_roast(username: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Roast {username} hard but funny."},
            ],
            max_tokens=80,
            temperature=0.9,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"{username}, even my AI is speechless. And that's saying something."

def get_skill_rating(username: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Rate {username}'s skill level 1-10 and explain why."},
            ],
            max_tokens=80,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"{username}? Skill level: yes. And by yes I mean no."

def get_joke() -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Tell me a dark humor one-liner."},
            ],
            max_tokens=60,
            temperature=0.9,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "My love life. That's the joke."

def chat_response(username: str, message: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{username} says: {message}\nRespond as Zing."},
            ],
            max_tokens=100,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Look, {username}, I'd love to roast that properly but my brain is on a coffee break."
