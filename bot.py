import os
import uuid
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

# ТОКЕН
BOT_TOKEN = os.getenv('BOT_TOKEN', '8321207190:AAFcKQ7HQlElYfGuRUoicfm2WvqoV1gOdSI')

# Шаги съёмки
STEPS = [
    "Общий вид слева",
    "Общий вид справа",
    "Двигатель (капот открыт)",
    "Левое переднее колесо",
    "Правое заднее колесо",
    "Рама снизу",
    "Гидравлика",
    "Кабина",
    "Навесное оборудование",
    "Готово!"
]

PHOTO, WAIT = range(2)

logging.basicConfig(level=logging.INFO)

def start(update, context):
    keyboard = [[InlineKeyboardButton("Начать осмотр", callback_data='start_inspection')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "🚜 **AgroInspectBot**\n\n"
        "Сфотографируй технику по шагам — я составлю Акт осмотра.\n"
        "Нажми кнопку ниже 👇",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return WAIT

def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'start_inspection':
        context.user_data['photos'] = []
        context.user_data['step'] = 0
        query.edit_message_text(text=f"📸 Сфотографируй: **{STEPS[0]}**", parse_mode='Markdown')
        return PHOTO
    return WAIT

def photo(update, context):
    step = context.user_data['step']
    photo_file = update.message.photo[-1].get_file()
    file_path = f"/tmp/{uuid.uuid4()}.jpg"
    photo_file.download(file_path)
    
    context.user_data['photos'].append(file_path)
    update.message.reply_text(f"✅ Принято: {STEPS[step]}")

    step += 1
    context.user_data['step'] = step

    if step < len(STEPS) - 1:
        update.message.reply_text(f"📸 Сфотографируй: **{STEPS[step]}**", parse_mode='Markdown')
    else:
        update.message.reply_text("🔄 Формирую Акт...")
        create_act(context, update)
        return ConversationHandler.END

    return PHOTO

def create_act(context, update):
    act_text = "📋 **АКТ ОСМОТРА ТЕХНИКИ**\n\n"
    act_text += f"📅 Дата: `{datetime.now().strftime('%d.%m.%Y %H:%M')}`\n\n"
    act_text += "📷 **Фотографии:**\n"

    for i, _ in enumerate(context.user_data['photos']):
        act_text += f"{i+1}. {STEPS[i]} — [фото сохранено]\n"

    act_text += "\n🔧 **ИИ-анализ дефектов:**\n"
    act_text += "_(скоро: ржавчина, износ шин, трещины...)_\n\n"
    act_text += "✅ Акт готов! Проверь и подпиши."

    update.message.reply_text(act_text, parse_mode='Markdown')

    # Очистка
    for p in context.user_data['photos']:
        if os.path.exists(p):
            os.remove(p)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAIT: [CallbackQueryHandler(button)],
            PHOTO: [MessageHandler(Filters.photo, photo)],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    logging.info("🚀 БОТ ЗАПУЩЕН!")
    updater.idle()

if __name__ == '__main__':
    main()
