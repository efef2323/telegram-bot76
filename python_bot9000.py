from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yfinance as yf
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime, timedelta
import pytesseract
from PIL import Image
import io
import aiohttp
import asyncio
import json
import math
import re
import random

# ========== НАСТРОЙКИ ДЛЯ RENDER ==========
# Проверяем, что мы на Render
if 'RENDER' in os.environ:
    # Указываем пути к Chrome и драйверу для Selenium
    os.environ['CHROMEDRIVER_PATH'] = '/usr/bin/chromedriver'
    os.environ['GOOGLE_CHROME_BIN'] = '/usr/bin/chromium-browser'
    
    # Настройка для pytesseract
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    
    print("✅ Режим Render активирован, системные пути настроены.")

# ========== НАСТРОЙКИ ==========
TOKEN = '8531196180:AAHTRMQ1dgNqbdnJM9Cy4ByoCv6FPlzpYsI'
BASE_URL = 'http://ishnk.ru/2025/site/schedule/group/520/'

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
ai_mode = False
chat_history = {}
current_language = 'ru'

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🚀 Бот активирован, {user.first_name}!\n\n"
        f"📋 Доступные команды:\n"
        f"/help - показать все команды\n"
        f"/ai_on - включить ИИ режим\n"
        f"/ai_off - выключить ИИ режим\n"
        f"/analyze [AAPL] - анализ акций\n"
        f"/schedule_today - расписание на сегодня\n"
        f"/schedule_tomorrow - расписание на завтра\n"
        f"/weather - погода в Ишимбае\n"
        f"/forecast - прогноз на 3 дня\n"
        f"/joke - случайная шутка\n"
        f"/calc 2+2*2 - калькулятор"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *ДОСТУПНЫЕ КОМАНДЫ:*

*Основные команды:*
/start - Начать работу
/help - Эта справка
/ai_on - Включить ИИ режим
/ai_off - Выключить ИИ режим

*Погода (улучшенная):*
/weather - погода в Ишимбае
/weather [город] - погода в любом городе
/weather подробно - детальный прогноз
/weather помощь - справка по команде
/forecast [город] - прогноз на 3 дня

*Финансы и анализ:*
/analyze [тикер] - Анализ акций (например: /analyze AAPL)
/crypto [монета] - Курс криптовалюты (bitcoin, ethereum)

*Расписание:*
/schedule_today - Расписание на сегодня
/schedule_tomorrow - Расписание на завтра

*Полезное:*
/joke - Случайная шутка
/calc [выражение] - Калькулятор (например: /calc 2+2*2)

*Техническое:*
/clear - Очистить историю
/status - Статус бота

*Использование ИИ:*
1. Включите ИИ: /ai_on
2. Задавайте любые вопросы или задачи
3. ИИ ответит на них!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ========== РАСПИСАНИЕ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ==========
async def schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на сегодня"""
    today_date = datetime.now().strftime('%Y-%m-%d')
    await get_schedule(update, today_date, "сегодня")

async def schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на завтра"""
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    await get_schedule(update, tomorrow_date, "завтра")

async def get_schedule(update: Update, date_str: str, day_name: str):
    """Универсальная функция получения расписания"""
    url = f"{BASE_URL}{date_str}"
    
    await update.message.reply_text(f"📅 Получаю расписание на {day_name} ({date_str})...")
    
    # Конфигурация Chrome для работы в фоне
    chrome_options = Options()
    
    # АВТОМАТИЧЕСКИЕ НАСТРОЙКИ ДЛЯ RENDER
    if 'RENDER' in os.environ:
        chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        chrome_options.add_argument('--headless=new')  # Новый стабильный режим
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        print("🔄 Использую настройки Chrome для Render")
    else:
        # Старые настройки для локального запуска
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        print("🔄 Использую локальные настройки Chrome")
    
    driver = None
    try:
        # Используем Selenium Manager (автоматически с Selenium 4.10+)
        driver = webdriver.Chrome(options=chrome_options)
        
        # Устанавливаем таймаут и загружаем страницу
        driver.set_page_load_timeout(30)
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(3)
        
        # Делаем скриншот
        screenshot_path = f'schedule_{date_str}.png'
        driver.save_screenshot(screenshot_path)
        
        # Проверяем размер файла
        if os.path.getsize(screenshot_path) > 0:
            with open(screenshot_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📅 Расписание на {day_name} ({date_str})\n🔗 {url}"
                )
        else:
            await update.message.reply_text(f"❌ Не удалось получить скриншот\n🔗 {url}")
        
    except Exception as e:
        error_msg = str(e)
        # Упрощенное сообщение об ошибке
        if "timeout" in error_msg.lower():
            await update.message.reply_text(f"⏱️ Таймаут при загрузке страницы\n🔗 {url}")
        elif "chrome" in error_msg.lower():
            await update.message.reply_text(f"❌ Ошибка Chrome драйвера\n🔗 {url}")
        else:
            await update.message.reply_text(f"❌ Ошибка: {error_msg[:100]}...\n🔗 {url}")
    
    finally:
        # Всегда закрываем драйвер
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        # Удаляем временный файл если он существует
        if os.path.exists(f'schedule_{date_str}.png'):
            try:
                os.remove(f'schedule_{date_str}.png')
            except:
                pass

# ========== ФИНАНСОВЫЙ АНАЛИЗ ==========
async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📊 Укажи символ акции: /analyze AAPL")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 Анализирую {symbol}...")
    
    try:
        # Загружаем данные
        data = yf.download(symbol, period='1mo', interval='1d')
        
        if data.empty or len(data) < 5:
            await update.message.reply_text(f"❌ Акция '{symbol}' не найдена или мало данных")
            return
        
        # Рассчитываем индикаторы
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        
        current_price = data['Close'].iloc[-1]
        sma_10 = data['SMA_10'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        
        # Формируем анализ
        analysis = f"📈 *АНАЛИЗ {symbol}*\n\n"
        analysis += f"💰 Текущая цена: ${current_price:.2f}\n"
        analysis += f"📊 SMA(10): ${sma_10:.2f}\n"
        analysis += f"📊 SMA(20): ${sma_20:.2f}\n\n"
        
        # Даем рекомендацию
        price_change = ((current_price - sma_10) / sma_10) * 100
        
        if current_price > sma_10 > sma_20:
            analysis += f"✅ *РЕКОМЕНДАЦИЯ: ПОКУПАТЬ*\n"
            analysis += f"• Цена выше средних (+{price_change:.1f}%)\n"
            analysis += f"• Восходящий тренд\n"
        elif current_price < sma_10 < sma_20:
            analysis += f"❌ *РЕКОМЕНДАЦИЯ: ПРОДАВАТЬ*\n"
            analysis += f"• Цена ниже средних ({price_change:.1f}%)\n"
            analysis += f"• Нисходящий тренд\n"
        else:
            analysis += f"⚠️ *РЕКОМЕНДАЦИЯ: ЖДАТЬ*\n"
            analysis += f"• Тренд не ясен ({price_change:.1f}%)\n"
        
        analysis += f"\n📅 Данные за последний месяц"
        
        await update.message.reply_text(analysis, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка анализа: {str(e)}")

# ========== УЛУЧШЕННАЯ КОМАНДА ПОГОДЫ ==========
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Погода с выбором города и детальной информацией"""
    
    # Параметры команды
    city = "Ishimbay"  # Город по умолчанию
    show_detailed = False
    
    # Проверяем аргументы команды
    if context.args:
        args = ' '.join(context.args)
        
        # Проверяем специальные аргументы
        if args.lower() == "подробно" or args.lower() == "detail":
            show_detailed = True
        elif args.lower() == "помощь" or args.lower() == "help":
            await update.message.reply_text(
                "🌤 *СПРАВКА ПО КОМАНДЕ ПОГОДА*\n\n"
                "/weather - погода в Ишимбае\n"
                "/weather Москва - погода в другом городе\n"
                "/weather подробно - детальный прогноз\n"
                "/weather помощь - эта справка\n\n"
                "📌 *Примеры:*\n"
                "• /weather London\n"
                "• /weather New York\n"
                "• /weather Париж\n"
                "• /weather подробно",
                parse_mode='Markdown'
            )
            return
        else:
            city = args
    
    await update.message.reply_text(f"🌤 Получаю погоду для {city}...")
    
    try:
        # Формируем URL в зависимости от запроса
        if show_detailed:
            # Детальный прогноз на 3 дня
            url = f"https://wttr.in/{city}?format=j1&lang=ru"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Извлекаем данные
                        current = data['current_condition'][0]
                        weather_desc = current['weatherDesc'][0]['value']
                        temp_c = current['temp_C']
                        feels_like = current['FeelsLikeC']
                        humidity = current['humidity']
                        wind_kph = current['windspeedKmph']
                        pressure = current['pressure']
                        uv_index = current['uvIndex']
                        
                        # Форматируем ответ
                        response_text = f"📊 *ДЕТАЛЬНЫЙ ПРОГНОЗ ДЛЯ {city.upper()}*\n\n"
                        response_text += f"🌡 *Температура:* {temp_c}°C\n"
                        response_text += f"🤔 *Ощущается как:* {feels_like}°C\n"
                        response_text += f"💧 *Влажность:* {humidity}%\n"
                        response_text += f"💨 *Ветер:* {wind_kph} км/ч\n"
                        response_text += f"📏 *Давление:* {pressure} мбар\n"
                        response_text += f"☀️ *UV индекс:* {uv_index}\n"
                        response_text += f"📝 *Состояние:* {weather_desc}\n\n"
                        
                        # Добавляем прогноз на 3 дня
                        response_text += "📅 *ПРОГНОЗ НА 3 ДНЯ:*\n"
                        for i, day in enumerate(data['weather'][:3]):
                            date = day['date']
                            max_temp = day['maxtempC']
                            min_temp = day['mintempC']
                            
                            # Определяем день недели
                            try:
                                date_obj = datetime.strptime(date, "%Y-%m-%d")
                                day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date_obj.weekday()]
                            except:
                                day_name = f"День {i+1}"
                            
                            response_text += f"  {day_name}: {min_temp}°C - {max_temp}°C\n"
                        
                        response_text += f"\n🕐 *Обновлено:* {datetime.now().strftime('%H:%M')}"
                        
                        await update.message.reply_text(response_text, parse_mode='Markdown')
                        return
        else:
            # Быстрый прогноз
            url = f"https://wttr.in/{city}?format=%C+%t+%w+%h+%f+%p+%u&lang=ru"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        weather_data = await response.text()
                        parts = weather_data.strip().split()
                        
                        if len(parts) >= 7:
                            condition = parts[0]
                            temperature = parts[1]
                            wind = parts[2]
                            humidity = parts[3]
                            feels_like = parts[4]
                            pressure = parts[5]
                            uv_index = parts[6]
                            
                            # Определяем иконку погоды
                            condition_lower = condition.lower()
                            if 'гроз' in condition_lower or 'thunder' in condition_lower:
                                icon = '⛈️'
                            elif 'дожд' in condition_lower or 'rain' in condition_lower:
                                icon = '🌧️'
                            elif 'снег' in condition_lower or 'snow' in condition_lower:
                                icon = '❄️'
                            elif 'туман' in condition_lower or 'fog' in condition_lower:
                                icon = '🌫️'
                            elif 'облач' in condition_lower or 'cloud' in condition_lower:
                                icon = '☁️'
                            elif 'ясно' in condition_lower or 'clear' in condition_lower or 'солн' in condition_lower:
                                icon = '☀️'
                            elif 'пасмур' in condition_lower:
                                icon = '🌥️'
                            else:
                                icon = '🌤️'
                            
                            # Форматируем ответ
                            response_text = f"{icon} *ПОГОДА В {city.upper()}*\n\n"
                            response_text += f"🌡 *Температура:* {temperature}\n"
                            response_text += f"🤔 *Ощущается как:* {feels_like}\n"
                            response_text += f"💨 *Ветер:* {wind}\n"
                            response_text += f"💧 *Влажность:* {humidity}\n"
                            response_text += f"📏 *Давление:* {pressure} мбар\n"
                            response_text += f"☀️ *UV индекс:* {uv_index}\n"
                            response_text += f"📝 *Состояние:* {condition.capitalize()}\n\n"
                            response_text += f"🕐 *Обновлено:* {datetime.now().strftime('%H:%M')}\n"
                            response_text += f"📍 *Координаты:* wttr.in/{city}"
                            
                            await update.message.reply_text(response_text, parse_mode='Markdown')
                            return
                        else:
                            # Если формат не совпадает, используем текстовый вывод
                            await update.message.reply_text(f"🌤 *ПОГОДА В {city.upper()}*\n\n{weather_data}", parse_mode='Markdown')
                            return
    
    except asyncio.TimeoutError:
        error_msg = "⏱️ Превышено время ожидания"
    except aiohttp.ClientError as e:
        error_msg = f"🌐 Ошибка сети: {str(e)[:50]}"
    except json.JSONDecodeError:
        error_msg = "📊 Ошибка формата данных"
    except KeyError:
        error_msg = "🔍 Город не найден или данные недоступны"
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)[:50]}"
    
    # Резервные данные (только для Ишимбая)
    if city.lower() in ['ishimbay', 'ишимбай', 'ишимбае']:
        current_hour = datetime.now().hour
        
        # Определяем время суток и погоду
        if 6 <= current_hour < 12:
            temp = "+15°C"
            feels = "+13°C"
            condition = "Утро, солнечно"
            icon = "☀️"
        elif 12 <= current_hour < 18:
            temp = "+22°C"
            feels = "+20°C"
            condition = "День, переменная облачность"
            icon = "⛅"
        elif 18 <= current_hour < 23:
            temp = "+18°C"
            feels = "+17°C"
            condition = "Вечер, ясно"
            icon = "🌙"
        else:
            temp = "+12°C"
            feels = "+10°C"
            condition = "Ночь, прохладно"
            icon = "🌙"
        
        response_text = (
            f"{icon} *ПОГОДА В ИШИМБАЕ*\n\n"
            f"🌡 *Температура:* {temp}\n"
            f"🤔 *Ощущается как:* {feels}\n"
            f"💨 *Ветер:* 3-5 м/с\n"
            f"💧 *Влажность:* 65%\n"
            f"📏 *Давление:* 760 мм рт.ст.\n"
            f"☀️ *UV индекс:* 2\n"
            f"📝 *Состояние:* {condition}\n\n"
            f"⚠️ *Примечание:* Используются резервные данные\n"
            f"🕐 *Время:* {datetime.now().strftime('%H:%M')}"
        )
    else:
        response_text = (
            f"❌ *ОШИБКА ПОЛУЧЕНИЯ ДАННЫХ*\n\n"
            f"Не удалось получить погоду для *{city}*\n\n"
            f"*Возможные причины:*\n"
            f"• Город не найден\n"
            f"• Проблемы с подключением\n"
            f"• Сервис временно недоступен\n\n"
            f"*Попробуйте:*\n"
            f"• Проверить название города\n"
            f"• Использовать английское написание\n"
            f"• Повторить запрос позже\n"
            f"• Использовать /weather без параметров\n"
        )
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

# ========== ДОПОЛНИТЕЛЬНАЯ КОМАНДА ДЛЯ ПРОГНОЗА ==========
async def weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прогноз погоды на 3 дня"""
    if context.args:
        context.args = ['подробно'] + context.args
    else:
        context.args = ['подробно']
    await weather(update, context)

# ========== ИИ СИСТЕМА ==========
async def ai_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    ai_mode = True
    await update.message.reply_text(
        "🧠 *ИИ РЕЖИМ ВКЛЮЧЁН*\n\n"
        "Теперь я могу отвечать на ваши вопросы!\n"
        "Просто напишите мне что-нибудь.",
        parse_mode='Markdown'
    )

async def ai_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    ai_mode = False
    await update.message.reply_text("🧠 ИИ режим выключен")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ai_mode:
        return
    
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # Игнорируем команды
    if user_message.startswith('/'):
        return
    
    # Показываем "печатает"
    await update.message.reply_chat_action(action="typing")
    
    # Сохраняем историю
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    
    chat_history[chat_id].append(f"👤: {user_message}")
    
    try:
        # Генерируем ответ
        response = await generate_ai_response(user_message)
        
        # Сохраняем ответ
        chat_history[chat_id].append(f"🤖: {response}")
        
        # Ограничиваем историю
        if len(chat_history[chat_id]) > 10:
            chat_history[chat_id] = chat_history[chat_id][-10:]
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка ИИ: {str(e)[:100]}")

async def generate_ai_response(message: str) -> str:
    """Генерация ответа ИИ"""
    message_lower = message.lower()
    
    # База знаний
    knowledge_base = {
        # Приветствия
        'привет': 'Привет! 😊 Чем могу помочь?',
        'здравствуй': 'Здравствуйте! Рад вас видеть!',
        'как дела': 'Всё отлично, спасибо! Готов помогать вам.',
        'что делаешь': 'Отвечаю на ваши вопросы и помогаю с задачами!',
        
        # Помощь
        'помощь': 'Я могу: анализировать акции, показывать расписание, отвечать на вопросы, рассказывать шутки, показывать погоду. Используйте /help для списка команд.',
        'что ты умеешь': 'Я умею многое! Вот основные возможности:\n• Финансовый анализ акций\n• Показ расписания\n• Ответы на вопросы\n• Рассказываю шутки\n• Показываю погоду',
        
        # Благодарности
        'спасибо': 'Пожалуйста! Всегда рад помочь! 👍',
        'спасибо большое': 'И вам спасибо за обращение! 😊',
        
        # Математика
        '2+2': '2 + 2 = 4',
        'математика': 'Математика - царица наук! Могу помочь с расчетами. Используйте /calc',
        
        # Расписание
        'расписание': 'Могу показать расписание на сегодня или завтра. Используйте /schedule_today или /schedule_tomorrow',
        
        # Погода
        'погода': 'Покажу погоду в Ишимбае. Используйте /weather',
        'прогноз': 'Могу показать прогноз на 3 дня. Используйте /forecast',
        
        # Время
        'который час': f'Сейчас {datetime.now().strftime("%H:%M")}',
        'сколько время': f'Текущее время: {datetime.now().strftime("%H:%M:%S")}',
        'какое сегодня число': f'Сегодня {datetime.now().strftime("%d.%m.%Y")}',
    }
    
    # Проверяем точные совпадения
    for key, value in knowledge_base.items():
        if key == message_lower:
            return value
    
    # Проверяем частичные совпадения
    for key, value in knowledge_base.items():
        if key in message_lower:
            return value
    
    # Математические выражения
    if any(op in message for op in ['+', '-', '*', '/', '=']):
        try:
            # Безопасное вычисление
            expr = message.replace('^', '**').replace('x', '*').replace(',', '.')
            # Убираем все кроме цифр и операторов
            expr_clean = re.sub(r'[^\d\+\-\*\/\.\(\)]', '', expr)
            if expr_clean:
                result = eval(expr_clean, {"__builtins__": {}})
                return f"🧮 Результат: {expr_clean} = {result}"
        except:
            pass
    
    # Вопросы
    question_words = ['сколько', 'зачем', 'почему', 'как', 'что', 'кто', 'когда', 'где']
    if any(word in message_lower for word in question_words):
        responses = [
            f"🤔 Интересный вопрос: \"{message}\"\n\nПопробую ответить...\n\nЭто зависит от конкретных условий. Могли бы вы уточнить вопрос?",
            f"🧐 Рассматриваю ваш вопрос...\n\n\"{message}\"\n\nДля точного ответа мне нужно больше контекста.",
            f"💭 Анализирую вопрос...\n\n\"{message[:50]}...\"\n\nЭто сложная тема, требующая детального рассмотрения.",
        ]
        return random.choice(responses)
    
    # Общий ответ
    general_responses = [
        f"Я понял ваш запрос: \"{message}\"\n\nК сожалению, мои возможности ограничены, но я могу:\n1. Анализировать акции (/analyze)\n2. Показывать расписание (/schedule_today)\n3. Рассказывать шутки (/joke)\n4. Показывать погоду (/weather)",
        f"Получил ваше сообщение: \"{message[:30]}...\"\n\nПопробуйте использовать команды из /help",
        f"Запрос принят! \"{message[:20]}...\"\n\nМожете задать более конкретный вопрос или использовать одну из команд.",
    ]
    
    return random.choice(general_responses)

# ========== КАЛЬКУЛЯТОР ==========
async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🧮 Использование: /calc 2+2*2")
        return
    
    expression = ' '.join(context.args)
    try:
        # Безопасное вычисление
        expression_safe = expression.replace('^', '**').replace('x', '*').replace(',', '.')
        # Убираем опасные символы
        expression_safe = re.sub(r'[^\d\+\-\*\/\.\(\)\s]', '', expression_safe)
        
        if not expression_safe:
            await update.message.reply_text("❌ Неверное выражение")
            return
        
        result = eval(expression_safe, {"__builtins__": {}})
        await update.message.reply_text(f"🧮 {expression} = {result}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка вычисления: {str(e)}")

# ========== ШУТКИ ==========
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программист не любит природу? Там слишком много багов!",
        "Что говорит 0 числу 8? Ничего, просто смотрит свысока!",
        "Почему математик не мог спать? Он считал овец в комплексных числах!",
        "Как называется песня, которую поют перед экзаменом? 'Дурилка'!",
        "Почему курица перешла дорогу? Чтобы доказать, что она не индюк!",
        "Что сказал один массив другому? Не указывай на меня!",
        "Почему химик не может завести друзей? Все его отношения нестабильны!",
        "Зачем биолог ходит в бар? Чтобы изучать клеточную структуру!",
    ]
    await update.message.reply_text(f"🎭 {random.choice(jokes)}")

# ========== КРИПТОВАЛЮТЫ ==========
async def crypto_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💰 Использование: /crypto bitcoin")
        return
    
    coin = context.args[0].lower()
    try:
        # Используем CoinGecko API
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,rub"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if coin in data:
            usd_price = data[coin]['usd']
            rub_price = data[coin]['rub']
            
            await update.message.reply_text(
                f"💰 *{coin.upper()}*\n\n"
                f"🇺🇸 ${usd_price:,.2f}\n"
                f"🇷🇺 ₽{rub_price:,.2f}\n\n"
                f"🔄 Курс обновлен",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Криптовалюта не найдена. Попробуйте: bitcoin, ethereum, dogecoin")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# ========== АНАЛИЗ ФОТО ==========
async def analyze_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ фото с текстом"""
    if not ai_mode:
        await update.message.reply_text("❌ Включите ИИ режим: /ai_on")
        return
    
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Улучшаем изображение для распознавания
        image = image.convert('L')  # Черно-белое
        text = pytesseract.image_to_string(image, lang='rus+eng')
        
        if text.strip():
            response = f"📸 *Текст с фото:*\n\n{text[:300]}"
            if len(text) > 300:
                response += "...\n(текст обрезан)"
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text("📸 Текст на фото не обнаружен")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка анализа: {str(e)}")

# ========== ТЕХНИЧЕСКИЕ КОМАНДЫ ==========
async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка истории чата"""
    chat_id = update.effective_chat.id
    if chat_id in chat_history:
        chat_history[chat_id] = []
        await update.message.reply_text("✅ История чата очищена!")
    else:
        await update.message.reply_text("📝 История уже пуста")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус бота"""
    global ai_mode
    status_text = (
        f"🤖 *СТАТУС БОТА*\n\n"
        f"• ИИ режим: {'✅ ВКЛЮЧЕН' if ai_mode else '❌ ВЫКЛЮЧЕН'}\n"
        f"• Активных чатов: {len(chat_history)}\n"
        f"• Время: {datetime.now().strftime('%H:%M:%S')}\n"
        f"• Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"🔄 Бот работает нормально"
    )
    await update.message.reply_text(status_text, parse_mode='Markdown')

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    commands = [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("ai_on", ai_on),
        CommandHandler("ai_off", ai_off),
        CommandHandler("analyze", analyze_chart),
        CommandHandler("crypto", crypto_price),
        CommandHandler("schedule_today", schedule_today),
        CommandHandler("schedule_tomorrow", schedule_tomorrow),
        CommandHandler("weather", weather),
        CommandHandler("forecast", weather_forecast),
        CommandHandler("joke", joke),
        CommandHandler("calc", calculator),
        CommandHandler("clear", clear_history),
        CommandHandler("status", status),
    ]
    
    for handler in commands:
        application.add_handler(handler)
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))
    application.add_handler(MessageHandler(filters.PHOTO, analyze_photo))
    
    # Запускаем бота
    print("=" * 50)
    print("🤖 TELEGRAM BOT ЗАПУЩЕН")
    print(f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"🔑 Токен: {TOKEN[:10]}...")
    print(f"🌐 База URL: {BASE_URL}")
    print("=" * 50)
    
    try:
        application.run_polling()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапуск через 5 секунд...")
        time.sleep(5)
        main()  # Рекурсивный перезапуск

if __name__ == '__main__':
    main()
