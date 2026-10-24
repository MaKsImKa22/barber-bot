import asyncio, sys, tempfile, os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["BOT_TOKEN"] = "42:TEST"
os.environ["ADMIN_ID"] = "999"

import config, db
db.DB_PATH = Path(tempfile.mkdtemp()) / "test.db"
import bot as app

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update, Message
from aiogram.methods import SendMessage, EditMessageText, AnswerCallbackQuery

sent = []
msg_id = [100]

class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        sent.append(method)
        if isinstance(method, (SendMessage, EditMessageText)):
            msg_id[0] += 1
            return Message.model_validate({"message_id": msg_id[0], "date": 0,
                "chat": {"id": getattr(method, "chat_id", 1) or 1, "type": "private"},
                "text": method.text})
        return True
    async def close(self): pass
    async def stream_content(self, *a, **k):
        yield b""

USER = {"id": 1, "is_bot": False, "first_name": "Тест", "username": "tester"}
CHAT = {"id": 1, "type": "private"}
uid = [0]

def msg(text=None, contact=None):
    uid[0] += 1
    m = {"message_id": uid[0], "date": 0, "chat": CHAT, "from": USER}
    if text: m["text"] = text
    if contact: m["contact"] = contact
    return Update.model_validate({"update_id": uid[0], "message": m})

def cb(data):
    uid[0] += 1
    return Update.model_validate({"update_id": uid[0], "callback_query": {
        "id": str(uid[0]), "from": USER, "chat_instance": "x", "data": data,
        "message": {"message_id": 5, "date": 0, "chat": CHAT, "from": {"id": 42, "is_bot": True, "first_name": "B"}, "text": "x"}}})

def last_kb_data():
    for m in reversed(sent):
        rm = getattr(m, "reply_markup", None)
        if rm is not None and hasattr(rm, "inline_keyboard"):
            return [b.callback_data for row in rm.inline_keyboard for b in row]
    return []

async def main():
    db.init_db()
    bot = Bot("42:TEST", session=FakeSession(), default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(app.router)

    async def step(u, label):
        n = len(sent)
        await dp.feed_update(bot, u)
        new = sent[n:]
        print(f"--- {label}: {[type(m).__name__ for m in new]}")
        for m in new:
            t = getattr(m, "text", None)
            if t: print("   ", t.replace("\n", " | ")[:150])
        return new

    await step(msg("/start"), "start")
    await step(msg("/myid"), "myid")
    await step(msg(app.BTN_BOOK), "book")
    await step(cb(last_kb_data()[0]), "service")
    day = last_kb_data()[0]
    await step(cb(day), "day")
    hours = last_kb_data()
    print("   hours:", hours)
    await step(cb(hours[0]), "time")
    await step(msg("abc"), "bad phone")
    await step(msg("+380 67 123 45 67"), "phone")
    new = await step(cb("confirm"), "confirm")
    assert any(getattr(m, "chat_id", None) == 999 for m in new), "admin not notified"

    # той самий слот має зникнути
    d = day.split(":", 1)[1]
    assert int(hours[0].split(":")[1]) not in app.free_hours(d)

    # подвійне бронювання
    assert db.add_booking(2, "X", "1", "s", d, int(hours[0].split(":")[1])) is None

    await step(msg(app.BTN_MY), "my")
    cancel = last_kb_data()[0]
    await step(cb(cancel), "cancel")
    assert db.user_bookings(1, "2000-01-01") == []

    await step(cb("svc:0"), "stale button")

    # адмін
    USER["id"] = 999
    await step(msg("/week"), "admin week")
    USER["id"] = 1
    await step(msg("/week"), "non-admin week (should be silent)")
    print("ALL OK")

asyncio.run(main())
