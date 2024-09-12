# - *- coding: utf- 8 - *-
from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from tgbot.services.api_cryptobot import CryptoBotAPI
from tgbot.database.db_payments import Paymentsx
from tgbot.keyboards.inline_admin import payment_method_finl, payment_yoomoney_finl, close_finl, payment_cryptobot_finl
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.services.api_cryptobot import CryptoBotAPI
from tgbot.utils.const_functions import ded
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


################################################################################
############################ ВЫБОР СПОСОБА ПОПОЛНЕНИЯ ##########################
# Открытие способов пополнения
@router.message(F.text == "🖲 Способы пополнений")
async def payment_methods(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🖲 Выберите способы пополнений</b>",
        reply_markup=payment_method_finl(),
    )


# Включение/выключение самих способов пополнения
@router.callback_query(F.data.startswith("payment_method:"))
async def payment_methods_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    way_pay = call.data.split(":")[1]
    way_status = call.data.split(":")[2]

    get_payment = Paymentsx.get()

    if way_pay == "Yoomoney":
        if way_status == "True" and get_payment.yoomoney_token == "None":
            return await call.answer("❗ Добавьте ЮMoney кошелёк перед включением Способов пополнений", True)

        Paymentsx.update(way_yoomoney=way_status)
    elif way_pay == "CryptoBot":
        if way_status == "True" and get_payment.crypto_bot_token == "None":
            return await call.answer("❗ Добавьте токен CryptoBot перед включением Способов пополнений", True)

        Paymentsx.update(way_crypto_bot=way_status)

    await call.message.edit_text(
        "<b>🖲 Выберите способы пополнений</b>",
        reply_markup=payment_method_finl(),
    )


# Открытие ЮMoney
@router.message(F.text == "🔮 ЮMoney")
async def payment_yoomoney_open(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🔮 Управление - ЮMoney</b>",
        reply_markup=payment_yoomoney_finl(),
    )


# Открытие CryptoBot
@router.message(F.text == "🤖 CryptoBot")
async def payment_cryptobot_open(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    await message.answer(
        "<b>🤖 Управление - CryptoBot</b>",
        reply_markup=payment_cryptobot_finl(),
    )


################################################################################
#################################### CryptoBot #################################
# Изменение токена CryptoBot
@router.callback_query(F.data == "payment_cryptobot_edit")
async def payment_cryptobot_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    await state.set_state("here_cryptobot_token")
    await call.message.edit_text(
        "<b>🤖 Введите токен CryptoBot</b>\n"
        "❕ Получить можно в @CryptoBot, написав /wallet, затем Crypto Pay API"
    )


# Проверка подключения CryptoBot
@router.callback_query(F.data == "payment_cryptobot_check")
async def payment_cryptobot_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    try:
        cache_message = await call.message.answer("<b>🤖 Проверка подключения CryptoBot...</b>")
        await call.answer()

        crypto_bot_api = CryptoBotAPI(bot=bot, arSession=arSession)
        status, response = await crypto_bot_api.get_exchange_rates()

        if status:
            await cache_message.edit_text(
                "<b>✅ CryptoBot подключен!</b>\n"
                "❕ Проверка прошла успешно"
            )
        else:
            await cache_message.edit_text(
                "<b>❌ CryptoBot не подключен...</b>\n"
                f"<code>Ошибка: {response}</code>"
            )
    except Exception as ex:
        await cache_message.edit_text(
            "<b>❌ CryptoBot не подключен...</b>\n"
            f"<code>Ошибка: {ex}</code>"
        )
        
# Проверка токена CryptoBot
@router.callback_query(F.data == "payment_cryptobot_check")
async def payment_cryptobot_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    try:
        cache_message = await call.message.answer("<b>🤖 Проверка подключения CryptoBot...</b>")
        await call.answer()

        crypto_bot_api = CryptoBotAPI(bot=bot, arSession=arSession)
        status, response = await crypto_bot_api.check_token()

        if status:
            await cache_message.edit_text(
                "<b>✅ CryptoBot подключен!</b>\n"
                "❕ Проверка прошла успешно"
            )
        else:
            await cache_message.edit_text(
                "<b>❌ CryptoBot не подключен...</b>\n"
                f"<code>Ошибка: {response}</code>"
            )
    except Exception as ex:
        await cache_message.edit_text(
            "<b>❌ CryptoBot не подключен...</b>\n"
            f"<code>Ошибка: {ex}</code>"
        )

################################ ПРИНЯТИЕ CRYPTOBOT #############################
# Принятие токена CryptoBot
@router.message(StateFilter("here_cryptobot_token"))
async def payment_cryptobot_edit_token(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    cache_message = await message.answer("<b>🤖 Проверка введённых CryptoBot данных... 🔄</b>")

    crypto_bot_token = message.text

    try:
        crypto_bot_api = CryptoBotAPI(
            bot=bot,
            arSession=arSession,
            token=crypto_bot_token
        )
        status, response = await crypto_bot_api.get_exchange_rates()

        if status:
            Paymentsx.update(crypto_bot_token=crypto_bot_token)
            await cache_message.edit_text(
                "<b>🤖 Токен CryptoBot был успешно изменён ✅</b>"
            )
        else:
            await cache_message.edit_text(
                "<b>❌ Не удалось подключиться к CryptoBot</b>\n"
                f"<code>Ошибка: {response}</code>"
            )
    except Exception as ex:
        await cache_message.edit_text(
            "<b>❌ Не удалось подключиться к CryptoBot</b>\n"
            f"<code>Ошибка: {ex}</code>"
        )

    await message.answer(
        "<b>🤖 Управление - CryptoBot</b>",
        reply_markup=payment_cryptobot_finl(),
    )

################################################################################
#################################### ЮMoney ####################################
# Баланс ЮMoney
@router.callback_query(F.data == "payment_yoomoney_balance")
async def payment_yoomoney_balance(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await YoomoneyAPI(
        bot=bot,
        arSession=arSession,
        update=call,
        skipping_error=True,
    ).balance()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Проверка ЮMoney
@router.callback_query(F.data == "payment_yoomoney_check")
async def payment_yoomoney_check(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await YoomoneyAPI(
        bot=bot,
        arSession=arSession,
        update=call,
        skipping_error=True,
    ).check()

    await call.message.answer(
        response,
        reply_markup=close_finl(),
    )


# Изменение ЮMoney
@router.callback_query(F.data == "payment_yoomoney_edit")
async def payment_yoomoney_edit(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    response = await YoomoneyAPI(
        bot=bot,
        arSession=arSession
    ).authorization_get()

    await state.set_state("here_yoomoney_token")
    await call.message.edit_text(
        ded(f"""
            <b>🔮 Для изменения ЮMoney кошелька</b>
            ▪️ Перейдите по ссылке ниже и авторизуйте приложение.
            ▪️ После авторизации, отправьте ссылку или код из адресной строки.
            🔗 {response}
        """),
        disable_web_page_preview=True,
    )


################################ ПРИНЯТИЕ ЮMONEY ###############################
# Принятие токена ЮMoney
@router.message(StateFilter("here_yoomoney_token"))
async def payment_yoomoney_edit_token(message: Message, bot: Bot, state: FSM, arSession: ARS):
    await state.clear()

    cache_message = await message.answer("<b>🔮 Проверка введённых ЮMoney данных... 🔄</b>")

    get_code = message.text

    try:
        get_code = get_code[get_code.index("code=") + 5:].replace(" ", "")
    except:
        ...

    status, token, response = await YoomoneyAPI(
        bot=bot,
        arSession=arSession,
    ).authorization_enter(str(get_code))

    if status:
        Paymentsx.update(yoomoney_token=token)

    await cache_message.edit_text(response)

    await message.answer(
        "<b>🔮 Управление - ЮMoney</b>",
        reply_markup=payment_yoomoney_finl(),
    )
