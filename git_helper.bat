@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM --- Определяем путь к скрипту ---
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM --- Красивый заголовок ---
echo.
echo ╔════════════════════════════════════════╗
echo ║     Git Helper - Помощник по Git       ║
echo ╚════════════════════════════════════════╝
echo.

REM --- Проверяем наличие Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    echo    Скачать: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM --- Проверяем/создаем виртуальное окружение ---
if not exist "venv\" (
    echo 🔹 Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Не удалось создать виртуальное окружение!
        pause
        exit /b 1
    )
    echo ✅ Виртуальное окружение создано!
    echo.
) else (
    echo ✅ Виртуальное окружение найдено
    echo.
)

REM --- Активируем виртуальное окружение ---
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Не удалось активировать виртуальное окружение!
    pause
    exit /b 1
)

:menu
REM --- Главное меню ---
echo.
echo ╔════════════════════════════════════════╗
echo ║           Выберите действие:           ║
echo ╠════════════════════════════════════════╣
echo ║  1  Создать SSH ключ                   ║
echo ║  2  Удалить SSH ключ                   ║
echo ║  3  Клонировать репозиторий            ║
echo ║  4  Выход                              ║
echo ╚════════════════════════════════════════╝
echo.

set /p "choice=Введите номер (1-4): "

if "%choice%"=="1" goto create_ssh_key
if "%choice%"=="2" goto delete_ssh_key
if "%choice%"=="3" goto clone_repo
if "%choice%"=="4" goto exit_script

echo ❌ Неверный выбор! Попробуйте снова.
goto menu

:create_ssh_key
echo.
echo ════════════════════════════════════════
echo 🔹 Запуск создания SSH ключа...
echo ════════════════════════════════════════
echo.
python "%SCRIPT_DIR%src\create_ssh_key.py"
set "exit_code=!errorlevel!"
echo.
if !exit_code! neq 0 echo ❌ Создание SSH ключа завершено с ошибкой
echo.
pause
goto menu

:delete_ssh_key
echo.
echo ════════════════════════════════════════
echo 🔹 Запуск удаления SSH ключа...
echo ════════════════════════════════════════
echo.
python "%SCRIPT_DIR%src\delete_ssh_key.py"
set "exit_code=!errorlevel!"
echo.
if !exit_code! neq 0 (
    echo ❌ Удаление завершено с ошибкой или отменено
) else (
    echo ✅ SSH ключ успешно удален
)
echo.
pause
goto menu

:clone_repo
echo.
echo ════════════════════════════════════════
echo 🔹 Запуск клонирования репозитория...
echo ════════════════════════════════════════
echo.
python "%SCRIPT_DIR%src\clone_repository.py"
set "exit_code=!errorlevel!"
echo.
if !exit_code! neq 0 (
    echo ❌ Клонирование завершено с ошибкой
) else (
    echo ✅ Репозиторий успешно склонирован
)
echo.
pause
goto menu

:exit_script
echo.
echo 👋 До свидания!
call venv\Scripts\deactivate.bat 2>nul
exit /b 0
