from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import time
import os
import io
from datetime import datetime, timedelta

TOKEN = os.environ.get('BOT_TOKEN', '8531196180:AAHTRMQ1dgNqbdnJM9Cy4ByoCv6FPlzpYsI')
BASE_URL = 'http://ishnk.ru/2025/site/schedule/group/520/'

async def schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')
    await send_screenshot(update, today, "сегодня")

async def schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    await send_screenshot(update, tomorrow, "завтра")

async def send_screenshot(update: Update, date_str: str, day_name: str):
    url = f"{BASE_URL}{date_str}"
    
    await update.message.reply_text(f"📅 Делаю скриншот на {day_name}...")
    
    # СПИСОК РАБОЧИХ API ДЛЯ СКРИНШОТОВ (пробуем все)
    screenshot_apis = [
        # 1. Google Render-Tron (бесплатный)
        f"https://render-tron.appspot.com/screenshot/{url}?width=1200&height=800",
        
        # 2. ApiFlash (бесплатный демо)
        f"https://api.apiflash.com/v1/urltoimage?access_key=demo&url={url}&width=1920&height=1080&full_page=true",
        
        # 3. ScreenshotAPI.net (бесплатный демо)
        f"https://screenshotapi.net/api/v1/screenshot?url={url}&width=1200&fresh=true&token=demo",
        
        # 4. Placeholder если все API не работают
        None
    ]
    
    for api_url in screenshot_apis:
        try:
            if api_url is None:
                # Последний вариант - делаем через Selenium (упрощенный)
                await send_selenium_screenshot(update, url, date_str, day_name)
                return
                
            print(f"🔄 Пробую API: {api_url[:50]}...")
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 5000:  # Проверяем что не пустой
                # Отправляем фото
                await update.message.reply_photo(
                    photo=response.content,
                    caption=f"📅 Расписание на {day_name}\n📅 Дата: {date_str}\n🔗 {url}"
                )
                print(f"✅ Скриншот отправлен через API")
                return
                
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            continue
    
    # Если все API не сработали, используем последний вариант
    await update.message.reply_text(
        f"📅 *Расписание на {day_name}*\n\n"
        f"📅 Дата: {date_str}\n"
        f"🔗 {url}\n\n"
        f"⚠️ API скриншотов временно не работают",
        parse_mode='Markdown'
    )

async def send_selenium_screenshot(update: Update, url: str, date_str: str, day_name: str):
    """Резервный вариант через Selenium с оптимизацией"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Ключевое: добавляем user-agent и ждем дольше
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Увеличиваем таймауты
        driver.set_page_load_timeout(60)
        
        driver.get(url)
        
        # Ждем ДОЛЬШЕ и делаем несколько действий
        time.sleep(8)  # Увеличенное ожидание
        
        # Прокручиваем страницу чтобы прогрузилась
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        
        # Проверяем что скриншот не белый (средняя яркость)
        from PIL import Image
        import numpy as np
        import io as io_module
        
        img = Image.open(io_module.BytesIO(screenshot))
        img_gray = img.convert('L')
        brightness = np.array(img_gray).mean()
        
        if brightness > 240:  # Если слишком белый (почти 255)
            raise Exception("Скриншот слишком белый")
        
        await update.message.reply_photo(
            photo=screenshot,
            caption=f"📅 Расписание на {day_name}\n📅 Дата: {date_str}\n🔗 {url}"
        )
        
    except Exception as e:
        print(f"❌ Ошибка Selenium: {e}")
        # Отправляем просто ссылку
        await update.message.reply_text(f"📅 Ссылка на расписание: {url}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Бот для скриншотов расписания\n\n"
        "Команды:\n"
        "/schedule_today - скриншот на сегодня\n"
        "/schedule_tomorrow - скриншот на завтра"
    )

def main():
    print("🤖 Бот запущен")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedule_today", schedule_today))
    app.add_handler(CommandHandler("schedule_tomorrow", schedule_tomorrow))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
