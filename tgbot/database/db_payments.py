import sqlite3

from pydantic import BaseModel

from tgbot.data.config import PATH_DATABASE
from tgbot.database.db_helper import dict_factory, update_format


# Модель таблицы
class PaymentModel(BaseModel):
    yoomoney_token: str
    way_yoomoney: str
    crypto_bot_token: str
    way_crypto_bot: str


# Работа с платежными системами
class Paymentsx:
    storage_name = "storage_payment"

    # Получение записи
    @staticmethod
    def get() -> PaymentModel:
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"SELECT * FROM {Paymentsx.storage_name}"

            return PaymentModel(**con.execute(sql).fetchone())

    # Редактирование записи
    @staticmethod
    def update(**kwargs):
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"UPDATE {Paymentsx.storage_name} SET"
            sql, parameters = update_format(sql, kwargs)

            con.execute(sql, parameters)

    # Добавление записи при первом запуске
    @staticmethod
    def add():
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"""INSERT INTO {Paymentsx.storage_name} (
                yoomoney_token, way_yoomoney, 
                crypto_bot_token, way_crypto_bot
            ) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            parameters = ('None', 'None', 'None', 'False', 'False', 'None', 'False')

            con.execute(sql, parameters)

    # Проверка наличия таблицы
    @staticmethod
    def create_table():
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"""
            CREATE TABLE IF NOT EXISTS {Paymentsx.storage_name} (
                yoomoney_token TEXT,
                way_yoomoney TEXT,
                crypto_bot_token TEXT,
                way_crypto_bot TEXT
            )"""

            con.execute(sql)

    # Проверка наличия записи
    @staticmethod
    def check_record():
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"SELECT * FROM {Paymentsx.storage_name}"

            result = con.execute(sql).fetchone()
            if result is None:
                Paymentsx.add()