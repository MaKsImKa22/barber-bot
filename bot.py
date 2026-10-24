import asyncio
import logging
import re
from datetime import date, datetime, timedelta
from html import escape

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
import db

router = Router()

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
BTN_BOOK = "📅 Записатися"
BTN_MY = "📋 Мої записи"
BTN_ABORT = "✖️ Скасувати"


class Booking(StatesGroup):
    service = State()
    day = State()
    time = State()
    phone = State()
    confirm = State()


class ServiceCb(CallbackData, prefix="svc"):
    idx: int


class DayCb(CallbackData, prefix="day"):
    day: str


class TimeCb(CallbackData, prefix="time"):
    hour: int


class CancelCb(CallbackData, prefix="cancel"):
    booking_id: int


# ---------- допоміжне ----------

def fmt_day(day_iso):
    d = date.fromisoformat(day_iso)
    return f"{WEEKDAYS[d.weekday()]} {d:%d.%m}"


def fmt_hour(hour):
    return f"{hour:02d}:00"


def free_hours(day_iso):
    busy = db.busy_hours(day_iso)
    hours = [h for h in range(config.WORK_START, config.WORK_END) if h not in busy]
    if day_iso == date.today().isoformat():
        hours = [h for h in hours if h > datetime.now().hour]
    return hours


def available_days():
    today = date.today()
    days = []
    for i in range(config.DAYS_AHEAD):
        d = today + timedelta(days=i)
        if d.weekday() not in config.DAYS_OFF and free_hours(d.isoformat()):
            days.append(d.isoformat())
    return days


def booking_text(service, day, hour):
    price = config.SERVICES.get(service, "?")
    return (
        f"💈 <b>{escape(service)}</b> — {price} грн\n"
        f"📅 {fmt_day(day)} о {fmt_hour(hour)}"
    )


async def notify_admin(bot, text):
    if not config.ADMIN_ID:
        return
    try:
        await bot.send_message(config.ADMIN_ID, text)
    except Exception:
        logging.exception("Не вдалося надіслати повідомлення адміну")


# ---------- клавіатури ----------

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BOOK), KeyboardButton(text=BTN_MY)]],
        resize_keyboard=True,
    )


def abort_button():
    return InlineKeyboardButton(text=BTN_ABORT, callback_data="abort")


def services_kb():
    kb = InlineKeyboardBuilder()
    for i, (name, price) in enumerate(config.SERVICES.items()):
        kb.button(text=f"{name} — {price} грн", callback_data=ServiceCb(idx=i))
    kb.adjust(1)
    kb.row(abort_button())
    return kb.as_markup()


def days_kb(days):
    kb = InlineKeyboardBuilder()
    for d in days:
        kb.button(text=fmt_day(d), callback_data=DayCb(day=d))
    kb.adjust(3)
    kb.row(abort_button())
    return kb.as_markup()


def hours_kb(hours):
    kb = InlineKeyboardBuilder()
    for h in hours:
        kb.button(text=fmt_hour(h), callback_data=TimeCb(hour=h))
    kb.adjust(4)
    kb.row(InlineKeyboardButton(text="⬅️ Інший день", callback_data="back_days"))
    kb.row(abort_button())
    return kb.as_markup()


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Надіслати мій номер", request_contact=True)],
            [KeyboardButton(text=BTN_ABORT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Підтвердити", callback_data="confirm")
    kb.button(text=BTN_ABORT, callback_data="abort")
    kb.adjust(2)
    return kb.as_markup()


def my_bookings_view(user_id):
    rows = db.user_bookings(user_id, date.today().isoformat())
    if not rows:
        return "У тебе поки немає записів.", None
    lines = ["<b>Твої записи:</b>\n"]
    kb = InlineKeyboardBuilder()
    for row in rows:
        lines.append(booking_text(row["service"], row["day"], row["hour"]) + "\n")
        kb.button(
            text=f"❌ Скасувати {fmt_day(row['day'])} {fmt_hour(row['hour'])}",
            callback_data=CancelCb(booking_id=row["id"]),
        )
    kb.adjust(1)
    return "\n".join(lines), kb.as_markup()


# ---------- загальні команди ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привіт, {escape(message.from_user.first_name)}! 👋\n"
        f"Я бот для запису в {config.BUSINESS_NAME}.\n\n"
        "Обери дію в меню нижче.",
        reply_markup=main_menu(),
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Твій Telegram ID: <code>{message.from_user.id}</code>")


@router.message(F.text == BTN_ABORT)
async def text_abort(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Запис скасовано.", reply_markup=main_menu())


@router.callback_query(F.data == "abort")
async def cb_abort(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Запис скасовано.")
    await callback.answer()


# ---------- процес запису ----------

@router.message(F.text == BTN_BOOK)
async def book_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Booking.service)
    await message.answer("Обери послугу:", reply_markup=services_kb())


@router.callback_query(Booking.service, ServiceCb.filter())
async def choose_service(callback: CallbackQuery, callback_data: ServiceCb, state: FSMContext):
    names = list(config.SERVICES)
    if not 0 <= callback_data.idx < len(names):
        await callback.answer()
        return
    service = names[callback_data.idx]
    await state.update_data(service=service)

    days = available_days()
    if not days:
        await state.clear()
        await callback.message.edit_text("На найближчий тиждень вільних місць немає 😔")
        await callback.answer()
        return

    await state.set_state(Booking.day)
    await callback.message.edit_text(
        f"Послуга: <b>{escape(service)}</b>\n\nОбери день:",
        reply_markup=days_kb(days),
    )
    await callback.answer()


@router.callback_query(Booking.time, F.data == "back_days")
async def back_to_days(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Booking.day)
    await callback.message.edit_text(
        f"Послуга: <b>{escape(data['service'])}</b>\n\nОбери день:",
        reply_markup=days_kb(available_days()),
    )
    await callback.answer()


@router.callback_query(Booking.day, DayCb.filter())
async def choose_day(callback: CallbackQuery, callback_data: DayCb, state: FSMContext):
    hours = free_hours(callback_data.day)
    if not hours:
        await callback.answer("Цей день уже повністю зайнятий, обери інший", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=days_kb(available_days()))
        return

    await state.update_data(day=callback_data.day)
    await state.set_state(Booking.time)
    data = await state.get_data()
    await callback.message.edit_text(
        f"Послуга: <b>{escape(data['service'])}</b>\n"
        f"День: <b>{fmt_day(callback_data.day)}</b>\n\nОбери час:",
        reply_markup=hours_kb(hours),
    )
    await callback.answer()


@router.callback_query(Booking.time, TimeCb.filter())
async def choose_time(callback: CallbackQuery, callback_data: TimeCb, state: FSMContext):
    data = await state.get_data()
    hours = free_hours(data["day"])
    if callback_data.hour not in hours:
        await callback.answer("Цей час щойно зайняли, обери інший", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=hours_kb(hours))
        return

    await state.update_data(hour=callback_data.hour)
    await state.set_state(Booking.phone)
    await callback.message.edit_text(booking_text(data["service"], data["day"], callback_data.hour))
    await callback.message.answer(
        "Залиш номер телефону, щоб майстер міг з тобою зв'язатися.\n"
        "Натисни кнопку нижче або напиши номер вручну.",
        reply_markup=phone_kb(),
    )
    await callback.answer()


async def save_phone(message: Message, state: FSMContext, phone):
    await state.update_data(phone=phone)
    await state.set_state(Booking.confirm)
    data = await state.get_data()
    await message.answer("Дякую! Перевір запис 👇", reply_markup=main_menu())
    await message.answer(
        booking_text(data["service"], data["day"], data["hour"])
        + f"\n📱 {escape(phone)}\n\nВсе правильно?",
        reply_markup=confirm_kb(),
    )


@router.message(Booking.phone, F.contact)
async def got_contact(message: Message, state: FSMContext):
    await save_phone(message, state, message.contact.phone_number)


@router.message(Booking.phone, F.text)
async def got_phone_text(message: Message, state: FSMContext):
    phone = re.sub(r"[^\d+]", "", message.text)
    if not re.fullmatch(r"\+?\d{10,13}", phone):
        await message.answer(
            "Не схоже на номер 🤔 Напиши у форматі +380XXXXXXXXX або натисни кнопку нижче."
        )
        return
    await save_phone(message, state, phone)


@router.callback_query(Booking.confirm, F.data == "confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = callback.from_user
    booking_id = db.add_booking(
        user.id, user.full_name, data["phone"], data["service"], data["day"], data["hour"]
    )

    if booking_id is None:
        hours = free_hours(data["day"])
        await state.set_state(Booking.time)
        await callback.message.edit_text(
            "Ой, цей час щойно хтось зайняв 😔 Обери інший:",
            reply_markup=hours_kb(hours),
        )
        await callback.answer()
        return

    await state.clear()
    text = booking_text(data["service"], data["day"], data["hour"])
    await callback.message.edit_text(
        f"✅ <b>Готово, ти записаний(-а)!</b>\n\n{text}\n\n"
        f"Скасувати запис можна в меню «{BTN_MY}»."
    )
    await callback.answer()

    username = f" (@{user.username})" if user.username else ""
    await notify_admin(
        bot,
        f"🆕 <b>Новий запис #{booking_id}</b>\n\n{text}\n"
        f"👤 {escape(user.full_name)}{username}\n📱 {escape(data['phone'])}",
    )


# ---------- мої записи ----------

@router.message(F.text == BTN_MY)
async def my_bookings(message: Message, state: FSMContext):
    await state.clear()
    text, kb = my_bookings_view(message.from_user.id)
    await message.answer(text, reply_markup=kb)


@router.callback_query(CancelCb.filter())
async def cancel_booking(callback: CallbackQuery, callback_data: CancelCb, bot: Bot):
    row = db.get_booking(callback_data.booking_id)
    if row is None or row["user_id"] != callback.from_user.id:
        await callback.answer("Запис не знайдено", show_alert=True)
        return

    db.delete_booking(row["id"])
    await callback.answer("Запис скасовано")
    text, kb = my_bookings_view(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb)

    await notify_admin(
        bot,
        f"❌ <b>Скасовано запис #{row['id']}</b>\n\n"
        f"{booking_text(row['service'], row['day'], row['hour'])}\n"
        f"👤 {escape(row['name'])}\n📱 {escape(row['phone'])}",
    )


# ---------- адмін ----------

def schedule_text(title, from_day, to_day):
    rows = db.bookings_between(from_day, to_day)
    if not rows:
        return f"<b>{title}</b>\n\nЗаписів немає."
    lines = [f"<b>{title}</b>\n"]
    for row in rows:
        lines.append(
            f"{fmt_day(row['day'])} {fmt_hour(row['hour'])} — {escape(row['service'])}\n"
            f"   👤 {escape(row['name'])}, 📱 {escape(row['phone'])}"
        )
    return "\n".join(lines)


@router.message(Command("today"), F.from_user.id == config.ADMIN_ID)
async def admin_today(message: Message):
    today = date.today().isoformat()
    await message.answer(schedule_text("Записи на сьогодні", today, today))


@router.message(Command("week"), F.from_user.id == config.ADMIN_ID)
async def admin_week(message: Message):
    today = date.today()
    await message.answer(
        schedule_text(
            "Записи на тиждень",
            today.isoformat(),
            (today + timedelta(days=config.DAYS_AHEAD)).isoformat(),
        )
    )


# ---------- застарілі кнопки ----------

@router.callback_query()
async def stale_button(callback: CallbackQuery):
    await callback.answer("Ця кнопка вже не активна. Почни заново через меню 🙂", show_alert=True)


async def main():
    logging.basicConfig(level=logging.INFO)
    if not config.BOT_TOKEN:
        raise SystemExit("Не знайдено BOT_TOKEN. Створи файл .env за зразком .env.example")

    db.init_db()
    session = AiohttpSession(proxy=config.PROXY) if config.PROXY else None
    bot = Bot(
        config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
