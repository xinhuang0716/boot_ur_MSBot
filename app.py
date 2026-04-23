"""
App (Azure Bot Framework Entry Point)
Creates an aiohttp HTTP server that listens for Activities sent by Bot Service.
"""

import sys
import traceback
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
)
from botbuilder.schema import Activity, ActivityTypes

from bot import OllamaBot
from config import DefaultConfig

CONFIG = DefaultConfig()

# ---------- Adapter ----------

SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


async def on_error(context: TurnContext, error: Exception) -> None:
    """Global error handler: prints the error and notifies the user."""
    print(f"\n[on_turn_error] Unhandled exception: {error}", file=sys.stderr)
    traceback.print_exc()

    await context.send_activity("The bot encountered an internal error. Please try again later.")

    # Send a Trace Activity to Bot Emulator only, for debugging purposes
    if context.activity.channel_id == "emulator":
        await context.send_activity(
            Activity(
                label="TurnError",
                name="on_turn_error Trace",
                timestamp=datetime.now(timezone.utc),
                type=ActivityTypes.trace,
                value=str(error),
                value_type="https://www.botframework.com/schemas/error",
            )
        )


ADAPTER.on_turn_error = on_error

# ---------- State ----------

STORAGE = MemoryStorage()
CONVERSATION_STATE = ConversationState(STORAGE)

# ---------- Bot Instance ----------

BOT = OllamaBot(CONVERSATION_STATE)

# ---------- Route Handlers ----------


async def messages(req: web.Request) -> web.Response:
    """Receives an Activity and delegates processing to the Adapter (POST /api/messages)."""
    if "application/json" not in req.headers.get("Content-Type", ""):
        return web.Response(status=415, text="Unsupported Media Type")

    activity = Activity().deserialize(await req.json())
    auth_header = req.headers.get("Authorization", "")

    invoke_response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if invoke_response: return web.json_response(data=invoke_response.body, status=invoke_response.status)
    return web.Response(status=201)


async def health(req: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok"})


# ---------- Application Setup ----------

APP = web.Application()
APP.router.add_get("/health", health)
APP.router.add_post("/api/messages", messages)

# ---------- Entry Point ----------

if __name__ == "__main__":
    print("Bot started")
    print(f"  Bot URL      : http://localhost:{CONFIG.BOT_PORT}/api/messages")
    print(f"  Health URL   : http://localhost:{CONFIG.BOT_PORT}/health")
    print(f"  Ollama       : {CONFIG.OLLAMA_BASE_URL}")
    web.run_app(APP, host="localhost", port=CONFIG.BOT_PORT)
