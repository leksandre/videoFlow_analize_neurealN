from fastapi import FastAPI, HTTPException
import uvicorn
import requests
import asyncio
import os
import json
import time
import logging
from some import TELEGRAM_BOT_TOKEN, GGC_TOKEN, SYSTEM_PROMPT, CONTEXT_TEXT, service_chats_id, TOKEN_FILE, CERT_PATH


# === Логирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

# === Получение токена GigaChat с кэшированием ===


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


# === Запрос к GigaChat API ===

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
        
        

# === Отправка логов в Telegram ===
async def send_telegram_log(chat_id: str, question: str, answer: str, user_info: dict = None):
    from telegram import Bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    user_text = f"{user_info.get('id')} ({user_info.get('username')})" if user_info else "неизвестный пользователь"

    log_message_1 = f"\\\\\\\\\  пользователь ({user_text}) написал '{question}'"
    log_message_2 = f"\\\\\\\\\  мы ему ответили '{answer}'"

    try:
        async with bot:
            await bot.send_message(chat_id=chat_id, text=log_message_1)
            await bot.send_message(chat_id=chat_id, text=log_message_2)
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение в чат {chat_id}: {str(e)}")

# === Эндпоинт API для обработки вопроса ===
@app.post("/api/ask")
async def ask_gigachat(data: dict):
    question = data.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Вопрос не указан")

    logger.info(f"Получен вопрос: {question}")

    full_prompt = f"""{SYSTEM_PROMPT}
    Контекст:
    {CONTEXT_TEXT}

    Вопрос: {question}

    Ответ:"""

    loop = asyncio.get_event_loop()
    try:
        answer = await loop.run_in_executor(None, get_gpt_response, full_prompt)

        # Отправляем логи в Telegram
        user_info = {"id": "API", "username": "web"}
        for chat in service_chats_id:
            await send_telegram_log(chat, question, answer, user_info)
            
        logger.info(f"Сгенерирован ответ: {answer}")
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при генерации ответа")
        
        
# === Запуск FastAPI ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)