import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN, DB_NAME
from app.handlers import router as handlers_router
from app.quests import quest_router
from app.review import review_router
from app.presets import preset_router
from database import init_db, close_db_connection, get_db

START_MESSAGE = "= - = - = - = - = - Bot has been started! = - = - = - = - = -"
STOP_MESSAGE = "= - = - = - = - = - Bot has been stopped! = - = - = - = - = -"

bot: Bot = Bot(token=TOKEN)
dp: Dispatcher = Dispatcher()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main() -> None:
    try:
        await init_db()
        db_instance = get_db()
        if db_instance is None:
            logger.error(f"Failed to initialize database '{DB_NAME}'. Exiting.")
            return
        
        dp.include_router(handlers_router)
        dp.include_router(quest_router)
        dp.include_router(review_router)
        dp.include_router(preset_router)
        
        logger.info("All routers registered.")
        logger.info(START_MESSAGE)
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during startup or polling: {e}")
    finally:
        await on_shutdown()

async def on_shutdown() -> None:
    logger.info("Stopping bot...")
    try:
        await bot.session.close()
        await close_db_connection()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info(STOP_MESSAGE)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program was stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")