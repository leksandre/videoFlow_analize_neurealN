import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import TimedOut, NetworkError
import requests
import time
import asyncio
from some import TELEGRAM_BOT_TOKEN, GGC_TOKEN, SYSTEM_PROMPT, CONTEXT_TEXT, service_chats_id, managers_chats_id, admin_chats_id, TOKEN_FILE, CERT_PATH, SPAM_DETECTION_PROMPT, RESPONSE_COOLDOWN, base_tokens, reserved_for_history, token_word

import re
import json
import os
from datetime import datetime
import random



max_total_tokens = base_tokens + reserved_for_history

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


chat_history = {}
last_response_time = {}  # { (chat_id, user_id): timestamp }

def estimate_prompt_length(prompt_text):
    """
    Оценивает длину промпта в символах (грубая оценка токенов)
    Примерно: 1 токен ≈ 4 символа для русского текста
    """
    return len(prompt_text)


def calculate_available_tokens(base_prompt_length):
    """
    Рассчитывает сколько токенов доступно для истории
    max_total_tokens - общий лимит
    """
    # Базовый промпт + ответ (base_tokens) + запас
    used_tokens = (base_prompt_length // token_word) + base_tokens + 100
    available_for_history = max_total_tokens - used_tokens
    return max(available_for_history, 0)


def get_optimized_history(chat_history, available_tokens):
    """Возвращает историю, которая влезает в доступные токены"""
    messages_to_include = []
    current_tokens = 0

    # Идем от самых новых к старым сообщениям
    for msg in reversed(chat_history[-4:]):  # максимум 4 последних
        msg_text = f"{msg['role']}: {msg['content']}"  # без timestamp для экономии
        msg_tokens = len(msg_text) // token_word

        if current_tokens + msg_tokens <= available_tokens:
            messages_to_include.insert(0, msg_text)  # добавляем в начало
            current_tokens += msg_tokens
        else:
            break

    return "\n".join(messages_to_include)



def cleanup_old_chats(max_chats=1000, max_messages_per_chat=50):
    """Очищает старые чаты чтобы не переполнять память"""
    global chat_history

    if len(chat_history) > max_chats:
        # Оставляем только самые новые чаты
        oldest_chats = sorted(chat_history.keys())[:-max_chats]
        for chat_id in oldest_chats:
            del chat_history[chat_id]

    # Ограничиваем историю в каждом чате
    for chat_id in chat_history:
        if len(chat_history[chat_id]) > max_messages_per_chat:
            chat_history[chat_id] = chat_history[chat_id][-max_messages_per_chat:]



def has_valid_message_text(update):
    """Проверяет, есть ли валидный текст сообщения"""
    return (update and
            hasattr(update, 'message') and
            update.message and
            hasattr(update.message, 'text') and
            update.message.text and
            len(update.message.text.strip()) > 0)



def is_spam_by_keywords(text: str) -> bool:
    """
    Быстрая проверка на спам по ключевым словам и паттернам.
    Возвращает True, если текст — спам.
    """
    if not text or len(text.strip()) == 0:
        return False

    text_lower = text.lower().strip()
    text_no_spaces = re.sub(r'\s+', '', text_lower)  # Для обхода "с л о в а"
    text_cleaned = re.sub(r'[^\w\s]', ' ', text_lower)  # Убираем знаки препинания

    # === 1. Проверка на подозрительные слова ===
    spam_keywords = [
        # Реклама / офферы
         'заработать', 'заработок',  'выиграть', 'выигрыш',
        'казино', 'ставки', 'крипто', 'инвестиции', 'инвестировать',
        'капуста', 'инвест',
        # Ссылки
        'http', 'https', 't.me/', 'ссылка', 'перейди по ссылке', 'перейти по',
        'сайт', 'сайта', 'ссылочку', 'ссылочку', 'ссылочку',
        # Рефералки / партнёрки
        'реферал', 'партнёрка', 'партнерка', 'доход', 'доход с',
        'вывести деньги', 'вывод денег', 'вывод', 'выведение',
        # Подозрительные слова
        'регистрация', 'акция', 'акция!', 'подарок', 'подарки',
        'только сегодня', 'ограниченное время', 'специально для вас',
        'ты выиграл', 'ты победил', 'поздравляем', 'премия',
        # Слова, связанные с рассылкой
        'рассылка', 'рассылку', 'всем', 'всем!', 'всем в группу',
        # Слова, связанные с "работать на нас"
        'работа', 'удалёнка', 'на дому', 'за компом', 'работа на дому',
        # Телеграм-каналы / боты
        '@', 'бот', 'канал', 'чат', 'чатик', 'группа', 'группу',
    ]

#     for word in spam_keywords:
#         if word in text_lower:
#             return True

    # === 2. Проверка на "обход слов" вида "с л о в о" ===
    for word in ['казино', 'инвестиции', 'заработать', 'выигрыш', 'крипто']:
        if word in text_no_spaces:
            return True

    # === 3. Проверка на подозрительные паттерны ===
    patterns = [
#         r'(?:http[s]?://|www\.)[^\s]+',      # Ссылки
#         r'(?:t\.me/|@)[a-zA-Z0-9_]+',        # Telegram-ссылки
#         r'[!?.]{5,}',                         # Много знаков подряд: !!!!! или ???????
#         r'[а-яё]{6,}',                        # Очень длинные русские слова (возможно, мусор)
#         r'\d{8,}',                            # Длинные числа (номера, счета)
        r'[^\w\s]{4,}',                       # Много специальных символов подряд: !@#$%^&*
        r'(?:капуста|казино|крипто|инвест)\w*',  # Улучшенная проверка слов через regex
    ]
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True

    # === 4. Проверка на слишком много смайлов ===
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+',
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    if len(emojis) > 15:  # Если больше 15 смайлов
        return True

    # === 5. Проверка на "капс" ===
    if text.isupper() and len(text) > 10:
        return True

    # === 6. Проверка на слишком короткие/бессмысленные сообщения ===
#     words = text_cleaned.split()
#     if len(words) <= 2 and any(len(word) < 3 for word in words if word.isalpha()):
#         # Например: "hi", "ok", "ааа", "!!!"
#         return True

    # === 7. Проверка на "спам-фразы" ===
    spam_phrases = [
        'только сегодня',
        'успей купить',
        'ограниченное предложение',
        'ты выиграл',
        'поздравляем',
        'регистрация по ссылке',
        'перейди по ссылке',
        'ссылка в профиле',
        'напиши мне',
        'пиши в личку',
        'пиши сюда',
        'тут можно',
        'тут выиграть',
        'работа на дому',
        'заработай быстро',
        'кликни сюда',
        'кликни здесь',
        'всем расскажу',
        'всем раздам',
        'всем бесплатно',
        'всем подарок',
        'только для вас',
        'специально для вас',
        'только сейчас',
        'уникальное предложение',
        'только для подписчиков',
        'только для участников',
        'только для друзей',
        'только для админов',
        'только для группы',
        'только для канала',
        'только для бота',
        'только для чата',
        'только для лички',
        'только для рефералов',
        'только для партнёров',
        'только для инвесторов',
        'только для клиентов',
        'только для сотрудников',
        'только для друзей',
        'только для семьи',
        'только для знакомых',
        'только для друзей',
        'только для подписчиков',
        'только для админов',
        'только для модераторов',
        'только для админов',
        'только для группы',
        'только для чата',
        'только для канала',
        'только для бота',
        'только для лички',
        'только для рефералов',
        'только для партнёров',
        'только для инвесторов',
        'только для клиентов',
        'только для сотрудников',
        'только для друзей',
        'только для семьи',
        'только для знакомых',
        'только для друзей',
        'только для подписчиков',
        'только для админов',
        'только для модераторов',
    ]

    for phrase in spam_phrases:
        if phrase in text_lower:
            return True

    # === 8. Проверка на слишком много ссылок (даже вида "https : // ...") ===
#     if text_lower.count('http') > 2 or text_lower.count('t.me') > 2:
#         return True

    # === 9. Проверка на "мусорные" символы ===
    # Если текст содержит много бессмысленных символов
#     non_alpha_ratio = len(re.findall(r'[^a-zA-Zа-яА-ЯёЁ0-9\s]', text)) / len(text)
#     if non_alpha_ratio > 0.4:  # Если больше 40% — мусор
#         return True

    # === 10. Проверка на "длинные числа" (номера/счёта) ===
#     if re.search(r'\b\d{8,}\b', text):  # Например, 12345678
#         return True

    return False

def is_spam_via_gigachat(text: str) -> bool:
    if not text or not text.strip():
        logger.info(f"проверка на спам - нет текста " + str(text))
        return False

    full_prompt = SPAM_DETECTION_PROMPT + text.strip()

#     logger.info(f"full_prompt {full_prompt}")
    logger.info(f"str(text) {str(text)}")
    try:
        # Используем уже существующую функцию запроса
        response = get_gpt_response(full_prompt, True)


#         response = await asyncio.wait_for(
#             asyncio.to_thread(get_gpt_response, full_prompt),
#             timeout=300  # 5 минут на выполнение запроса
#         )



        logger.info(f"проверка на спам бот говорит {response}")


        # Нормализуем ответ: убираем пробелы, приводим к нижнему регистру
        clean_response = response.strip().lower()

        logger.info(f"проверка 2 на спам бот говорит {clean_response}")

        # Извлекаем первое слово (на случай, если ИИ напишет пояснение)
        first_word = re.split(r'\s+', clean_response)[0]

        logger.info(f"проверка first_word {first_word}")

#         for chat in service_chats_id:
#             await context.bot.send_message(chat_id=chat, text="--> !!! проверка на спам от пользователь написал '"+str(text)+"' бот говорит что - "+str(response)
#             #, parse_mode="HTML"
#             )


        return first_word == "спам"

    except Exception as e:
        logger.warning(f"Ошибка при проверке спама через GigaChat: {str(e)}")
        # На случай ошибки — лучше не банить (консервативно)
        return False



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

def get_gpt_response(prompt, spam_check = False):
    try:
        # Получаем токен (из кэша или новый)
        access_token = get_gigachat_token()

        # Оцениваем длину промпта в токенах
        estimated_prompt_tokens = len(prompt) // token_word

        tokens_for_response = min(max_total_tokens, estimated_prompt_tokens)


        """
        GigaChat 2 Lite	GigaChat-2	128 тыс.	да	Быстрая и легкая модель
        для простых повседневных задач
        GigaChat 2 Pro	GigaChat-2-Pro	128 тыс.	да	Усовершенствованная модель
        для ресурсоемких задач,
        обеспечивающая максимальную эффективность
        в обработке данных,
        креативности и соблюдении инструкций
        GigaChat 2 Max	GigaChat-2-Max	128 тыс.	да	Мощная модель для самых сложных и масштабных задач,
        требующих высочайшего уровня креативности
        и качества исполнения
        """


#         model = "GigaChat-Pro-preview" # "GigaChat-Pro-preview GigaChat-2-Pro" "GigaChat-2" "GigaChat-2-Max"
        model = "GigaChat-2" #

        if spam_check:
            tokens_for_response = 100
            model = "GigaChat-2"

        logger.info(f"Промпт: len(prompt) {len(prompt)} требует (//{token_word}) = {estimated_prompt_tokens} токенов, "
                   f"доступно для ответа (max_total_tokens): {max_total_tokens}, "
                   f"установлено: {tokens_for_response}")

        # Запрос к GigaChat API
        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        chat_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }


        chat_payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "n":1,
            "top_p": 0.2,
            "temperature": 0.3,
            "max_tokens": tokens_for_response
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
        
        


async def process_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not has_valid_message_text(update):
            logger.warning("Нет валидного текста сообщения")
            return

        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        user_text = update.message.text
        chat_type = update.effective_chat.type

        user = update.message.from_user

        if chat_type not in ['group', 'supergroup']: #проеряем спам только в группах
            return False # говорим не прерывать

        if not user_text or len(user_text.strip()) == 0:
            return True
        # Обрезаем до 500 символов — спам редко бывает длинным
        user_text = user_text[:500]
        text = user_text
        # === Проверка спама через ИИ ===
        try:
            if is_spam_by_keywords(text):
                is_spam_msg = True
                for chat in service_chats_id:
                    logger.info(f"СПАМ ОБНАРУЖЕН по ключевым словам '"+str(text)+"' пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"' ")
                    await context.bot.send_message(chat_id=chat, text="--> !!! СПАМ обнаружен по ключевым словам '"+str(text)+"' пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"'"
                    #, parse_mode="HTML"
                    )
            else:

#                 try:
#                     is_spam_msg = await asyncio.wait_for(
#                         asyncio.to_thread(is_spam_via_gigachat, user_text),
#                         timeout=300
#                     )
#                 except asyncio.TimeoutError:
#                     logger.warning("Превышено время ожидания ответа от GigaChat 2")
#                     is_spam_msg = False

                is_spam_msg = await asyncio.wait_for(
                    asyncio.to_thread(is_spam_via_gigachat, user_text),
                    timeout=300
                )

                if is_spam_msg == True:
                    for chat in service_chats_id:
                        logger.info(f"--> !!! проверка на спам -  пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"' бот говорит что - "+str(is_spam_msg))
                        await context.bot.send_message(chat_id=chat, text="--> !!! проверка на спам -  пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"' бот говорит что - "+str(is_spam_msg)
                        #, parse_mode="HTML"
                        )
        except asyncio.TimeoutError:
            logger.warning("Таймаут при проверке спама")
            is_spam_msg = False

        if is_spam_msg == True:
            for chat in service_chats_id:
                user = update.message.from_user
                r_text = ""
            logger.info(f"СПАМ ОБНАРУЖЕН от {user_id} в чате {chat_id}: {user_text}")

            # 1. Удаляем сообщение спамера
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                logger.info(f"Сообщение {message_id} удалено.")
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {str(e)}")


#             warning_msg = (
#                 "⚠️ Ваше сообщение похоже на спам. "
#                 "Пожалуйста, задавайте вопросы по теме компании Дом Отель. "
#                 "Реклама и офферные предложения запрещены.\n\n"
#                 "Ваше сообщение удалено, и вы временно забанены на  60 минут."
#             )
#             try:
#                 await context.bot.send_message(
#                     chat_id=chat_id,
#                     text=warning_msg
# #                     ,reply_to_message_id=message_id
#                 )
#             except Exception as e:
#                 logger.warning(f"Не удалось отправить предупреждение: {str(e)}")


            try:
                until_date = int(time.time()) + (60*60*6)  # 1 минута на 60 минут в часе на 3 часа
                await context.bot.ban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    until_date=until_date
                )
                logger.info(f"Пользователь {user_id} забанен на 360 минут в чате {chat_id}")
            except Exception as e:
                logger.error(f"Не удалось забанить пользователя {user_id}: {str(e)}")

            # 4. Логируем в сервисные чаты
            for chat in service_chats_id:
                await context.bot.send_message(
                    chat_id=chat,
                    text=f"🚨 СПАМ: пользователь {user_id} забанен на 6 часов в группе {chat_id}. Сообщение: '{user_text}'"
                )


            return True


        return False # говорим не прерывать /// True #говорим  прерывать

# === Команды бота ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Задай мне вопрос по компании Дом Отель.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not has_valid_message_text(update):
        logger.warning("Нет валидного текста сообщения")
        return

    try:
        user_text = update.message.text
        user_text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s.,]', '', user_text)

        chat_id = update.effective_chat.id

        user_id = update.effective_user.id
        message_id = update.message.message_id
        chat_type = update.effective_chat.type

        # Получаем текущую дату и время
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if str(user_id) in managers_chats_id:        #id нашх сотрудников
            if chat_type in ['group', 'supergroup']: #в группах
                return False

        have_to_break = await process_spam(update,context)

        if have_to_break:
            return





        if chat_type in ['group', 'supergroup']:  # Отвечаем в группах стандартным приглашением

#             return # пока заблокируем ответы в группе ()

            current_timestamp = datetime.now().timestamp()
            now = datetime.now()


#             # Проверяем, является ли текущий день будним (0=понедельник, 6=воскресенье)
#             if now.weekday() >= 5:  # 5 = суббота, 6 = воскресенье
#                 logger.info(f"Выходной день ({now.strftime('%A')}), ответ в группе {chat_id} не отправлен.")
#                 return  # Не отвечаем в субботу и воскресенье


            key = (chat_id, user_id)  # Уникальный ключ: чат + пользователь

            # Проверяем, был ли уже ответ этому пользователю менее 30 минут назад
            if key in last_response_time:
                time_since_last = current_timestamp - last_response_time[key]
                if time_since_last < RESPONSE_COOLDOWN:
                    logger.info(f"Пропущен ответ на пользователя {user_id} в чате {chat_id}: кулдаун ещё действует ({int(time_since_last)} из {RESPONSE_COOLDOWN} сек)")
                    return  # Не отвечаем, если прошло меньше 30 минут

            # Если прошло достаточно времени — отправляем сообщение
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "Я ИИ бот. Для быстрого ответа задайте вопрос @DomOtelManual_bot, например - «расчет по квратире 32», или «2К с ПВ 800». Или ждите ответа менеджера. "
                    ),
                    reply_to_message_id=update.message.message_id
                )
                # Обновляем время последнего ответа этому пользователю
                last_response_time[key] = current_timestamp
                logger.info(f"Ответ отправлен пользователю {user_id} в чате {chat_id}")
                return  # Не отвечаем больш ничего
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение: {str(e)}")
                return


        logger.info(f"Получен запрос от пользователя: {user_text}")

        # Инициализируем историю чата, если её ещё нет
        if chat_id not in chat_history:
            chat_history[chat_id] = []






#         history_prompt = "\n".join(
#             f"[{msg['timestamp']}] {msg['role']}: {msg['content']}"
#             for msg in chat_history[chat_id][-10:]  # Берем последние 10 сообщений
#         )

        # Базовый промпт без истории
        base_prompt = f"""{SYSTEM_PROMPT}
        Контекст:
        {CONTEXT_TEXT}

        Текущий вопрос: {user_text}

        Ответ:"""

        base_length = estimate_prompt_length(base_prompt)
        available_history_tokens = calculate_available_tokens(base_length)

        # Получаем оптимизированную историю
        if available_history_tokens > 50:  # Минимум 50 токенов для истории
            history_prompt = get_optimized_history(chat_history[chat_id], available_history_tokens)
            full_prompt = f"""{SYSTEM_PROMPT}
        Контекст:
        {CONTEXT_TEXT}

        История чата:
        {history_prompt}

        Текущий вопрос: {user_text}

        Ответ:"""
        else:
            full_prompt = base_prompt
            logger.info(f"История не включена. Доступно токенов для истории: {available_history_tokens}")

        logger.info(f"Длина промпта: {estimate_prompt_length(full_prompt)} символов")








        

        
        # Показываем статус "печатает" пока ждем ответ
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        

        
        # Увеличиваем таймаут для запроса к GigaChat
        try:
            reply_text = await asyncio.wait_for(
                asyncio.to_thread(get_gpt_response, full_prompt),
                timeout=300  # 5 минут на выполнение запроса
            )
        except asyncio.TimeoutError:
            logger.warning("Превышено время ожидания ответа от GigaChat")
            reply_text = "Извините, обработка запроса заняла слишком много времени. Попробуйте позже."


        chat_history[chat_id].append({
            "role": "user",
            "content": user_text,
            "timestamp": current_time
        })

        # Добавляем ответ бота в историю
        chat_history[chat_id].append({
            "role": "assistant",
            "content": reply_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        reply_text = reply_text.replace('*', '')
        reply_text = reply_text.replace('#', '')
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_text,
            reply_to_message_id=update.message.message_id
            #, parse_mode="HTML"
        )

        user = update.message.from_user
        for chat in service_chats_id:
            await context.bot.send_message(chat_id=chat, text="--> !!! пользователь ("+str(update.effective_chat.id)+") ("+str(user)+") написал '"+user_text+"'"
            #, parse_mode="HTML"
            )
            await context.bot.send_message(chat_id=chat, text="--> !!! мы ему ответили '"+reply_text+"'"
            #, parse_mode="HTML"
            )

        #         chatId = "-1002235142487"
        await context.bot.send_message(chat_id="-1002303418717", text="username @"+str(user.username)+" - написал '"+user_text+"' @AnnaErkes @MaksShevnin "
        #, parse_mode="HTML"
        )


        if random.random() < 0.01:  # 1% шанс
            cleanup_old_chats()
            logger.info("Выполнена рандомная очистка старых чатов")

    except (TimedOut, NetworkError) as e:
        logger.warning(f"Таймаут при отправке сообщения: {str(e)}")
        await asyncio.sleep(1)
        await handle_message(update, context)  # Повторная попытка
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        chat_type = update.effective_chat.type
        if chat_type not in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        if 1:
            for chat in admin_chats_id:
                await context.bot.send_message(
                    chat_id=chat,
                    text=f"Произошла ошибка: {str(e)}"
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
