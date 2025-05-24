"""
Скрипт для выполнения миграций базы данных
"""
import os
import sys
import datetime

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import Base, engine, SessionLocal
from sqlalchemy import inspect, text
from models.models import *  # Импортируем все модели
from scripts.migrations.update_sample_requests import run_migration as update_sample_requests
from scripts.migrations.add_samples_tables import run_migration as add_samples_tables

def run_migrations():
    """Выполнить миграции базы данных"""
    inspector = inspect(engine)
    
    # Получаем список существующих таблиц
    existing_tables = inspector.get_table_names()
    print(f"Существующие таблицы: {existing_tables}")
    
    # Создаем все таблицы, которых еще нет
    Base.metadata.create_all(bind=engine)
    print("Созданы все таблицы, указанные в моделях")
    
    # Проверяем наличие столбцов в таблице qc_checks
    if 'qc_checks' in existing_tables:
        columns = {col['name'] for col in inspector.get_columns('qc_checks')}
        print(f"Столбцы в таблице qc_checks: {columns}")
        
        # Проверяем наличие столбцов для химического состава
        chem_columns = {'chem_c', 'chem_si', 'chem_mn', 'chem_s', 'chem_p', 'chem_cr', 
                      'chem_ni', 'chem_cu', 'chem_ti', 'chem_al', 'chem_mo', 'chem_v', 'chem_nb'}
        
        missing_columns = chem_columns - columns
        if missing_columns:
            print(f"Отсутствующие столбцы: {missing_columns}")
            print("Требуется обновление структуры таблицы.")
            
            try:
                # В SQLite ALTER TABLE добавляет только один столбец за операцию
                # Поэтому нам нужно создать новую таблицу и скопировать данные
                backup_table_name = f"qc_checks_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"Создаем резервную копию таблицы: {backup_table_name}")
                
                # Создаем новую таблицу с обновленной схемой
                print("Пересоздаем таблицу с новой схемой...")
                
                # Используем правильный метод для выполнения SQL-запросов
                with engine.connect() as connection:
                    connection.execute(text(f"ALTER TABLE qc_checks RENAME TO {backup_table_name}"))
                
                # Создаем новую таблицу с правильной схемой
                Base.metadata.create_all(bind=engine)
                
                # Копируем данные из старой таблицы в новую
                copy_columns = columns - missing_columns
                columns_str = ", ".join(copy_columns)
                
                with engine.connect() as connection:
                    connection.execute(text(f"INSERT INTO qc_checks ({columns_str}) SELECT {columns_str} FROM {backup_table_name}"))
                    connection.commit()
                
                print("Миграция данных успешно выполнена!")
            except Exception as e:
                print(f"Ошибка при обновлении таблицы: {str(e)}")
                print("Рекомендуется удалить базу данных и запустить программу заново.")
    
    # Обновляем таблицу sample_requests
    print("Обновляем таблицу sample_requests...")
    update_sample_requests()
    print("Обновление таблицы sample_requests завершено")
    
    # Добавляем таблицы samples и lab_test_samples
    print("Добавляем таблицы для образцов...")
    add_samples_tables()
    print("Добавление таблиц для образцов завершено")
    
    return True

if __name__ == "__main__":
    print("Запуск миграции базы данных...")
    success = run_migrations()
    if success:
        print("Миграция успешно завершена.")
    else:
        print("Ошибка при выполнении миграций.")
    
    # Проверяем наличие пользователя admin
    db = SessionLocal()
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        print("Создаем пользователя admin...")
        admin = User(
            username='admin',
            password_hash='$2b$12$MtmYHYgbQpQtUZmYZU7.4eGZO/IwfZ9TQiHqeLE4EZ4bgCKgKNDLm',  # Пароль 'admin'
            full_name='Администратор системы',
            role='admin',
            can_edit=True,
            can_view=True,
            can_delete=True,
            can_admin=True
        )
        db.add(admin)
        db.commit()
        print("Пользователь admin создан!")
    else:
        print("Пользователь admin уже существует.") 