import os
import uuid
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import threading

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL')  # Render даёт автоматически

app = Flask(__name__)
bot = Bot(BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# === ШАГИ ===
STEPS = [
    "Общий вид слева", "Общий вид справа", "Двигатель", 
    "Левое переднее колесо", "Правое заднее колесо", 
    "Рама снизу", "Гидравлика", "Кабина", "Навесное", "Готово!"
]
PHOTO, WAIT = range(2)

# === ХЕНДЛЕРЫ ===
def start(update, context):
    keyboard = [[InlineKeyboardButton("Начать осмотр", callback_data='go')]]
    update.message.reply_text(
        "AgroInspectBot\n\n"
        "Сфотографируй технику по шагам — я составлю Акт.\n"
        "Нажми кнопку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAIT

def button(update, context):
    query = update.callback_query
    query.answer()
    context.user_data['photos'] = []
    context.user_data['step'] = 0
    query.edit_message_text(f"Сфотографируй: {STEPS[0]}")
    return PHOTO

def photo(update, context):
    step = context.user_data['step']
    photo_file = update.message.photo[-1].get_file()
    file_path = f"/tmp/{uuid.uuid4()}.jpg"
    photo_file.download(file_path)
    context.user_data['photos'].append(file_path)
    update.message.reply_text(f"Принято: {STEPS[step]}")
    step += 1
    context.user_data['step'] = step
    if step < len(STEPS)-1:
        update.message.reply_text(f"Сфотографируй: {STEPS[step]}")
    else:
        update.message.reply_text("Формирую Акт...")
        create_act(context, update)
        return ConversationHandler.END
    return PHOTO

def create_act(context, update):
    act = f"АКТ ОСМОТРА\nДата: {datetime.now():%d.%m.%Y %H:%M}\n\n"
    for i in range(len(context.user_data['photos'])):
        act += f"{i+1}. {STEPS[i]}\n"
    act += "\nИИ-анализ скоро!"
    update.message.reply_text(act)
    for p in context.user_data['photos']:
        if os.path.exists(p): os.remove(p)

# === РЕГИСТРАЦИЯ ===
conv = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={WAIT: [CallbackQueryHandler(button)], PHOTO: [MessageHandler(Filters.photo, photo)]},
    fallbacks=[],
)
dispatcher.add_handler(conv)

# === WEBHOOK ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'

@app.route('/')
def index():
    return "Bot is alive!"

# === ЗАПУСК ===
def run_webhook():
    if WEBHOOK_URL:
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logging.info(f"Webhook установлен: {WEBHOOK_URL}/webhook")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_webhook()
