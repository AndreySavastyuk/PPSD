from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                             QFormLayout, QMessageBox, QHeaderView, QTabWidget,
                             QGroupBox, QCheckBox, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.connection import SessionLocal
from models.models import User, UserRole
from utils.auth import create_user, update_user
from sqlalchemy import desc

class AdminTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create title
        title_label = QLabel("Администрирование системы")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # Create tab widget for different admin sections
        self.admin_tabs = QTabWidget()
        
        # Users tab
        self.users_tab = QWidget()
        self.setup_users_tab()
        self.admin_tabs.addTab(self.users_tab, "Пользователи")
        
        # System settings tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.admin_tabs.addTab(self.settings_tab, "Настройки системы")
        
        # Logs tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.admin_tabs.addTab(self.logs_tab, "Журнал событий")
        
        main_layout.addWidget(self.admin_tabs)
    
    def setup_users_tab(self):
        """Setup the users management tab"""
        layout = QVBoxLayout(self.users_tab)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Add user button
        self.add_user_btn = QPushButton("Добавить пользователя")
        self.add_user_btn.clicked.connect(self.show_add_user_dialog)
        toolbar_layout.addWidget(self.add_user_btn)
        
        # Search field
        self.users_search_input = QLineEdit()
        self.users_search_input.setPlaceholderText("Поиск...")
        self.users_search_input.textChanged.connect(self.filter_users)
        toolbar_layout.addWidget(self.users_search_input)
        
        # Refresh button
        self.users_refresh_btn = QPushButton("Обновить")
        self.users_refresh_btn.clicked.connect(self.load_users)
        toolbar_layout.addWidget(self.users_refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Имя пользователя", "Полное имя", "Роль", "Активен", 
            "Редактирование", "Удаление"
        ])
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Connect double click
        self.users_table.cellDoubleClicked.connect(self.show_edit_user_dialog)
        
        layout.addWidget(self.users_table)
        
        # Load users
        self.load_users()
    
    def setup_settings_tab(self):
        """Setup the system settings tab"""
        layout = QVBoxLayout(self.settings_tab)
        
        # Create settings form
        settings_group = QGroupBox("Настройки системы")
        settings_layout = QFormLayout(settings_group)
        
        # Placeholder settings
        settings_layout.addRow("Каталог для сертификатов:", QLineEdit("docs_storage/certificates"))
        settings_layout.addRow("Каталог для отчетов:", QLineEdit("docs_storage/test_reports"))
        settings_layout.addRow("Каталог для заявок:", QLineEdit("docs_storage/sample_requests"))
        
        # Save button
        save_settings_btn = QPushButton("Сохранить настройки")
        save_settings_btn.clicked.connect(lambda: QMessageBox.information(self, "Функция в разработке", 
                                      "Сохранение настроек находится в разработке."))
        
        layout.addWidget(settings_group)
        layout.addWidget(save_settings_btn)
        layout.addStretch()
    
    def setup_logs_tab(self):
        """Setup the logs tab"""
        layout = QVBoxLayout(self.logs_tab)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Date filter
        toolbar_layout.addWidget(QLabel("Дата:"))
        toolbar_layout.addWidget(QComboBox())
        
        # User filter
        toolbar_layout.addWidget(QLabel("Пользователь:"))
        toolbar_layout.addWidget(QComboBox())
        
        # Refresh button
        self.logs_refresh_btn = QPushButton("Обновить")
        toolbar_layout.addWidget(self.logs_refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Дата/время", "Пользователь", "Действие", "Объект", "Результат"
        ])
        
        # Set column widths
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.logs_table)
        
        # Placeholder message
        layout.addWidget(QLabel("Функция журналирования находится в разработке."))
    
    def load_users(self):
        """Load users from database"""
        db = SessionLocal()
        try:
            users = db.query(User).order_by(User.username).all()
            
            # Clear table
            self.users_table.setRowCount(0)
            
            # Add users to table
            for row, user in enumerate(users):
                self.users_table.insertRow(row)
                
                # Set data
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.username))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.full_name))
                
                # Role
                role_display = {
                    UserRole.ADMIN.value: "Администратор",
                    UserRole.WAREHOUSE.value: "Кладовщик",
                    UserRole.QC.value: "Сотрудник ОТК",
                    UserRole.LAB.value: "Инженер ЦЗЛ"
                }.get(user.role, user.role)
                self.users_table.setItem(row, 3, QTableWidgetItem(role_display))
                
                # Active status
                self.users_table.setItem(row, 4, QTableWidgetItem("Да" if user.is_active else "Нет"))
                
                # Permissions
                self.users_table.setItem(row, 5, QTableWidgetItem("Да" if user.can_edit else "Нет"))
                self.users_table.setItem(row, 6, QTableWidgetItem("Да" if user.can_delete else "Нет"))
            
            # Update status
            self.parent.status_bar.showMessage(f"Загружено {len(users)} пользователей")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке пользователей: {str(e)}")
        finally:
            db.close()
    
    def filter_users(self):
        """Filter users by search text"""
        search_text = self.users_search_input.text().lower()
        
        for row in range(self.users_table.rowCount()):
            show_row = True
            
            # Check if row matches search text
            if search_text:
                match_found = False
                for col in range(1, 4):  # Check username, full name, role
                    item = self.users_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                if not match_found:
                    show_row = False
            
            # Show/hide row
            self.users_table.setRowHidden(row, not show_row)
    
    def show_add_user_dialog(self):
        """Show dialog to add new user"""
        QMessageBox.information(self, "Функция в разработке", 
                             "Добавление пользователя находится в разработке.")
    
    def show_edit_user_dialog(self, row, column):
        """Show dialog to edit user"""
        user_id = self.users_table.item(row, 0).text()
        username = self.users_table.item(row, 1).text()
        
        QMessageBox.information(self, "Функция в разработке", 
                             f"Редактирование пользователя {username} (ID: {user_id}) находится в разработке.") 