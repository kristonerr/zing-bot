import discord
import asyncio
import time
from discord import app_commands
from discord.ext import commands
from database import init_db, is_banned, is_premium_guild, get_guild_language, set_guild_language, add_lead, update_lead_stage, update_lead_interest, update_lead_score, get_lead, get_leads
from ai_handler import chat_response, handle_onboarding, get_first_dm
from config import BOT_NAME

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="zing ",
    intents=intents,
    description="Your AI concierge for Discord communities",
)

_cooldowns = {}
_processed_messages = set()
_dm_counts = {}
_user_guilds = {}  # user_id -> guild_id (last seen guild)
_dm_history = {}  # user_id -> list of {"role": "user"/"assistant", "content": str}

@bot.event
async def on_member_join(member):
    try:
        if member.bot:
            return

        guild = member.guild
        lang = get_guild_language(str(guild.id))
        add_lead(str(guild.id), str(member.id), member.display_name)
        _user_guilds[str(member.id)] = str(guild.id)

        try:
            first_msg = get_first_dm(lang)
            await member.send(first_msg)
            update_lead_stage(str(guild.id), str(member.id), "greeting", f"Sent welcome DM to {member.display_name}")
        except discord.Forbidden:
            update_lead_stage(str(guild.id), str(member.id), "dm_blocked", f"Could not DM {member.display_name} — DMs closed")
        except Exception as e:
            update_lead_stage(str(guild.id), str(member.id), "error", f"DM error: {e}")
    except Exception as e:
        print(f"on_member_join error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    msg_id = message.id
    if msg_id in _processed_messages:
        return
    _processed_messages.add(msg_id)
    if len(_processed_messages) > 1000:
        _processed_messages.clear()

    if isinstance(message.channel, discord.DMChannel):
        user_id = str(message.author.id)
        now = time.time()
        if user_id in _cooldowns and now - _cooldowns[user_id] < 2:
            return
        _cooldowns[user_id] = now

        guild_id = _user_guilds.get(user_id)
        if not guild_id:
            await message.channel.send("Hey! Which server are you from? I need to know to help you better.")
            return

        content_lower = message.clean_content.lower()
        if "english" in content_lower or "i speak english" in content_lower:
            lang = "en"
        else:
            lang = "ru"

        if user_id not in _dm_history:
            _dm_history[user_id] = []
        prev_history = _dm_history[user_id]  # only past exchanges, not current msg yet
        if len(prev_history) > 10:
            prev_history = prev_history[-10:]
            _dm_history[user_id] = prev_history

        _dm_counts[user_id] = _dm_counts.get(user_id, 0) + 1
        count = _dm_counts[user_id]

        reply = handle_onboarding(message.author.display_name, message.clean_content, lang, count, prev_history)
        await message.channel.send(reply)

        _dm_history[user_id].append({"role": "user", "content": message.clean_content})
        _dm_history[user_id].append({"role": "assistant", "content": reply})

        if count == 1:
            update_lead_stage(guild_id, user_id, "chatting", f"Reply: {message.clean_content[:50]}")
        elif count >= 5:
            update_lead_stage(guild_id, user_id, "engaged", f"Active conversation ({count} msgs)")
        return

    lang = get_guild_language(str(message.guild.id))

    is_mentioned = bot.user in message.mentions
    starts_with_zing = message.content.lower().startswith("zing ")

    if is_mentioned or starts_with_zing:
        content = message.clean_content.lower()

        if is_banned(str(message.guild.id), str(message.author.id)):
            msg = "You're muted in this server." if lang == "en" else "Ты в муте на этом сервере."
            await message.reply(msg)
            return

        if "language" in content or "язык" in content:
            if "ru" in content or "рус" in content:
                set_guild_language(str(message.guild.id), "ru")
                await message.reply("Язык переключён на русский! Теперь буду помогать по-нашему 😊")
            elif "en" in content or "англ" in content:
                set_guild_language(str(message.guild.id), "en")
                await message.reply("Language set to English! Happy to help 😊")
            else:
                await message.reply(f"Current language: **{lang.upper()}**. Use `@Zing language ru` or `@Zing language en` to switch.")
            return

        if "test" in content and "onboard" in content:
            first_msg = get_first_dm(lang)
            add_lead(str(message.guild.id), str(message.author.id), message.author.display_name)
            _user_guilds[str(message.author.id)] = str(message.guild.id)
            await message.reply(f"**Simulating new member join...**\n\n{first_msg}")
            return

        if "help" in content:
            help_en = (
                f"**👋 {BOT_NAME} — AI Concierge**\n\n"
                "Just **@mention me** or start a message with `zing ` and I'll help!\n\n"
                "`@Zing` — Ask me anything\n"
                "`@Zing language ru/en` — Switch language\n"
                "`@Zing test onboard` — Simulate new member join\n"
                "`/leads` — View recent leads (admin only)"
            )
            help_ru = (
                f"**👋 {BOT_NAME} — AI-консьерж**\n\n"
                "Просто **упомяни меня** или начни сообщение с `zing ` и я помогу!\n\n"
                "`@Zing` — Спроси что угодно\n"
                "`@Zing language ru/en` — Сменить язык\n"
                "`@Zing test onboard` — Тест приветствия новичка\n"
                "`/leads` — Просмотр лидов (только админы)"
            )
            await message.reply(help_ru if lang == "ru" else help_en)
            return

        if "leads" in content:
            if message.author.guild_permissions.administrator:
                rows = get_leads(str(message.guild.id), 10)
                if not rows:
                    await message.reply("No leads yet." if lang == "en" else "Лидов пока нет.")
                else:
                    desc = "**📋 Recent Leads**\n" if lang == "en" else "**📋 Последние лиды**\n"
                    for row in rows:
                        stage = row["stage"]
                        interest = row["interest"] or "—"
                        score = row["score"] or "—"
                        desc += f"• **{row['username']}** [{score}] — {stage}" + (f" | {interest}" if interest != "—" else "") + "\n"
                    await message.reply(desc)
            else:
                await message.reply("Only admins can view leads." if lang == "en" else "Только админы могут смотреть лиды.")
            return

        user_id = str(message.author.id)
        _user_guilds[user_id] = str(message.guild.id)
        now = time.time()
        if user_id in _cooldowns and now - _cooldowns[user_id] < 3:
            return
        _cooldowns[user_id] = now

        reply = chat_response(message.author.display_name, message.clean_content, lang)
        await message.reply(reply)

@bot.event
async def on_ready():
    try:
        init_db()
        await bot.tree.sync()
        print(f"{BOT_NAME} is online! Servers: {len(bot.guilds)}")
    except Exception as e:
        print(f"on_ready error: {e}")

@bot.tree.command(name="language", description="Switch language / Сменить язык")
@app_commands.describe(lang="Choose language: en or ru")
@app_commands.choices(lang=[
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Русский", value="ru"),
])
async def language(interaction: discord.Interaction, lang: str):
    set_guild_language(str(interaction.guild_id), lang)
    msg = "Language set to English! 😊" if lang == "en" else "Язык переключён на русский! 😊"
    await interaction.response.send_message(msg, ephemeral=False)

@bot.tree.command(name="leads", description="View recent leads (admin only)")
async def leads(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can use this." if get_guild_language(str(interaction.guild_id)) == "en" else "Только админы могут это использовать.", ephemeral=True)
        return
    rows = get_leads(str(interaction.guild_id), 10)
    if not rows:
        await interaction.response.send_message("No leads yet." if get_guild_language(str(interaction.guild_id)) == "en" else "Лидов пока нет.", ephemeral=True)
        return
    desc = "**📋 Recent Leads**\n" if get_guild_language(str(interaction.guild_id)) == "en" else "**📋 Последние лиды**\n"
    for row in rows:
        stage = row["stage"]
        interest = row["interest"] or "—"
        score = row["score"] or "—"
        desc += f"• **{row['username']}** [{score}] — {stage}" + (f" | {interest}" if row["interest"] else "") + "\n"
    await interaction.response.send_message(desc, ephemeral=True)

@bot.tree.command(name="premium", description="Check premium status")
async def premium(interaction: discord.Interaction):
    lang = get_guild_language(str(interaction.guild_id))
    if is_premium_guild(str(interaction.guild_id)):
        await interaction.response.send_message("This server is premium. Thank you for your support! 🎉" if lang == "en" else "Этот сервер премиум. Спасибо за поддержку! 🎉", ephemeral=True)
    else:
        await interaction.response.send_message("This server is on the free tier. Ask your admin about premium!" if lang == "en" else "Этот сервер на бесплатном тарифе. Спроси админа про премиум!", ephemeral=True)

@bot.tree.command(name="stats", description="Show Zing server stats")
async def stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"Zing is running on {len(bot.guilds)} servers, helping communities grow! 🚀", ephemeral=True)


