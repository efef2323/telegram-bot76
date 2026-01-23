@echo off
chcp 65001
title Pocket Option Trading Bot - Денис Никита
echo =========================================
echo      ЗАПУСК ТОРГОВОГО БОТА POCKET OPTION
echo =========================================
echo.

echo Проверка установки Python...
python --version
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Установите Python с сайта python.org
    pause
    exit /b 1
)

echo Проверка установки библиотек...
python -c "import selenium, undetected_chromedriver" >nul 2>&1
if errorlevel 1 (
    echo Библиотеки не установлены. Запускаю установку...
    call install_requirements.bat
)

echo.
echo Запуск основного скрипта...
echo.
python main_bot.py

echo.
pause
