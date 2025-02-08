# ppsb>main
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router
from app.quests import quest_router, start_check_quest_timers
from app.review import review_router
from app.presets import preset_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(router)
dp.include_router(quest_router)
dp.include_router(review_router)
dp.include_router(preset_router)

# logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Главная функция
async def main():
    try:
        logger.info('= - = - = - = - = - Bot has been started! = - = - = - = - = -')
        logger.info("Starting polling...")
        await start_check_quest_timers(bot)  # Запуск проверки таймеров квестов
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await on_shutdown()

# Функция завершения работы бота
async def on_shutdown():
    logger.info("Stopping bot...")
    await bot.session.close()
    logger.info("= - = - = - = - = - Bot has been stopped! = - = - = - = - = -")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program was stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")