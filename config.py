import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip() or 0)
# Потрібен на безкоштовному PythonAnywhere: http://proxy.server:3128
PROXY = os.getenv("PROXY", "").strip() or None

BUSINESS_NAME = "Барбершоп «Бритва»"

# Послуга -> ціна в гривнях
SERVICES = {
    "Чоловіча стрижка": 400,
    "Стрижка бороди": 250,
    "Стрижка + борода": 600,
}

WORK_START = 10  # перший слот о 10:00
WORK_END = 19    # останній слот о 18:00
DAYS_AHEAD = 7   # на скільки днів вперед можна записатися
DAYS_OFF = {6}   # вихідні: 0 = понеділок ... 6 = неділя
