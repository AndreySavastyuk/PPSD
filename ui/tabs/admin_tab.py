from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                             QFormLayout, QMessageBox, QHeaderView, QTabWidget,
                             QGroupBox, QCheckBox, QDialog, QDialogButtonBox,
                             QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.connection import SessionLocal
from models.models import User, UserRole
from utils.auth import create_user, update_user
from sqlalchemy import desc
from ui.themes import theme_manager
from ui.styles import (apply_button_style, apply_input_style, apply_combobox_style, 
                       apply_table_style, refresh_table_style)
from ui.icons.icon_provider import IconProvider

class AdminTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.init_ui()
    
    def refresh_styles(self):
        """Обновить стили после смены темы"""
        try:
            # Обновляем стили таблиц
            if hasattr(self, 'users_table'):
                refresh_table_style(self.users_table)
            if hasattr(self, 'logs_table'):
                refresh_table_style(self.logs_table)
                
            # Обновляем другие элементы при необходимости
            self.update()
        except Exception as e:
            print(f"Ошибка обновления стилей в admin_tab: {e}")
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Create title with modern стиль
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Администрирование системы")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Create tab widget for different admin sections with flexible sizing
        self.admin_tabs = QTabWidget()
        self.admin_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Create toolbar with flexible layout
        toolbar_widget = QFrame()
        toolbar_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)
        
        # Add user button
        self.add_user_btn = QPushButton("Добавить пользователя")
        self.add_user_btn.setIcon(IconProvider.create_user_icon())
        apply_button_style(self.add_user_btn, 'primary')
        self.add_user_btn.clicked.connect(self.show_add_user_dialog)
        toolbar_layout.addWidget(self.add_user_btn)
        
        # Добавляем растяжку для разделения кнопок и поиска
        toolbar_layout.addStretch()
        
        # Search field с иконкой
        search_widget = QFrame()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(4, 4, 4, 4)
        search_layout.setSpacing(4)
        
        search_icon_label = QLabel()
        search_icon_label.setPixmap(IconProvider.create_search_icon().pixmap(16, 16))
        search_layout.addWidget(search_icon_label)
        
        self.users_search_input = QLineEdit()
        self.users_search_input.setPlaceholderText("Поиск пользователей...")
        apply_input_style(self.users_search_input, 'search')
        self.users_search_input.textChanged.connect(self.filter_users)
        search_layout.addWidget(self.users_search_input)
        
        toolbar_layout.addWidget(search_widget)
        
        # Refresh button
        self.users_refresh_btn = QPushButton("Обновить")
        self.users_refresh_btn.setIcon(IconProvider.create_refresh_icon())
        apply_button_style(self.users_refresh_btn, 'default')
        self.users_refresh_btn.clicked.connect(self.load_users)
        toolbar_layout.addWidget(self.users_refresh_btn)
        
        layout.addWidget(toolbar_widget)
        
        # Container for table with flexible sizing
        table_container = QFrame()
        table_container.setFrameStyle(QFrame.Shape.StyledPanel)
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)
        
        # Table title
        table_title = QLabel("Пользователи системы")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_layout.addWidget(table_title)
        
        # Create users table с гибкими размерами
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Имя пользователя", "Полное имя", "Роль", "Активен", 
            "Редактирование", "Удаление"
        ])
        
        # Применяем гибкие стили к таблице
        apply_table_style(self.users_table)
        
        # Set column resize modes для лучшей адаптивности
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Имя пользователя - растягивается
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Полное имя - растягивается
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Роль
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Активен
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Редактирование
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Удаление
        
        # Connect double click
        self.users_table.cellDoubleClicked.connect(self.show_edit_user_dialog)
        
        table_layout.addWidget(self.users_table)
        
        # Add table status row
        status_layout = QHBoxLayout()
        
        self.users_status_label = QLabel("Загрузка данных...")
        status_layout.addWidget(self.users_status_label)
        
        status_layout.addStretch()
        
        self.users_count_label = QLabel("Пользователей: 0")
        self.users_count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_layout.addWidget(self.users_count_label)
        
        table_layout.addLayout(status_layout)
        
        layout.addWidget(table_container, 1)  # 1 = stretch factor для расширения таблицы
        
        # Load users
        self.load_users()
    
    def setup_settings_tab(self):
        """Setup the system settings tab"""
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Create settings form с гибким layout
        settings_group = QGroupBox("Настройки системы")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Directory settings с адаптивными полями
        cert_path_input = QLineEdit("docs_storage/certificates")
        apply_input_style(cert_path_input)
        settings_layout.addRow("Каталог для сертификатов:", cert_path_input)
        
        reports_path_input = QLineEdit("docs_storage/test_reports")
        apply_input_style(reports_path_input)
        settings_layout.addRow("Каталог для отчетов:", reports_path_input)
        
        requests_path_input = QLineEdit("docs_storage/sample_requests")
        apply_input_style(requests_path_input)
        settings_layout.addRow("Каталог для заявок:", requests_path_input)
        
        layout.addWidget(settings_group)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Save button
        save_settings_btn = QPushButton("Сохранить настройки")
        save_settings_btn.setIcon(IconProvider.create_save_icon())
        apply_button_style(save_settings_btn, 'primary')
        save_settings_btn.clicked.connect(lambda: QMessageBox.information(self, "Функция в разработке", 
                                      "Сохранение настроек находится в разработке."))
        buttons_layout.addWidget(save_settings_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def setup_logs_tab(self):
        """Setup the logs tab"""
        layout = QVBoxLayout(self.logs_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Create toolbar с гибким layout
        toolbar_widget = QFrame()
        toolbar_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)
        
        # Date filter
        date_label = QLabel("Дата:")
        toolbar_layout.addWidget(date_label)
        
        date_filter = QComboBox()
        date_filter.addItems(["Все", "Сегодня", "Неделя", "Месяц"])
        apply_combobox_style(date_filter)
        toolbar_layout.addWidget(date_filter)
        
        # User filter
        user_label = QLabel("Пользователь:")
        toolbar_layout.addWidget(user_label)
        
        user_filter = QComboBox()
        user_filter.addItems(["Все пользователи"])
        apply_combobox_style(user_filter)
        toolbar_layout.addWidget(user_filter)
        
        toolbar_layout.addStretch()
        
        # Refresh button
        self.logs_refresh_btn = QPushButton("Обновить")
        self.logs_refresh_btn.setIcon(IconProvider.create_refresh_icon())
        apply_button_style(self.logs_refresh_btn, 'default')
        toolbar_layout.addWidget(self.logs_refresh_btn)
        
        layout.addWidget(toolbar_widget)
        
        # Container for table
        table_container = QFrame()
        table_container.setFrameStyle(QFrame.Shape.StyledPanel)
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)
        
        # Table title
        table_title = QLabel("Журнал событий")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_layout.addWidget(table_title)
        
        # Create logs table с гибкими размерами
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Дата/время", "Пользователь", "Действие", "Объект", "Результат"
        ])
        
        # Применяем гибкие стили к таблице
        apply_table_style(self.logs_table)
        
        # Set column resize modes
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Дата/время
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Пользователь
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Действие - растягивается
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Объект - растягивается
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Результат
        
        table_layout.addWidget(self.logs_table)
        
        # Placeholder message
        placeholder_label = QLabel("Функция журналирования находится в разработке.")
        placeholder_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Normal))
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(placeholder_label)
        
        layout.addWidget(table_container, 1)  # 1 = stretch factor
    
    def load_users(self):
        """Load users from database"""
        self.users_status_label.setText("Загрузка данных...")
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
                    UserRole.LAB.value: "Инженер ЦЗЛ",
                    UserRole.PRODUCTION.value: "Производство"
                }.get(user.role, user.role)
                self.users_table.setItem(row, 3, QTableWidgetItem(role_display))
                
                # Active status
                self.users_table.setItem(row, 4, QTableWidgetItem("Да" if user.is_active else "Нет"))
                
                # Permissions
                self.users_table.setItem(row, 5, QTableWidgetItem("Да" if user.can_edit else "Нет"))
                self.users_table.setItem(row, 6, QTableWidgetItem("Да" if user.can_delete else "Нет"))
            
            # Update status
            self.parent.status_bar.showMessage(f"Загружено {len(users)} пользователей")
            self.users_status_label.setText("Данные загружены")
            self.users_count_label.setText(f"Пользователей: {len(users)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке пользователей: {str(e)}")
            self.users_status_label.setText("Ошибка загрузки")
        finally:
            db.close()
    
    def filter_users(self):
        """Filter users by search text"""
        search_text = self.users_search_input.text().lower()
        
        visible_count = 0
        
        for row in range(self.users_table.rowCount()):
            show_row = True
            
            # Check if row matches search text
            if search_text:
                match_found = False
                for col in range(3):  # Проверяем ID, имя пользователя и полное имя
                    item = self.users_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                if not match_found:
                    show_row = False
            
            # Show/hide row
            self.users_table.setRowHidden(row, not show_row)
            
            if show_row:
                visible_count += 1
        
        # Update status
        if search_text:
            self.users_status_label.setText(f"Отфильтровано: {search_text}")
            self.users_count_label.setText(f"Показано: {visible_count} / {self.users_table.rowCount()}")
        else:
            self.users_status_label.setText("Все пользователи")
            self.users_count_label.setText(f"Пользователей: {self.users_table.rowCount()}")
    
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