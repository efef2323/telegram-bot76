@echo off
chcp 65001
echo =========================================
echo    УСТАНОВКА БИБЛИОТЕК ДЛЯ ТОРГОВОГО БОТА
echo =========================================
echo.

echo 1. Обновление pip...
python -m pip install --upgrade pip
echo.

echo 2. Установка Selenium...
pip install selenium==4.15.0
echo.

echo 3. Установка undetected-chromedriver...
pip install undetected-chromedriver==3.5.4
echo.

echo 4. Установка webdriver-manager...
pip install webdriver-manager==3.8.6
echo.

echo 5. Установка дополнительных библиотек...
pip install numpy==1.24.3
pip install pandas==2.0.3
echo.

echo =========================================
echo          УСТАНОВКА ЗАВЕРШЕНА!
echo =========================================
echo.
echo Теперь можно запустить бота:
echo 1. Дважды кликните на start_bot.bat
echo 2. Или запустите вручную: python main_bot.py
echo.
pause
