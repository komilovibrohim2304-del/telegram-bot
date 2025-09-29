import logging
import random
import os
from aiogram import Bot, Dispatcher, executor, types

# Token environmentdan olinadi
API_TOKEN = os.getenv("8499894637:AAHAWZyQIgHTmD-kFF2HvmVvMB0qw8ejdE8")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Sessiyalar
user_sessions = {}
managers_list = {}  # manager_id -> name

# Faqat siz uchun (admin ID kiriting)
ADMIN_ID = 1249958916


@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    args = message.get_args()
    uid = message.from_user.id
    name = message.from_user.full_name

    # Agar manager ro‘yxatdan o‘tish uchun kelsa
    if args and args.lower() == "register_manager":
        managers_list[uid] = name
        await message.answer(f"✅ Siz menejer sifatida ro'yxatga olindingiz.\nID: {uid}")
        return

    # Oddiy mijoz oqimi
    await message.answer("Assalomu alaykum! 👋\nIltimos, ismingizni yuboring.")
    user_sessions[uid] = {"step": "ask_name"}


@dp.message_handler(commands=['list_managers'])
async def list_managers(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not managers_list:
        await message.answer("❌ Hozircha menejerlar ro'yxati bo'sh.")
        return
    text = "\n".join([f"{mid}: {mname}" for mid, mname in managers_list.items()])
    await message.answer("📋 Menejerlar:\n" + text)


@dp.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_sessions:
        await message.answer("Boshlash uchun /start buyrug‘ini yuboring.")
        return

    step = user_sessions[user_id].get("step")

    if step == "ask_name":
        user_sessions[user_id]["name"] = message.text
        user_sessions[user_id]["step"] = "ask_phone"

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("Telefon raqamni yuborish", request_contact=True))
        await message.answer("Telefon raqamingizni yuboring 📞", reply_markup=kb)

    elif step == "chat":
        manager_id = user_sessions[user_id]["manager_id"]
        await bot.send_message(manager_id, f"👤 {user_sessions[user_id]['name']}: {message.text}")


@dp.message_handler(content_types=['contact'])
async def contact_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_sessions or user_sessions[user_id].get("step") != "ask_phone":
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

    # Foydalanuvchiga javob
    await message.answer("Rahmat, sizga eng yaxshi mutaxassisni biriktirdim !", reply_markup=types.ReplyKeyboardRemove())

    # Menejerga yuborish
    await bot.send_message(
        manager_id,
        f"🆕 Yangi mijoz:\n\n👤 Ism: {name}\n📞 Telefon: {message.contact.phone_number}\n\nEndi yozishishingiz mumkin."
    )


@dp.message_handler()
async def relay_from_manager(message: types.Message):
    if message.from_user.id in managers_list:
        # Mijozni topish
        for uid, sess in user_sessions.items():
            if sess.get("manager_id") == message.from_user.id:
                await bot.send_message(uid, f"{managers_list[message.from_user.id]}: {message.text}")
                break


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
