import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from bot_config import BOT_TOKEN, CHANNEL_ID
from db import create_table, add_or_update_subscriber, get_subscription_status, get_conn
from telegram.ext import CommandHandler, MessageHandler, filters


logging.basicConfig(level=logging.INFO)

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member
    user = member.new_chat_member.user
    status = member.new_chat_member.status
    # Только если пользователь стал участником
    if status == "member":
        # Добавляем в базу с subscription=False (по умолчанию)
        add_or_update_subscriber(user.id, user.full_name, False)
        # Проверяем подписку
        sub = get_subscription_status(user.id)
        if not sub:
            try:
                await context.bot.ban_chat_member(CHANNEL_ID, user.id)
                await context.bot.unban_chat_member(CHANNEL_ID, user.id)  # мгновенное удаление
            except Exception as e:
                logging.error(f"Ошибка удаления пользователя: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_subscriber(user.id, user.full_name, False)
    keyboard = [
        [KeyboardButton("Проверить подписку"), KeyboardButton("Оплатил подписку")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать! Вы успешно зарегистрированы. Вам необходимо оплатить подписку для доступа в канал!",
        reply_markup=reply_markup
    )

async def check_subscription_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    sub = get_subscription_status(user.id)
    if sub is True:
        await update.message.reply_text("Ваша подписка активна!")
    else:
        # Попытка удалить пользователя из канала
        try:
            await context.bot.ban_chat_member(CHANNEL_ID, user.id)
            await context.bot.unban_chat_member(CHANNEL_ID, user.id)
            await update.message.reply_text("Ваша подписка неактивна. Вы были удалены из канала. Оплатите подписку для доступа в канал!")
        except Exception as e:
            await update.message.reply_text(f"Ваша подписка неактивна. Не удалось удалить из канала автоматически. Обратитесь к администратору. Ошибка: {e}")

async def paid_subscription_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_subscriber(user.id, user.full_name, True)
    # Попытка получить invite link
    try:
        invite_link = await context.bot.create_chat_invite_link(CHANNEL_ID, member_limit=1)
        await update.message.reply_text(f"Ваша подписка активирована! Вот ссылка для доступа в канал: {invite_link.invite_link}")
    except Exception as e:
        await update.message.reply_text(f"Ваша подписка активирована, но не удалось получить ссылку для входа в канал. Обратитесь к администратору. Ошибка: {e}")
"""
async def debug_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, subscription FROM subscribers;")
                rows = cur.fetchall()
                if not rows:
                    await update.message.reply_text("Таблица пуста.")
                    return
                msg = "Список пользователей в базе:\n"
                for row in rows:
                    msg += f"ID: {row[0]}, Имя: {row[1]}, Подписка: {row[2]}\n"
                await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении данных: {e}")
"""

async def remove_unsubscribed_users_job(context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM subscribers WHERE subscription=FALSE;")
                rows = cur.fetchall()
                for row in rows:
                    user_id = row[0]
                    try:
                        member = await app.bot.get_chat_member(CHANNEL_ID, user_id)
                        if member.status not in ("member", "administrator", "creator"):
                            continue  # Уже не в канале, пропускаем
                        await app.bot.ban_chat_member(CHANNEL_ID, user_id)
                        await app.bot.unban_chat_member(CHANNEL_ID, user_id)
                        await app.bot.send_message(user_id, "Ваша подписка закончилась. Вы были удалены из канала!")
                    except Exception as e:
                        pass
    except Exception as e:
        pass

def main():
    create_table()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Проверить подписку$"), check_subscription_reply))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Оплатил подписку$"), paid_subscription_reply))
    #app.add_handler(CommandHandler("debug_users", debug_users))
    app.job_queue.run_repeating(remove_unsubscribed_users_job, interval=60, first=5)
    app.run_polling()

if __name__ == "__main__":
    main() 