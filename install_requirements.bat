@echo off
echo Установка необходимых библиотек...
echo.

python -m pip install --upgrade pip

pip install selenium==4.15.0
pip install webdriver-manager==3.8.6
pip install numpy==1.24.3
pip install pandas==2.0.3

echo.
echo Установка завершена!
echo.
pause
