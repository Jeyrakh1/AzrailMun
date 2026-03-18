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
# ──────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    domain = State()
    amount = State()
    nick = State()
    wallet = State()


def is_trc20(addr: str) -> bool:
    return addr.startswith('T') and len(addr) == 34


def short_id(n=4):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def normalize_domain(domain: str) -> str:
    """Добавляет https:// если протокол не указан, убирает слэш в конце."""
    d = domain.strip().rstrip('/')
    if not d.startswith(('http://', 'https://')):
        d = 'https://' + d
    return d.rstrip('/')


def build_link(domain: str, amount: float, nick: str, wallet: str) -> str:
    base = normalize_domain(domain)
    amt = str(int(amount)) if amount == int(amount) else str(amount)
    raw = f"{amt}|{nick}|{wallet}|{short_id(4)}"
    token = base64.urlsafe_b64encode(raw.encode()).decode().rstrip('=')
    return f"{base}/#t={token}"


def amt_str(amount: float) -> str:
    return str(int(amount)) if amount == int(amount) else str(amount)


# ─── /start ───────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Cryptomus Payout Bot</b>\n\n"
        "Команда /gen — создание ссылки на счёт.\n\n"
        "Вам понадобятся: домен, сумма, ник и кошелёк TRC-20.",
        parse_mode="HTML"
    )


# ─── /gen ─────────────────────────────────────────────────────
@dp.message(Command("gen"))
async def cmd_gen(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.domain)
    await message.answer("🌐 Введите ваш домен:", parse_mode="HTML")


# ─── Шаг 1: домен ─────────────────────────────────────────────
@dp.message(StateFilter(Form.domain))
async def step_domain(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith('/'):
        return
    domain = message.text.strip()
    if not domain:
        await message.answer("❌ Введите домен. Например: <code>invoice-recieve.pro</code>", parse_mode="HTML")
        return
    await state.update_data(domain=domain)
    await state.set_state(Form.amount)
    await message.answer(
        f"🌐 Домен: <b>{normalize_domain(domain)}</b>\n\n"
        f"💵 Введите сумму:",
        parse_mode="HTML"
    )


# ─── Шаг 2: сумма ─────────────────────────────────────────────
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
    await state.set_state(Form.nick)
    await message.answer(
        f"💰 Сумма: <b>{amt_str(amount)}.00 USDT</b>\n\n"
        f"Введите ник:\n"
        f"<i>Пример:</i> <code>MANAGER CP COMPANY</code>",
        parse_mode="HTML"
    )


# ─── Шаг 3: ник ────────────────────────────────────────────────
@dp.message(StateFilter(Form.nick))
async def step_nick(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith('/'):
        return
    nick = message.text.strip()
    if not nick:
        await message.answer("❌ Введите ник.")
        return
    await state.update_data(nick=nick)
    await state.set_state(Form.wallet)
    await message.answer(
        f"👤 Ник: <b>{nick.upper()}</b>\n\n"
        f"Введите TRC-20 адрес кошелька получателя:\n"
        f"<i>Пример:</i> <code>TUeapnPqxQBEuFjuJXCMLzNSywwCuBmQeE</code>",
        parse_mode="HTML"
    )


# ─── Шаг 4: кошелёк ───────────────────────────────────────────
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

    data = await state.get_data()
    await state.clear()

    domain = data["domain"]
    amount = data["amount"]
    nick = data["nick"]
    link = build_link(domain, amount, nick, wallet)
    wallet_short = wallet[:9] + '...' + wallet[-6:]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👆 Нажмите здесь, чтобы открыть счёт", url=link)]
    ])

    await message.answer(
        f"✅ <b>Счет сформирован</b>\n\n"
        f"🌐 Домен: <code>{normalize_domain(domain)}</code>\n"
        f"💰 Сумма: <code>{amt_str(amount)}.00 USDT</code>\n"
        f"👤 Ник: <code>{nick.upper()}</code>\n"
        f"👛 Кошелёк: <code>{wallet_short}</code>\n\n"
        f"🔗 Ссылка:\n<code>{link}</code>",
        parse_mode="HTML",
        reply_markup=kb
    )


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
