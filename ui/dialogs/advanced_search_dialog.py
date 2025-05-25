"""
Диалоговое окно расширенного поиска для ППСД
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFrame,
                             QDateEdit, QCheckBox, QGroupBox, QGridLayout,
                             QScrollArea, QButtonGroup, QRadioButton, QDialogButtonBox,
                             QSizePolicy, QWidget)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QIcon
from datetime import datetime, timedelta
from ui.themes import theme_manager
from ui.styles import apply_button_style, apply_input_style, apply_combobox_style
from ui.icons.icon_provider import IconProvider
from models.models import MaterialStatus, MaterialType
from database.connection import SessionLocal
from models.models import MaterialEntry, Supplier

class AdvancedSearchDialog(QDialog):
    """Диалоговое окно расширенного поиска"""
    
    search_requested = Signal(dict)  # Сигнал с параметрами поиска
    
    def __init__(self, search_type="materials", parent=None):
        super().__init__(parent)
        self.search_type = search_type
        self.filters = {}
        self.setWindowTitle("Расширенный поиск")
        self.setWindowIcon(IconProvider.create_search_icon())
        self.setModal(True)
        
        # Используем гибкие размеры
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Применяем QSS стили
        self.setStyleSheet(theme_manager.get_current_stylesheet())
        
        self.init_ui()
        self.load_data()
    
    def refresh_styles(self):
        """Обновить стили после смены темы"""
        try:
            # Применяем новую тему
            self.setStyleSheet(theme_manager.get_current_stylesheet())
            self.update()
        except Exception as e:
            print(f"Ошибка обновления стилей в advanced_search_dialog: {e}")
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Заголовок
        title_label = QLabel("Расширенный поиск и фильтрация")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("searchDialogTitle")
        layout.addWidget(title_label)
        
        # Создаем прокручиваемую область для фильтров с гибкими размерами
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setObjectName("searchScrollArea")
        
        scroll_widget = QWidget()
        scroll_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_layout = QVBoxLayout(scroll_widget)
        
        if self.search_type == "materials":
            self.create_material_filters(scroll_layout)
        elif self.search_type == "samples":
            self.create_sample_filters(scroll_layout)
        elif self.search_type == "tests":
            self.create_test_filters(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Кнопки с гибким layout
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                    QDialogButtonBox.StandardButton.Cancel |
                                    QDialogButtonBox.StandardButton.Reset)
        
        # Настраиваем кнопки
        search_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)
        search_btn.setText("Найти")
        search_btn.setIcon(IconProvider.create_search_icon())
        apply_button_style(search_btn, 'primary')
        
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("Отмена")
        apply_button_style(cancel_btn, 'secondary')
        
        clear_btn = button_box.button(QDialogButtonBox.StandardButton.Reset)
        clear_btn.setText("Очистить")
        clear_btn.setIcon(IconProvider.create_filter_icon())
        apply_button_style(clear_btn, 'default')
        
        # Подключаем сигналы
        button_box.accepted.connect(self.perform_search)
        button_box.rejected.connect(self.reject)
        clear_btn.clicked.connect(self.clear_filters)
        
        layout.addWidget(button_box)
    
    def create_material_filters(self, layout):
        """Создание фильтров для материалов"""
        # Основная информация
        basic_group = QGroupBox("Основная информация")
        basic_group.setObjectName("searchGroupBox")
        basic_layout = QGridLayout(basic_group)
        
        # Поиск по тексту
        basic_layout.addWidget(QLabel("Поиск по тексту:"), 0, 0)
        self.text_search = QLineEdit()
        self.text_search.setPlaceholderText("Номер партии, марка, поставщик...")
        self.text_search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.text_search, 'search')
        basic_layout.addWidget(self.text_search, 0, 1, 1, 3)
        
        # Марка материала
        basic_layout.addWidget(QLabel("Марка материала:"), 1, 0)
        self.material_grade = QComboBox()
        self.material_grade.setEditable(True)
        self.material_grade.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_combobox_style(self.material_grade)
        basic_layout.addWidget(self.material_grade, 1, 1)
        
        # Тип продукта
        basic_layout.addWidget(QLabel("Тип продукта:"), 1, 2)
        self.product_type = QComboBox()
        self.product_type.addItem("Все типы", "")
        for material_type in MaterialType:
            display_name = self.get_material_type_display(material_type.value)
            self.product_type.addItem(display_name, material_type.value)
        self.product_type.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_combobox_style(self.product_type)
        basic_layout.addWidget(self.product_type, 1, 3)
        
        # Поставщик
        basic_layout.addWidget(QLabel("Поставщик:"), 2, 0)
        self.supplier = QComboBox()
        self.supplier.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_combobox_style(self.supplier)
        basic_layout.addWidget(self.supplier, 2, 1, 1, 2)
        
        # Номер плавки
        basic_layout.addWidget(QLabel("Номер плавки:"), 3, 0)
        self.melt_number = QLineEdit()
        self.melt_number.setPlaceholderText("Введите номер плавки...")
        self.melt_number.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.melt_number)
        basic_layout.addWidget(self.melt_number, 3, 1)
        
        # Номер партии
        basic_layout.addWidget(QLabel("Номер партии:"), 3, 2)
        self.batch_number = QLineEdit()
        self.batch_number.setPlaceholderText("Введите номер партии...")
        self.batch_number.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.batch_number)
        basic_layout.addWidget(self.batch_number, 3, 3)
        
        layout.addWidget(basic_group)
        
        # Статус
        status_group = QGroupBox("Статус материала")
        status_group.setObjectName("searchGroupBox")
        status_layout = QVBoxLayout(status_group)
        
        self.status_group = QButtonGroup()
        status_grid = QGridLayout()
        
        all_status_radio = QRadioButton("Все статусы")
        all_status_radio.setChecked(True)
        self.status_group.addButton(all_status_radio, -1)
        status_grid.addWidget(all_status_radio, 0, 0)
        
        row = 0
        col = 1
        for i, status in enumerate(MaterialStatus):
            display_name = self.get_status_display_name(status.value)
            radio = QRadioButton(display_name)
            self.status_group.addButton(radio, i)
            status_grid.addWidget(radio, row, col)
            
            col += 1
            if col > 2:  # 3 колонки
                col = 0
                row += 1
        
        status_layout.addLayout(status_grid)
        layout.addWidget(status_group)
        
        # Даты
        date_group = QGroupBox("Период")
        date_group.setObjectName("searchGroupBox")
        date_layout = QGridLayout(date_group)
        
        # Дата поступления
        date_layout.addWidget(QLabel("Дата поступления:"), 0, 0)
        date_layout.addWidget(QLabel("с"), 0, 1)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.date_from)
        date_layout.addWidget(self.date_from, 0, 2)
        
        date_layout.addWidget(QLabel("по"), 0, 3)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.date_to)
        date_layout.addWidget(self.date_to, 0, 4)
        
        layout.addWidget(date_group)
        
        # Дополнительные параметры
        additional_group = QGroupBox("Дополнительные параметры")
        additional_layout = QGridLayout(additional_group)
        
        # Размеры
        additional_layout.addWidget(QLabel("Диаметр/толщина (мм):"), 0, 0)
        self.size_from = QLineEdit()
        self.size_from.setPlaceholderText("от")
        self.size_from.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.size_from)
        additional_layout.addWidget(self.size_from, 0, 1)
        
        additional_layout.addWidget(QLabel("до"), 0, 2)
        self.size_to = QLineEdit()
        self.size_to.setPlaceholderText("до")
        self.size_to.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        apply_input_style(self.size_to)
        additional_layout.addWidget(self.size_to, 0, 3)
        
        # Чекбоксы для дополнительных условий
        self.has_certificate = QCheckBox("Только с сертификатами")
        additional_layout.addWidget(self.has_certificate, 1, 0, 1, 2)
        
        self.requires_lab = QCheckBox("Требует проверки ЦЗЛ")
        additional_layout.addWidget(self.requires_lab, 1, 2, 1, 2)
        
        self.edit_requested = QCheckBox("С запросами на редактирование")
        additional_layout.addWidget(self.edit_requested, 2, 0, 1, 2)
        
        layout.addWidget(additional_group)
    
    def create_sample_filters(self, layout):
        """Создание фильтров для образцов"""
        # Заглушка для фильтров образцов
        info_label = QLabel("Фильтры для образцов будут добавлены позже")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
    
    def create_test_filters(self, layout):
        """Создание фильтров для испытаний"""
        # Заглушка для фильтров испытаний
        info_label = QLabel("Фильтры для испытаний будут добавлены позже")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
    
    def load_data(self):
        """Загрузка данных для комбобоксов"""
        if self.search_type == "materials":
            self.load_material_data()
    
    def load_material_data(self):
        """Загрузка данных для фильтров материалов"""
        db = SessionLocal()
        try:
            # Загружаем марки материалов
            self.material_grade.clear()
            self.material_grade.addItem("Все марки", "")
            
            grades = db.query(MaterialEntry.material_grade).distinct().filter(
                MaterialEntry.is_deleted == False
            ).order_by(MaterialEntry.material_grade).all()
            
            for grade_tuple in grades:
                grade = grade_tuple[0]
                if grade:
                    # Очищаем марку от стандарта
                    clean_grade = self.clean_material_grade(grade)
                    self.material_grade.addItem(clean_grade, grade)
            
            # Загружаем поставщиков
            self.supplier.clear()
            self.supplier.addItem("Все поставщики", "")
            
            suppliers = db.query(Supplier).filter(Supplier.is_deleted == False).order_by(Supplier.name).all()
            for supplier in suppliers:
                self.supplier.addItem(supplier.name, supplier.id)
                
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
        finally:
            db.close()
    
    def clean_material_grade(self, grade_text):
        """Очищает марку материала от стандарта (ГОСТ)"""
        if not grade_text:
            return grade_text
        
        # Удаляем различные варианты ГОСТ
        import re
        # Паттерн для удаления ГОСТ и скобок
        patterns = [
            r'\s*\(ГОСТ.*?\)',  # Удаляем (ГОСТ...)
            r'\s*ГОСТ.*$',      # Удаляем ГОСТ в конце строки
            r'\s*\([^)]*ГОСТ[^)]*\)',  # Удаляем любые скобки с ГОСТ
        ]
        
        clean_text = grade_text
        for pattern in patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        return clean_text.strip()
    
    def get_material_type_display(self, type_code):
        """Получить отображаемое название типа материала"""
        type_names = {
            MaterialType.SHEET.value: "Лист",
            MaterialType.PIPE.value: "Труба", 
            MaterialType.ROD.value: "Пруток",
            MaterialType.ANGLE.value: "Уголок",
            MaterialType.CHANNEL.value: "Швеллер",
            MaterialType.OTHER.value: "Другое"
        }
        return type_names.get(type_code, type_code)
    
    def get_status_display_name(self, status_code):
        """Получить отображаемое название статуса"""
        status_names = {
            MaterialStatus.RECEIVED.value: "Получен на склад",
            MaterialStatus.PENDING_QC.value: "Ожидает проверки ОТК",
            MaterialStatus.QC_CHECKED.value: "Проверен ОТК",
            MaterialStatus.QC_PASSED.value: "Проверка ОТК пройдена",
            MaterialStatus.QC_FAILED.value: "Проверка ОТК не пройдена",
            MaterialStatus.LAB_CHECK_PENDING.value: "Ожидает проверки ЦЗЛ",
            MaterialStatus.LAB_TESTING.value: "На лабораторных испытаниях",
            MaterialStatus.READY_FOR_USE.value: "Готов к использованию",
            MaterialStatus.IN_USE.value: "В производстве",
            MaterialStatus.REJECTED.value: "Отклонен",
            MaterialStatus.EDIT_REQUESTED.value: "Запрос на редактирование"
        }
        return status_names.get(status_code, status_code)
    
    def perform_search(self):
        """Выполнение поиска"""
        filters = self.get_current_filters()
        self.search_requested.emit(filters)
        self.accept()
    
    def get_current_filters(self) -> dict:
        """Получение текущих фильтров"""
        filters = {}
        
        if self.search_type == "materials":
            # Текстовый поиск
            if self.text_search.text().strip():
                filters['text_search'] = self.text_search.text().strip()
            
            # Марка материала
            if hasattr(self, 'material_grade') and self.material_grade.currentData():
                filters['material_grade'] = self.material_grade.currentData()
            
            # Тип продукта
            if hasattr(self, 'product_type') and self.product_type.currentData():
                filters['product_type'] = self.product_type.currentData()
            
            # Поставщик
            if hasattr(self, 'supplier') and self.supplier.currentData():
                filters['supplier'] = self.supplier.currentData()
            
            # Номер плавки
            if self.melt_number.text().strip():
                filters['melt_number'] = self.melt_number.text().strip()
            
            # Номер партии
            if self.batch_number.text().strip():
                filters['batch_number'] = self.batch_number.text().strip()
            
            # Статус
            if hasattr(self, 'status_group'):
                checked_id = self.status_group.checkedId()
                if checked_id >= 0:  # -1 означает "Все статусы"
                    statuses = list(MaterialStatus)
                    if checked_id < len(statuses):
                        filters['status'] = statuses[checked_id]
            
            # Даты
            if hasattr(self, 'date_from') and hasattr(self, 'date_to'):
                filters['date_from'] = self.date_from.date().toPython()
                filters['date_to'] = self.date_to.date().toPython()
            
            # Размеры
            if self.size_from.text().strip():
                try:
                    filters['size_from'] = float(self.size_from.text())
                except ValueError:
                    pass
            
            if self.size_to.text().strip():
                try:
                    filters['size_to'] = float(self.size_to.text())
                except ValueError:
                    pass
            
            # Дополнительные параметры
            if hasattr(self, 'has_certificate') and self.has_certificate.isChecked():
                filters['has_certificate'] = True
            
            if hasattr(self, 'requires_lab') and self.requires_lab.isChecked():
                filters['requires_lab'] = True
            
            if hasattr(self, 'edit_requested') and self.edit_requested.isChecked():
                filters['edit_requested'] = True
        
        return filters
    
    def clear_filters(self):
        """Очистка всех фильтров"""
        if self.search_type == "materials":
            self.text_search.clear()
            self.material_grade.setCurrentIndex(0)
            self.product_type.setCurrentIndex(0)
            self.supplier.setCurrentIndex(0)
            self.melt_number.clear()
            self.batch_number.clear()
            
            # Сброс статуса на "Все"
            if hasattr(self, 'status_group'):
                all_button = self.status_group.button(-1)
                if all_button:
                    all_button.setChecked(True)
            
            # Сброс дат
            if hasattr(self, 'date_from') and hasattr(self, 'date_to'):
                self.date_from.setDate(QDate.currentDate().addDays(-30))
                self.date_to.setDate(QDate.currentDate())
            
            # Сброс размеров
            self.size_from.clear()
            self.size_to.clear()
            
            # Сброс чекбоксов
            if hasattr(self, 'has_certificate'):
                self.has_certificate.setChecked(False)
            if hasattr(self, 'requires_lab'):
                self.requires_lab.setChecked(False)
            if hasattr(self, 'edit_requested'):
                self.edit_requested.setChecked(False) 