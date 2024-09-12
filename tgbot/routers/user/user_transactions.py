# - *- coding: utf- 8 - *-
from typing import Union

from aiogram import Router, Bot, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from tgbot.database.db_payments import Paymentsx
from tgbot.database.db_refill import Refillx
from tgbot.database.db_users import Userx
from tgbot.keyboards.inline_user import refill_bill_finl, refill_method_finl
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.services.api_cryptobot import CryptoBotAPI
from tgbot.utils.const_functions import is_number, to_number, gen_id
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc_functions import send_admins

min_refill_usd = 1  # Минимальная сумма пополнения в долларах для CryptoBot
min_refill_rub = 100  # Минимальная сумма пополнения в рублях для других способов

router = Router(name=__name__)

# Выбор способа пополнения
@router.callback_query(F.data == "user_refill")
async def refill_method(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    get_payment = Paymentsx.get()

    if get_payment.way_yoomoney == "False" and get_payment.way_crypto_bot == "False":
        return await call.answer("❗️ Пополнения временно недоступны", True)

    await call.message.edit_text(
        "<b>💰 Выберите способ пополнения</b>",
        reply_markup=refill_method_finl(),
    )

# Выбор способа пополнения
@router.callback_query(F.data.startswith("user_refill_method:"))
async def refill_method_select(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    pay_method = call.data.split(":")[1]

    await state.update_data(here_pay_method=pay_method)

    if pay_method == "CryptoBot":
        await call.message.edit_text("<b>💰 Введите сумму пополнения в долларах (USDT)</b>")
    else:
        await call.message.edit_text("<b>💰 Введите сумму пополнения в рублях</b>")

    await state.set_state("here_refill_amount")

# Принятие суммы для пополнения средств
@router.message(F.text, StateFilter("here_refill_amount"))
async def refill_amount_get(message: Message, bot: Bot, state: FSM, arSession: ARS):
    pay_method = (await state.get_data())['here_pay_method']
    
    if not is_number(message.text):
        return await message.answer(
            "<b>❌ Данные были введены неверно.</b>\n"
            "💰 Введите сумму для пополнения средств",
        )

    amount = to_number(message.text)

    if pay_method == "CryptoBot":
        if amount < min_refill_usd or amount > 1000:
            return await message.answer(
                f"<b>❌ Неверная сумма пополнения</b>\n"
                f"❗️ Cумма должна быть от <code>{min_refill_usd}$</code> до <code>1000$</code>\n"
                f"💰 Введите сумму для пополнения средств в долларах (USDT)",
            )
    else:
        if amount < min_refill_rub or amount > 100_000:
            return await message.answer(
                f"<b>❌ Неверная сумма пополнения</b>\n"
                f"❗️ Cумма должна быть от <code>{min_refill_rub}₽</code> до <code>100 000₽</code>\n"
                f"💰 Введите сумму для пополнения средств в рублях",
            )

    cache_message = await message.answer("<b>♻️ Подождите, платёж генерируется...</b>")

    await state.clear()

    if pay_method == "Yoomoney":
        bill_message, bill_link, bill_receipt = await (
            YoomoneyAPI(
                bot=bot,
                arSession=arSession,
            )
        ).bill(amount)
    elif pay_method == "CryptoBot":
        crypto_bot_api = CryptoBotAPI(bot=bot, arSession=arSession)
        status, invoice = await crypto_bot_api.create_invoice(amount)
        if status:
            bill_message = f"<b>💰 Счет на оплату {amount}$ USDT создан</b>"
            bill_link = invoice['pay_url']
            bill_receipt = invoice['invoice_id']
        else:
            return await message.answer("<b>❌ Ошибка создания счета. Попробуйте позже.</b>")
    else:
        return await message.answer("<b>❌ Ошибка выбора способа оплаты</b>")

    if bill_message:
        await cache_message.edit_text(
            bill_message,
            reply_markup=refill_bill_finl(bill_link, bill_receipt, pay_method),
        )

# Проверка оплаты - CryptoBot
@router.callback_query(F.data.startswith('Pay:CryptoBot'))
async def refill_check_cryptobot(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS):
    pay_way = call.data.split(":")[1]
    pay_receipt = call.data.split(":")[2]

    crypto_bot_api = CryptoBotAPI(bot=bot, arSession=arSession)
    status, invoice = await crypto_bot_api.get_invoice(int(pay_receipt))

    if status and invoice['status'] == 'paid':
        get_refill = Refillx.get(refill_receipt=pay_receipt)

        if get_refill is None:
            # Получаем курс USDT к RUB
            rates_status, rates = await crypto_bot_api.get_exchange_rates()
            if not rates_status:
                return await call.answer("❗ Не удалось получить курс валют. Попробуйте позже.", True)

            usdt_rate = next((rate['rate'] for rate in rates if rate['source'] == 'USDT' and rate['target'] == 'RUB'), None)
            if not usdt_rate:
                return await call.answer("❗ Не удалось получить курс USDT. Попробуйте позже.", True)

            # Конвертируем USDT в рубли
            amount_rub = float(invoice['amount']) * float(usdt_rate)

            await refill_success(
                bot=bot,
                call=call,
                pay_way=pay_way,
                pay_amount=amount_rub,
                pay_receipt=pay_receipt,
                pay_comment=invoice['payload'],
            )
        else:
            await call.answer("❗ Ваше пополнение уже зачислено.", True, cache_time=60)
    elif status and invoice['status'] == 'active':
        await call.answer("❗ Счет не оплачен. Попробуйте еще раз после оплаты.", True, cache_time=5)
    else:
        await call.answer("❗ Не удалось проверить платеж. Попробуйте позже.", True, cache_time=5)

################################################################################
#################################### ПРОЧЕЕ ####################################
# Зачисление средств
async def refill_success(
        bot: Bot,
        call: CallbackQuery,
        pay_way: str,
        pay_amount: float,
        pay_receipt: Union[str, int] = None,
        pay_comment: str = None,
):
    get_user = Userx.get(user_id=call.from_user.id)

    if pay_receipt is None:
        pay_receipt = gen_id()
    if pay_comment is None:
        pay_comment = ""

    Refillx.add(
        user_id=get_user.user_id,
        refill_comment=pay_comment,
        refill_amount=pay_amount,
        refill_receipt=pay_receipt,
        refill_method=pay_way,
    )

    Userx.update(
        call.from_user.id,
        user_balance=round(get_user.user_balance + pay_amount, 2),
        user_refill=round(get_user.user_refill + pay_amount, 2),
    )

    await call.message.edit_text(
        f"<b>💰 Вы пополнили баланс на сумму <code>{pay_amount}₽</code>. Удачи ❤️\n"
        f"🧾 Чек: <code>#{pay_receipt}</code></b>",
    )

    await send_admins(
        bot,
        f"👤 Пользователь: <b>@{get_user.user_login}</b> | <a href='tg://user?id={get_user.user_id}'>{get_user.user_name}</a> | <code>{get_user.user_id}</code>\n"
        f"💰 Сумма пополнения: <code>{pay_amount}₽</code>\n"
        f"🧾 Чек: <code>#{pay_receipt}</code>"
    )