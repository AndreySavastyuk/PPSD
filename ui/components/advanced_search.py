"""
Расширенная система поиска и фильтрации для ППСД
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFrame,
                             QDateEdit, QCheckBox, QGroupBox, QGridLayout,
                             QScrollArea, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider
from models.models import MaterialStatus

class AdvancedSearchWidget(QFrame):
    """Виджет расширенного поиска с множественными фильтрами"""
    
    search_requested = Signal(dict)  # Сигнал с параметрами поиска
    filters_cleared = Signal()
    
    def __init__(self, search_type="materials"):
        super().__init__()
        self.search_type = search_type
        self.filters = {}
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Расширенный поиск")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Кнопка сворачивания/разворачивания
        self.toggle_btn = QPushButton("Скрыть")
        self.toggle_btn.setIcon(IconProvider.create_filter_icon())
        self.toggle_btn.clicked.connect(self.toggle_visibility)
        header_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(header_layout)
        
        # Контейнер для фильтров
        self.filters_container = QFrame()
        self.create_filters_content()
        layout.addWidget(self.filters_container)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        search_btn = QPushButton("Найти")
        search_btn.setIcon(IconProvider.create_search_icon())
        search_btn.clicked.connect(self.perform_search)
        search_btn.setStyleSheet(theme_manager.get_button_style('primary'))
        actions_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_filters)
        clear_btn.setStyleSheet(theme_manager.get_button_style('neutral'))
        actions_layout.addWidget(clear_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
    
    def create_filters_content(self):
        """Создание содержимого фильтров"""
        layout = QVBoxLayout(self.filters_container)
        layout.setSpacing(16)
        
        # Создаем прокручиваемую область для фильтров
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        if self.search_type == "materials":
            self.create_material_filters(scroll_layout)
        elif self.search_type == "samples":
            self.create_sample_filters(scroll_layout)
        elif self.search_type == "tests":
            self.create_test_filters(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def create_material_filters(self, layout):
        """Создание фильтров для материалов"""
        # Основная информация
        basic_group = QGroupBox("Основная информация")
        basic_layout = QGridLayout(basic_group)
        
        # Поиск по тексту
        basic_layout.addWidget(QLabel("Поиск по тексту:"), 0, 0)
        self.text_search = QLineEdit()
        self.text_search.setPlaceholderText("Номер партии, марка, поставщик...")
        basic_layout.addWidget(self.text_search, 0, 1, 1, 2)
        
        # Марка материала
        basic_layout.addWidget(QLabel("Марка материала:"), 1, 0)
        self.material_grade = QComboBox()
        self.material_grade.addItem("Все марки", "")
        basic_layout.addWidget(self.material_grade, 1, 1)
        
        # Тип продукта
        basic_layout.addWidget(QLabel("Тип продукта:"), 1, 2)
        self.product_type = QComboBox()
        self.product_type.addItem("Все типы", "")
        basic_layout.addWidget(self.product_type, 1, 3)
        
        # Поставщик
        basic_layout.addWidget(QLabel("Поставщик:"), 2, 0)
        self.supplier = QComboBox()
        self.supplier.addItem("Все поставщики", "")
        basic_layout.addWidget(self.supplier, 2, 1, 1, 2)
        
        layout.addWidget(basic_group)
        
        # Статус и даты
        status_group = QGroupBox("Статус и даты")
        status_layout = QGridLayout(status_group)
        
        # Статус
        status_layout.addWidget(QLabel("Статус:"), 0, 0)
        self.status_group = QButtonGroup()
        status_h_layout = QHBoxLayout()
        
        all_status_radio = QRadioButton("Все")
        all_status_radio.setChecked(True)
        self.status_group.addButton(all_status_radio, -1)
        status_h_layout.addWidget(all_status_radio)
        
        for i, status in enumerate(MaterialStatus):
            radio = QRadioButton(status.value)
            self.status_group.addButton(radio, i)
            status_h_layout.addWidget(radio)
        
        status_h_layout.addStretch()
        status_layout.addLayout(status_h_layout, 0, 1, 1, 3)
        
        # Дата поступления
        status_layout.addWidget(QLabel("Дата поступления:"), 1, 0)
        status_layout.addWidget(QLabel("с"), 1, 1)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        status_layout.addWidget(self.date_from, 1, 2)
        
        status_layout.addWidget(QLabel("по"), 1, 3)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        status_layout.addWidget(self.date_to, 1, 4)
        
        layout.addWidget(status_group)
        
        # Дополнительные параметры
        additional_group = QGroupBox("Дополнительные параметры")
        additional_layout = QGridLayout(additional_group)
        
        # Размеры
        additional_layout.addWidget(QLabel("Диаметр/толщина:"), 0, 0)
        self.size_from = QLineEdit()
        self.size_from.setPlaceholderText("от")
        additional_layout.addWidget(self.size_from, 0, 1)
        
        additional_layout.addWidget(QLabel("до"), 0, 2)
        self.size_to = QLineEdit()
        self.size_to.setPlaceholderText("до")
        additional_layout.addWidget(self.size_to, 0, 3)
        
        # Чекбоксы для дополнительных условий
        self.has_certificate = QCheckBox("Только с сертификатами")
        additional_layout.addWidget(self.has_certificate, 1, 0, 1, 2)
        
        self.has_samples = QCheckBox("Только с образцами")
        additional_layout.addWidget(self.has_samples, 1, 2, 1, 2)
        
        self.critical_only = QCheckBox("Только критичные")
        additional_layout.addWidget(self.critical_only, 2, 0, 1, 2)
        
        layout.addWidget(additional_group)
    
    def create_sample_filters(self, layout):
        """Создание фильтров для образцов"""
        # Основная информация
        basic_group = QGroupBox("Информация об образце")
        basic_layout = QGridLayout(basic_group)
        
        # Код образца
        basic_layout.addWidget(QLabel("Код образца:"), 0, 0)
        self.sample_code = QLineEdit()
        self.sample_code.setPlaceholderText("Введите код образца")
        basic_layout.addWidget(self.sample_code, 0, 1, 1, 2)
        
        # Статус образца
        basic_layout.addWidget(QLabel("Статус:"), 1, 0)
        self.sample_status = QComboBox()
        self.sample_status.addItems(["Все статусы", "Создан", "В испытаниях", "Завершен"])
        basic_layout.addWidget(self.sample_status, 1, 1)
        
        layout.addWidget(basic_group)
    
    def create_test_filters(self, layout):
        """Создание фильтров для испытаний"""
        # Информация об испытаниях
        test_group = QGroupBox("Параметры испытаний")
        test_layout = QGridLayout(test_group)
        
        # Тип испытания
        test_layout.addWidget(QLabel("Тип испытания:"), 0, 0)
        self.test_type = QComboBox()
        self.test_type.addItem("Все типы", "")
        test_layout.addWidget(self.test_type, 0, 1)
        
        # Результат
        test_layout.addWidget(QLabel("Результат:"), 0, 2)
        self.test_result = QComboBox()
        self.test_result.addItems(["Все результаты", "Соответствует", "Не соответствует", "В процессе"])
        test_layout.addWidget(self.test_result, 0, 3)
        
        layout.addWidget(test_group)
    
    def toggle_visibility(self):
        """Переключение видимости фильтров"""
        if self.filters_container.isVisible():
            self.filters_container.hide()
            self.toggle_btn.setText("Показать")
        else:
            self.filters_container.show()
            self.toggle_btn.setText("Скрыть")
    
    def perform_search(self):
        """Выполнение поиска с текущими фильтрами"""
        filters = self.get_current_filters()
        self.search_requested.emit(filters)
    
    def get_current_filters(self) -> dict:
        """Получение текущих фильтров"""
        filters = {}
        
        if self.search_type == "materials":
            if hasattr(self, 'text_search') and self.text_search.text():
                filters['text_search'] = self.text_search.text()
            
            if hasattr(self, 'material_grade') and self.material_grade.currentData():
                filters['material_grade'] = self.material_grade.currentData()
            
            if hasattr(self, 'product_type') and self.product_type.currentData():
                filters['product_type'] = self.product_type.currentData()
            
            if hasattr(self, 'supplier') and self.supplier.currentData():
                filters['supplier'] = self.supplier.currentData()
            
            # Статус
            if hasattr(self, 'status_group'):
                checked_id = self.status_group.checkedId()
                if checked_id >= 0:
                    filters['status'] = list(MaterialStatus)[checked_id]
            
            # Даты
            if hasattr(self, 'date_from'):
                filters['date_from'] = self.date_from.date().toPython()
            if hasattr(self, 'date_to'):
                filters['date_to'] = self.date_to.date().toPython()
            
            # Размеры
            if hasattr(self, 'size_from') and self.size_from.text():
                try:
                    filters['size_from'] = float(self.size_from.text())
                except ValueError:
                    pass
            
            if hasattr(self, 'size_to') and self.size_to.text():
                try:
                    filters['size_to'] = float(self.size_to.text())
                except ValueError:
                    pass
            
            # Чекбоксы
            if hasattr(self, 'has_certificate'):
                filters['has_certificate'] = self.has_certificate.isChecked()
            if hasattr(self, 'has_samples'):
                filters['has_samples'] = self.has_samples.isChecked()
            if hasattr(self, 'critical_only'):
                filters['critical_only'] = self.critical_only.isChecked()
        
        elif self.search_type == "samples":
            if hasattr(self, 'sample_code') and self.sample_code.text():
                filters['sample_code'] = self.sample_code.text()
            if hasattr(self, 'sample_status') and self.sample_status.currentIndex() > 0:
                filters['sample_status'] = self.sample_status.currentText()
        
        elif self.search_type == "tests":
            if hasattr(self, 'test_type') and self.test_type.currentData():
                filters['test_type'] = self.test_type.currentData()
            if hasattr(self, 'test_result') and self.test_result.currentIndex() > 0:
                filters['test_result'] = self.test_result.currentText()
        
        return filters
    
    def clear_filters(self):
        """Очистка всех фильтров"""
        # Очищаем текстовые поля
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        
        # Сбрасываем комбобоксы
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(0)
        
        # Сбрасываем чекбоксы
        for widget in self.findChildren(QCheckBox):
            widget.setChecked(False)
        
        # Сбрасываем радиокнопки
        if hasattr(self, 'status_group'):
            self.status_group.button(-1).setChecked(True)
        
        # Сбрасываем даты
        if hasattr(self, 'date_from'):
            self.date_from.setDate(QDate.currentDate().addDays(-30))
        if hasattr(self, 'date_to'):
            self.date_to.setDate(QDate.currentDate())
        
        self.filters_cleared.emit()
    
    def apply_styles(self):
        """Применение стилей"""
        colors = theme_manager.get_current_theme()['colors']
        
        self.setStyleSheet(f"""
        AdvancedSearchWidget {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
        }}
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {colors['border']};
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 8px;
            color: {colors['text_primary']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {colors['text_primary']};
        }}
        """)
        
        # Применяем стили для полей ввода через theme_manager
        input_style = theme_manager.get_input_style()
        
        # Применяем стили ко всем полям ввода
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(input_style)
        
        for widget in self.findChildren(QComboBox):
            widget.setStyleSheet(input_style)
            
        for widget in self.findChildren(QDateEdit):
            widget.setStyleSheet(input_style)

class QuickSearchBar(QWidget):
    """Быстрая строка поиска"""
    
    search_requested = Signal(str)
    
    def __init__(self, placeholder="Быстрый поиск..."):
        super().__init__()
        self.init_ui(placeholder)
    
    def init_ui(self, placeholder):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        search_btn = QPushButton()
        search_btn.setIcon(IconProvider.create_search_icon())
        search_btn.setFixedSize(32, 32)
        search_btn.clicked.connect(self.perform_search)
        search_btn.setStyleSheet(theme_manager.get_button_style('primary'))
        layout.addWidget(search_btn)
    
    def perform_search(self):
        """Выполнение быстрого поиска"""
        text = self.search_input.text().strip()
        if text:
            self.search_requested.emit(text)
    
    def clear(self):
        """Очистка поля поиска"""
        self.search_input.clear() 