import discord
import asyncio
import time
from discord import app_commands
from discord.ext import commands
from database import init_db, is_banned, is_premium_guild, get_guild_language, set_guild_language, add_lead, update_lead_stage, update_lead_interest, get_leads
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

@bot.event
async def on_member_join(member):
    if member.bot:
        return

    guild = member.guild
    lang = get_guild_language(str(guild.id))
    add_lead(str(guild.id), str(member.id), member.display_name)

    try:
        first_msg = get_first_dm(lang)
        await member.send(first_msg)
        update_lead_stage(str(guild.id), str(member.id), "greeting", f"Sent welcome DM to {member.display_name}")
    except discord.Forbidden:
        update_lead_stage(str(guild.id), str(member.id), "dm_blocked", f"Could not DM {member.display_name} — DMs closed")
    except Exception as e:
        update_lead_stage(str(guild.id), str(member.id), "error", f"DM error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        lang = "ru"  # default for DMs
        reply = handle_onboarding(message.author.display_name, message.clean_content, lang)
        await message.channel.send(reply)
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

        if "help" in content:
            help_en = (
                f"**👋 {BOT_NAME} — AI Concierge**\n\n"
                "Just **@mention me** or start a message with `zing ` and I'll help!\n\n"
                "`@Zing` — Ask me anything, I'm here to help\n"
                "`@Zing language ru/en` — Switch language\n"
                "`/language` — Switch language (slash command)\n"
                "`/leads` — View recent leads (admin only)\n"
                "`/premium` — Check premium status\n"
                "`/stats` — Bot stats"
            )
            help_ru = (
                f"**👋 {BOT_NAME} — AI-консьерж**\n\n"
                "Просто **упомяни меня** или начни сообщение с `zing ` и я помогу!\n\n"
                "`@Zing` — Спроси что угодно, я здесь чтобы помочь\n"
                "`@Zing language ru/en` — Сменить язык\n"
                "`/language` — Сменить язык (слэш-команда)\n"
                "`/leads` — Просмотр лидов (только админы)\n"
                "`/premium` — Статус премиума\n"
                "`/stats` — Статистика бота"
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
                        desc += f"• **{row['username']}** — {stage}" + (f" | Interest: {interest}" if interest != "—" else "") + "\n"
                    await message.reply(desc)
            else:
                await message.reply("Only admins can view leads." if lang == "en" else "Только админы могут смотреть лиды.")
            return

        user_id = str(message.author.id)
        now = time.time()
        if user_id in _cooldowns and now - _cooldowns[user_id] < 3:
            return
        _cooldowns[user_id] = now

        reply = chat_response(message.author.display_name, message.clean_content, lang)
        await message.reply(reply)

@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync()
    print(f"{BOT_NAME} is online! Servers: {len(bot.guilds)}")

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
        desc += f"• **{row['username']}** — {stage}" + (f" | {interest}" if row["interest"] else "") + "\n"
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

def run_bot():
    pass
