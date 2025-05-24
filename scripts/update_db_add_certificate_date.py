"""
Скрипт для обновления структуры базы данных
Добавляет поле certificate_date в таблицу material_entries
"""
import os
import sys
import logging
import datetime

# Добавляем корневой каталог проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from sqlalchemy import Column, DateTime, text, inspect
from database.connection import engine, Base, SessionLocal
from models.models import MaterialEntry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_certificate_date_column():
    """Добавляет колонку certificate_date в таблицу material_entries"""
    logger.info("Начало обновления базы данных...")
    
    session = SessionLocal()
    connection = engine.connect()
    
    try:
        # Проверяем, существует ли уже колонка certificate_date
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('material_entries')]
        
        if 'certificate_date' not in columns:
            logger.info("Добавление колонки certificate_date в таблицу material_entries...")
            connection.execute(text("ALTER TABLE material_entries ADD COLUMN certificate_date DATETIME"))
            logger.info("Колонка certificate_date успешно добавлена.")
        else:
            logger.info("Колонка certificate_date уже существует в таблице material_entries.")
        
        connection.close()
        session.commit()
        logger.info("Обновление базы данных завершено успешно!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении базы данных: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_certificate_date_column() 