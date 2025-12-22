from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import time
import os
import io
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get('BOT_TOKEN', '8531196180:AAHTRMQ1dgNqbdnJM9Cy4ByoCv6FPlzpYsI')
BASE_URL = 'http://ishnk.ru/2025/site/schedule/group/520/'

# ========== РАСПИСАНИЕ С СЕЛЕНИУМОМ (РАБОТАЕТ НА RENDER) ==========
async def schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_date = datetime.now().strftime('%Y-%m-%d')
    await get_schedule_selenium(update, today_date, "сегодня")

async def schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    await get_schedule_selenium(update, tomorrow_date, "завтра")

async def get_schedule_selenium(update: Update, date_str: str, day_name: str):
    """Создает скриншот через Selenium - работает на Render"""
    url = f"{BASE_URL}{date_str}"
    
    await update.message.reply_text(f"📅 Делаю скриншот расписания на {day_name}...")
    
    driver = None
    try:
        # НАСТРОЙКИ ДЛЯ RENDER
        chrome_options = Options()
        
        # Обязательные настройки для работы на Render
        chrome_options.add_argument('--headless=new')  # Новый headless режим
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Указываем пути к Chrome на Render
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Создаем драйвер с настройками
        driver = webdriver.Chrome(options=chrome_options)
        
        # Устанавливаем таймауты
        driver.set_page_load_timeout(45)
        driver.implicitly_wait(10)
        
        print(f"🔄 Загружаю страницу: {url}")
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(5)
        
        # Проверяем, что страница загрузилась
        print(f"📄 Заголовок страницы: {driver.title}")
        
        # Делаем скриншот
        print("📸 Делаю скриншот...")
        screenshot = driver.get_screenshot_as_png()
        
        # Конвертируем в bytes для Telegram
        photo_bytes = io.BytesIO(screenshot)
        photo_bytes.name = f'schedule_{date_str}.png'
        
        # Отправляем фото
        await update.message.reply_photo(
            photo=photo_bytes,
            caption=f"📅 Расписание на {day_name}\n📅 Дата: {date_str}\n🔗 {url}"
        )
        print(f"✅ Скриншот отправлен!")
        
    except Exception as e:
        print(f"❌ Ошибка Selenium: {str(e)}")
        # Если не удалось сделать скриншот, отправляем ссылку
        await update.message.reply_text(
            f"📅 *Расписание на {day_name}*\n\n"
            f"Не удалось сделать скриншот\n"
            f"🔗 Ссылка: {url}",
            parse_mode='Markdown'
        )
    
    finally:
        # Всегда закрываем драйвер
        if driver:
            try:
                driver.quit()
                print("🚪 Драйвер закрыт")
            except:
                pass

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Бот со скриншотами расписания!\n\n"
        "📋 Команды:\n"
        "/schedule_today - скриншот расписания на сегодня\n"
        "/schedule_tomorrow - скриншот на завтра\n"
        "/weather - погода\n"
        "/joke - шутка"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "🤖 *ДОСТУПНЫЕ КОМАНДЫ:*\n\n"
    help_text += "/start - Начать\n"
    help_text += "/schedule_today - Скриншот расписания сегодня\n"
    help_text += "/schedule_tomorrow - Скриншот расписания завтра\n"
    help_text += "/weather - Погода\n"
    help_text += "/joke - Шутка"
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌤 *ПОГОДА В ИШИМБАЕ*\n\n🌡 +18°C\n📝 Облачно\n💨 3 м/с", parse_mode='Markdown')

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программист не любит природу? Там слишком много багов!",
        "Что говорит 0 числу 8? Ничего, просто смотрит свысока!",
        "Почему курица перешла дорогу? Чтобы доказать, что она не индюк!",
    ]
    await update.message.reply_text(f"🎭 {random.choice(jokes)}")

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота - минимальная версия"""
    print("=" * 50)
    print("🤖 TELEGRAM BOT СО СКРИНШОТАМИ ЗАПУЩЕН")
    print(f"🔑 Токен: {TOKEN[:10]}...")
    print(f"🌐 База URL: {BASE_URL}")
    print("=" * 50)
    
    # Простое создание приложения БЕЗ лишних параметров
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    commands = [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("schedule_today", schedule_today),
        CommandHandler("schedule_tomorrow", schedule_tomorrow),
        CommandHandler("weather", weather),
        CommandHandler("joke", joke),
    ]
    
    for handler in commands:
        application.add_handler(handler)
    
    # Запуск polling с минимальными параметрами
    try:
        print("🔄 Запускаю polling...")
        application.run_polling(
            drop_pending_updates=True,  # Важно для избежания конфликтов
            close_loop=False
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("🔄 Перезапуск через 10 секунд...")
        time.sleep(10)
        main()

if __name__ == '__main__':
    # Задержка перед запуском для завершения старых процессов
    print("⏳ Ожидание 10 секунд перед запуском...")
    time.sleep(10)
    main()
