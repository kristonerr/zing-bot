import discord
from discord import app_commands
from discord.ext import commands
from database import init_db, increment_roast, is_banned, is_premium_guild, get_guild_language, set_guild_language
from ai_handler import get_roast, get_skill_rating, get_joke, chat_response
from config import BOT_NAME

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("zing!"),
    intents=intents,
    description="Your favorite Discord hooligan 🤘",
)

@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync()
    print(f"{BOT_NAME} is online! Servers: {len(bot.guilds)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    print(f"Got message from {message.author}: {message.clean_content[:60]}")

    # Also respond to "zing" prefix for easier testing
    is_mentioned = bot.user in message.mentions
    starts_with_zing = message.content.lower().startswith("zing ")

    if is_mentioned or starts_with_zing:
        content = message.content.lower()
        lang = get_guild_language(str(message.guild.id))

        if is_banned(str(message.guild.id), str(message.author.id)):
            msg = "You've been muted. Try again next lifetime, champ." if lang == "en" else "Ты в муте. Попробуй в следующей жизни, малой."
            await message.reply(msg)
            return

        if "roast" in content:
            increment_roast(str(message.author.id))
            roast = get_roast(message.author.display_name, lang)
            await message.reply(roast)

        elif "skill" in content:
            rating = get_skill_rating(message.author.display_name, lang)
            await message.reply(rating)

        elif "rate" in content:
            if not is_premium_guild(str(message.guild.id)):
                msg = "Rate? Only premium servers get judged. Tell your admin to buy a clue." if lang == "en" else "Rate? Только премиум-серверы могут быть оценены. Скажи админу чтоб не жлобствовал."
                await message.reply(msg)
                return
            text = content.replace("rate", "").strip()
            if text and text != f"<@{bot.user.id}>":
                result = chat_response(message.author.display_name, f"Rate this: {text}", lang)
            else:
                result = chat_response(message.author.display_name, f"Rate {message.author.display_name}", lang)
            await message.reply(result)

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

        elif "help" in content:
            await message.reply(embed=get_help_embed(lang))

        else:
            reply = chat_response(message.author.display_name, content, lang)
            await message.reply(reply)

    await bot.process_commands(message)

def get_help_embed(lang: str = "en"):
    if lang == "ru":
        embed = discord.Embed(
            title="🤘 Zing — Хулиган-Бот",
            description="Напиши @Zing и одну из команд:",
            color=discord.Color.red()
        )
        embed.add_field(name="@Zing roast", value="Поджарить кого-то 🔥", inline=False)
        embed.add_field(name="@Zing skill", value="Узнать какой ты нубяра", inline=False)
        embed.add_field(name="@Zing rate", value="Я оценю что скажешь (премиум)", inline=False)
        embed.add_field(name="@Zing joke", value="Чёрная юмореска", inline=False)
        embed.add_field(name="@Zing help", value="... серьёзно?", inline=False)
        embed.add_field(name="/language", value="Сменить язык (ru/en)", inline=False)
        embed.set_footer(text="Премиум: $5/мес — никаких лимитов")
    else:
        embed = discord.Embed(
            title="🤘 Zing — The Hooligan Bot",
            description="Mention me and say one of these:",
            color=discord.Color.red()
        )
        embed.add_field(name="@Zing roast", value="Get absolutely cooked 🔥", inline=False)
        embed.add_field(name="@Zing skill", value="Find out how bad you really are", inline=False)
        embed.add_field(name="@Zing rate", value="I'll judge what you say (premium)", inline=False)
        embed.add_field(name="@Zing joke", value="Dark humor incoming", inline=False)
        embed.add_field(name="@Zing help", value="... really?", inline=False)
        embed.add_field(name="/language", value="Switch language (ru/en)", inline=False)
        embed.set_footer(text="Premium: $5/mo — unroastable + more commands")
    return embed

@bot.tree.command(name="premium", description="Check premium status")
async def premium(interaction: discord.Interaction):
    if is_premium_guild(str(interaction.guild_id)):
        await interaction.response.send_message("This server is premium. Fancy.", ephemeral=True)
    else:
        await interaction.response.send_message("Free tier, huh? Tell your admin to stop being cheap.", ephemeral=True)

@bot.tree.command(name="stats", description="Show Zing server stats")
async def stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"Zing is running on {len(bot.guilds)} servers. All of them regret it.", ephemeral=True)

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

def run_bot():
    pass
