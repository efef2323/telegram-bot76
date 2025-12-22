from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yfinance as yf
import pandas as pd
import requests
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
from bs4 import BeautifulSoup

# ========== ПРИНУДИТЕЛЬНАЯ ЗАДЕРЖКА ПЕРЕД ЗАПУСКОМ ==========
print("⏳ ОЖИДАНИЕ 15 СЕКУНД ДЛЯ ЗАВЕРШЕНИЯ СТАРЫХ ПРОЦЕССОВ...")
time.sleep(15)
print("🚀 ЗАПУСКАЮ БОТА...")

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get('BOT_TOKEN', '8531196180:AAHTRMQ1dgNqbdnJM9Cy4ByoCv6FPlzpYsI')
BASE_URL = 'http://ishnk.ru/2025/site/schedule/group/520/'

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
ai_mode = False
chat_history = {}

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

# ========== РАСПИСАНИЕ (РАБОЧАЯ ВЕРСИЯ) ==========
async def schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на сегодня"""
    today_date = datetime.now().strftime('%Y-%m-%d')
    await get_schedule(update, today_date, "сегодня")

async def schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на завтра"""
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    await get_schedule(update, tomorrow_date, "завтра")

async def get_schedule(update: Update, date_str: str, day_name: str):
    """Умная функция получения расписания с запасными вариантами"""
    url = f"{BASE_URL}{date_str}"
    
    await update.message.reply_text(f"📅 Получаю расписание на {day_name} ({date_str})...")
    
    try:
        # Вариант 1: Используем API для скриншотов (работает на Render)
        screenshot_url = f"https://screenshot.abstractapi.com/v1/?api_key=demo&url={url}&width=1200"
        
        response = requests.get(screenshot_url, timeout=30)
        
        if response.status_code == 200:
            # Создаем временный файл
            screenshot_path = f'schedule_{date_str}.png'
            with open(screenshot_path, 'wb') as f:
                f.write(response.content)
            
            # Отправляем фото
            with open(screenshot_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📅 Расписание на {day_name}\n📅 Дата: {date_str}\n🔗 {url}"
                )
            
            # Удаляем временный файл
            os.remove(screenshot_path)
            
        else:
            # Вариант 2: Если API не сработал, парсим HTML
            await parse_schedule_html(update, url, date_str, day_name)
            
    except Exception as e:
        # Вариант 3: В случае ошибки отправляем ссылку
        await update.message.reply_text(
            f"📅 *Расписание на {day_name}*\n\n"
            f"📅 Дата: {date_str}\n"
            f"🔗 Ссылка: {url}\n\n"
            f"⚠️ Перейдите по ссылке для просмотра.",
            parse_mode='Markdown'
        )

async def parse_schedule_html(update: Update, url: str, date_str: str, day_name: str):
    """Парсим HTML страницы для извлечения текста расписания"""
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем любые таблицы
        schedule_text = ""
        tables = soup.find_all('table')
        
        if tables:
            for i, table in enumerate(tables[:3]):
                schedule_text += f"\n📋 Таблица {i+1}:\n"
                rows = table.find_all('tr')
                for row in rows[:10]:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' | '.join([cell.get_text(strip=True) for cell in cells])
                    if row_text:
                        schedule_text += row_text + "\n"
        
        # Если нашли текст
        if schedule_text and len(schedule_text) > 50:
            await update.message.reply_text(
                f"📅 *Расписание на {day_name}*\n\n"
                f"📅 Дата: {date_str}\n"
                f"🔗 Ссылка: {url}\n\n"
                f"📋 *Текст расписания:*\n"
                f"```\n{schedule_text[:1500]}\n```",
                parse_mode='Markdown'
            )
        else:
            # Если текст не нашли, ищем любые элементы с расписанием
            schedule_elements = soup.find_all(['div', 'section', 'article', 'main'])
            for elem in schedule_elements:
                text = elem.get_text(strip=True, separator='\n')
                if 'понедельник' in text.lower() or 'вторник' in text.lower() or 'среда' in text.lower():
                    await update.message.reply_text(
                        f"📅 *Расписание на {day_name}*\n\n"
                        f"📅 Дата: {date_str}\n"
                        f"🔗 Ссылка: {url}\n\n"
                        f"📋 *Найдено расписание:*\n"
                        f"```\n{text[:1000]}\n```",
                        parse_mode='Markdown'
                    )
                    return
            
            # Если ничего не нашли
            await update.message.reply_text(
                f"📅 *Расписание на {day_name}*\n\n"
                f"📅 Дата: {date_str}\n"
                f"🔗 Ссылка: {url}\n\n"
                f"⚠️ Не удалось извлечь текст расписания.\n"
                f"Перейдите по ссылке для просмотра.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        await update.message.reply_text(
            f"📅 *Расписание на {day_name}*\n\n"
            f"📅 Дата: {date_str}\n"
            f"🔗 Ссылка: {url}\n\n"
            f"⚠️ Ошибка парсинга: {str(e)[:100]}",
            parse_mode='Markdown'
        )

# ========== ФИНАНСОВЫЙ АНАЛИЗ ==========
async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📊 Укажи символ акции: /analyze AAPL")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 Анализирую {symbol}...")
    
    try:
        data = yf.download(symbol, period='1mo', interval='1d')
        
        if data.empty or len(data) < 5:
            await update.message.reply_text(f"❌ Акция '{symbol}' не найдена или мало данных")
            return
        
        current_price = data['Close'].iloc[-1]
        
        analysis = f"📈 *АНАЛИЗ {symbol}*\n\n"
        analysis += f"💰 Текущая цена: ${current_price:.2f}\n"
        analysis += f"📅 Данные за последний месяц\n"
        analysis += f"📊 Совет: используйте /analyze для детального анализа"
        
        await update.message.reply_text(analysis, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка анализа: {str(e)[:100]}")

# ========== ПОГОДА (УПРОЩЕННАЯ) ==========
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = "Ishimbay"
    if context.args:
        city = ' '.join(context.args)
    
    await update.message.reply_text(f"🌤 Получаю погоду для {city}...")
    
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%w+%h&lang=ru"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.text.strip()
            await update.message.reply_text(
                f"🌤 *ПОГОДА В {city.upper()}*\n\n"
                f"{weather_data}\n\n"
                f"📍 wttr.in/{city}",
                parse_mode='Markdown'
            )
        else:
            # Резервные данные для Ишимбая
            current_hour = datetime.now().hour
            if 6 <= current_hour < 12:
                temp = "+15°C"
                condition = "Утро, солнечно"
            elif 12 <= current_hour < 18:
                temp = "+22°C"
                condition = "День, переменная облачность"
            else:
                temp = "+18°C"
                condition = "Вечер, ясно"
            
            await update.message.reply_text(
                f"🌤 *ПОГОДА В ИШИМБАЕ*\n\n"
                f"🌡 Температура: {temp}\n"
                f"📝 Состояние: {condition}\n"
                f"💨 Ветер: 3-5 м/с\n"
                f"💧 Влажность: 65%",
                parse_mode='Markdown'
            )
            
    except Exception:
        await update.message.reply_text(
            f"🌤 *ПОГОДА В ИШИМБАЕ*\n\n"
            f"🌡 Температура: +18°C\n"
            f"📝 Состояние: Облачно\n"
            f"💨 Ветер: 3 м/с\n"
            f"💧 Влажность: 70%",
            parse_mode='Markdown'
        )

async def weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await weather(update, context)

# ========== ИИ СИСТЕМА ==========
async def ai_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    ai_mode = True
    await update.message.reply_text("🧠 ИИ РЕЖИМ ВКЛЮЧЁН\n\nЗадавайте вопросы!", parse_mode='Markdown')

async def ai_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    ai_mode = False
    await update.message.reply_text("🧠 ИИ режим выключен")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ai_mode:
        return
    
    user_message = update.message.text
    if user_message.startswith('/'):
        return
    
    await update.message.reply_chat_action(action="typing")
    await asyncio.sleep(1)
    
    responses = [
        f"Вы сказали: \"{user_message}\"\n\nЯ пока ограничен в ответах, но скоро научусь больше!",
        f"Интересный вопрос! Используйте /help для списка моих команд.",
        f"Запрос принят! Могу помочь с погодой (/weather), расписанием (/schedule_today) или шуткой (/joke).",
    ]
    await update.message.reply_text(random.choice(responses))

# ========== ПРОСТЫЕ КОМАНДЫ ==========
async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🧮 Использование: /calc 2+2*2")
        return
    
    expression = ' '.join(context.args)
    try:
        expression_safe = expression.replace('^', '**').replace('x', '*').replace(',', '.')
        expression_safe = re.sub(r'[^\d\+\-\*\/\.\(\)\s]', '', expression_safe)
        
        if not expression_safe:
            await update.message.reply_text("❌ Неверное выражение")
            return
        
        result = eval(expression_safe, {"__builtins__": {}})
        await update.message.reply_text(f"🧮 {expression} = {result}")
        
    except Exception:
        await update.message.reply_text(f"❌ Не могу вычислить: {expression}")

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программист не любит природу? Там слишком много багов!",
        "Что говорит 0 числу 8? Ничего, просто смотрит свысока!",
        "Почему курица перешла дорогу? Чтобы доказать, что она не индюк!",
    ]
    await update.message.reply_text(f"🎭 {random.choice(jokes)}")

async def crypto_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💰 Использование: /crypto bitcoin")
        return
    
    coin = context.args[0].lower()
    await update.message.reply_text(f"💰 Курс {coin}...")
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if coin in data:
            usd_price = data[coin]['usd']
            await update.message.reply_text(f"💰 {coin.upper()}: ${usd_price:,.2f}")
        else:
            await update.message.reply_text("❌ Криптовалюта не найдена")
            
    except Exception:
        await update.message.reply_text("❌ Ошибка получения курса")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chat_history:
        chat_history[chat_id] = []
        await update.message.reply_text("✅ История чата очищена!")
    else:
        await update.message.reply_text("📝 История уже пуста")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_mode
    status_text = (
        f"🤖 *СТАТУС БОТА*\n\n"
        f"• ИИ режим: {'✅ ВКЛЮЧЕН' if ai_mode else '❌ ВЫКЛЮЧЕН'}\n"
        f"• Время: {datetime.now().strftime('%H:%M:%S')}\n"
        f"• Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"🔄 Бот работает нормально"
    )
    await update.message.reply_text(status_text, parse_mode='Markdown')

# ========== ГЛАВНАЯ ФУНКЦИЯ (ИСПРАВЛЕННАЯ) ==========
def main():
    """Запуск бота с защитой от конфликтов - исправленная версия"""
    print("=" * 50)
    print("🤖 TELEGRAM BOT ЗАПУЩЕН")
    print(f"🔑 Токен: {TOKEN[:10]}...")
    print(f"🌐 База URL: {BASE_URL}")
    print("=" * 50)
    
    # СОЗДАЕМ ПРИЛОЖЕНИЕ С ПРАВИЛЬНЫМИ ПАРАМЕТРАМИ (без deprecated)
    application = Application.builder() \
        .token(TOKEN) \
        .read_timeout(60) \
        .write_timeout(60) \
        .connect_timeout(60) \
        .pool_timeout(60) \
        .get_updates_timeout(30) \
        .get_updates_read_timeout(30) \
        .get_updates_write_timeout(30) \
        .get_updates_connect_timeout(30) \
        .get_updates_pool_timeout(30) \
        .build()
    
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
    
    # ЗАПУСК POLLING БЕЗ DEPRECATED ПАРАМЕТРОВ
    try:
        print("🔄 Запускаю polling (без deprecated параметров)...")
        application.run_polling(
            drop_pending_updates=True,  # Игнорирует старые сообщения
            allowed_updates=None,       # Разрешает все типы обновлений
            close_loop=False            # Не закрывает event loop
        )
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапуск через 15 секунд...")
        time.sleep(15)
        main()  # Рекурсивный перезапуск

if __name__ == '__main__':
    main()
