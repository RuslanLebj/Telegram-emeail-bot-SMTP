import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start от пользователя.

    Отправляет сообщение с просьбой ввести email для продолжения взаимодействия с ботом.

    Args:
        update (Update): Объект, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст команды.
    """
    await update.message.reply_text("Здравствуйте! Пожалуйста, введите ваш email.")


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод email от пользователя.

    Проверяет, что введенная строка является корректным email, сохраняет email
    в данные пользователя и запрашивает ввод текста сообщения для отправки.

    Args:
        update (Update): Объект, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст команды.
    """
    email = update.message.text
    if "@" in email and "." in email:
        user_data[update.message.chat_id] = {"email": email}
        await update.message.reply_text(
            "Email принят. Теперь, пожалуйста, напишите текст сообщения для отправки."
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, введите корректный email (например, user@example.com)."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод текста сообщения от пользователя.

    Если пользователь уже предоставил email, то отправляет email с введенным текстом.
    Если email не был предоставлен, запрашивает его ввод.

    Args:
        update (Update): Объект, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст команды.
    """
    chat_id = update.message.chat_id
    if chat_id in user_data and "email" in user_data[chat_id]:
        email = user_data[chat_id]["email"]
        message_text = update.message.text

        if send_email(email, message_text):
            await update.message.reply_text(
                "Сообщение успешно отправлено на указанный email."
            )
        else:
            await update.message.reply_text(
                "Ошибка отправки сообщения. Пожалуйста, проверьте настройки SMTP."
            )

        del user_data[chat_id]  # Очищаем данные пользователя после отправки сообщения
    else:
        await update.message.reply_text("Пожалуйста, сначала введите ваш email.")


def send_email(to_email: str, message_text: str) -> bool:
    """
    Отправляет email-сообщение с использованием SMTP.

    Args:
        to_email (str): Адрес получателя.
        message_text (str): Текст сообщения для отправки.

    Returns:
        bool: True, если сообщение отправлено успешно, иначе False.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_LOGIN
        msg["To"] = to_email
        msg["Subject"] = "Уведомление от Telegram-бота"
        msg.attach(MIMEText(message_text, "plain"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False


def main():
    """
    Основная функция, которая инициализирует и запускает Telegram-бота.

    Конфигурирует обработчики команд и сообщений, а затем запускает бота в режиме polling.
    """
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r"[^@]+@[^@]+\.[^@]+"), handle_email))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()