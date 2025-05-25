from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QFormLayout, QMessageBox, QFileDialog, QHeaderView,
    QGroupBox, QSpinBox, QDoubleSpinBox, QDialog, QInputDialog,
    QSplitter, QFrame, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QBrush, QAction

import os
import datetime
from database.connection import SessionLocal
from models.models import User, MaterialEntry, Supplier, MaterialType, MaterialStatus
from sqlalchemy import desc, and_, or_
from ui.tabs.warehouse_entry_form import WarehouseEntryForm
from ui.icons.icon_provider import IconProvider
from ui.styles import (apply_button_style, apply_input_style, apply_combobox_style, 
                       apply_table_style, refresh_table_style)
from ui.themes import theme_manager
from ui.dialogs.advanced_search_dialog import AdvancedSearchDialog
from utils.material_utils import clean_material_grade, get_material_type_display, get_status_display_name

class WarehouseTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.init_ui()
        
    def refresh_styles(self):
        """Обновить стили после смены темы"""
        try:
            # Обновляем стили таблицы
            if hasattr(self, 'materials_table'):
                refresh_table_style(self.materials_table)
                
            # Обновляем другие элементы при необходимости
            self.update()
        except Exception as e:
            print(f"Ошибка обновления стилей в warehouse_tab: {e}")
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Create title with modern стиль
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Учет материалов на складе")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Create toolbar with flexible layout
        toolbar_widget = QFrame()
        toolbar_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)
        
        # Add new material button with icon
        self.add_btn = QPushButton("Добавить материал")
        self.add_btn.setIcon(IconProvider.create_material_entry_icon())
        apply_button_style(self.add_btn, 'secondary')
        self.add_btn.clicked.connect(self.show_add_material_form)
        toolbar_layout.addWidget(self.add_btn)

        # Edit material button
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.setIcon(IconProvider.create_edit_icon())
        apply_button_style(self.edit_btn, 'primary')
        self.edit_btn.clicked.connect(self.edit_selected_material)
        toolbar_layout.addWidget(self.edit_btn)
        
        # Сертификаты - кнопка просмотра сертификатов
        self.cert_btn = QPushButton("Сертификаты")
        self.cert_btn.setIcon(IconProvider.create_certificate_icon())
        apply_button_style(self.cert_btn, 'primary')
        self.cert_btn.clicked.connect(self.open_certificate_browser)
        toolbar_layout.addWidget(self.cert_btn)
        
        # Добавляем растяжку для разделения кнопок действий и поиска
        toolbar_layout.addStretch()
        
        # Search field with icon - теперь гибкий
        search_widget = QFrame()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(4, 4, 4, 4)
        search_layout.setSpacing(4)
        
        search_icon_label = QLabel()
        search_icon_label.setPixmap(IconProvider.create_search_icon().pixmap(16, 16))
        search_layout.addWidget(search_icon_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по марке, партии, плавке...")
        apply_input_style(self.search_input, 'search')
        self.search_input.textChanged.connect(self.filter_materials)
        search_layout.addWidget(self.search_input)
        
        toolbar_layout.addWidget(search_widget)
        
        # Status filter with icon - гибкий
        filter_widget = QFrame()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        filter_layout.setSpacing(4)
        
        filter_icon_label = QLabel()
        filter_icon_label.setPixmap(IconProvider.create_filter_icon().pixmap(16, 16))
        filter_layout.addWidget(filter_icon_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", "")
        for status in MaterialStatus:
            self.status_filter.addItem(get_status_display_name(status.value), status.value)
        apply_combobox_style(self.status_filter)
        self.status_filter.currentIndexChanged.connect(self.filter_materials)
        filter_layout.addWidget(self.status_filter)
        
        toolbar_layout.addWidget(filter_widget)
        
        # Кнопка расширенного поиска
        self.advanced_search_btn = QPushButton("Расширенный поиск")
        self.advanced_search_btn.setIcon(IconProvider.create_filter_icon())
        apply_button_style(self.advanced_search_btn, 'default')
        self.advanced_search_btn.clicked.connect(self.show_advanced_search)
        toolbar_layout.addWidget(self.advanced_search_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setIcon(IconProvider.create_refresh_icon())
        apply_button_style(self.refresh_btn, 'default')
        self.refresh_btn.clicked.connect(self.load_materials)
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(toolbar_widget)
        
        # Второй ряд кнопок для управления
        actions_widget = QFrame()
        actions_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(12, 8, 12, 8)
        actions_layout.setSpacing(8)
        
        # Status management button
        self.change_status_btn = QPushButton("Изменить статус")
        self.change_status_btn.setIcon(IconProvider.create_status_change_icon())
        apply_button_style(self.change_status_btn, 'default')
        self.change_status_btn.clicked.connect(self.change_status)
        actions_layout.addWidget(self.change_status_btn)
        
        # QR code generator button
        self.qr_btn = QPushButton("QR-код")
        self.qr_btn.setIcon(IconProvider.create_qr_code_icon())
        apply_button_style(self.qr_btn, 'default')
        self.qr_btn.clicked.connect(self.generate_sample_qr)
        actions_layout.addWidget(self.qr_btn)
        
        # Excel export button
        self.excel_btn = QPushButton("Экспорт")
        self.excel_btn.setIcon(IconProvider.create_excel_icon())
        apply_button_style(self.excel_btn, 'secondary')
        self.excel_btn.clicked.connect(self.export_to_excel)
        actions_layout.addWidget(self.excel_btn)
        
        actions_layout.addStretch()
        
        main_layout.addWidget(actions_widget)
        
        # Container for table with flexible sizing
        table_container = QFrame()
        table_container.setFrameStyle(QFrame.Shape.StyledPanel)
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)
        
        # Table title
        table_title = QLabel("Материалы на складе")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        table_layout.addWidget(table_title)
        
        # Create materials table с гибкими размерами
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(11)  # Расширено до 11 колонок
        self.materials_table.setHorizontalHeaderLabels([
            "Номер заказа", "Марка материала", "Вид проката", "Размер", "Плавка", "Сертификат", 
            "Партия", "Общая длина/площадь", "Дата прихода", "Статус", "Поставщик"
        ])
        
        # Применяем гибкие стили к таблице
        apply_table_style(self.materials_table)
        
        # Set column resize modes для лучшей адаптивности
        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Номер заказа
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Марка материала - растягивается
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Вид проката
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Размер
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Плавка
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Сертификат
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Партия
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Общая длина/площадь
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Дата прихода
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Статус
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Поставщик
        
        # Настраиваем контекстное меню для таблицы
        self.materials_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.materials_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Двойной клик по строке для редактирования
        self.materials_table.cellDoubleClicked.connect(self.on_table_double_click)
        
        table_layout.addWidget(self.materials_table)
        
        # Add table status row
        status_layout = QHBoxLayout()
        
        self.table_status_label = QLabel("Загрузка данных...")
        status_layout.addWidget(self.table_status_label)
        
        status_layout.addStretch()
        
        self.records_count_label = QLabel("Записей: 0")
        self.records_count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_layout.addWidget(self.records_count_label)
        
        table_layout.addLayout(status_layout)
        
        main_layout.addWidget(table_container, 1)  # 1 = stretch factor для расширения таблицы
        
        # Load materials
        self.load_materials()
    
    def show_advanced_search(self):
        """Показать диалог расширенного поиска"""
        dialog = AdvancedSearchDialog("materials", self)
        dialog.search_requested.connect(self.perform_advanced_search)
        dialog.exec()
    
    def perform_advanced_search(self, filters):
        """Perform advanced search with filters"""
        db = SessionLocal()
        try:
            # Start with base query
            query = db.query(MaterialEntry).filter(MaterialEntry.is_deleted == False)
            
            # Apply filters
            if 'text_search' in filters:
                text = f"%{filters['text_search']}%"
                query = query.filter(
                    or_(
                        MaterialEntry.material_grade.ilike(text),
                        MaterialEntry.batch_number.ilike(text),
                        MaterialEntry.melt_number.ilike(text)
                    )
                )
            
            if 'material_grade' in filters:
                query = query.filter(MaterialEntry.material_grade == filters['material_grade'])
            
            if 'product_type' in filters:
                query = query.filter(MaterialEntry.material_type == filters['product_type'])
            
            if 'status' in filters:
                query = query.filter(MaterialEntry.status == filters['status'].value)
            
            if 'date_from' in filters:
                query = query.filter(MaterialEntry.created_at >= filters['date_from'])
            
            if 'date_to' in filters:
                query = query.filter(MaterialEntry.created_at <= filters['date_to'])
            
            if 'supplier' in filters:
                query = query.filter(MaterialEntry.supplier_id == filters['supplier'])
            
            if 'melt_number' in filters:
                query = query.filter(MaterialEntry.melt_number.ilike(f"%{filters['melt_number']}%"))
            
            if 'batch_number' in filters:
                query = query.filter(MaterialEntry.batch_number.ilike(f"%{filters['batch_number']}%"))
            
            if 'size_from' in filters:
                query = query.filter(
                    or_(
                        MaterialEntry.diameter >= filters['size_from'],
                        MaterialEntry.thickness >= filters['size_from']
                    )
                )
            
            if 'size_to' in filters:
                query = query.filter(
                    or_(
                        MaterialEntry.diameter <= filters['size_to'],
                        MaterialEntry.thickness <= filters['size_to']
                    )
                )
            
            if 'has_certificate' in filters:
                query = query.filter(MaterialEntry.certificate_file_path.isnot(None))
            
            if 'requires_lab' in filters:
                query = query.filter(MaterialEntry.requires_lab_verification == True)
            
            if 'edit_requested' in filters:
                query = query.filter(MaterialEntry.edit_requested == True)
            
            # Execute query
            materials = query.order_by(desc(MaterialEntry.created_at)).all()
            
            # Update table
            self.update_materials_table(materials, db)
            
            # Update status
            self.parent.status_bar.showMessage(f"Найдено {len(materials)} материалов по фильтрам")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске: {str(e)}")
        finally:
            db.close()
    
    def update_materials_table(self, materials, db):
        """Update materials table with given materials"""
        # Clear table
        self.materials_table.setRowCount(0)
        
        # Add materials to table
        for row, material in enumerate(materials):
            self.materials_table.insertRow(row)
            
            # Номер заказа (теперь первый столбец)
            order_item = QTableWidgetItem(material.order_number or "")
            order_item.setToolTip(f"Заказ: {material.order_number or 'Не указан'}")
            self.materials_table.setItem(row, 0, order_item)
            
            # Марка материала (теперь второй столбец)
            # Очищаем марку материала от стандарта
            clean_grade = clean_material_grade(material.material_grade)
            grade_item = QTableWidgetItem(clean_grade)
            grade_item.setData(Qt.UserRole, material.id)
            grade_item.setToolTip(f"Полное название: {material.material_grade}")
            self.materials_table.setItem(row, 1, grade_item)
            
            # Тип проката
            type_display = get_material_type_display(material.material_type)
            type_item = QTableWidgetItem(type_display)
            type_item.setToolTip(f"Тип материала: {type_display}")
            self.materials_table.setItem(row, 2, type_item)
            
            # Размер (диаметр/толщина)
            size_text = ""
            if material.material_type == MaterialType.ROD.value:
                size_text = f"Ø{material.diameter}" if material.diameter else ""
            elif material.material_type == MaterialType.SHEET.value:
                size_text = f"{material.thickness} мм" if material.thickness else ""
            elif material.material_type == MaterialType.PIPE.value:
                size_text = f"Ø{material.diameter}x{material.wall_thickness}" if material.diameter else ""
            else:
                size_text = f"Ø{material.diameter}" if material.diameter else f"{material.thickness} мм" if material.thickness else ""
            
            size_item = QTableWidgetItem(size_text)
            size_tooltip = "Размер: " + size_text
            if material.material_type == MaterialType.SHEET.value and material.width and material.length:
                size_tooltip += f"\nШирина: {material.width} мм\nДлина: {material.length} мм"
            size_item.setToolTip(size_tooltip)
            self.materials_table.setItem(row, 3, size_item)
            
            # Плавка
            melt_item = QTableWidgetItem(material.melt_number)
            melt_item.setToolTip(f"Плавка: {material.melt_number}")
            self.materials_table.setItem(row, 4, melt_item)
            
            # Сертификат (номер + дата)
            cert_date_str = material.certificate_date.strftime("%d.%m.%Y") if material.certificate_date else ""
            cert_text = f"{material.certificate_number} от {cert_date_str}" if cert_date_str else material.certificate_number
            cert_item = QTableWidgetItem(cert_text)
            cert_tooltip = f"Сертификат: {cert_text}"
            if material.certificate_file_path:
                cert_tooltip += f"\nФайл: {material.certificate_file_path}"
            cert_item.setToolTip(cert_tooltip)
            self.materials_table.setItem(row, 5, cert_item)
            
            # Партия
            batch_item = QTableWidgetItem(material.batch_number or "")
            batch_item.setToolTip(f"Партия: {material.batch_number or 'Не указана'}")
            self.materials_table.setItem(row, 6, batch_item)
            
            # Общая длина/площадь
            length_text = ""
            if material.material_type == MaterialType.SHEET.value and material.width and material.length:
                # Для листов считаем площадь в м²
                area = (material.width * material.length) / 1000000  # переводим из мм² в м²
                length_text = f"{area:.2f} м²"
            elif material.material_type == MaterialType.ROD.value or material.material_type == MaterialType.PIPE.value:
                # Для прутков и труб считаем общую длину в метрах
                if hasattr(material, 'sizes') and material.sizes:
                    total_length = sum(size.length * size.quantity for size in material.sizes) / 1000  # переводим из мм в м
                    length_text = f"{total_length:.2f} м"
            
            length_item = QTableWidgetItem(length_text)
            if material.material_type == MaterialType.SHEET.value:
                length_item.setToolTip(f"Площадь: {length_text}")
            else:
                length_item.setToolTip(f"Общая длина: {length_text}")
            self.materials_table.setItem(row, 7, length_item)
            
            # Дата прихода
            created_date = material.created_at.strftime("%d.%m.%Y") if material.created_at else ""
            date_item = QTableWidgetItem(created_date)
            if material.created_at:
                date_item.setToolTip(f"Создано: {material.created_at.strftime('%d.%m.%Y %H:%M:%S')}")
            self.materials_table.setItem(row, 8, date_item)
            
            # Статус (теперь в колонке 9)
            status_display = get_status_display_name(material.status)
            status_item = QTableWidgetItem(status_display)
            status_item.setToolTip(f"Статус: {status_display}")
            
            # Подсветка статусов разными цветами
            if material.status == MaterialStatus.RECEIVED.value:
                status_item.setBackground(QBrush(QColor(240, 240, 240)))  # Светло-серый
            elif material.status == MaterialStatus.PENDING_QC.value:
                status_item.setBackground(QBrush(QColor(255, 230, 180)))  # Светло-оранжевый
            elif material.status == MaterialStatus.QC_PASSED.value:
                status_item.setBackground(QBrush(QColor(200, 255, 200)))  # Светло-зеленый
            elif material.status == MaterialStatus.QC_FAILED.value:
                status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Светло-красный
            elif material.status == MaterialStatus.LAB_TESTING.value:
                status_item.setBackground(QBrush(QColor(200, 220, 255)))  # Светло-синий
            elif material.status == MaterialStatus.READY_FOR_USE.value:
                status_item.setBackground(QBrush(QColor(180, 255, 180)))  # Ярко-зеленый
            elif material.status == MaterialStatus.REJECTED.value:
                status_item.setBackground(QBrush(QColor(255, 180, 180)))  # Ярко-красный
            elif material.status == MaterialStatus.EDIT_REQUESTED.value:
                status_item.setBackground(QBrush(QColor(255, 255, 180)))  # Светло-желтый
            
            self.materials_table.setItem(row, 9, status_item)
            
            # Поставщик (теперь в колонке 10)
            supplier = db.query(Supplier).filter(Supplier.id == material.supplier_id).first()
            supplier_name = supplier.name if supplier else "Неизвестно"
            supplier_item = QTableWidgetItem(supplier_name)
            if supplier:
                supplier_tooltip = f"Поставщик: {supplier.name}"
                if supplier.contact_info:
                    supplier_tooltip += f"\nКонтакты: {supplier.contact_info}"
                supplier_item.setToolTip(supplier_tooltip)
            self.materials_table.setItem(row, 10, supplier_item)
            
            # Выделяем цветом записи с запросом на редактирование
            if material.edit_requested:
                for col in range(0, 11):  # Теперь 11 колонок
                    if col != 9:  # Не меняем цвет столбца статуса, так как он уже имеет свой цвет
                        item = self.materials_table.item(row, col)
                        if item:
                            item.setBackground(QBrush(QColor(255, 255, 200)))  # Светло-желтый
        
        # После заполнения таблицы данными:
        self.materials_table.resizeColumnsToContents()
        
        # Ограничим максимальную ширину колонок и установим минимальную
        min_widths = {
            0: 80,   # Номер заказа
            1: 120,  # Марка материала 
            2: 80,   # Вид проката
            3: 80,   # Размер
            4: 80,   # Плавка
            5: 100,  # Сертификат
            6: 80,   # Партия
            7: 120,  # Общая длина/площадь
            8: 80,   # Дата прихода
            9: 100,  # Статус
            10: 100  # Поставщик
        }
        
        max_width = 300
        for col in range(self.materials_table.columnCount()):
            current_width = self.materials_table.columnWidth(col)
            min_width = min_widths.get(col, 60)
            
            # Устанавливаем ширину между минимальной и максимальной
            if current_width < min_width:
                self.materials_table.setColumnWidth(col, min_width)
            elif current_width > max_width:
                self.materials_table.setColumnWidth(col, max_width)
                
        # Марка материала может растягиваться
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    
    def load_materials(self):
        """Load materials from database"""
        self.table_status_label.setText("Загрузка данных...")
        db = SessionLocal()
        try:
            # Get all materials that are not deleted
            materials = db.query(MaterialEntry).filter(
                MaterialEntry.is_deleted == False
            ).order_by(desc(MaterialEntry.created_at)).all()
            
            # Update table
            self.update_materials_table(materials, db)
            
            # Update status
            self.parent.status_bar.showMessage(f"Загружено {len(materials)} материалов")
            self.table_status_label.setText("Данные загружены")
            self.records_count_label.setText(f"Записей: {len(materials)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке материалов: {str(e)}")
        finally:
            db.close()
    
    def filter_materials(self):
        """Filter materials by search text and status"""
        search_text = self.search_input.text().lower()
        status = self.status_filter.currentData()
        
        visible_count = 0
        
        for row in range(self.materials_table.rowCount()):
            show_row = True
            
            # Check if row matches search text
            if search_text:
                match_found = False
                for col in range(0, 10):  # Проверяем колонки 0-9 (информация о материале, без статуса)
                    item = self.materials_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                if not match_found:
                    show_row = False
            
            # Check if row matches status filter
            if status and show_row:
                status_item = self.materials_table.item(row, 9)  # Статус теперь в колонке 9
                status_display = status_item.text() if status_item else ""
                if get_status_display_name(status) != status_display:
                    show_row = False
            
            # Show/hide row
            self.materials_table.setRowHidden(row, not show_row)
            
            if show_row:
                visible_count += 1
        
        # Update status
        if search_text or status:
            self.table_status_label.setText(f"Отфильтровано: {search_text if search_text else ''} {get_status_display_name(status) if status else ''}")
            self.records_count_label.setText(f"Показано: {visible_count} / {self.materials_table.rowCount()}")
        else:
            self.table_status_label.setText("Все записи")
            self.records_count_label.setText(f"Записей: {self.materials_table.rowCount()}")
    
    def show_add_material_form(self):
        """Show form to add new material"""
        self.entry_form = WarehouseEntryForm(self, user=self.user)
        self.entry_form.setWindowTitle("Добавление материала")
        self.entry_form.setWindowIcon(IconProvider.create_material_entry_icon())
        if self.entry_form.exec() == QDialog.DialogCode.Accepted:
            self.load_materials()
    
    def edit_selected_material(self):
        """Редактирование выбранного материала"""
        # Проверяем, есть ли выделенные строки
        selected_rows = self.materials_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите материал для редактирования")
            return
            
        # Получаем ID материала
        row = selected_rows[0].row()
        material_id = self.materials_table.item(row, 1).data(Qt.UserRole)
        
        # Проверяем статус материала
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            if not material:
                QMessageBox.warning(self, "Предупреждение", "Материал не найден")
                return
                
            # Если материал уже в процессе проверки ОТК или дальше, требуется запрос
            if material.status not in [MaterialStatus.RECEIVED.value, MaterialStatus.EDIT_REQUESTED.value]:
                # Спрашиваем комментарий для запроса
                comment, ok = QInputDialog.getText(
                    self, 
                    "Запрос на редактирование", 
                    "Материал уже находится в процессе проверки. Введите причину изменения:",
                    QLineEdit.Normal, 
                    ""
                )
                
                if not ok or not comment.strip():
                    return  # Пользователь отменил или не ввёл комментарий
                
                # Создаем запрос на редактирование
                material.edit_requested = True
                material.edit_comment = comment
                material.status = MaterialStatus.EDIT_REQUESTED.value
                db.commit()
                
                QMessageBox.information(
                    self, 
                    "Запрос отправлен", 
                    "Запрос на редактирование отправлен сотруднику ОТК. "
                    "Вы сможете редактировать запись после подтверждения."
                )
                self.load_materials()
                return
                
            # Если материал еще не в процессе проверки или это подтвержденный запрос,
            # открываем форму редактирования
            self.entry_form = WarehouseEntryForm(self, user=self.user, material_id=material_id)
            self.entry_form.setWindowTitle(f"Редактирование материала #{material_id}")
            self.entry_form.setWindowIcon(IconProvider.create_edit_icon())
            
            if self.entry_form.exec() == QDialog.DialogCode.Accepted:
                # Если это был запрос на редактирование, сбрасываем флаг
                if material.edit_requested:
                    material.edit_requested = False
                    material.edit_comment = None
                    material.status = MaterialStatus.RECEIVED.value
                    db.commit()
                self.load_materials()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке запроса: {str(e)}")
        finally:
            db.close()
    
    def change_status(self):
        """Изменение статуса выбранного материала"""
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите материал для изменения статуса")
            return
        
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 1).data(Qt.UserRole)
        
        from ui.dialogs.status_change_dialog import StatusChangeDialog
        dialog = StatusChangeDialog(material_id, self.user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_materials()
    
    def generate_sample_qr(self):
        """Генерация QR-кода для образца"""
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            # Открываем общий генератор QR-кодов
            from ui.dialogs.qr_dialog import QRDialog
            dialog = QRDialog(parent=self)
            dialog.exec()
            return
        
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 1).data(Qt.UserRole)
        
        # Получаем данные материала для формирования кода образца
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            if material:
                # Формируем код образца
                sample_code = f"{material_id:03d}-{material.melt_number}-01"
                
                from ui.dialogs.qr_dialog import QRDialog
                dialog = QRDialog(sample_code, self)
                dialog.exec()
        finally:
            db.close()
    
    def export_to_excel(self):
        """Экспорт текущих материалов в Excel"""
        try:
            from utils.excel_export import export_materials_to_excel
            from PySide6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Сохранить отчет Excel", 
                f"warehouse_materials_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel файлы (*.xlsx)"
            )
            
            if filename:
                export_materials_to_excel(filename)
                QMessageBox.information(self, "Экспорт завершен", 
                                      f"Материалы успешно экспортированы в файл:\n{filename}")
                
                # Предложить открыть файл
                reply = QMessageBox.question(self, "Открыть файл?", 
                                           "Хотите открыть созданный файл?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(filename)  # Windows
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать данные:\n{str(e)}")
    
    def open_certificate_browser(self):
        """Открыть диалог просмотра сертификатов"""
        from ui.dialogs.certificate_browser_dialog import CertificateBrowserDialog
        dialog = CertificateBrowserDialog(self)
        dialog.exec()
    
    def on_table_double_click(self, row, column):
        """Обработка двойного клика по ячейке таблицы"""
        # Редактировать материал при двойном клике
        self.edit_selected_material()
    
    def show_context_menu(self, position):
        """Показать контекстное меню для таблицы материалов"""
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            return
            
        menu = QMenu(self)
        
        # Пункт меню "Редактировать"
        edit_action = QAction(IconProvider.create_edit_icon(), "Редактировать", self)
        edit_action.triggered.connect(self.edit_selected_material)
        menu.addAction(edit_action)
        
        # Пункт меню "Изменить статус"
        status_action = QAction(IconProvider.create_status_change_icon(), "Изменить статус", self)
        status_action.triggered.connect(self.change_status)
        menu.addAction(status_action)
        
        # Добавляем разделитель
        menu.addSeparator()
        
        # Пункт меню "Просмотреть сертификат"
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 1).data(Qt.UserRole)
        
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            
            if material and material.certificate_file_path and os.path.exists(material.certificate_file_path):
                view_cert_action = QAction(IconProvider.create_certificate_icon(), "Просмотреть сертификат", self)
                view_cert_action.triggered.connect(lambda: self.view_certificate(material.certificate_file_path))
                menu.addAction(view_cert_action)
        finally:
            db.close()
        
        # Пункт меню "Создать QR-код"
        qr_action = QAction(IconProvider.create_qr_code_icon(), "Создать QR-код", self)
        qr_action.triggered.connect(self.generate_sample_qr)
        menu.addAction(qr_action)
        
        # Показываем меню
        menu.exec(self.materials_table.mapToGlobal(position))
    
    def view_certificate(self, certificate_path):
        """Просмотр сертификата для материала"""
        if not certificate_path or not os.path.exists(certificate_path):
            QMessageBox.warning(self, "Предупреждение", "Файл сертификата не найден")
            return
            
        # Открываем сертификат
        from utils.certificate_manager import open_certificate
        if not open_certificate(certificate_path):
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть файл сертификата") 