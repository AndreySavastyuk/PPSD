"""
Скрипт для обновления структуры базы данных
Делает поле batch_number необязательным и добавляет флаг no_melt_number
"""
import os
import sys
import logging
import datetime

# Добавляем корневой каталог проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from sqlalchemy import Column, DateTime, text, inspect, Boolean
from database.connection import engine, Base, SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_columns():
    """Обновляет колонки batch_number и добавляет флаг no_melt_number"""
    logger.info("Начало обновления базы данных...")
    
    session = SessionLocal()
    connection = engine.connect()
    
    try:
        # Получаем информацию о таблице
        inspector = inspect(engine)
        
        # Обновляем batch_number, делая его nullable, и добавляем no_melt_number
        logger.info("Изменение структуры таблицы material_entries...")
        
        # Отключаем внешние ключи
        connection.execute(text("PRAGMA foreign_keys=off"))
        
        # Начинаем транзакцию
        connection.execute(text("BEGIN TRANSACTION"))
        
        # Создаем новую временную таблицу
        connection.execute(text("""
        CREATE TABLE material_entries_temp (
            id INTEGER PRIMARY KEY,
            material_grade VARCHAR(50) NOT NULL,
            material_type VARCHAR(20) NOT NULL,
            thickness FLOAT,
            width FLOAT,
            length FLOAT,
            diameter FLOAT,
            wall_thickness FLOAT,
            quantity FLOAT NOT NULL,
            unit VARCHAR(10) DEFAULT 'кг',
            certificate_number VARCHAR(100) NOT NULL,
            certificate_date DATETIME,
            batch_number VARCHAR(100),  -- Делаем необязательным (было NOT NULL)
            melt_number VARCHAR(100) NOT NULL,
            order_number VARCHAR(100),
            certificate_file_path VARCHAR(255),
            status VARCHAR(30) DEFAULT 'received',
            requires_lab_verification BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            supplier_id INTEGER NOT NULL,
            created_by_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            grade_id INTEGER,
            type_id INTEGER,
            no_melt_number BOOLEAN DEFAULT FALSE, -- Добавляем новую колонку
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
            FOREIGN KEY (created_by_id) REFERENCES users (id),
            FOREIGN KEY (grade_id) REFERENCES material_grades (id),
            FOREIGN KEY (type_id) REFERENCES product_types (id)
        )
        """))
        
        # Копируем данные, инициализируя no_melt_number как FALSE для существующих записей
        connection.execute(text("""
        INSERT INTO material_entries_temp 
        SELECT id, material_grade, material_type, thickness, width, length, diameter, 
               wall_thickness, quantity, unit, certificate_number, certificate_date, 
               batch_number, melt_number, order_number, certificate_file_path, status,
               requires_lab_verification, is_deleted, supplier_id, created_by_id, 
               created_at, updated_at, grade_id, type_id, FALSE
        FROM material_entries
        """))
        
        # Удаляем старую таблицу
        connection.execute(text("DROP TABLE material_entries"))
        
        # Переименовываем временную таблицу
        connection.execute(text("ALTER TABLE material_entries_temp RENAME TO material_entries"))
        
        # Пересоздаем индексы
        connection.execute(text("CREATE INDEX ix_material_entries_id ON material_entries (id)"))
        
        # Завершаем транзакцию
        connection.execute(text("COMMIT"))
        
        # Включаем обратно внешние ключи
        connection.execute(text("PRAGMA foreign_keys=on"))
        
        logger.info("Обновление базы данных завершено успешно!")
        
    except Exception as e:
        connection.execute(text("ROLLBACK"))
        logger.error(f"Ошибка при обновлении базы данных: {str(e)}")
        raise
    finally:
        connection.close()
        session.close()

if __name__ == "__main__":
    update_columns() 