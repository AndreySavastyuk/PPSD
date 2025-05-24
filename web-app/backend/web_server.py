#!/usr/bin/env python3
"""
Flask веб-сервер для системы ППСД
Обслуживает веб-интерфейс и проксирует запросы к API
"""

import os
import sys
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for
from flask_cors import CORS
import requests
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
CORS(app)

# Конфигурация
API_BASE_URL = 'http://localhost:8000'
WEB_PORT = 5000

@app.route('/')
def index():
    """Главная страница веб-интерфейса"""
    return render_template('index.html')

@app.route('/api/<path:endpoint>')
def proxy_api(endpoint):
    """Прокси для API запросов"""
    try:
        # Формируем URL для API
        api_url = f"{API_BASE_URL}/{endpoint}"
        
        # Передаем параметры запроса
        params = request.args.to_dict()
        
        # Выполняем запрос к API
        if request.method == 'GET':
            response = requests.get(api_url, params=params)
        elif request.method == 'POST':
            response = requests.post(api_url, json=request.json, params=params)
        elif request.method == 'PUT':
            response = requests.put(api_url, json=request.json, params=params)
        elif request.method == 'DELETE':
            response = requests.delete(api_url, params=params)
        else:
            return jsonify({'error': 'Method not allowed'}), 405
        
        # Возвращаем ответ от API
        return response.json(), response.status_code
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'API server is not available',
            'message': 'Убедитесь, что API сервер запущен на порту 8000'
        }), 503
    except Exception as e:
        return jsonify({
            'error': 'Proxy error',
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Проверка состояния веб-сервера"""
    try:
        # Проверяем доступность API
        api_response = requests.get(f"{API_BASE_URL}/", timeout=5)
        api_status = "OK" if api_response.status_code == 200 else "ERROR"
    except:
        api_status = "UNAVAILABLE"
    
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'web_server': 'OK',
        'api_server': api_status,
        'version': '1.0.0'
    })

@app.route('/about')
def about():
    """Страница информации о системе"""
    return render_template('about.html')

@app.route('/login')
def login():
    """Страница входа (заглушка)"""
    return render_template('login.html')

@app.errorhandler(404)
def not_found(error):
    """Обработчик 404 ошибки"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500 ошибки"""
    return render_template('500.html'), 500

def check_api_server():
    """Проверка доступности API сервера"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    print(f"🚀 Запуск веб-сервера ППСД на порту {WEB_PORT}")
    print(f"🔗 Интерфейс: http://localhost:{WEB_PORT}")
    print(f"🌐 API: {API_BASE_URL}")
    
    # Проверяем доступность API
    if check_api_server():
        print("✅ API сервер доступен")
    else:
        print("⚠️  API сервер недоступен. Запустите его командой: uvicorn api:app --reload")
    
    print("-" * 50)
    
    app.run(
        host='0.0.0.0',
        port=WEB_PORT,
        debug=True,
        threaded=True
    ) 