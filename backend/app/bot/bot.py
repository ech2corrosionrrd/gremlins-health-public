import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault
from app.core.config import settings
from app.bot.handlers import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot):
    """Register bot commands in Telegram UI menu for Ukrainian and English."""
    commands_uk = [
        BotCommand(command="start", description="🚀 Запустити Gremlins Health"),
        BotCommand(command="help", description="📖 Повна довідка та інструкція"),
        BotCommand(command="gremlin", description="🐾 Мій Гремлін та догляд"),
        BotCommand(command="map", description="🏔️ Карта трейлів та вершини"),
        BotCommand(command="camera", description="📸 Захищена камера та cNFT"),
        BotCommand(command="raid", description="⚔️ Кланові рейд-боси"),
        BotCommand(command="security", description="🛡️ Античит та приватність"),
        BotCommand(command="wallet", description="💎 Solana гаманець та $GRLN"),
    ]

    commands_en = [
        BotCommand(command="start", description="🚀 Launch Gremlins Health"),
        BotCommand(command="help", description="📖 Full Guide & Documentation"),
        BotCommand(command="gremlin", description="🐾 Gremlin companion & care"),
        BotCommand(command="map", description="🏔️ Trail matrix & summits"),
        BotCommand(command="camera", description="📸 Verified camera & cNFT"),
        BotCommand(command="raid", description="⚔️ Clan raid bosses"),
        BotCommand(command="security", description="🛡️ Anticheat & privacy"),
        BotCommand(command="wallet", description="💎 Solana wallet & $GRLN"),
    ]

    try:
        await bot.set_my_commands(commands_uk, scope=BotCommandScopeDefault(), language_code="uk")
        await bot.set_my_commands(commands_en, scope=BotCommandScopeDefault())
        logger.info("✅ Bot commands registered successfully in Telegram UI menu.")
    except Exception as e:
        logger.warning(f"Could not register bot commands in Telegram UI: {e}")


async def start_bot():
    bot_token = settings.TELEGRAM_BOT_TOKEN
    web_app_url = settings.TELEGRAM_WEBAPP_URL

    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.warning("TELEGRAM_BOT_TOKEN is not set.")
        return

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Pass web_app_url to all handlers
    dp["web_app_url"] = web_app_url

    bot_info = await bot.get_me()
    logger.info(f"✅ Bot connected successfully: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"🚀 Gremlins Health TMA WebApp URL set to: {web_app_url}")

    await setup_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
