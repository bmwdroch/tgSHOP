# - *- coding: utf- 8 - *-
import sqlite3

from pydantic import BaseModel

from tgbot.data.config import PATH_DATABASE
from tgbot.database.db_helper import dict_factory, update_format
from tgbot.utils.const_functions import get_unix

# Модель таблицы
class SettingsModel(BaseModel):
    status_work: str
    status_refill: str
    status_buy: str
    misc_faq: str
    misc_support: str
    misc_bot: str
    misc_item_hide: str
    misc_profit_day: int
    misc_profit_week: int
    misc_profit_month: int

# Работа с настройками
class Settingsx:
    storage_name = "storage_settings"

    # Получение записи
    @staticmethod
    def get() -> SettingsModel:
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"SELECT * FROM {Settingsx.storage_name}"
            result = con.execute(sql).fetchone()
            if result:
                return SettingsModel(**result)
            return None

    # Добавление записи
    @staticmethod
    def add(token: str, admin_id: str):
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"""INSERT INTO {Settingsx.storage_name} (
                status_work, status_refill, status_buy, misc_faq, misc_support,
                misc_bot, misc_item_hide, misc_profit_day, misc_profit_week, misc_profit_month
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            con.execute(sql, [
                'True', 'True', 'True', 'None', 'None',
                token, 'False', get_unix(), get_unix(), get_unix()
            ])

    # Редактирование записи
    @staticmethod
    def update(**kwargs):
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"UPDATE {Settingsx.storage_name} SET"
            sql, parameters = update_format(sql, kwargs)
            con.execute(sql, parameters)