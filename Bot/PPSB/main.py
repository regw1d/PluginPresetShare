# main
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router 
from app.quest import quest_router
from app.contact import contact_router

bot = Bot(token=TOKEN)

dp = Dispatcher()
dp.include_router(router)
dp.include_router(quest_router)
dp.include_router(contact_router)

# logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info('= - = - = - = - = - Bot has been started! = - = - = - = - = -')
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await on_shutdown()
        
async def on_shutdown():
    logger.info("Stopping bot...")
    await bot.session.close()
    logger.info("= - = - = - = - = - Bot has been stopped! = - = - = - = - = -")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program was stoped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

# python 3.13.0 | aiogram 3.17.0 | last format day 25.01.2025 - 04:12 | PPSB - @PluginPresetsShareBot