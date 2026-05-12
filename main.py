import asyncio
import os
from aiohttp import web
from bot import run_bot, bot

async def health_check(request):
    return web.Response(text="Zing is alive 🤘")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health_check)
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server running on port {port}")

async def start_all():
    await start_web()
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    print("Starting Zing... 🤘")
    asyncio.run(start_all())
