import os
import uuid
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler

BOT_TOKEN = os.getenv('BOT_TOKEN')

STEPS = [
    "Общий вид слева", "Общий вид справа", "Двигатель", 
    "Левое переднее колесо", "Правое заднее колесо", 
    "Рама снизу", "Гидравлика", "Кабина", 
    "Навесное", "Готово!"
]

PHOTO, WAIT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Начать осмотр", callback_data='go')]]
    await update.message.reply_text("Нажми кнопку → следуй инструкциям", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAIT

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['photos'] = []
    context.user_data['step'] = 0
    await query.edit_message_text(f"Сфотографируй: {STEPS[0]}")
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data['step']
    photo = update.message.photo[-1]
    file_path = f"/tmp/{uuid.uuid4()}.jpg"
    await (await photo.get_file()).download_to_drive(file_path)
    context.user_data['photos'].append(file_path)
    await update.message.reply_text(f"Принято: {STEPS[step]}")
    step += 1
    context.user_data['step'] = step
    if step < len(STEPS) - 1:
        await update.message.reply_text(f"Сфотографируй: {STEPS[step]}")
    else:
        await update.message.reply_text("Формирую Акт...")
        await create_act(context, update)
        return ConversationHandler.END
    return PHOTO

async def create_act(context, update: Update):
    act = f"АКТ ОСМОТРА\nДата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    for i in range(len(context.user_data['photos'])):
        act += f"{i+1}. {STEPS[i]}\n"
    act += "\nИИ-анализ скоро!"
    await update.message.reply_text(act)
    for p in context.user_data['photos']:
        if os.path.exists(p): os.remove(p)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={WAIT: [CallbackQueryHandler(button)], PHOTO: [MessageHandler(filters.PHOTO, photo)]},
        fallbacks=[],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
