import logging
import random
import os
from pathlib import Path

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

NUMBER_OF_IMAGES = 54


# ---------- Настройка логирования с цветами для всех уровней ----------
class ColoredFormatter(logging.Formatter):
    """Форматировщик с цветным выводом для разных уровней логирования"""
    COLORS = {
        'DEBUG': '\033[36m',  # голубой
        'INFO': '\033[32m',  # зелёный
        'WARNING': '\033[33m',  # жёлтый
        'ERROR': '\033[91m',  # ярко‑красный
        'CRITICAL': '\033[41m\033[37m',  # красный фон, белый текст
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


# Настраиваем корневой логгер
logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
if root_logger.handlers:
    root_logger.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# ---------- Глобальная переменная токена (получаем из окружения) ----------
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("Переменная окружения TELEGRAM_BOT_TOKEN не установлена или пуста.")
    exit(1)
logger.info("Токен успешно загружен из переменной окружения")

"""token = Path("token.txt")

try:
    token = token.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("Файл token.txt пуст")
    logger.info("Токен успешно загружен из token.txt")
except FileNotFoundError:
    logger.error("Файл token.txt не найден. Создайте его и запишите токен бота.")
    exit(1)
except Exception as e:
    logger.error("Ошибка при чтении токена: %s", e)
    exit(1)
"""

# ---------- Команды для меню бота ----------
COMMANDS = [
    BotCommand("start", "Запустить бота"),
    BotCommand("what_gosling_are_you_today", "Какой ты Гослинг сегодня"),
]


# ---------- Обработчики команд ----------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение со списком команд."""
    welcome_text = (
        "Hello, I'm Gosling today bot!\n\n"
        "Доступные команды:\n"
        "/start — Запустить бота\n"
        "/what_gosling_are_you_today — Узнать, какой вы гослинг сегодня"
    )
    await update.message.reply_text(welcome_text)


async def gosling_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет картинку с номером и упоминанием пользователя в тот же чат,
    откуда пришла команда.
    """
    number = random.randint(1, NUMBER_OF_IMAGES)
    user = update.effective_user
    caption = f"{user.mention_html()}"

    # Путь к изображению
    BASE_DIR = Path(__file__).parent
    image_path = BASE_DIR / "Gosling_today_images" / f"Gosling_{number}.jpg"

    try:
        if not image_path.exists():
            raise FileNotFoundError(f"Файл {image_path} не найден")

        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode='HTML'
            )
            logger.info(
                f"Картинка Gosling_{number}.jpg отправлена пользователю {user.id} в чат {update.effective_chat.id}")

    except FileNotFoundError as e:
        await update.message.reply_text(
            f"{user.mention_html()}, картинка не найдена",
            parse_mode='HTML'
        )
        logger.error(f"Файл изображения не найден: {e}")

    except Exception as e:
        await update.message.reply_text(
            f"{user.mention_html()}, не удалось отправить картинку",
            parse_mode='HTML'
        )
        logger.error("Ошибка при отправке картинки: %s", e)


# ---------- Обработчик ошибок ----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Возникло исключение при обработке обновления:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла внутренняя ошибка. Попробуйте позже."
        )


# ---------- Функция, выполняющаяся после инициализации приложения ----------
async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(COMMANDS)
    logger.info("Команды бота успешно установлены.")


# ---------- Точка входа ----------
def main() -> None:
    """Создаёт приложение, добавляет обработчики и запускает бота."""

    # Создаём HTTP‑клиент с увеличенными таймаутами
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=60.0
    )

    application = (
        Application.builder()
        .token(token)  # используется глобальная переменная token
        .request(request)
        .post_init(post_init)
        .build()
    )

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("what_gosling_are_you_today", gosling_command))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и готов к работе...")
    application.run_polling(poll_interval=4)


if __name__ == "__main__":
    main()
