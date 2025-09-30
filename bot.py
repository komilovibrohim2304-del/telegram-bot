import json
import random
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart, Command

# ====== CONFIG ======
TOKEN = "8499894637:AAHAWZyQIgHTmD-kFF2HvmVvMB0qw8ejdE8"
WEBHOOK_URL = "https://telegram-bot-1riz.onrender.com"   # Render.com URL
ADMIN_ID = 1249958916  # o'zingizni Telegram ID'ingiz
MANAGERS_FILE = Path("managers.json")

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ====== MANAGERS STORAGE ======
def load_managers():
    if MANAGERS_FILE.exists():
        return json.loads(MANAGERS_FILE.read_text())
    return {}

def save_managers(managers: dict):
    MANAGERS_FILE.write_text(json.dumps(managers))

managers_list = load_managers()

# ====== USER SESSIONS ======
user_sessions = {}

# ====== HANDLERS ======
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_sessions[message.from_user.id] = {"step": "ask_name"}
    await message.answer("Assalomu alaykum! 👋\nIltimos, ismingizni yozing:")


@dp.message(F.text, lambda msg: user_sessions.get(msg.from_user.id, {}).get("step") == "ask_name")
async def name_handler(message: Message):
    user_id = message.from_user.id
    user_sessions[user_id]["name"] = message.text
    user_sessions[user_id]["step"] = "ask_phone"

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

    await message.answer("Rahmat! Endi telefon raqamingizni yuboring:", reply_markup=kb)


@dp.message(F.contact)
async def contact_handler(message: Message):
    user_id = message.from_user.id
    if user_sessions.get(user_id, {}).get("step") != "ask_phone":
        return

    user_sessions[user_id]["phone"] = message.contact.phone_number

    if not managers_list:
        await message.answer("❌ Hozircha hech qanday menejer ro'yxatda yo'q.")
        return

    # Tasodifiy menejer tanlash
    manager_id, manager_name = random.choice(list(managers_list.items()))
    user_sessions[user_id]["manager_id"] = int(manager_id)
    user_sessions[user_id]["step"] = "chat"

    name = user_sessions[user_id]["name"]

    await message.answer(
        "✅ Rahmat! Sizga mutaxassis biriktirildi.\nTez orada u siz bilan bog‘lanadi.",
        reply_markup=ReplyKeyboardRemove()
    )

    await bot.send_message(
        manager_id,
        f"🆕 Yangi mijoz:\n\n👤 Ism: {name}\n📞 Telefon: {message.contact.phone_number}\n\nEndi yozishishingiz mumkin."
    )


# ====== ADMIN COMMANDS ======
@dp.message(Command("add_manager"))
async def add_manager(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Sizda ruxsat yo‘q.")
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("ℹ️ Foydalanish: /add_manager <id> <ism>")

    manager_id, manager_name = parts[1], parts[2]
    managers_list[manager_id] = manager_name
    save_managers(managers_list)
    await message.answer(f"✅ Menejer qo‘shildi: {manager_name} ({manager_id})")


@dp.message(Command("del_manager"))
async def del_manager(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Sizda ruxsat yo‘q.")
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("ℹ️ Foydalanish: /del_manager <id>")

    manager_id = parts[1]
    if manager_id in managers_list:
        name = managers_list.pop(manager_id)
        save_managers(managers_list)
        await message.answer(f"✅ Menejer o‘chirildi: {name} ({manager_id})")
    else:
        await message.answer("❌ Bunday menejer yo‘q.")


@dp.message(Command("list_managers"))
async def list_managers(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Sizda ruxsat yo‘q.")

    if not managers_list:
        return await message.answer("📭 Menejerlar ro‘yxati bo‘sh.")
    
    text = "📋 Menejerlar ro‘yxati:\n"
    for mid, name in managers_list.items():
        text += f"- {name} ({mid})\n"
    await message.answer(text)


# ====== START WEBHOOK ======
async def main():
    from aiohttp import web

    async def handle_webhook(request):
        update = await request.json()
        await dp.feed_webhook_update(bot, update)
        return web.Response()

    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    # Webhookni sozlash
    await bot.set_webhook(WEBHOOK_URL)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logging.info("Webhook server started!")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
