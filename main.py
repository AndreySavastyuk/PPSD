import sys
import logging
import os
from PySide6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from utils.painter_fix import patch_painter
from database.connection import Base, engine
from ui.themes import theme_manager, ThemeType

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Создаем директорию для логов, если она не существует
os.makedirs("logs", exist_ok=True)

def migrate_database():
    """Выполнить миграции базы данных"""
    try:
        from scripts.run_migrations import run_migrations
        result = run_migrations()
        if result:
            logging.info("Database migration completed successfully")
        else:
            logging.error("Database migration failed")
    except Exception as e:
        logging.error(f"Error running migrations: {str(e)}")
        # Создаем базовые таблицы, даже если миграция не удалась
        Base.metadata.create_all(bind=engine)

def main():
    """Main application entry point"""
    logging.info("Starting application")
    
    # Применяем патч для QPainter
    patch_painter()
    logging.info("QPainter patch applied")
    
    # Выполняем миграции базы данных
    migrate_database()
    logging.info("Database migration completed")
    
    app = QApplication(sys.argv)
    logging.info("QApplication created")
    
    app.setStyle("Fusion")  # Используем стиль Fusion для лучшего вида
    logging.info("Style set to Fusion")
    
    # Устанавливаем тему по умолчанию
    try:
        theme_manager.set_theme(ThemeType.LIGHT)
        logging.info("Theme set to Light")
    except Exception as e:
        logging.error(f"Error setting theme: {str(e)}")
    
    try:
        # Создаем окно входа вместо главного окна
        logging.info("Creating login window")
        window = LoginWindow()
        logging.info("Login window created")
        
        window.show()
        logging.info("Login window shown")
        
        logging.info("Starting application event loop")
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Error in application startup: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 