from aiohttp import web


async def health_check(_request):
    return web.Response(text="OK")
