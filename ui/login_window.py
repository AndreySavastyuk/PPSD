import sys
import os
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QMessageBox, QFrame, QComboBox)
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtCore import Qt

from database.connection import SessionLocal
from utils.auth import authenticate_user
from sqlalchemy import text
from models.models import UserRole, User
from ui.themes import theme_manager
from ui.notifications import notification_manager

# Настройка логирования для входа
login_logger = logging.getLogger('login')

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window properties
        self.setWindowTitle("ППСД - Вход в систему")
        self.setMinimumSize(400, 300)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Применяем тему
        self.setStyleSheet(theme_manager.generate_stylesheet())
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Add header
        header_label = QLabel("Система проверки сертификатных данных")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add subtitle
        subtitle_label = QLabel("Авторизация пользователя")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        # Create login form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 10, 30, 10)
        form_layout.setSpacing(10)
        
        # Username field
        username_label = QLabel("Имя пользователя:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Login button
        self.login_button = QPushButton("Войти")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet(theme_manager.get_button_style('primary'))
        form_layout.addWidget(self.login_button)
        
        # Role selection for test login
        test_login_container = QWidget()
        test_login_layout = QHBoxLayout(test_login_container)
        test_login_layout.setContentsMargins(0, 0, 0, 0)

        self.role_combo = QComboBox()
        self.role_combo.addItem("Кладовщик", UserRole.WAREHOUSE.value)
        self.role_combo.addItem("Сотрудник ОТК", UserRole.QC.value)
        self.role_combo.addItem("Инженер ЦЗЛ", UserRole.LAB.value)
        self.role_combo.addItem("Производство", UserRole.PRODUCTION.value)
        self.role_combo.addItem("Администратор", UserRole.ADMIN.value)
        test_login_layout.addWidget(self.role_combo)
        
        # Test login button
        self.test_login_button = QPushButton("Тестовый вход (без пароля)")
        self.test_login_button.setMinimumHeight(30)
        self.test_login_button.clicked.connect(self.test_login)
        self.test_login_button.setStyleSheet(theme_manager.get_button_style('secondary'))
        test_login_layout.addWidget(self.test_login_button)
        
        form_layout.addWidget(test_login_container)
        
        # Add form to main layout
        main_layout.addWidget(form_container)
        main_layout.addStretch()
        
        # Add footer
        footer_label = QLabel("© 2023 ППСД")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)
        
        # Connect enter key to login
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        
        # Стилизация полей ввода
        self.username_input.setStyleSheet(theme_manager.get_input_style())
        self.password_input.setStyleSheet(theme_manager.get_input_style())
        
        # Set initial focus
        self.username_input.setFocus()
    
    def login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        login_logger.info(f"Попытка входа пользователя: {username}")
        print(f"[LOGIN] Попытка входа пользователя: {username}")
        
        if not username or not password:
            error_msg = "Пожалуйста, введите имя пользователя и пароль."
            login_logger.warning(f"Пустые поля: username='{username}', password='{bool(password)}'")
            print(f"[LOGIN] Ошибка: {error_msg}")
            notification_manager.show_warning(error_msg, parent_widget=self)
            return
        
        # Authenticate user
        db = SessionLocal()
        try:
            login_logger.info(f"Подключение к базе данных установлено")
            print(f"[LOGIN] Подключение к базе данных установлено")
            
            # Сначала проверим, есть ли пользователь в базе
            user_exists = db.query(User).filter(User.username == username).first()
            if not user_exists:
                login_logger.warning(f"Пользователь '{username}' не найден в базе данных")
                print(f"[LOGIN] Пользователь '{username}' не найден в базе данных")
            else:
                login_logger.info(f"Пользователь '{username}' найден. Роль: {user_exists.role}, Активен: {user_exists.is_active}")
                print(f"[LOGIN] Пользователь '{username}' найден. Роль: {user_exists.role}, Активен: {user_exists.is_active}")
            
            user = authenticate_user(db, username, password)
            
            if user:
                # Login successful
                success_msg = f"Добро пожаловать, {user.full_name}!"
                login_logger.info(f"Вход выполнен успешно: {user.full_name} (роль: {user.role})")
                print(f"[LOGIN] Успешный вход: {user.full_name} (роль: {user.role})")
                notification_manager.show_success(success_msg, parent_widget=self)
                
                # Import here to avoid circular imports
                from ui.main_window import MainWindow
                
                # Open main window
                self.main_window = MainWindow(user)
                self.main_window.show()
                self.close()
            else:
                # Login failed
                error_msg = "Неверное имя пользователя или пароль."
                login_logger.error(f"Неудачная попытка входа для пользователя: {username}")
                print(f"[LOGIN] Ошибка аутентификации для пользователя: {username}")
                notification_manager.show_error(error_msg, parent_widget=self)
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            error_msg = f"Ошибка при входе в систему: {str(e)}"
            login_logger.error(f"Исключение при входе: {str(e)}", exc_info=True)
            print(f"[LOGIN] Критическая ошибка: {str(e)}")
            notification_manager.show_error(error_msg, parent_widget=self)
        finally:
            db.close()
            login_logger.info("Подключение к базе данных закрыто")
            print(f"[LOGIN] Подключение к базе данных закрыто")

    def test_login(self):
        """Войти как тестовый пользователь (без пароля) с выбранной ролью"""
        selected_role = self.role_combo.currentData()
        
        login_logger.info(f"Попытка тестового входа с ролью: {selected_role}")
        print(f"[TEST_LOGIN] Попытка тестового входа с ролью: {selected_role}")
        
        db = SessionLocal()
        try:
            login_logger.info(f"Подключение к базе данных установлено для тестового входа")
            print(f"[TEST_LOGIN] Подключение к базе данных установлено")
            
            # Ищем активного пользователя с выбранной ролью
            user = db.execute(
                text(f"SELECT * FROM users WHERE role='{selected_role}' AND is_active=1 LIMIT 1")
            ).fetchone()
            
            login_logger.info(f"Поиск пользователя с ролью '{selected_role}': {'найден' if user else 'не найден'}")
            print(f"[TEST_LOGIN] Поиск пользователя с ролью '{selected_role}': {'найден' if user else 'не найден'}")
            
            # Если нет пользователя с выбранной ролью, берем любого активного
            if not user:
                user = db.execute(text("SELECT * FROM users WHERE is_active=1 LIMIT 1")).fetchone()
                login_logger.info(f"Поиск любого активного пользователя: {'найден' if user else 'не найден'}")
                print(f"[TEST_LOGIN] Поиск любого активного пользователя: {'найден' if user else 'не найден'}")
                
            if user:
                from ui.main_window import MainWindow
                # Получаем ORM-объект
                orm_user = db.query(User).filter(User.id == user.id).first()
                
                success_msg = f"Тестовый вход выполнен: {orm_user.full_name}"
                login_logger.info(f"Тестовый вход успешен: {orm_user.full_name} (роль: {orm_user.role})")
                print(f"[TEST_LOGIN] Успешный тестовый вход: {orm_user.full_name} (роль: {orm_user.role})")
                notification_manager.show_success(success_msg, parent_widget=self)
                
                self.main_window = MainWindow(orm_user)
                self.main_window.show()
                self.close()
            else:
                error_msg = "Нет активных пользователей для тестового входа."
                login_logger.error("Не найдено активных пользователей в базе данных")
                print(f"[TEST_LOGIN] Ошибка: нет активных пользователей")
                notification_manager.show_error(error_msg, parent_widget=self)
        except Exception as e:
            error_msg = f"Ошибка при тестовом входе: {str(e)}"
            login_logger.error(f"Исключение при тестовом входе: {str(e)}", exc_info=True)
            print(f"[TEST_LOGIN] Критическая ошибка: {str(e)}")
            notification_manager.show_error(error_msg, parent_widget=self)
        finally:
            db.close()
            login_logger.info("Подключение к базе данных закрыто для тестового входа")
            print(f"[TEST_LOGIN] Подключение к базе данных закрыто")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())