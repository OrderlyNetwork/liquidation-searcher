from aiohttp import web

from liquidation_searcher.utils.log import logger

from .handlers.health import health_check


def web_app(port):
    app = web.Application()
    app.add_routes(
        [
            web.get("/health", health_check),
        ]
    )
    logger.info("listening on port: {}", port)
    return app


async def run_web(port):
    app = web_app(port)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
