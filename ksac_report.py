from telethon import TelegramClient
from flask import Flask
from threading import Thread
import asyncio
import datetime
import random
import logging
import sys
import os
import fcntl

# --------------------
# 🛠️ Telegram API config
api_id = 25554948
api_hash = 'd0ef27a9bd3c7001c4605c40ee1303ff'
phone_number = '+85510734840'
receiver_phone = '+85595994655'

# --------------------
# 🌐 Flask app for uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "KSAC Auto Report Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# --------------------
# 🕒 Schedule: tuples of (display_time, (start_hour, start_minute), (end_hour, end_minute))
schedule_ranges = [
    ("06:00", (5, 30), (5, 40)),
    ("11:00", (10, 55), (11, 0)),
    ("16:00", (15, 55), (16, 0))
]

# --------------------
# 🔢 Convert number to Khmer numerals
def khmer_number(num):
    khmer_digits = '០១២៣៤៥៦៧៨៩'
    return ''.join(khmer_digits[int(d)] if d.isdigit() else d for d in str(num))

# --------------------
# 📅 Get Khmer date string
def get_khmer_date():
    now = datetime.datetime.now()
    day = khmer_number(now.day)
    khmer_months = [
        "", "មករា", "កុម្ភៈ", "មីនា", "មេសា", "ឧសភា", "មិថុនា",
        "កក្កដា", "សីហា", "កញ្ញា", "តុលា", "វិច្ឆិកា", "ធ្នូ"
    ]
    month = khmer_months[now.month]
    year = khmer_number(now.year)
    return f"ថ្ងៃទី{day} ខែ{month} ឆ្នាំ{year}"

# --------------------
# ✉️ Compose message content
def create_message(report_time):
    date_str = get_khmer_date()
    hr, mn = report_time.split(':')
    kh_hr = khmer_number(int(hr))
    kh_mn = ''.join(khmer_number(d) for d in mn)
    msg = f"""ក្រុមហ៊ុន KSAC សូមរាយការណ៍ជូនមន្ដ្រីប្រចាំការ
{date_str} ម៉ោង {kh_hr}:{kh_mn} នាទី
ស្ដីពី សភាពការណ៍សន្តិសុខតាមបណ្តាគោលដៅ ៖
- សភាពការណ៍ ពុំមានអ្វីកើតឡើងគួរឲ្យកត់សម្គាល់ទេ
- កម្លាំងភ្នាក់ងារសន្តិសុខសរុប ៖ ១៣៧ នាក់ ស្រី ១៣ នាក់
- គោលដៅសរុបចំនួន ៖ ២៤ គោលដៅ
-​ ស្ថានីយប្រេងឥន្ធនៈPTT ៖ មានចំនួន ០២ គោលដៅ ប៉ុន្ដែពុំមានជនជាតិថៃបម្រើការងារទេ
អាស្រ័យដូចបានគោរពរាយការណ៍ជូនមកខាងលើនេះ សូមមន្ដ្រីប្រចាំការ មេត្តាជ្រាបជារបាយការណ៍។"""
    return msg

# --------------------
# 🧠 Prevent duplicate sending
def has_sent(report_label, date=None):
    if not date:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
    key = f"{date}_{report_label}"
    if os.path.exists("sent_report.log"):
        with open("sent_report.log", "r") as f:
            if key in f.read():
                return True
    return False

def mark_sent(report_label):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    key = f"{date}_{report_label}"
    with open("sent_report.log", "a") as f:
        f.write(key + "\n")

# --------------------
# 🔧 Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("ksac_report.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# --------------------
# 🔒 Ensure only one instance running
def ensure_single_instance():
    lock_file = open("ksac_bot.lock", "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except BlockingIOError:
        print("[✗] Another instance is already running.")
        sys.exit()

# --------------------
# 🔁 Async function to send reports
async def send_reports():
    client = TelegramClient('ksac_session', api_id, api_hash)
    await client.start(phone=phone_number)

    logging.info("[✓] KSAC report script started and logged in.")

    try:
        receiver = await client.get_input_entity(receiver_phone)
        logging.info(f"[✓] Receiver entity loaded: {receiver}")
    except Exception as e:
        logging.error(f"[✗] Failed to load receiver entity: {e}")
        return

    while True:
        now = datetime.datetime.now()
        sent = False

        for report_time, (h_start, m_start), (h_end, m_end) in schedule_ranges:
            if has_sent(report_time):
                logging.info(f"[↩] Skipping {report_time} report: already sent today.")
                continue

            start_time = now.replace(hour=h_start, minute=m_start, second=0, microsecond=0)
            end_time = now.replace(hour=h_end, minute=m_end, second=0, microsecond=0)

            if end_time <= start_time:
                end_time += datetime.timedelta(days=1)

            total_seconds = int((end_time - start_time).total_seconds())
            if total_seconds <= 0:
                continue

            rand_seconds = random.randint(0, total_seconds - 1)
            next_send_time = start_time + datetime.timedelta(seconds=rand_seconds)

            if next_send_time <= now or has_sent(report_time):
                continue

            wait_seconds = (next_send_time - now).total_seconds()
            logging.info(f"[⏱️] Waiting to send the {report_time} report at {next_send_time.strftime('%H:%M:%S')}...")
            await asyncio.sleep(wait_seconds)

            if has_sent(report_time):
                logging.info(f"[↩] Report {report_time} already sent after waiting. Skipping.")
                continue

            message = create_message(report_time)
            try:
                await client.send_message(receiver, message)
                mark_sent(report_time)
                logging.info(f"[✓] Report {report_time} sent successfully at {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                logging.error(f"[✗] Failed to send report: {e}")

            sent = True
            break

        if not sent:
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            wake_time = tomorrow.replace(hour=5, minute=55, second=0, microsecond=0)
            wait_seconds = (wake_time - datetime.datetime.now()).total_seconds()
            logging.info(f"[Zzz] All reports done for today. Sleeping until {wake_time.strftime('%H:%M:%S')}")
            await asyncio.sleep(wait_seconds)

# --------------------
# 🔃 Start both Flask + bot
def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_reports())

if __name__ == "__main__":
    ensure_single_instance()
    logging.info(f"[⚙] KSAC Bot started at {datetime.datetime.now().isoformat()}")
    Thread(target=run_flask, daemon=True).start()
    start_bot()
