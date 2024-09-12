import json
from typing import Union

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientConnectorCertificateError

from tgbot.database.db_payments import Paymentsx
from tgbot.utils.const_functions import ded, send_errors, gen_id
from tgbot.utils.misc.bot_models import ARS
from tgbot.utils.misc_functions import send_admins


class CryptoBotAPI:
    def __init__(
            self,
            bot: Bot,
            arSession: ARS,
            update: Union[Message, CallbackQuery] = None,
            token: str = None,
            skipping_error: bool = False,
    ):
        if token is not None:
            self.token = token
        else:
            get_payment = Paymentsx.get()
            self.token = get_payment.crypto_bot_token

        self.base_url = 'https://pay.crypt.bot/api/'
        self.headers = {
            'Crypto-Pay-API-Token': self.token,
            'Content-Type': 'application/json',
        }

        self.bot = bot
        self.bot_username = None  
        self.arSession = arSession
        self.update = update
        self.skipping_error = skipping_error

    async def error_wallet_admin(self, error_code: str = "Unknown"):
        if not self.skipping_error:
            await send_admins(
                self.bot,
                f"<b>🤖 CryptoBot недоступен. Как можно быстрее замените токен</b>\n"
                f"❗️ Error: <code>{error_code}</code>"
            )

    async def error_wallet_user(self):
        if self.update is not None and not self.skipping_error:
            if isinstance(self.update, Message):
                await self.update.edit_text(
                    "<b>❗ Извиняемся за доставленные неудобства, оплата временно недоступна.\n"
                    "⌛ Попробуйте чуть позже.</b>"
                )
            elif isinstance(self.update, CallbackQuery):
                await self.update.answer(
                    "❗ Извиняемся за доставленные неудобства, оплата временно недоступна.\n"
                    "⌛ Попробуйте чуть позже."
                )
            else:
                await send_errors(self.bot, 4938221)

    async def get_bot_username(self):
        if self.bot_username is None:
            bot_info = await self.bot.get_me()
            self.bot_username = bot_info.username
        return self.bot_username

    async def create_invoice(self, amount: float, description: str = None) -> tuple[bool, Union[str, dict]]:
        method = 'createInvoice'
        bot_username = await self.get_bot_username()
        payload = {
            'asset': 'USDT',
            'amount': str(amount),
            'description': description or '',
            'hidden_message': '',
            'paid_btn_name': 'callback',
            'paid_btn_url': f"https://t.me/{bot_username}" if bot_username else "",
            'payload': str(gen_id()),
            'allow_comments': False,
            'allow_anonymous': False,
            'expires_in': 1800
        }

        try:
            status, response = await self._request(method, payload)
            if status:
                return True, response
            else:
                error_message = f"Failed to create invoice: {response}"
                await self.error_wallet_admin(error_message, payload)
                return False, error_message
        except Exception as e:
            error_message = f"Exception while creating invoice: {str(e)}"
            await self.error_wallet_admin(error_message, payload)
            return False, error_message

    async def error_wallet_admin(self, error_code: str = "Unknown", payload: dict = None):
        if not self.skipping_error:
            message = f"<b>🤖 CryptoBot недоступен. Как можно быстрее замените токен</b>\n" \
                      f"❗️ Error: <code>{error_code}</code>"
            if payload:
                message += f"\n\n<b>Отправленный запрос:</b>\n<code>{json.dumps(payload, indent=2)}</code>"
            await send_admins(self.bot, message)

    async def get_invoice(self, invoice_id: int) -> tuple[bool, Union[str, dict]]:
        method = 'getInvoices'
        payload = {
            'invoice_ids': str(invoice_id),
        }

        status, response = await self._request(method, payload)
        if status and response.get('items'):
            return True, response['items'][0]
        else:
            error_message = f"Failed to get invoice: {response}"
            await self.error_wallet_admin(error_message)
            return False, error_message

    async def get_exchange_rates(self) -> tuple[bool, Union[str, list]]:
        method = 'getExchangeRates'
        
        status, response = await self._request(method)
        if status:
            return True, response
        else:
            error_message = f"Failed to get exchange rates: {response}"
            await self.error_wallet_admin(error_message)
            return False, error_message

    async def _request(self, method: str, data: dict = None) -> tuple[bool, Union[str, dict]]:
        session = await self.arSession.get_session()
        url = f"{self.base_url}{method}"

        try:
            async with session.post(url, headers=self.headers, json=data) as response:
                response_data = await response.json()

                if response.status == 200 and response_data.get('ok'):
                    return True, response_data.get('result', {})
                else:
                    error_message = f"{response.status} - {str(response_data)}"
                    await self.error_wallet_user()
                    await self.error_wallet_admin(error_message)
                    return False, error_message
        except ClientConnectorCertificateError:
            error_message = "CERTIFICATE_VERIFY_FAILED"
            await self.error_wallet_user()
            await self.error_wallet_admin(error_message)
            return False, error_message
        except Exception as ex:
            error_message = str(ex)
            await self.error_wallet_user()
            await self.error_wallet_admin(error_message)
            return False, error_message

    async def check_token(self) -> tuple[bool, str]:
        """Проверка валидности токена"""
        method = 'getMe'
        status, response = await self._request(method)
        if status:
            return True, "Токен CryptoBot валиден"
        else:
            return False, f"Токен CryptoBot невалиден: {response}"