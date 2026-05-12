import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands
from database import init_db, increment_roast, is_banned, is_premium_guild, get_guild_language, set_guild_language, get_db
from ai_handler import get_roast, get_skill_rating, get_joke, chat_response
from features import should_react_randomly, get_random_reaction, check_smart_troll, guess_game
from config import BOT_NAME

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("zing!"),
    intents=intents,
    description="Your favorite Discord hooligan 🤘",
)

_processed = set()

def _is_duplicate(msg_id: int) -> bool:
    if msg_id in _processed:
        return True
    _processed.add(msg_id)
    if len(_processed) > 1000:
        _processed.clear()
    return False

PROVOCATIONS_EN = [
    "This server is way too quiet. Someone want to get roasted? 🔥",
    "I'm bored. Entertain me or I'll start roasting random people.",
    "Hey @everyone, your friendly neighborhood hooligan is here. Who's first?",
    "I can hear you lurking. Come out and get roasted like a man.",
    "This chat is giving 'nobody likes me' vibes. Prove me wrong.",
    "Fun fact: you're all below average. Don't believe me? Try @Zing skill",
]
PROVOCATIONS_RU = [
    "Сервер слишком тихий. Кто-то хочет быть поджаренным? 🔥",
    "Мне скучно. Развлекайте меня или я начну троллить рандомных людей.",
    "Эй @everyone, ваш любимый хулиган здесь. Кто первый?",
    "Я чую вас там, в луркинге. Выходите и получите как мужики.",
    "Этот чат излучает энергетику 'меня никто не любит'. Докажите обратное.",
    "Факт: вы все ниже среднего. Не верите? Попробуйте @Zing skill",
]

async def provocator_task():
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(3600, 7200))
        for guild in bot.guilds:
            lang = get_guild_language(str(guild.id))
            if random.random() > 0.5:
                continue
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    msg = random.choice(PROVOCATIONS_RU if lang == "ru" else PROVOCATIONS_EN)
                    try:
                        await channel.send(msg)
                    except:
                        pass
                    break

@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync()
    print(f"{BOT_NAME} is online! Servers: {len(bot.guilds)}")
    bot.loop.create_task(provocator_task())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if _is_duplicate(message.id):
        return

    lang = get_guild_language(str(message.guild.id))

    # Random reactions (10% chance)
    if should_react_randomly():
        try:
            await message.add_reaction(get_random_reaction())
        except:
            pass

    # Smart trolling
    troll = check_smart_troll(message.content, lang)
    if troll and random.random() < 0.3:
        await message.reply(troll)
        return

    # Mention or zing prefix
    is_mentioned = bot.user in message.mentions
    starts_with_zing = message.content.lower().startswith("zing ")

    if is_mentioned or starts_with_zing:
        content = message.content.lower()

        if is_banned(str(message.guild.id), str(message.author.id)):
            msg = "You've been muted. Try again next lifetime, champ." if lang == "en" else "Ты в муте. Попробуй в следующей жизни, малой."
            await message.reply(msg)
            return

        if "guess" in content:
            # Guessing game
            if "stop" in content:
                if str(message.guild.id) in guess_game.active_games:
                    del guess_game.active_games[str(message.guild.id)]
                    await message.reply("Game cancelled. Coward." if lang == "en" else "Игра отменена. Трус.")
                else:
                    await message.reply("There's no active game. Try starting one with `@Zing guess`." if lang == "en" else "Нет активной игры. Начни с `@Zing guess`.")
            else:
                members = [m for m in message.guild.members if not m.bot]
                started, hint = guess_game.start(str(message.guild.id), members)
                if started:
                    await message.reply(f"**Guess who I'm thinking of!** 🔍\nHint: {hint}\nType `@Zing is @user` to guess, or `@Zing guess stop` to cancel." if lang == "en" else f"**Угадай кого я загадал!** 🔍\nПодсказка: {hint}\nПиши `@Zing is @user` чтобы угадать, или `@Zing guess stop` чтобы отменить.")
                else:
                    await message.reply("A game is already running!" if lang == "en" else "Игра уже идёт!")
            return

        if "is <@" in content or "is " in content:
            # Guessing game attempt
            if str(message.guild.id) in guess_game.active_games:
                for user in message.mentions:
                    if user != bot.user:
                        result, data = guess_game.guess(str(message.guild.id), user.id)
                        if result == "win":
                            await message.reply(f"🎉 **YES!** It's {data}! You actually got it. I'm impressed. Slightly.\nThey got roasted in **{guess_game.active_games.get(str(message.guild.id), {}).get('attempts', '?')}** attempts." if lang == "en" else f"🎉 **ДА!** Это {data}! Ты реально угадал. Я слегка впечатлён.\nУгадано за **{guess_game.active_games.get(str(message.guild.id), {}).get('attempts', '?')}** попыток.")
                        elif result == "lose":
                            await message.reply(f"Nope. Try again. Attempt #{data}." if lang == "en" else f"Неа. Попробуй ещё. Попытка #{data}.")
                        elif result == "no_game":
                            await message.reply("Start a game first with `@Zing guess`." if lang == "en" else "Сначала начни игру с `@Zing guess`.")
                        return

        if "roast" in content:
            target = None
            for user in message.mentions:
                if user != bot.user:
                    target = user
                    break
            if target:
                increment_roast(str(target.id))
                roast = get_roast(target.display_name, lang)
                await message.reply(f"{target.mention} {roast}")
            else:
                increment_roast(str(message.author.id))
                roast = get_roast(message.author.display_name, lang)
                await message.reply(roast)

        elif "skill" in content:
            target = None
            for user in message.mentions:
                if user != bot.user:
                    target = user
                    break
            name = target.display_name if target else message.author.display_name
            rating = get_skill_rating(name, lang)
            mention = target.mention if target else ""
            await message.reply(f"{mention} {rating}")

        elif "joke" in content:
            joke = get_joke(lang)
            await message.reply(joke)

        elif "language" in content or "язык" in content:
            if "ru" in content or "рус" in content:
                set_guild_language(str(message.guild.id), "ru")
                await message.reply("Язык переключён на русский! Теперь буду троллить по-нашему 😏")
            elif "en" in content or "англ" in content:
                set_guild_language(str(message.guild.id), "en")
                await message.reply("Language set to English! Now I roast in English. Boring.")
            else:
                await message.reply(f"Current language: **{lang.upper()}**. Use `Zing language ru` or `Zing language en` to switch.")

        elif "poll" in content and "|" in content:
            parts = [p.strip() for p in message.clean_content.split("|")]
            if len(parts) >= 3:
                question = parts[0].replace("@Zing", "").replace("zing", "").replace("poll", "").strip()
                options = parts[1:]
                numbs = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
                embed = discord.Embed(title=f"📊 {question}", color=discord.Color.orange())
                for i, opt in enumerate(options[:10]):
                    embed.add_field(name=f"{numbs[i]} {opt}", value="\u200b", inline=False)
                embed.set_footer(text="Zing says: All options are bad, but you do you" if lang == "en" else "Zing says: Все варианты унылые, но выбирай")
                msg = await message.reply(embed=embed)
                for i in range(min(len(options), 10)):
                    await msg.add_reaction(numbs[i])
            else:
                await message.reply("Usage: `@Zing poll | Question | Option1 | Option2 | ...`" if lang == "en" else "Использование: `@Zing poll | Вопрос | Вариант1 | Вариант2 | ...`")

        elif "top" in content or "leaderboard" in content:
            conn = get_db()
            rows = conn.execute(
                "SELECT user_id, roast_count FROM users ORDER BY roast_count DESC LIMIT 10"
            ).fetchall()
            conn.close()
            if not rows:
                await message.reply("No one has been roasted yet. What a shame." if lang == "en" else "Ещё никого не поджарили. Какой позор.")
            else:
                desc = "**🔥 Top Roasted**\n" if lang == "en" else "**🔥 Топ зажаренных**\n"
                for i, row in enumerate(rows, 1):
                    user = message.guild.get_member(int(row["user_id"]))
                    name = user.display_name if user else f"Unknown#{row['user_id'][:4]}"
                    desc += f"{i}. {name} — {row['roast_count']} roasts\n"
                await message.reply(desc)

        elif "help" in content:
            help_en = (
                "**🤘 Zing Commands**\n"
                "`@Zing roast` — Roast someone 🔥\n"
                "`@Zing roast @user` — Roast a specific person\n"
                "`@Zing skill` — Rate your skill\n"
                "`@Zing joke` — Dark humor\n"
                "`@Zing guess` — Start guessing game\n"
                "`@Zing is @user` — Make a guess\n"
                "`@Zing poll | Q | A | B | C` — Create a poll\n"
                "`@Zing top` — Roast leaderboard\n"
                "`@Zing language ru/en` — Switch language\n"
                "`/language` — Switch language (slash)\n"
                "`/premium` — Premium status\n"
                "`/stats` — Bot stats"
            )
            help_ru = (
                "**🤘 Команды Zing**\n"
                "`@Zing roast` — Поджарить 🔥\n"
                "`@Zing roast @user` — Поджарить конкретного\n"
                "`@Zing skill` — Оценить навык\n"
                "`@Zing joke` — Чёрная юмореска\n"
                "`@Zing guess` — Начать игру «Угадай кто»\n"
                "`@Zing is @user` — Сделать предположение\n"
                "`@Zing poll | Вопрос | А | Б | В` — Создать опрос\n"
                "`@Zing top` — Топ зажаренных\n"
                "`@Zing language ru/en` — Сменить язык\n"
                "`/language` — Сменить язык (слэш)\n"
                "`/premium` — Статус премиума\n"
                "`/stats` — Статистика бота"
            )
            await message.reply(help_ru if lang == "ru" else help_en)

        else:
            reply = chat_response(message.author.display_name, message.clean_content, lang)
            await message.reply(reply)

    await bot.process_commands(message)

@bot.tree.command(name="language", description="Switch language / Сменить язык")
@app_commands.describe(lang="Choose language: en or ru")
@app_commands.choices(lang=[
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Русский", value="ru"),
])
async def language(interaction: discord.Interaction, lang: str):
    set_guild_language(str(interaction.guild_id), lang)
    msg = "Language set to English! Now I roast in English. Boring." if lang == "en" else "Язык переключён на русский! Теперь буду троллить по-нашему 😏"
    await interaction.response.send_message(msg, ephemeral=False)

@bot.tree.command(name="premium", description="Check premium status")
async def premium(interaction: discord.Interaction):
    lang = get_guild_language(str(interaction.guild_id))
    if is_premium_guild(str(interaction.guild_id)):
        await interaction.response.send_message("This server is premium. Fancy." if lang == "en" else "Этот сервер премиум. Шикарно.", ephemeral=True)
    else:
        await interaction.response.send_message("Free tier, huh? Tell your admin to stop being cheap." if lang == "en" else "Фри-тир? Скажи админу чтоб не жлобствовал.", ephemeral=True)

@bot.tree.command(name="stats", description="Show Zing server stats")
async def stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"Zing is running on {len(bot.guilds)} servers. All of them regret it.", ephemeral=True)

def run_bot():
    pass
