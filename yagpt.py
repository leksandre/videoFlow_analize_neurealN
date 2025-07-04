import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut, NetworkError
import requests
import time
import asyncio
from some import TELEGRAM_BOT_TOKEN, GGC_TOKEN, SYSTEM_PROMPT, CONTEXT_TEXT, service_chats_id, TOKEN_FILE, CERT_PATH

import json
import os
from datetime import datetime


# Глобальный словарь для хранения истории чатов
chat_history = {}

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
    """
    Получает токен GigaChat, сохраняет его в файл и проверяет актуальность.
    Возвращает актуальный токен.
    """
    # Пытаемся загрузить сохраненный токен из файла
    token_data = load_token_from_file()
    
    # Если токен есть в файле и еще действителен, возвращаем его
    if token_data and 'access_token' in token_data and 'expires_at' in token_data:
        current_time = int(time.time() * 1000)  # Текущее время в миллисекундах
        if current_time < token_data['expires_at']:
            return token_data['access_token']
    
    # Если токена нет или он просрочен, запрашиваем новый
    try:
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        auth_payload = {'scope': 'GIGACHAT_API_PERS'}
        auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': '86921efa-c9de-40fe-8086-8a7379a0f516',
            'Authorization': GGC_TOKEN
        }

        response = requests.post(
            auth_url,
            headers=auth_headers,
            data=auth_payload,
            verify=CERT_PATH  # Используем сертификат для верификации
        )
        response.raise_for_status()
        token_data = response.json()
        
        # Сохраняем новый токен в файл
        save_token_to_file(token_data)
        
        logger.info("Получен новый токен GigaChat")
        return token_data['access_token']
        
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL ошибка: {str(e)}")
        raise Exception("Ошибка SSL при подключении к серверу")
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {str(e)}")
        raise

def load_token_from_file():
    """Загружает токен из JSON-файла, если он существует."""
    if not os.path.exists(TOKEN_FILE):
        return None
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Не удалось загрузить токен из файла: {str(e)}")
        return None

def save_token_to_file(token_data):
    """Сохраняет токен в JSON-файл."""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
    except Exception as e:
        logger.error(f"Не удалось сохранить токен в файл: {str(e)}")

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
            "max_tokens": 5000
        }

        response = requests.post(
            chat_url,
            headers=chat_headers,
            json=chat_payload,
            verify=CERT_PATH  # Используем сертификат для верификации
        )
        response.raise_for_status()
        chat_data = response.json()
        
        return chat_data['choices'][0]['message']['content']

    except requests.exceptions.SSLError as e:
        logger.error(f"SSL ошибка при запросе к API: {str(e)}")
        return "Произошла ошибка безопасности при подключении к серверу."
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
        chat_id = update.effective_chat.id
        
        # Получаем текущую дату и время
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Инициализируем историю чата, если её ещё нет
        if chat_id not in chat_history:
            chat_history[chat_id] = []
            
        chat_history[chat_id].append({
            "role": "user",
            "content": user_text,
            "timestamp": current_time
        })
         
        history_prompt = "\n".join(
            f"[{msg['timestamp']}] {msg['role']}: {msg['content']}"
            for msg in chat_history[chat_id][-10:]  # Берем последние 10 сообщений
        )
        
        logger.info(f"Получен запрос от пользователя: {user_text}")
        
        # Показываем статус "печатает" пока ждем ответ
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        full_prompt = f"""{SYSTEM_PROMPT}
        Контекст:
        {CONTEXT_TEXT}
        
        История чата:
        {history_prompt}
        
        Текущий вопрос: {user_text}
        
        Ответ:"""
        
        # Увеличиваем таймаут для запроса к GigaChat
        try:
            reply_text = await asyncio.wait_for(
                asyncio.to_thread(get_gpt_response, full_prompt),
                timeout=300  # 5 минут на выполнение запроса
            )
        except asyncio.TimeoutError:
            logger.warning("Превышено время ожидания ответа от GigaChat")
            reply_text = "Извините, обработка запроса заняла слишком много времени. Попробуйте позже."

        
        # Добавляем ответ бота в историю
        chat_history[chat_id].append({
            "role": "assistant",
            "content": reply_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_text,
            reply_to_message_id=update.message.message_id
        )
        
        for chat in service_chats_id: 
            user = update.message.from_user
            await context.bot.send_message(chat_id=chat, text="--> !!! пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"'" )
            await context.bot.send_message(chat_id=chat, text="--> !!! мы ему ответили '"+reply_text+"'" )
        
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
