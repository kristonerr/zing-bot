import discord
import asyncio
import sqlite3
import time
from discord import app_commands
from discord.ext import commands
from database import init_db, is_banned, is_premium_guild, get_guild_language, set_guild_language, add_lead, update_lead_stage, update_lead_interest, update_lead_score, update_lead_thread, get_lead, get_leads, set_onboard_channel, get_onboard_channel, set_auto_role, get_auto_role
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
_thread_map = {}  # thread_id -> {"guild_id": str, "user_id": str}
_user_lang = {}  # user_id -> "ru" or "en" (per-user language preference)

@bot.event
async def on_member_join(member):
    try:
        if member.bot:
            return

        guild = member.guild
        lang = get_guild_language(str(guild.id))
        add_lead(str(guild.id), str(member.id), member.display_name)
        _user_guilds[str(member.id)] = str(guild.id)

        # Auto-assign role if configured
        auto_role_id = get_auto_role(str(guild.id))
        if auto_role_id:
            try:
                role = guild.get_role(int(auto_role_id))
                if role:
                    await member.add_roles(role, reason="Auto-role on join")
            except Exception as e:
                print(f"Auto-role error: {e}")

        # Try private thread first
        thread = None
        onboard_channel_id = get_onboard_channel(str(guild.id))
        channel = None
        if onboard_channel_id:
            channel = guild.get_channel(int(onboard_channel_id))
        if not channel:
            targets = ["onboarding", "welcome", "приветствие", "знакомства", "general", "main"]
            for target in targets:
                channel = discord.utils.find(lambda c: c.name.lower() == target, guild.text_channels)
                if channel:
                    break
        if not channel:
            channel = guild.system_channel
        if not channel:
            channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).create_private_threads), None)

        if channel:
            perms = channel.permissions_for(guild.me)
            if not perms.create_private_threads:
                update_lead_stage(str(guild.id), str(member.id), "no_perms", "Bot needs Create Private Threads permission")
                print(f"No CREATE_PRIVATE_THREADS in #{channel.name}")
            elif not perms.send_messages_in_threads:
                update_lead_stage(str(guild.id), str(member.id), "no_perms", "Bot needs Send Messages In Threads permission")
                print(f"No SEND_MESSAGES_IN_THREADS in #{channel.name}")
            else:
                try:
                    thread_name = f"⚡ hi — {member.display_name}" if lang == "en" else f"⚡ привет — {member.display_name}"
                    thread = await channel.create_thread(
                        name=thread_name[:100],
                        type=discord.ChannelType.private_thread,
                        reason=f"Onboarding for {member.display_name}",
                    )
                    await thread.add_user(member)
                    first_msg = get_first_dm(lang)
                    await thread.send(first_msg)
                    update_lead_thread(str(guild.id), str(member.id), str(thread.id))
                    update_lead_stage(str(guild.id), str(member.id), "greeting", f"Created thread {thread.name}")
                    _thread_map[str(thread.id)] = {"guild_id": str(guild.id), "user_id": str(member.id)}
                    return
                except discord.Forbidden:
                    update_lead_stage(str(guild.id), str(member.id), "thread_forbidden", "Missing permissions for thread")
                except Exception as e:
                    print(f"Thread creation failed: {e}")
                    update_lead_stage(str(guild.id), str(member.id), "thread_failed", f"Could not create thread: {e}")

        # Fallback to DM
        try:
            first_msg = get_first_dm(lang)
            await member.send(first_msg)
            _user_guilds[str(member.id)] = str(guild.id)
            update_lead_stage(str(guild.id), str(member.id), "greeting", f"Sent welcome DM to {member.display_name}")
        except discord.Forbidden:
            update_lead_stage(str(guild.id), str(member.id), "dm_blocked", f"Could not DM {member.display_name}")
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
            lead = get_lead(None, user_id)
            if lead:
                guild_id = lead["guild_id"]
                _user_guilds[user_id] = guild_id

        content_lower = message.clean_content.lower()
        if "english" in content_lower or "i speak english" in content_lower or "switch to english" in content_lower:
            _user_lang[user_id] = "en"
        elif "русский" in content_lower or "переключи на русский" in content_lower or "по русски" in content_lower:
            _user_lang[user_id] = "ru"
        lang = _user_lang.get(user_id, "ru")

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

        if guild_id and count == 1:
            update_lead_stage(guild_id, user_id, "chatting", f"Reply: {message.clean_content[:50]}")
        elif guild_id and count >= 5:
            update_lead_stage(guild_id, user_id, "engaged", f"Active conversation ({count} msgs)")
        return

    # Thread onboarding handler (reply in onboarding threads)
    if isinstance(message.channel, discord.Thread) and message.channel.name.startswith("⚡"):
        user_id = str(message.author.id)
        thread_id = str(message.channel.id)

        thread_data = _thread_map.get(thread_id)
        if not thread_data:
            lead = get_lead(None, user_id)
            if lead and lead.get("thread_id") == thread_id:
                thread_data = {"guild_id": lead["guild_id"], "user_id": lead["user_id"]}
                _thread_map[thread_id] = thread_data
        if not thread_data:
            return

        guild_id = thread_data["guild_id"]
        _user_guilds[user_id] = guild_id
        now = time.time()
        if user_id in _cooldowns and now - _cooldowns[user_id] < 2:
            return
        _cooldowns[user_id] = now

        # Detect per-user language
        content_lower = message.clean_content.lower()
        if "english" in content_lower or "i speak english" in content_lower or "switch to english" in content_lower:
            _user_lang[user_id] = "en"
        elif "русский" in content_lower or "переключи на русский" in content_lower or "по русски" in content_lower:
            _user_lang[user_id] = "ru"
        lang = _user_lang.get(user_id, get_guild_language(guild_id))
        if user_id not in _dm_history:
            _dm_history[user_id] = []
        prev_history = _dm_history[user_id]
        if len(prev_history) > 10:
            prev_history = prev_history[-10:]

        _dm_counts[user_id] = _dm_counts.get(user_id, 0) + 1
        count = _dm_counts[user_id]

        reply = handle_onboarding(message.author.display_name, message.clean_content, lang, count, prev_history)
        await message.channel.send(reply)

        _dm_history[user_id].append({"role": "user", "content": message.clean_content})
        _dm_history[user_id].append({"role": "assistant", "content": reply})

        if count == 1:
            update_lead_stage(guild_id, user_id, "chatting", f"Thread reply: {message.clean_content[:50]}")
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

        if "test" in content and "thread" in content:
            channel = message.channel
            can_create = channel.permissions_for(message.guild.me).create_private_threads
            perms_msg = f"Create Private Threads: **{'✅' if can_create else '❌'}**\n" if lang == "en" else f"Создание приватных тредов: **{'✅' if can_create else '❌'}**\n"
            try:
                thread = await channel.create_thread(
                    name=f"⚡ test — {message.author.display_name}"[:100],
                    type=discord.ChannelType.private_thread,
                    reason="Thread test",
                )
                await thread.add_user(message.author)
                await thread.send("Thread works! 🎉" if lang == "en" else "Тред работает! 🎉")
                await message.reply(perms_msg + ("Thread created! Check the thread above ^^" if lang == "en" else "Тред создан! Глянь выше ^^"))
            except Exception as e:
                await message.reply(perms_msg + f"Error: {e}")
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
        # Recover thread map from DB after restart
        conn = sqlite3.connect("zing.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT guild_id, user_id, thread_id FROM leads WHERE thread_id IS NOT NULL").fetchall()
        conn.close()
        for row in rows:
            if row["thread_id"]:
                _thread_map[row["thread_id"]] = {"guild_id": row["guild_id"], "user_id": row["user_id"]}
        for guild in bot.guilds:
            try:
                bot.tree.copy_global_to(guild=discord.Object(id=guild.id))
                await bot.tree.sync(guild=discord.Object(id=guild.id))
            except:
                pass
        print(f"{BOT_NAME} is online! Servers: {len(bot.guilds)}, Threads restored: {len(rows)}")
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

@bot.tree.command(name="setup", description="Auto-configure server for onboarding (admin only)")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can use this." if get_guild_language(str(interaction.guild_id)) == "en" else "Только админы могут это использовать.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)
    guild = interaction.guild
    me = guild.me
    lang = get_guild_language(str(guild.id))

    if not me.guild_permissions.manage_roles:
        await interaction.followup.send("I need **Manage Roles** permission! 🥺" if lang == "en" else "Мне нужно право **Управлять ролями**! 🥺")
        return
    if not me.guild_permissions.manage_channels:
        await interaction.followup.send("I need **Manage Channels** permission! 🥺" if lang == "en" else "Мне нужно право **Управлять каналами**! 🥺")
        return

    msgs = []
    role_name = "Newcomer" if lang == "en" else "Новичок"
    channel_name = "onboarding" if lang == "en" else "знакомства"

    # 1. Create role
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        role = await guild.create_role(name=role_name, reason="Zing auto-setup")
        msgs.append(f"✅ Role **{role_name}** created" if lang == "en" else f"✅ Роль **{role_name}** создана")
    else:
        msgs.append(f"✅ Role **{role_name}** already exists" if lang == "en" else f"✅ Роль **{role_name}** уже существует")
    set_auto_role(str(guild.id), str(role.id))

    # 2. Create channel
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=False),
            me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, create_private_threads=True, send_messages_in_threads=True, manage_threads=True),
        }
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, reason="Zing auto-setup")
        msgs.append(f"✅ Channel **#{channel_name}** created" if lang == "en" else f"✅ Канал **#{channel_name}** создан")
    else:
        msgs.append(f"✅ Channel **#{channel_name}** already exists" if lang == "en" else f"✅ Канал **#{channel_name}** уже существует")
    set_onboard_channel(str(guild.id), str(channel.id))

    # 3. Language
    set_guild_language(str(guild.id), "ru")

    msg = "\n".join(msgs)
    msg += "\n\n" + (f"🎉 **Setup complete!** New members will get a private thread in **#{channel_name}**" if lang == "en" else f"🎉 **Настройка завершена!** Новые участники будут получать приватный тред в **#{channel_name}**")
    await interaction.followup.send(msg)

@bot.tree.command(name="setchannel", description="Set channel for onboarding threads (admin only)")
@app_commands.describe(channel="The channel where onboarding threads will be created")
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can use this." if get_guild_language(str(interaction.guild_id)) == "en" else "Только админы могут это использовать.", ephemeral=True)
        return
    set_onboard_channel(str(interaction.guild_id), str(channel.id))
    msg = f"Onboarding channel set to {channel.mention}! 🎉" if get_guild_language(str(interaction.guild_id)) == "en" else f"Канал онбординга установлен: {channel.mention}! 🎉"
    await interaction.response.send_message(msg, ephemeral=False)

@bot.tree.command(name="setrole", description="Auto-assign role to new members (admin only)")
@app_commands.describe(role="The role to assign when someone joins")
async def setrole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can use this." if get_guild_language(str(interaction.guild_id)) == "en" else "Только админы могут это использовать.", ephemeral=True)
        return
    set_auto_role(str(interaction.guild_id), str(role.id))
    msg = f"Auto-role set to {role.mention}! New members will get it on join 🎉" if get_guild_language(str(interaction.guild_id)) == "en" else f"Роль установлена: {role.mention}! Новые участники будут получать её при входе 🎉"
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

@bot.tree.command(name="sync", description="Force sync all commands (admin only)")
async def sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can use this." if get_guild_language(str(interaction.guild_id)) == "en" else "Только админы могут это использовать.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    bot.tree.copy_global_to(guild=discord.Object(id=interaction.guild_id))
    await bot.tree.sync(guild=discord.Object(id=interaction.guild_id))
    msg = "Commands synced! You may need to restart Discord (Ctrl+R) to see them." if get_guild_language(str(interaction.guild_id)) == "en" else "Команды синхронизированы! Может понадобиться перезапустить Discord (Ctrl+R)."
    await interaction.followup.send(msg)


