from aiohttp import web
from config import PORT

async def handle(request):
    return web.Response(text="Render Rename Bot Running")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
