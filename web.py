import os
import asyncio
from aiohttp import web
from config import PORT

async def handler(request):
    return web.Response(text="✅ Bot is running!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 Web server running on port {PORT}")
    while True:
        await asyncio.sleep(3600)

# Run web server when called from bot.py
if __name__ == "__main__":
    asyncio.run(start_web())
