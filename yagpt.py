import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut, NetworkError
import requests
import time
import asyncio
from some import TELEGRAM_BOT_TOKEN, GGC_TOKEN

# === Логирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные для кэширования токена
cached_token = None
token_expires_at = 0

def get_gigachat_token():
    global cached_token, token_expires_at
    
    # Если токен еще действителен, возвращаем его
    if cached_token and time.time() * 1000 < token_expires_at:
        return cached_token
    
    try:
        # Запрос нового токена
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        auth_payload = {'scope': 'GIGACHAT_API_PERS'}
        auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': '86921efa-c9de-40fe-8086-8a7379a0f516',
            'Authorization': 'Basic '+str(GGC_TOKEN)
        }

        response = requests.post(auth_url, headers=auth_headers, data=auth_payload, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Обновляем кэш
        cached_token = data['access_token']
        token_expires_at = data['expires_at']
        
        logger.info("Получен новый токен GigaChat")
        return cached_token
        
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {str(e)}")
        raise

def get_gpt_response(prompt):
    try:
        # Получаем токен (из кэша или новый)
        access_token = get_gigachat_token()
        
        # Запрос к GigaChat API
        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        chat_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        chat_payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(chat_url, headers=chat_headers, json=chat_payload, verify=False)
        response.raise_for_status()
        chat_data = response.json()
        
        return chat_data['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {str(e)}")
        return "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
    except KeyError as e:
        logger.error(f"Ошибка парсинга ответа: {str(e)}")
        return "Произошла ошибка при обработке ответа сервера."
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return "Произошла непредвиденная ошибка."

# ... (остальной код бота остается без изменений)


# === Команды бота ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Задай мне вопрос по компании Дом Отель.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text
        logger.info(f"Получен запрос от пользователя: {user_text}")
        
        # Показываем статус "печатает" пока ждем ответ
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Увеличиваем таймаут для запроса к GigaChat
        try:
            reply_text = await asyncio.wait_for(
                asyncio.to_thread(get_gpt_response, user_text),
                timeout=300  # 5 минут на выполнение запроса
            )
        except asyncio.TimeoutError:
            logger.warning("Превышено время ожидания ответа от GigaChat")
            reply_text = "Извините, обработка запроса заняла слишком много времени. Попробуйте позже."
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_text,
            reply_to_message_id=update.message.message_id
        )
        
    except (TimedOut, NetworkError) as e:
        logger.warning(f"Таймаут при отправке сообщения: {str(e)}")
        await asyncio.sleep(1)
        await handle_message(update, context)  # Повторная попытка
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка. Пожалуйста, попробуйте позже."
        )

# === Запуск бота с увеличенными таймаутами ===
if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).read_timeout(60).write_timeout(60).pool_timeout(60).get_updates_read_timeout(60).build()

        start_handler = CommandHandler('start', start)
        message_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND),
            handle_message
        )

        application.add_handler(start_handler)
        application.add_handler(message_handler)

        logger.info("Бот запущен с увеличенными таймаутами")
        application.run_polling(
            poll_interval=3.0,  # Интервал опроса сервера
            timeout=60,         # Таймаут long polling
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Ошибка в основном цикле: {str(e)}")
