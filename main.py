import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from collections import defaultdict
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# Web server (Replit keep-alive)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

API_TOKEN = os.getenv("UNO_BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN не найден. Убедись, что .env содержит UNO_BOT_TOKEN=...")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

registered_users = {}
scores = defaultdict(int)
user_languages = defaultdict(lambda: 'az')  # язык по умолчанию — азербайджанский
last_winner = None  # для отслеживания победителя по сообщениям

translations = {
    'ru': {
        'start': "Привет! Хочешь участвовать в турнире по УНО?",
        'registered': "Ты зарегистрирован!",
        'already_registered': "Ты уже в списке участников!",
        'waiting': "Жди начала турнира!",
        'no_players': "Пока никто не зарегистрирован.",
        'players': "Участники турнира:\n",
        'score_usage': "Используй формат: /score @username 50",
        'score_added': "Добавлено {points} очков для @{username}",
        'no_scores': "Пока нет результатов.",
        'leaders': "Лидеры турнира:\n",
        'notifications_sent': "Уведомления отправлены.",
        'notify_usage': "Напиши сообщение: /notify Турнир через 10 минут!",
        'help': (
            "\U0001F4D8 Команды:\n"
            "/start — начать и зарегистрироваться\n"
            "/players — список участников\n"
            "/score @username 50 — добавить очки\n"
            "/leaders — показать лидеров\n"
            "/notify — уведомление участникам\n"
            "/language — изменить язык\n"
            "/help — помощь"
        ),
        'choose_language': "Выберите язык:"
    },
    'az': {
        'start': "Salam! UNO turnirində iştirak etmək istəyirsən?",
        'registered': "Qeydiyyatdan keçdin!",
        'already_registered': "Artıq qeydiyyatdasan!",
        'waiting': "Turnirin başlamasını gözlə!",
        'no_players': "Hələ heç kim qeydiyyatdan keçməyib.",
        'players': "Turnirin iştirakçıları:\n",
        'score_usage': "Format belə olmalıdır: /score @istifadəçi 50",
        'score_added': "{username} üçün {points} xal əlavə edildi",
        'no_scores': "Hələ nəticə yoxdur.",
        'leaders': "Turnirin liderləri:\n",
        'notifications_sent': "Bildirişlər göndərildi.",
        'notify_usage': "Mesajı belə yaz: /notify Turnir 10 dəqiqəyə başlayır!",
        'help': (
            "\U0001F4D8 Əmrlər:\n"
            "/start — Başla və qeydiyyatdan keç\n"
            "/players — İştirakçı siyahısı\n"
            "/score @istifadəçi 50 — Xal əlavə et\n"
            "/leaders — Liderləri göstər\n"
            "/notify — Bütün iştirakçılara mesaj göndər\n"
            "/language — Dili dəyiş\n"
            "/help — Bu yardımı göstər"
        ),
        'choose_language': "Zəhmət olmasa dili seçin:"
    },
    'en': {
        'start': "Hello! Do you want to join the UNO tournament?",
        'registered': "You are registered!",
        'already_registered': "You're already in!",
        'waiting': "Wait for the tournament to start!",
        'no_players': "No players yet.",
        'players': "Tournament participants:\n",
        'score_usage': "Use format: /score @username 50",
        'score_added': "{points} points added for @{username}",
        'no_scores': "No results yet.",
        'leaders': "Top players:\n",
        'notifications_sent': "Notifications sent.",
        'notify_usage': "Use like: /notify Tournament starts in 10 minutes!",
        'help': (
            "\U0001F4D8 Commands:\n"
            "/start — Register\n"
            "/players — List players\n"
            "/score @username 50 — Add score\n"
            "/leaders — Show top\n"
            "/notify — Notify everyone\n"
            "/language — Change language\n"
            "/help — Show help"
        ),
        'choose_language': "Please select a language:"
    }
}

def get_lang(user_id):
    return user_languages[user_id]

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Qeydiyyat", callback_data="register"))
    await message.answer(translations[lang]['start'], reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'register')
async def process_register(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    username = callback_query.from_user.username or callback_query.from_user.full_name
    if user_id not in registered_users:
        registered_users[user_id] = username
        await bot.answer_callback_query(callback_query.id, text=translations[lang]['registered'])
        await bot.send_message(user_id, translations[lang]['waiting'])
    else:
        await bot.answer_callback_query(callback_query.id, text=translations[lang]['already_registered'])

@dp.message_handler(commands=['players'])
async def show_players(message: types.Message):
    lang = get_lang(message.from_user.id)
    if not registered_users:
        await message.answer(translations[lang]['no_players'])
        return
    text = "\n".join([f"{i+1}. @{username}" for i, username in enumerate(registered_users.values())])
    await message.answer(translations[lang]['players'] + text)

@dp.message_handler(commands=['score'])
async def add_score(message: types.Message):
    lang = get_lang(message.from_user.id)
    try:
        _, username, points = message.text.split()
        username = username.replace('@', '')
        user_id = next(uid for uid, uname in registered_users.items() if uname == username)
        scores[user_id] += int(points)
        await message.answer(translations[lang]['score_added'].format(points=points, username=username))
    except:
        await message.answer(translations[lang]['score_usage'])

@dp.message_handler(commands=['leaders'])
async def show_leaders(message: types.Message):
    lang = get_lang(message.from_user.id)
    if not scores:
        await message.answer(translations[lang]['no_scores'])
        return
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    text = translations[lang]['leaders']
    for i, (uid, score) in enumerate(sorted_scores[:5]):
        text += f"{i+1}. @{registered_users[uid]} — {score} xal\n"
    await message.answer(text)

@dp.message_handler(commands=['notify'])
async def notify_all(message: types.Message):
    lang = get_lang(message.from_user.id)
    text = message.text.replace('/notify', '').strip()
    if not text:
        await message.answer(translations[lang]['notify_usage'])
        return
    for uid in registered_users:
        try:
            await bot.send_message(uid, text)
        except:
            continue
    await message.answer(translations[lang]['notifications_sent'])

@dp.message_handler(commands=['language'])
async def change_language(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇦🇿 Azərbaycan", callback_data="lang_az"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    )
    await message.answer("Dil seçin / Выберите язык / Select language:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split("_")[1]
    user_languages[callback_query.from_user.id] = lang_code
    await bot.answer_callback_query(callback_query.id, text="✅ Dəyişildi")

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    lang = get_lang(message.from_user.id)
    await message.answer(translations[lang]['help'])

@dp.message_handler(lambda message: message.text.endswith("won!"))
async def catch_winner(message: types.Message):
    global last_winner
    name = message.text.replace(" won!", "").strip()
    last_winner = name
    print(f"📌 Победитель найден: {name}")

@dp.message_handler(lambda message: message.text == "Game ended!")
async def award_points(message: types.Message):
    global last_winner
    if not last_winner:
        return
    for user_id, username in registered_users.items():
        if username.lower() == last_winner.lower():
            scores[user_id] += 100
            lang = get_lang(user_id)
            await message.reply(
                f"🎉 {last_winner} {translations[lang]['score_added'].format(points=100, username=last_winner)}")
            last_winner = None
            return
    await message.reply(f"⚠ Qalib {last_winner} qeydiyyatda deyil.")
    last_winner = None

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
