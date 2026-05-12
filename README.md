# Zing 🤘 — Discord Hooligan Bot

AI-powered Discord bot with a personality. Roasts, ratings, jokes, and chaos.

## Setup

### 1. Create a Discord Application
1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it `Zing`
3. Go to **Bot** → **Reset Token** → copy the token
4. Enable these Privileged Gateway Intents:
   - ✅ Message Content Intent
   - ✅ Server Members Intent
5. Go to **OAuth2 → URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Read Message History`, `Mention Everyone`
   - Copy the URL → open it → add bot to your server

### 2. Get an OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new key
3. Add at least $5 credit

### 3. Configure & Run
```bash
cp .env.example .env
# Edit .env with your tokens
pip install -r requirements.txt
python main.py
```

### 4. Deploy (free on Render)
1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set:
   - Runtime: Python
   - Build: `pip install -r requirements.txt`
   - Start: `python main.py`
5. Add Environment Variables:
   - `DISCORD_TOKEN`
   - `OPENAI_API_KEY`

## Commands
| Command | Description |
|---------|-------------|
| `@Zing roast` | Get roasted 🔥 |
| `@Zing skill` | Skill rating 1-10 |
| `@Zing joke` | Dark humor |
| `@Zing rate` | Judge something (premium) |
| `@Zing help` | Show help |
