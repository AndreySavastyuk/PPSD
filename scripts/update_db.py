import os
import sys
import sqlite3

# Добавим путь к корневой директории проекта, чтобы импорты работали корректно
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, Base
from models.models import TestType

def update_lab_tests_table():
    """Добавляет новую колонку test_type_id в таблицу lab_tests"""
    print("Обновление структуры базы данных...")
    
    # Подключение к базе данных SQLite
    conn = sqlite3.connect("database/ppsd.db")
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(lab_tests)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Добавляем колонку test_type_id, если её нет
        if "test_type_id" not in column_names:
            print("Добавление колонки test_type_id в таблицу lab_tests...")
            cursor.execute("ALTER TABLE lab_tests ADD COLUMN test_type_id INTEGER")
            print("Колонка test_type_id успешно добавлена")
        else:
            print("Колонка test_type_id уже существует")
        
        # Проверяем, существует ли таблица test_types
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_types'")
        test_types_exists = cursor.fetchone()
        
        if not test_types_exists:
            print("Создание таблицы test_types...")
            # Создаем таблицу test_types
            Base.metadata.tables["test_types"].create(bind=engine)
            print("Таблица test_types успешно создана")
        else:
            print("Таблица test_types уже существует")
            
        conn.commit()
        print("Обновление структуры базы данных завершено успешно")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при обновлении структуры базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_lab_tests_table() 