from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                             QFormLayout, QMessageBox, QFileDialog, QHeaderView,
                             QGroupBox, QCheckBox, QTabWidget, QDialog, QDialogButtonBox,
                             QTextEdit, QDateTimeEdit, QInputDialog, QScrollArea,
                             QSplitter, QFrame)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QColor, QBrush, QIcon

from database.connection import SessionLocal
from models.models import MaterialEntry, QCCheck, MaterialStatus, Supplier, SampleRequest, LabTest, User, TestType
from sqlalchemy import desc
import datetime
import os
import shutil
from ui.icons.icon_provider import IconProvider
from ui.tabs.lab_dialogs import MaterialDetailsDialog, SampleRequestDialog, TestResultDialog
from ui.tabs.lab_test_detail import LabTestDetailDialog
from ui.tabs.sample_management_dialog import SampleManagementDialog
from utils.material_utils import clean_material_grade, get_material_type_display, get_status_display_name

class LabTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create title
        title_label = QLabel("Лаборатория ЦЗЛ")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # Create tab widget for different views
        self.view_tabs = QTabWidget()
        
        # Pending verification tab
        self.pending_verification_tab = QWidget()
        self.setup_pending_verification_tab()
        self.view_tabs.addTab(self.pending_verification_tab, "Ожидают проверки")
        
        # Sample requests tab
        self.sample_requests_tab = QWidget()
        self.setup_sample_requests_tab()
        self.view_tabs.addTab(self.sample_requests_tab, "Заявки на пробы")
        
        # Test results tab
        self.test_results_tab = QWidget()
        self.setup_test_results_tab()
        self.view_tabs.addTab(self.test_results_tab, "Результаты испытаний")
        
        main_layout.addWidget(self.view_tabs)
    
    def setup_pending_verification_tab(self):
        """Setup the tab for materials pending verification"""
        layout = QVBoxLayout(self.pending_verification_tab)
        
        # Добавляем информационную плашку
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setFrameShadow(QFrame.Shadow.Raised)
        info_layout = QHBoxLayout(info_frame)
        
        info_icon_label = QLabel()
        info_icon = QIcon("ui/icons/info_icon.png")
        if info_icon.isNull():
            # Если иконки нет, используем просто текст
            info_icon_label.setText("ⓘ")
            info_icon_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        else:
            pixmap = info_icon.pixmap(24, 24)
            info_icon_label.setPixmap(pixmap)
        info_layout.addWidget(info_icon_label)
        
        info_text = QLabel("Здесь отображаются материалы, отправленные ОТК на проверку в ЦЗЛ. "
                         "Дважды щелкните по материалу для просмотра деталей и запроса проб.")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text, 1)
        
        layout.addWidget(info_frame)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Фильтр по статусу
        status_label = QLabel("Статус:")
        toolbar_layout.addWidget(status_label)
        
        self.pending_status_filter = QComboBox()
        self.pending_status_filter.addItem("Ожидают проверки", MaterialStatus.LAB_CHECK_PENDING.value)
        self.pending_status_filter.addItem("Запрошены пробы", MaterialStatus.SAMPLES_REQUESTED.value)
        self.pending_status_filter.addItem("Пробы отобраны", MaterialStatus.SAMPLES_COLLECTED.value)
        self.pending_status_filter.addItem("На испытаниях", MaterialStatus.TESTING.value)
        self.pending_status_filter.addItem("Все", "")
        self.pending_status_filter.currentIndexChanged.connect(self.load_pending_materials)
        toolbar_layout.addWidget(self.pending_status_filter)
        
        # Search field
        self.pending_search_input = QLineEdit()
        self.pending_search_input.setPlaceholderText("Поиск...")
        self.pending_search_input.textChanged.connect(self.filter_pending_materials)
        toolbar_layout.addWidget(self.pending_search_input)
        
        # Refresh button
        self.pending_refresh_btn = QPushButton("Обновить")
        refresh_icon = QIcon("ui/icons/refresh_icon.png")
        if not refresh_icon.isNull():
            self.pending_refresh_btn.setIcon(refresh_icon)
        self.pending_refresh_btn.clicked.connect(self.load_pending_materials)
        toolbar_layout.addWidget(self.pending_refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create materials table
        self.pending_materials_table = QTableWidget()
        self.pending_materials_table.setColumnCount(7)
        self.pending_materials_table.setHorizontalHeaderLabels([
            "Марка материала", "Тип", "Размер", "Плавка", "Поставщик", "Статус", ""
        ])
        
        # Set column widths
        header = self.pending_materials_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Размер
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Колонка под иконки
        
        # Connect double click
        self.pending_materials_table.cellDoubleClicked.connect(self.show_verification_form)
        
        layout.addWidget(self.pending_materials_table)
        
        # Add filter hint
        hint_label = QLabel("Цветовые индикаторы: ")
        hint_label.setStyleSheet("color: #666;")
        hint_layout = QHBoxLayout()
        hint_layout.addWidget(hint_label)
        
        # Индикаторы цветов
        for status, color, text in [
            (MaterialStatus.LAB_CHECK_PENDING.value, QColor(200, 200, 255), "Ожидает проверки"),
            (MaterialStatus.SAMPLES_REQUESTED.value, QColor(255, 255, 160), "Запрошены пробы"),
            (MaterialStatus.SAMPLES_COLLECTED.value, QColor(255, 220, 160), "Пробы отобраны"),
            (MaterialStatus.TESTING.value, QColor(160, 255, 255), "На испытаниях")
        ]:
            color_box = QFrame()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999;")
            hint_layout.addWidget(color_box)
            
            hint_text = QLabel(text)
            hint_text.setStyleSheet("color: #666;")
            hint_layout.addWidget(hint_text)
            
            # Разделитель
            if status != MaterialStatus.TESTING.value:
                hint_layout.addWidget(QLabel("|"))
        
        hint_layout.addStretch(1)
        layout.addLayout(hint_layout)
        
        # Load materials
        self.load_pending_materials()
    
    def setup_sample_requests_tab(self):
        """Setup the tab for sample requests"""
        layout = QVBoxLayout(self.sample_requests_tab)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Filter by status
        status_label = QLabel("Статус:")
        toolbar_layout.addWidget(status_label)
        
        self.request_status_filter = QComboBox()
        self.request_status_filter.addItem("Ожидают отбора", "pending")
        self.request_status_filter.addItem("Отобраны", "collected")
        self.request_status_filter.addItem("Все", "")
        self.request_status_filter.currentIndexChanged.connect(self.load_sample_requests)
        toolbar_layout.addWidget(self.request_status_filter)
        
        # Search field
        self.request_search_input = QLineEdit()
        self.request_search_input.setPlaceholderText("Поиск...")
        self.request_search_input.textChanged.connect(self.filter_sample_requests)
        toolbar_layout.addWidget(self.request_search_input)
        
        # Refresh button
        self.request_refresh_btn = QPushButton("Обновить")
        self.request_refresh_btn.clicked.connect(self.load_sample_requests)
        toolbar_layout.addWidget(self.request_refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create requests table
        self.sample_requests_table = QTableWidget()
        self.sample_requests_table.setColumnCount(5)
        self.sample_requests_table.setHorizontalHeaderLabels([
            "Марка материала", "Партия", "Размер пробы", "Отобрана", "Отправлена"
        ])
        
        # Set column widths
        header = self.sample_requests_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect double click
        self.sample_requests_table.cellDoubleClicked.connect(self.show_sample_request_form)
        
        layout.addWidget(self.sample_requests_table)
        
        # Load requests
        self.load_sample_requests()
    
    def setup_test_results_tab(self):
        """Setup the tab for test results"""
        layout = QVBoxLayout(self.test_results_tab)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Filter by status
        status_label = QLabel("Статус:")
        toolbar_layout.addWidget(status_label)
        
        self.test_status_filter = QComboBox()
        self.test_status_filter.addItem("В процессе", "in_progress")
        self.test_status_filter.addItem("Завершены", "completed")
        self.test_status_filter.addItem("Все", "")
        self.test_status_filter.currentIndexChanged.connect(self.load_test_results)
        toolbar_layout.addWidget(self.test_status_filter)
        
        # Search field
        self.test_search_input = QLineEdit()
        self.test_search_input.setPlaceholderText("Поиск...")
        self.test_search_input.textChanged.connect(self.filter_test_results)
        toolbar_layout.addWidget(self.test_search_input)
        
        # Refresh button
        self.test_refresh_btn = QPushButton("Обновить")
        self.test_refresh_btn.clicked.connect(self.load_test_results)
        toolbar_layout.addWidget(self.test_refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create tests table
        self.test_results_table = QTableWidget()
        self.test_results_table.setColumnCount(5)
        self.test_results_table.setHorizontalHeaderLabels([
            "Марка материала", "Партия", "Тип теста", "Результат", "Годен"
        ])
        
        # Set column widths
        header = self.test_results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect double click
        self.test_results_table.cellDoubleClicked.connect(self.show_test_result_form)
        
        layout.addWidget(self.test_results_table)
        
        # Load test results
        self.load_test_results()
    
    def load_pending_materials(self):
        """Load materials pending verification"""
        try:
            db = SessionLocal()
            
            # Фильтр по статусу
            status_filter = self.pending_status_filter.currentData() if hasattr(self, 'pending_status_filter') else ""
            
            # Get materials that need verification
            query = db.query(MaterialEntry).filter(
                MaterialEntry.is_deleted == False
            )
            
            # Применяем фильтр по статусу, если выбран
            if status_filter:
                query = query.filter(MaterialEntry.status == status_filter)
            else:
                # Если не выбран конкретный статус, показываем все материалы в процессе лабораторной проверки
                query = query.filter(
                    MaterialEntry.status.in_([
                        MaterialStatus.LAB_CHECK_PENDING.value,
                        MaterialStatus.SAMPLES_REQUESTED.value,
                        MaterialStatus.SAMPLES_COLLECTED.value,
                        MaterialStatus.TESTING.value,
                        MaterialStatus.TESTING_COMPLETED.value
                    ])
                )
            
            # Получаем все подходящие материалы
            materials = query.order_by(desc(MaterialEntry.created_at)).all()
            
            # Clear table
            self.pending_materials_table.setRowCount(0)
            
            # Add materials to table
            for row, material in enumerate(materials):
                self.pending_materials_table.insertRow(row)
                
                # Material grade - очищаем от стандарта
                clean_grade = clean_material_grade(material.material_grade)
                grade_item = QTableWidgetItem(clean_grade)
                grade_item.setData(Qt.UserRole, material.id)  # Store ID in user role
                self.pending_materials_table.setItem(row, 0, grade_item)
                
                # Material type
                type_display = get_material_type_display(material.material_type)
                self.pending_materials_table.setItem(row, 1, QTableWidgetItem(type_display))
                
                # Размер (диаметр/толщина)
                size_text = ""
                if material.diameter:
                    size_text = f"Ø{material.diameter} мм"
                elif material.thickness:
                    size_text = f"{material.thickness}×{material.width}×{material.length} мм"
                self.pending_materials_table.setItem(row, 2, QTableWidgetItem(size_text))
                
                # Melt number
                self.pending_materials_table.setItem(row, 3, QTableWidgetItem(material.melt_number))
                
                # Supplier
                supplier = db.query(Supplier).filter(Supplier.id == material.supplier_id).first()
                supplier_name = supplier.name if supplier else "Неизвестно"
                self.pending_materials_table.setItem(row, 4, QTableWidgetItem(supplier_name))
                
                # Status
                status_text = get_status_display_name(material.status)
                status_item = QTableWidgetItem(status_text)
                self.pending_materials_table.setItem(row, 5, status_item)
                
                # Иконка состояния
                icon_item = QTableWidgetItem("")
                
                # Устанавливаем иконку в зависимости от статуса
                if material.status == MaterialStatus.LAB_CHECK_PENDING.value:
                    icon_item.setText("🔍")  # Лупа - ожидает проверки
                elif material.status == MaterialStatus.SAMPLES_REQUESTED.value:
                    icon_item.setText("📋")  # Запрошены пробы
                elif material.status == MaterialStatus.SAMPLES_COLLECTED.value:
                    icon_item.setText("✂️")  # Пробы отобраны
                elif material.status == MaterialStatus.TESTING.value:
                    icon_item.setText("🧪")  # На испытаниях
                elif material.status == MaterialStatus.TESTING_COMPLETED.value:
                    icon_item.setText("✓")  # Испытания завершены
                self.pending_materials_table.setItem(row, 6, icon_item)
                
                # Color row by status
                row_color = None
                if material.status == MaterialStatus.LAB_CHECK_PENDING.value:
                    row_color = QColor(200, 200, 255)  # Light blue
                elif material.status == MaterialStatus.SAMPLES_REQUESTED.value:
                    row_color = QColor(255, 255, 160)  # Light yellow
                elif material.status == MaterialStatus.SAMPLES_COLLECTED.value:
                    row_color = QColor(255, 220, 160)  # Light orange
                elif material.status == MaterialStatus.TESTING.value:
                    row_color = QColor(160, 255, 255)  # Light cyan
                elif material.status == MaterialStatus.TESTING_COMPLETED.value:
                    row_color = QColor(200, 255, 200)  # Light green
                
                if row_color:
                    self.color_row(self.pending_materials_table, row, row_color)
            
            # Update status
            self.parent.status_bar.showMessage(f"Загружено {len(materials)} материалов")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке материалов: {str(e)}")
        finally:
            db.close()
    
    def color_row(self, table, row, color):
        """Set background color for entire row"""
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setBackground(QBrush(color))
    
    def filter_pending_materials(self):
        """Filter materials by search text"""
        search_text = self.pending_search_input.text().lower()
        
        for row in range(self.pending_materials_table.rowCount()):
            show_row = True
            
            # Проверяем совпадение с поисковым запросом
            if search_text:
                match_found = False
                
                # Проверяем все столбцы кроме ID и иконки
                for col in range(1, 6):
                    item = self.pending_materials_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                if not match_found:
                    show_row = False
            
            # Скрываем или показываем строку
            self.pending_materials_table.setRowHidden(row, not show_row)
    
    def show_verification_form(self, row, column):
        """Show form to view/process material pending verification"""
        # Get material ID from the first column's user role
        material_id = self.pending_materials_table.item(row, 0).data(Qt.UserRole)
        
        try:
            # Get session
            db = SessionLocal()
            
            # Get material by ID
            material = db.query(MaterialEntry).filter(
                MaterialEntry.id == material_id
            ).first()
            
            if not material:
                QMessageBox.warning(self, "Ошибка", "Материал не найден")
                db.close()
                return
            
            # Create dialog
            verification_dialog = QDialog(self)
            verification_dialog.setWindowTitle(f"Проверка материала #{material.id}")
            verification_dialog.resize(700, 600)
            
            layout = QVBoxLayout(verification_dialog)
            
            # Material info section
            material_info_group = QGroupBox("Информация о материале")
            material_info_layout = QFormLayout(material_info_group)
            
            # Очищаем марку от стандарта
            clean_grade = clean_material_grade(material.material_grade)
            material_info_layout.addRow("Марка:", QLabel(clean_grade))
            material_info_layout.addRow("Тип:", QLabel(get_material_type_display(material.material_type)))
            material_info_layout.addRow("Партия:", QLabel(material.batch_number))
            material_info_layout.addRow("Плавка:", QLabel(material.melt_number))
            
            # Get supplier
            supplier = db.query(Supplier).filter(
                Supplier.id == material.supplier_id
            ).first()
            if supplier:
                material_info_layout.addRow("Поставщик:", QLabel(supplier.name))
            
            layout.addWidget(material_info_group)
            
            # Certificate section
            certificate_group = QGroupBox("Сертификат")
            certificate_layout = QVBoxLayout(certificate_group)
            
            if material.certificate_file_path:
                view_certificate_btn = QPushButton("Просмотреть сертификат")
                view_certificate_btn.clicked.connect(lambda: self.open_certificate(material.certificate_file_path))
                certificate_layout.addWidget(view_certificate_btn)
            else:
                certificate_layout.addWidget(QLabel("Сертификат не загружен"))
            
            layout.addWidget(certificate_group)
            
            # QC Check section if available
            qc_check = db.query(QCCheck).filter(
                QCCheck.material_entry_id == material.id,
                QCCheck.is_deleted == False
            ).first()
            
            if qc_check:
                qc_group = QGroupBox("Результаты проверки ОТК")
                qc_layout = QVBoxLayout(qc_group)
                
                # Create grid layout for QC check items with icons
                checks_layout = QFormLayout()
                
                # Function to create check result with icon
                def add_check_item(label, result):
                    check_layout = QHBoxLayout()
                    if result:
                        icon = QLabel("✅")  # Green checkmark for success
                        icon.setStyleSheet("color: green; font-size: 14px;")
                    else:
                        icon = QLabel("❌")  # Red X for failed checks
                        icon.setStyleSheet("color: red; font-size: 14px;")
                    
                    check_layout.addWidget(icon)
                    check_layout.addWidget(QLabel(label))
                    return check_layout
                
                checks_layout.addRow(add_check_item("Сертификат читабелен", qc_check.certificate_readable))
                checks_layout.addRow(add_check_item("Материал соответствует", qc_check.material_matches))
                checks_layout.addRow(add_check_item("Размеры соответствуют", qc_check.dimensions_match))
                checks_layout.addRow(add_check_item("Данные сертификата корректны", qc_check.certificate_data_correct))
                
                qc_layout.addLayout(checks_layout)
                
                if qc_check.notes:
                    qc_layout.addWidget(QLabel("Примечания ОТК:"))
                    qc_notes = QTextEdit()
                    qc_notes.setHtml(qc_check.notes) # Handle HTML content properly
                    qc_notes.setReadOnly(True)
                    qc_layout.addWidget(qc_notes)
                
                layout.addWidget(qc_group)
            
            # Test group - select tests to perform
            test_group = QGroupBox("Назначение испытаний")
            test_layout = QVBoxLayout(test_group)
            
            # Mechanical tests
            mech_label = QLabel("Механические испытания:")
            mech_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            test_layout.addWidget(mech_label)
            
            self.tensile_test_cb = QCheckBox("Испытание на растяжение")
            self.hardness_test_cb = QCheckBox("Испытание на твердость")
            self.impact_test_cb = QCheckBox("Испытание на ударную вязкость")
            
            test_layout.addWidget(self.tensile_test_cb)
            test_layout.addWidget(self.hardness_test_cb)
            test_layout.addWidget(self.impact_test_cb)
            
            # Chemical tests
            chem_label = QLabel("Химический анализ:")
            chem_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            test_layout.addWidget(chem_label)
            
            self.spectral_analysis_cb = QCheckBox("Спектральный анализ")
            self.carbon_content_cb = QCheckBox("Содержание углерода")
            self.other_elements_cb = QCheckBox("Другие элементы")
            
            test_layout.addWidget(self.spectral_analysis_cb)
            test_layout.addWidget(self.carbon_content_cb)
            test_layout.addWidget(self.other_elements_cb)
            
            # Metallographic tests
            met_label = QLabel("Металлографический анализ:")
            met_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            test_layout.addWidget(met_label)
            
            self.macro_structure_cb = QCheckBox("Макроструктура")
            self.micro_structure_cb = QCheckBox("Микроструктура")
            self.grain_size_cb = QCheckBox("Размер зерна")
            
            test_layout.addWidget(self.macro_structure_cb)
            test_layout.addWidget(self.micro_structure_cb)
            test_layout.addWidget(self.grain_size_cb)
            
            # Notes
            test_layout.addWidget(QLabel("Примечания:"))
            self.notes_text = QTextEdit()
            self.notes_text.setPlaceholderText("Дополнительные указания по проведению испытаний...")
            test_layout.addWidget(self.notes_text)
            
            layout.addWidget(test_group)
            
            # Add buttons for different actions
            buttons_layout = QHBoxLayout()
            
            # Buttons for automatic creation of tests based on checkbox selection
            create_tests_btn = QPushButton("Назначить выбранные испытания")
            create_tests_btn.clicked.connect(lambda: self.create_lab_test(material, verification_dialog))
            buttons_layout.addWidget(create_tests_btn)
            
            # Button for creating a new test using the detailed form
            create_detailed_test_btn = QPushButton("Новое испытание (подробно)")
            create_detailed_test_btn.clicked.connect(lambda: self.show_new_test_form(material_id))
            buttons_layout.addWidget(create_detailed_test_btn)
            
            # Close button
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(verification_dialog.reject)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            # Show dialog
            db.close()
            verification_dialog.exec_()
            
            # Reload materials list after dialog
            self.load_pending_materials()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму проверки: {str(e)}")
            
    def show_new_test_form(self, material_id):
        """Show form to create a new test for the material"""
        try:
            dialog = LabTestDetailDialog(self, material_entry_id=material_id)
            dialog.test_updated.connect(self.load_test_results)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму создания теста: {str(e)}")
    
    def load_sample_requests(self):
        """Load sample requests"""
        try:
            # Clear the current table
            self.sample_requests_table.setRowCount(0)
            
            # Get session
            db = SessionLocal()
            
            # Get status filter
            status_filter = self.request_status_filter.currentData()
            
            # Build query
            query = db.query(SampleRequest).filter(SampleRequest.is_deleted == False)
            
            if status_filter == "pending":
                query = query.filter(SampleRequest.is_collected == False)
            elif status_filter == "collected":
                query = query.filter(SampleRequest.is_collected == True)
            
            # Execute query
            requests = query.order_by(desc(SampleRequest.created_at)).all()
            
            # Populate table
            for row, request in enumerate(requests):
                self.sample_requests_table.insertRow(row)
                
                # Найдем информацию о материале
                material = db.query(MaterialEntry).filter(
                    MaterialEntry.id == request.material_entry_id
                ).first()
                
                # Марка материала - очищаем от стандарта
                if material:
                    clean_grade = clean_material_grade(material.material_grade)
                else:
                    clean_grade = "Неизвестно"
                material_item = QTableWidgetItem(clean_grade)
                material_item.setData(Qt.UserRole, request.id)  # Store request ID
                self.sample_requests_table.setItem(row, 0, material_item)
                
                # Партия
                batch_number = material.batch_number if material else "Неизвестно"
                self.sample_requests_table.setItem(row, 1, QTableWidgetItem(batch_number))
                
                # Размер пробы
                sample_size = f"{request.sample_size} {request.sample_unit}"
                self.sample_requests_table.setItem(row, 2, QTableWidgetItem(sample_size))
                
                # Отобрана
                collected = "Да" if request.is_collected else "Нет"
                self.sample_requests_table.setItem(row, 3, QTableWidgetItem(collected))
                
                # Отправлена
                sent = "Да" if request.is_sent_to_lab else "Нет"
                self.sample_requests_table.setItem(row, 4, QTableWidgetItem(sent))
            
            # Close session
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить заявки на пробы: {str(e)}")
    
    def filter_sample_requests(self):
        """Filter sample requests by search text"""
        search_text = self.request_search_input.text().lower()
        
        # If search text is empty, show all rows
        if not search_text:
            for row in range(self.sample_requests_table.rowCount()):
                self.sample_requests_table.setRowHidden(row, False)
            return
        
        # Otherwise, hide rows that don't match the search text
        for row in range(self.sample_requests_table.rowCount()):
            visible = False
            for col in range(self.sample_requests_table.columnCount()):
                item = self.sample_requests_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.sample_requests_table.setRowHidden(row, not visible)
    
    def show_sample_request_form(self, row, column):
        """Show form to view/edit sample request"""
        # Get request ID from the first column's user role
        request_id = self.sample_requests_table.item(row, 0).data(Qt.UserRole)
        
        # Создаем диалог
        dialog = SampleRequestDialog(request_id=request_id, user=self.user, parent=self)
        
        # Подключаем обработчик закрытия диалога
        dialog.finished.connect(lambda result: self.load_sample_requests() if result == QDialog.Accepted else None)
        
        # Показываем диалог
        dialog.exec()
        
        # Обновляем таблицу после закрытия диалога
        self.load_sample_requests()
    
    def load_test_results(self):
        """Load test results"""
        try:
            # Clear the current table
            self.test_results_table.setRowCount(0)
            
            # Get session
            db = SessionLocal()
            
            # Get status filter
            status_filter = self.test_status_filter.currentData()
            
            # Build query
            query = db.query(LabTest).filter(LabTest.is_deleted == False)
            
            if status_filter == "in_progress":
                query = query.filter(LabTest.is_passed == None)
            elif status_filter == "completed":
                query = query.filter(LabTest.is_passed != None)
            
            # Execute query
            lab_tests = query.order_by(desc(LabTest.performed_at)).all()
            
            # Populate table
            for row, test in enumerate(lab_tests):
                self.test_results_table.insertRow(row)
                
                # Найдем информацию о материале
                material = db.query(MaterialEntry).filter(
                    MaterialEntry.id == test.material_entry_id
                ).first()
                
                # Марка материала - очищаем от стандарта
                if material:
                    clean_grade = clean_material_grade(material.material_grade)
                else:
                    clean_grade = "Неизвестно"
                grade_item = QTableWidgetItem(clean_grade)
                grade_item.setData(Qt.UserRole, test.id)  # Store test ID
                self.test_results_table.setItem(row, 0, grade_item)
                
                # Партия
                batch_number = material.batch_number if material else "Неизвестно"
                self.test_results_table.setItem(row, 1, QTableWidgetItem(batch_number))
                
                # Тип теста
                test_type_display = {
                    "mechanical_tensile": "Механический (растяж.)",
                    "mechanical_hardness": "Механический (тверд.)",
                    "mechanical_impact": "Механический (удар)",
                    "chemical_spectral": "Химический (спектр)",
                    "chemical_carbon": "Химический (углерод)",
                    "chemical_elements": "Химический (элементы)",
                    "metallographic_macro": "Метал. (макро)",
                    "metallographic_micro": "Метал. (микро)",
                    "metallographic_grain": "Метал. (зерно)"
                }.get(test.test_type, test.test_type)
                self.test_results_table.setItem(row, 2, QTableWidgetItem(test_type_display))
                
                # Результат
                result_summary = "Нет данных"
                if test.results:
                    # Если результат длинный, показываем только первые 30 символов
                    if len(test.results) > 30:
                        result_summary = test.results[:30] + "..."
                    else:
                        result_summary = test.results
                self.test_results_table.setItem(row, 3, QTableWidgetItem(result_summary))
                
                # Годен/Брак/В процессе + цвет и иконка
                passed_item = QTableWidgetItem()
                if test.is_passed is None:
                    passed_item.setText("⏳ В процессе")
                    passed_item.setBackground(QBrush(QColor(255, 255, 180)))  # Желтый
                elif test.is_passed:
                    passed_item.setText("✔ Годен")
                    passed_item.setBackground(QBrush(QColor(200, 255, 200)))  # Зеленый
                else:
                    passed_item.setText("✖ Брак")
                    passed_item.setBackground(QBrush(QColor(255, 200, 200)))  # Красный
                self.test_results_table.setItem(row, 4, passed_item)
                
                # Цвет всей строки
                row_color = None
                if test.is_passed is None:
                    row_color = QColor(255, 255, 180)
                elif test.is_passed:
                    row_color = QColor(220, 255, 220)
                else:
                    row_color = QColor(255, 220, 220)
                if row_color:
                    self.color_row(self.test_results_table, row, row_color)
            
            # Close session
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить результаты испытаний: {str(e)}")
    
    def filter_test_results(self):
        """Filter test results by search text"""
        search_text = self.test_search_input.text().lower()
        
        # If search text is empty, show all rows
        if not search_text:
            for row in range(self.test_results_table.rowCount()):
                self.test_results_table.setRowHidden(row, False)
            return
        
        # Otherwise, hide rows that don't match the search text
        for row in range(self.test_results_table.rowCount()):
            visible = False
            for col in range(self.test_results_table.columnCount()):
                item = self.test_results_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            self.test_results_table.setRowHidden(row, not visible)
    
    def show_test_result_form(self, row, column):
        """Show form to view/edit test result"""
        test_id = self.test_results_table.item(row, 0).data(Qt.UserRole)
        
        try:
            dialog = LabTestDetailDialog(self, test_id=test_id)
            dialog.test_updated.connect(self.load_test_results)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму результата испытания: {str(e)}")
    
    def open_certificate(self, file_path):
        """Open certificate file"""
        import os
        import platform
        import subprocess
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux и другие Unix-подобные
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def create_lab_test(self, material, dialog):
        """Create lab test for material"""
        # Collect selected tests
        test_types = []
        
        # Mechanical tests
        if self.tensile_test_cb.isChecked():
            test_types.append("mechanical_tensile")
        if self.hardness_test_cb.isChecked():
            test_types.append("mechanical_hardness")
        if self.impact_test_cb.isChecked():
            test_types.append("mechanical_impact")
        
        # Chemical tests
        if self.spectral_analysis_cb.isChecked():
            test_types.append("chemical_spectral")
        if self.carbon_content_cb.isChecked():
            test_types.append("chemical_carbon")
        if self.other_elements_cb.isChecked():
            test_types.append("chemical_elements")
        
        # Metallographic tests
        if self.macro_structure_cb.isChecked():
            test_types.append("metallographic_macro")
        if self.micro_structure_cb.isChecked():
            test_types.append("metallographic_micro")
        if self.grain_size_cb.isChecked():
            test_types.append("metallographic_grain")
        
        # Check if any test is selected
        if not test_types:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один тип испытания")
            return
        
        # Get notes
        notes = self.notes_text.toPlainText()
        
        try:
            # Get session
            db = SessionLocal()
            
            # Update material status
            material = db.query(MaterialEntry).filter(
                MaterialEntry.id == material.id
            ).first()
            
            if material:
                material.status = MaterialStatus.TESTING.value
                
                # Create lab tests for each selected test type
                for test_type in test_types:
                    lab_test = LabTest(
                        material_entry_id=material.id,
                        performed_by_id=self.user.id,
                        test_type=test_type,
                        results=notes if notes else None
                    )
                    db.add(lab_test)
                
                db.commit()
                QMessageBox.information(self, "Успех", "Испытания назначены")
                dialog.accept()
                
                # Refresh materials list
                self.load_pending_materials()
                self.load_test_results()
            else:
                QMessageBox.warning(self, "Ошибка", "Материал не найден")
            
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать испытание: {str(e)}") 