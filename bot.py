import discord
from discord import app_commands
from discord.ext import commands
from database import init_db, increment_roast, is_banned, is_premium_guild
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

    # Only respond when mentioned
    if bot.user in message.mentions:
        content = message.content.lower()

        if is_banned(str(message.guild.id), str(message.author.id)):
            await message.reply("You've been muted. Try again next lifetime, champ.")
            return

        if "roast" in content:
            increment_roast(str(message.author.id))
            roast = get_roast(message.author.display_name)
            await message.reply(roast)

        elif "skill" in content:
            rating = get_skill_rating(message.author.display_name)
            await message.reply(rating)

        elif "rate" in content:
            if not is_premium_guild(str(message.guild.id)):
                await message.reply("Rate? Only premium servers get judged. Tell your admin to buy a clue.")
                return
            text = content.replace("rate", "").strip()
            if text and text != f"<@{bot.user.id}>":
                result = chat_response(message.author.display_name, f"Rate this: {text}")
            else:
                result = chat_response(message.author.display_name, f"Rate {message.author.display_name}")
            await message.reply(result)

        elif "joke" in content:
            joke = get_joke()
            await message.reply(joke)

        elif "help" in content:
            await message.reply(embed=get_help_embed())

        else:
            reply = chat_response(message.author.display_name, content)
            await message.reply(reply)

    await bot.process_commands(message)

def get_help_embed():
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

def run_bot():
    pass
