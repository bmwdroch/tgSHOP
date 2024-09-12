import asyncio
import os
import sys
import configparser

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.utils.token import validate_token, TokenValidationError

from tgbot.data.config import get_admins, BOT_SCHEDULER
from tgbot.database.db_helper import create_dbx
from tgbot.database.db_settings import Settingsx
from tgbot.middlewares import register_all_middlwares
from tgbot.routers import register_all_routers
from tgbot.services.api_session import AsyncRequestSession
from tgbot.utils.misc.bot_commands import set_commands
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc_functions import check_bot_username, startup_notify, autosettings_unix

def update_config(token: str, admin_id: str):
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    if 'settings' not in config:
        config['settings'] = {}
    
    config['settings']['token'] = token
    config['settings']['admin_id'] = admin_id
    
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

def get_console_input():
    while True:
        token = input("Введите токен бота: ").strip()
        try:
            validate_token(token)
            break
        except TokenValidationError:
            print("Неверный формат токена. Попробуйте еще раз.")
    
    admin_id = input("Введите ID администратора: ").strip()
    return token, admin_id

def get_bot_token():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    while True:
        if 'settings' in config and 'token' in config['settings']:
            token = config['settings']['token']
            try:
                validate_token(token)
                return token
            except TokenValidationError:
                print("Токен в файле настроек недействителен.")
        
        print("Токен бота не найден или недействителен. Пожалуйста, введите новый токен.")
        token, admin_id = get_console_input()
        update_config(token, admin_id)
        
        # Перезагрузка конфигурации после обновления
        config.read('settings.ini')

async def main():
    bot_token = get_bot_token()
    bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    arSession = AsyncRequestSession()

    BOT_SCHEDULER.start()

    register_all_middlwares(dp)
    register_all_routers(dp)

    create_dbx()

    settings = Settingsx.get()
    if settings is None:
        print("Настройки не найдены. Добавляем начальные настройки.")
        Settingsx.add(bot_token, get_admins()[0] if get_admins() else "")

    try:
        await autosettings_unix()
        await set_commands(bot)
        await check_bot_username(bot)
        await startup_notify(bot, arSession)

        bot_logger.warning("BOT WAS STARTED")
        print(f"~~~~~ Bot was started - @{(await bot.get_me()).username} ~~~~~")

        if len(get_admins()) == 0:
            print("***** ENTER ADMIN ID IN settings.ini *****")

        await bot.delete_webhook()
        await bot.get_updates(offset=-1)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), arSession=arSession)
    finally:
        await arSession.close()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        bot_logger.warning("Bot was stopped")
    finally:
        if sys.platform.startswith("win"):
            os.system("cls")
        else:
            os.system("clear")