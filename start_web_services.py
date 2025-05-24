#!/usr/bin/env python3
"""
Скрипт для запуска всех веб-сервисов системы ППСД
"""

import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime

def print_banner():
    """Печать баннера"""
    print("=" * 60)
    print("🏭 СИСТЕМА ПРОВЕРКИ СЕРТИФИКАТНЫХ ДАННЫХ (ППСД)")
    print("🚀 ЗАПУСК ВЕБ-СЕРВИСОВ")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print()

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'flask',
        'flask-cors',
        'pandas',
        'requests',
        'python-telegram-bot'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - НЕ УСТАНОВЛЕН")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Установите недостающие пакеты:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Все зависимости установлены")
    return True

def start_service(name, command, cwd=None):
    """Запуск сервиса"""
    print(f"🚀 Запуск {name}...")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Небольшая задержка для проверки запуска
        time.sleep(2)
        
        if process.poll() is None:
            print(f"  ✅ {name} запущен (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"  ❌ Ошибка запуска {name}")
            print(f"     STDOUT: {stdout}")
            print(f"     STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"  ❌ Ошибка запуска {name}: {e}")
        return None

def monitor_service(name, process):
    """Мониторинг сервиса"""
    try:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[{name}] {output.strip()}")
    except:
        pass

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    print()
    
    # Словарь для хранения процессов
    processes = {}
    monitor_threads = []
    
    # Настройка переменных окружения
    os.environ['PYTHONPATH'] = os.getcwd()
    
    # Сервисы для запуска
    services = [
        {
            'name': 'Основной API (FastAPI)',
            'command': 'python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000',
            'port': 8000,
            'url': 'http://localhost:8000'
        },
        {
            'name': 'Аналитический API',
            'command': 'python web-app/backend/analytics_api.py',
            'port': 8001,
            'url': 'http://localhost:8001'
        },
        {
            'name': 'Веб-интерфейс (Flask)',
            'command': 'python web-app/backend/web_server.py',
            'port': 5000,
            'url': 'http://localhost:5000'
        }
    ]
    
    print("🎯 ПЛАН ЗАПУСКА:")
    for service in services:
        print(f"  • {service['name']} - {service['url']}")
    print()
    
    # Запускаем сервисы
    for service in services:
        process = start_service(service['name'], service['command'])
        if process:
            processes[service['name']] = process
            
            # Запускаем мониторинг в отдельном потоке
            monitor_thread = threading.Thread(
                target=monitor_service,
                args=(service['name'], process),
                daemon=True
            )
            monitor_thread.start()
            monitor_threads.append(monitor_thread)
        
        time.sleep(1)
    
    print()
    print("🌐 ВЕБ-СЕРВИСЫ ЗАПУЩЕНЫ:")
    print("-" * 40)
    for service in services:
        if service['name'] in processes:
            print(f"✅ {service['name']}")
            print(f"   🔗 {service['url']}")
            if 'docs' in service.get('features', []):
                print(f"   📚 {service['url']}/docs")
        else:
            print(f"❌ {service['name']} - НЕ ЗАПУЩЕН")
    
    print()
    print("📋 ПОЛЕЗНЫЕ ССЫЛКИ:")
    print("   🏠 Главная страница:        http://localhost:5000")
    print("   📊 Дашборд аналитики:       http://localhost:5000/dashboard")
    print("   🔧 API документация:        http://localhost:8000/docs")
    print("   📈 Аналитический API:       http://localhost:8001/docs")
    
    print()
    print("💡 КОМАНДЫ УПРАВЛЕНИЯ:")
    print("   Ctrl+C - Остановить все сервисы")
    print("   docker-compose up - Альтернативный запуск через Docker")
    
    # Опциональный запуск Telegram бота
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token:
        print("\n🤖 Запуск Telegram бота...")
        bot_process = start_service(
            'Telegram Bot',
            'python web-app/backend/notifications.py'
        )
        if bot_process:
            processes['Telegram Bot'] = bot_process
    else:
        print("\n⚠️  TELEGRAM_BOT_TOKEN не установлен. Telegram бот не запущен.")
        print("   Установите токен: export TELEGRAM_BOT_TOKEN=your_token")
    
    print()
    print("🎉 ВСЕ СЕРВИСЫ ГОТОВЫ К РАБОТЕ!")
    print("🔍 Логи сервисов отображаются ниже...")
    print("=" * 60)
    
    # Обработчик сигналов для корректного завершения
    def signal_handler(sig, frame):
        print("\n\n🛑 ОСТАНОВКА СЕРВИСОВ...")
        for name, process in processes.items():
            try:
                print(f"   ⏹️  Остановка {name}...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
            except:
                pass
        print("✅ Все сервисы остановлены")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ожидание завершения
    try:
        while True:
            time.sleep(1)
            # Проверяем, что все процессы еще работают
            for name, process in list(processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  Процесс {name} завершился неожиданно")
                    del processes[name]
            
            if not processes:
                print("❌ Все процессы завершились")
                break
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == '__main__':
    main() 