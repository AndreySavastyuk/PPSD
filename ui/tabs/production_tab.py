from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                             QFormLayout, QMessageBox, QFileDialog, QHeaderView,
                             QGroupBox, QCheckBox, QTabWidget, QDialog, QDialogButtonBox,
                             QTextEdit, QDateTimeEdit, QInputDialog, QScrollArea,
                             QSplitter, QFrame)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QFont, QColor, QBrush, QIcon

from database.connection import SessionLocal
from models.models import MaterialEntry, MaterialStatus, SampleRequest, User
from sqlalchemy import desc
import datetime
import os
import shutil

class ProductionTab(QWidget):
    sample_updated = Signal()
    
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create title
        title_label = QLabel("Производство (подготовка проб и образцов)")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # Create tab widget for different views
        self.view_tabs = QTabWidget()
        
        # Pending sample requests tab
        self.pending_samples_tab = QWidget()
        self.setup_pending_samples_tab()
        self.view_tabs.addTab(self.pending_samples_tab, "Заявки на образцы")
        
        # Completed samples tab
        self.completed_samples_tab = QWidget()
        self.setup_completed_samples_tab()
        self.view_tabs.addTab(self.completed_samples_tab, "Изготовленные образцы")
        
        main_layout.addWidget(self.view_tabs)
    
    def setup_pending_samples_tab(self):
        """Setup the tab for pending sample requests"""
        layout = QVBoxLayout(self.pending_samples_tab)
        
        # Add info panel
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setFrameShadow(QFrame.Shadow.Raised)
        info_layout = QHBoxLayout(info_frame)
        
        info_text = QLabel("Здесь отображаются заявки на изготовление образцов. "
                           "Дважды щелкните по заявке для просмотра деталей и отметки о выполнении.")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Status filter
        status_label = QLabel("Статус:")
        toolbar_layout.addWidget(status_label)
        
        self.sample_status_filter = QComboBox()
        self.sample_status_filter.addItem("В обработке", "processing")
        self.sample_status_filter.addItem("Все", "")
        self.sample_status_filter.currentIndexChanged.connect(self.load_pending_samples)
        toolbar_layout.addWidget(self.sample_status_filter)
        
        # Search field
        self.sample_search_input = QLineEdit()
        self.sample_search_input.setPlaceholderText("Поиск...")
        self.sample_search_input.textChanged.connect(self.filter_pending_samples)
        toolbar_layout.addWidget(self.sample_search_input)
        
        # Refresh button
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_pending_samples)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create samples table
        self.pending_samples_table = QTableWidget()
        self.pending_samples_table.setColumnCount(5)
        self.pending_samples_table.setHorizontalHeaderLabels([
            "Марка материала", "Партия", "Размер пробы", "Тест", "Дата заявки"
        ])
        
        # Set column widths
        header = self.pending_samples_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect double click
        self.pending_samples_table.cellDoubleClicked.connect(self.show_sample_details)
        
        layout.addWidget(self.pending_samples_table)
        
        # Load data
        self.load_pending_samples()
    
    def setup_completed_samples_tab(self):
        """Setup the tab for completed samples"""
        layout = QVBoxLayout(self.completed_samples_tab)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Date filter
        date_label = QLabel("Период:")
        toolbar_layout.addWidget(date_label)
        
        self.date_filter = QComboBox()
        self.date_filter.addItem("Сегодня", "today")
        self.date_filter.addItem("Неделя", "week")
        self.date_filter.addItem("Месяц", "month")
        self.date_filter.addItem("Все", "all")
        self.date_filter.currentIndexChanged.connect(self.load_completed_samples)
        toolbar_layout.addWidget(self.date_filter)
        
        # Search field
        self.completed_search_input = QLineEdit()
        self.completed_search_input.setPlaceholderText("Поиск...")
        self.completed_search_input.textChanged.connect(self.filter_completed_samples)
        toolbar_layout.addWidget(self.completed_search_input)
        
        # Refresh button
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_completed_samples)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create samples table
        self.completed_samples_table = QTableWidget()
        self.completed_samples_table.setColumnCount(6)
        self.completed_samples_table.setHorizontalHeaderLabels([
            "Марка материала", "Партия", "Размер пробы", "Тест", "Дата изготовления", "Изготовитель"
        ])
        
        # Set column widths
        header = self.completed_samples_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect double click
        self.completed_samples_table.cellDoubleClicked.connect(self.show_sample_details)
        
        layout.addWidget(self.completed_samples_table)
        
        # Load data
        self.load_completed_samples()
    
    def load_pending_samples(self):
        """Load pending sample requests"""
        try:
            # Clear the table
            self.pending_samples_table.setRowCount(0)
            
            # Get the session
            db = SessionLocal()
            
            # Get status filter
            status_filter = self.sample_status_filter.currentData()
            
            # Build query for sample requests
            query = db.query(SampleRequest).filter(
                SampleRequest.is_deleted == False
            )
            
            if status_filter == "processing":
                # Show only samples that are not collected yet
                query = query.filter(
                    SampleRequest.is_collected == False
                )
            
            # Execute query
            sample_requests = query.order_by(desc(SampleRequest.created_at)).all()
            
            # Populate table
            for row, request in enumerate(sample_requests):
                # Get material info
                material = db.query(MaterialEntry).filter(
                    MaterialEntry.id == request.material_entry_id
                ).first()
                
                # Skip if material not found
                if not material:
                    continue
                
                self.pending_samples_table.insertRow(row)
                
                # Марка материала
                material_grade = material.material_grade
                grade_item = QTableWidgetItem(material_grade)
                grade_item.setData(Qt.UserRole, request.id)  # Store request ID
                self.pending_samples_table.setItem(row, 0, grade_item)
                
                # Партия
                batch_number = material.batch_number or "Н/Д"
                self.pending_samples_table.setItem(row, 1, QTableWidgetItem(batch_number))
                
                # Размер пробы
                sample_size = f"{request.sample_size} {request.sample_unit}"
                self.pending_samples_table.setItem(row, 2, QTableWidgetItem(sample_size))
                
                # Тип теста
                test_types = []
                if request.mechanical_test:
                    test_types.append("Механические")
                if request.chemical_test:
                    test_types.append("Химические")
                if request.metallographic_test:
                    test_types.append("Металлография")
                
                test_type_str = ", ".join(test_types) if test_types else "Не указано"
                self.pending_samples_table.setItem(row, 3, QTableWidgetItem(test_type_str))
                
                # Дата заявки
                date_str = request.created_at.strftime("%d.%m.%Y %H:%M") if request.created_at else ""
                self.pending_samples_table.setItem(row, 4, QTableWidgetItem(date_str))
                
                # Highlight the row based on request status
                if not request.is_collected:
                    self.color_row(self.pending_samples_table, row, QColor(255, 255, 180))  # Light yellow
            
            # Close session
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке заявок: {str(e)}")
    
    def load_completed_samples(self):
        """Load completed samples"""
        try:
            # Clear the table
            self.completed_samples_table.setRowCount(0)
            
            # Get the session
            db = SessionLocal()
            
            # Get date filter
            date_filter = self.date_filter.currentData()
            
            # Build query for sample requests
            query = db.query(SampleRequest).filter(
                SampleRequest.is_deleted == False,
                SampleRequest.is_collected == True
            )
            
            # Apply date filter
            now = datetime.datetime.now()
            if date_filter == "today":
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(SampleRequest.collected_at >= today_start)
            elif date_filter == "week":
                week_start = now - datetime.timedelta(days=now.weekday())
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(SampleRequest.collected_at >= week_start)
            elif date_filter == "month":
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(SampleRequest.collected_at >= month_start)
            
            # Execute query
            completed_requests = query.order_by(desc(SampleRequest.collected_at)).all()
            
            # Populate table
            for row, request in enumerate(completed_requests):
                # Get material info
                material = db.query(MaterialEntry).filter(
                    MaterialEntry.id == request.material_entry_id
                ).first()
                
                # Skip if material not found
                if not material:
                    continue
                    
                # Get user who created the request
                user = db.query(User).filter(
                    User.id == request.created_by_id
                ).first()
                
                self.completed_samples_table.insertRow(row)
                
                # Марка материала
                material_grade = material.material_grade
                grade_item = QTableWidgetItem(material_grade)
                grade_item.setData(Qt.UserRole, request.id)  # Store request ID
                self.completed_samples_table.setItem(row, 0, grade_item)
                
                # Партия
                batch_number = material.batch_number or "Н/Д"
                self.completed_samples_table.setItem(row, 1, QTableWidgetItem(batch_number))
                
                # Размер пробы
                sample_size = f"{request.sample_size} {request.sample_unit}"
                self.completed_samples_table.setItem(row, 2, QTableWidgetItem(sample_size))
                
                # Тип теста
                test_types = []
                if request.mechanical_test:
                    test_types.append("Механические испытания")
                if request.chemical_test:
                    test_types.append("Химический анализ")
                if request.metallographic_test:
                    test_types.append("Металлографический анализ")
                
                test_type_str = ", ".join(test_types) if test_types else "Не указано"
                self.completed_samples_table.setItem(row, 3, QTableWidgetItem(test_type_str))
                
                # Дата изготовления
                date_str = request.collected_at.strftime("%d.%m.%Y %H:%M") if request.collected_at else ""
                self.completed_samples_table.setItem(row, 4, QTableWidgetItem(date_str))
                
                # Изготовитель
                user_name = user.full_name if user else "Неизвестно"
                self.completed_samples_table.setItem(row, 5, QTableWidgetItem(user_name))
                
                # Highlight the row indicating it's completed
                self.color_row(self.completed_samples_table, row, QColor(220, 255, 220))  # Light green
            
            # Close session
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке образцов: {str(e)}")
    
    def filter_pending_samples(self):
        """Filter pending samples table by search text"""
        search_text = self.sample_search_input.text().lower()
        
        for row in range(self.pending_samples_table.rowCount()):
            show_row = False
            
            # If search text is empty, show all rows
            if not search_text:
                show_row = True
            else:
                # Check if search text matches any cell in the row
                for col in range(self.pending_samples_table.columnCount()):
                    item = self.pending_samples_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            
            # Hide or show the row
            self.pending_samples_table.setRowHidden(row, not show_row)
    
    def filter_completed_samples(self):
        """Filter completed samples table by search text"""
        search_text = self.completed_search_input.text().lower()
        
        for row in range(self.completed_samples_table.rowCount()):
            show_row = False
            
            # If search text is empty, show all rows
            if not search_text:
                show_row = True
            else:
                # Check if search text matches any cell in the row
                for col in range(self.completed_samples_table.columnCount()):
                    item = self.completed_samples_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            
            # Hide or show the row
            self.completed_samples_table.setRowHidden(row, not show_row)
    
    def show_sample_details(self, row, column):
        """Show details about a sample request and allow marking it as completed"""
        if self.view_tabs.currentIndex() == 0:
            # Pending samples tab
            table = self.pending_samples_table
        else:
            # Completed samples tab
            table = self.completed_samples_table
        
        # Get request ID from data
        request_id = table.item(row, 0).data(Qt.UserRole)
        
        try:
            # Get session
            db = SessionLocal()
            
            # Get request
            request = db.query(SampleRequest).filter(
                SampleRequest.id == request_id,
                SampleRequest.is_deleted == False
            ).first()
            
            if not request:
                QMessageBox.warning(self, "Ошибка", "Заявка не найдена")
                db.close()
                return
            
            # Get material
            material = db.query(MaterialEntry).filter(
                MaterialEntry.id == request.material_entry_id
            ).first()
            
            if not material:
                QMessageBox.warning(self, "Ошибка", "Материал не найден")
                db.close()
                return
            
            # Create dialog
            details_dialog = SampleDetailsDialog(self, request, material, self.user)
            
            if details_dialog.exec() == QDialog.Accepted:
                # Reload data after dialog is closed
                self.load_pending_samples()
                self.load_completed_samples()
                
                # Emit signal that sample was updated
                self.sample_updated.emit()
            
            # Close session
            db.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии деталей: {str(e)}")
    
    def color_row(self, table, row, color):
        """Set background color for entire row"""
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setBackground(QBrush(color))


class SampleDetailsDialog(QDialog):
    def __init__(self, parent, request, material, user):
        super().__init__(parent)
        self.parent = parent
        self.request = request
        self.material = material
        self.user = user
        self.setWindowTitle(f"Детали заявки на образцы #{request.id}")
        self.resize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Material info section
        material_group = QGroupBox("Информация о материале")
        material_layout = QFormLayout(material_group)
        
        material_layout.addRow("Марка:", QLabel(self.material.material_grade))
        material_layout.addRow("Тип:", QLabel(self.material.material_type))
        material_layout.addRow("Партия:", QLabel(self.material.batch_number or ""))
        material_layout.addRow("Плавка:", QLabel(self.material.melt_number))
        
        # Display size information based on material type
        size_info = ""
        if self.material.material_type == "rod":
            size_info = f"Ø{self.material.diameter} мм"
        elif self.material.material_type == "sheet":
            size_info = f"{self.material.thickness}×{self.material.width}×{self.material.length} мм"
        elif self.material.material_type == "pipe":
            size_info = f"Ø{self.material.diameter}×{self.material.wall_thickness} мм, L={self.material.length} мм"
        
        material_layout.addRow("Размеры:", QLabel(size_info))
        
        layout.addWidget(material_group)
        
        # Sample request info
        request_group = QGroupBox("Информация о заявке")
        request_layout = QFormLayout(request_group)
        
        request_layout.addRow("Размер пробы:", QLabel(f"{self.request.sample_size} {self.request.sample_unit}"))
        
        test_types = []
        if self.request.mechanical_test:
            test_types.append("Механические испытания")
        if self.request.chemical_test:
            test_types.append("Химический анализ")
        if self.request.metallographic_test:
            test_types.append("Металлографический анализ")
        
        request_layout.addRow("Типы испытаний:", QLabel(", ".join(test_types)))
        
        # Sample cutting diagram
        diagram_group = QGroupBox("Схема вырезки образцов")
        diagram_layout = QVBoxLayout(diagram_group)
        
        self.diagram_text = QTextEdit()
        self.diagram_text.setReadOnly(True)
        
        # Set diagram text based on material type and test types
        diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
        
        if self.material.material_type == "rod":
            diagram_text += "• Для механических испытаний: отрезать от торца стержня образец длиной не менее 200 мм\n"
            diagram_text += "• Для химического анализа: стружка с любого участка или фрагмент Ø10×10 мм\n"
            diagram_text += "• Для металлографии: поперечный срез толщиной 10-15 мм\n"
        elif self.material.material_type == "sheet":
            diagram_text += "• Для механических испытаний: вырезать образец размером 300×100 мм с середины листа\n"
            diagram_text += "• Для химического анализа: фрагмент 20×20 мм с любого участка\n"
            diagram_text += "• Для металлографии: образец 20×20 мм с края листа\n"
        elif self.material.material_type == "pipe":
            diagram_text += "• Для механических испытаний: отрезать кольцо шириной 50 мм\n"
            diagram_text += "• Для химического анализа: стружка или фрагмент 10×10 мм\n"
            diagram_text += "• Для металлографии: поперечный срез шириной 10-15 мм\n"
        
        self.diagram_text.setText(diagram_text)
        diagram_layout.addWidget(self.diagram_text)
        
        # Actual cutting place
        if not self.request.is_collected:
            # Create form for sample location
            self.sample_location_combo = QComboBox()
            
            # Add location options based on material type
            if self.material.material_type == "rod":
                self.sample_location_combo.addItems(["Выберите место...", "С торца стержня", "Из середины стержня", "Произвольно"])
            elif self.material.material_type == "sheet":
                self.sample_location_combo.addItems(["Выберите место...", "С края листа", "Из середины листа", "По диагонали"])
            elif self.material.material_type == "pipe":
                self.sample_location_combo.addItems(["Выберите место...", "С торца трубы", "Из середины трубы", "Произвольно"])
            else:
                self.sample_location_combo.addItems(["Выберите место...", "Произвольно"])
            
            diagram_layout.addWidget(QLabel("Место отбора:"))
            diagram_layout.addWidget(self.sample_location_combo)
            
            self.sample_description = QTextEdit()
            self.sample_description.setPlaceholderText("Укажите дополнительные детали по месту вырезки образца...")
            diagram_layout.addWidget(QLabel("Дополнительное описание:"))
            diagram_layout.addWidget(self.sample_description)
            
            # Add custom cutting scheme option
            self.custom_scheme_check = QCheckBox("Использовать специальную схему разделки")
            self.custom_scheme_check.setChecked(False)
            diagram_layout.addWidget(self.custom_scheme_check)
            
            # Show existing values if available
            if self.request.sample_location:
                index = self.sample_location_combo.findText(self.request.sample_location)
                if index >= 0:
                    self.sample_location_combo.setCurrentIndex(index)
            
            if self.request.sample_description:
                self.sample_description.setPlainText(self.request.sample_description)
            
            if self.request.sample_cutting_scheme:
                self.custom_scheme_check.setChecked(True)
        else:
            # Show existing location and description as read-only
            location_text = self.request.sample_location if self.request.sample_location else "Не указано"
            diagram_layout.addWidget(QLabel(f"Место отбора: {location_text}"))
            
            if self.request.sample_description:
                description_label = QLabel("Дополнительное описание:")
                diagram_layout.addWidget(description_label)
                
                description_text = QTextEdit()
                description_text.setPlainText(self.request.sample_description)
                description_text.setReadOnly(True)
                diagram_layout.addWidget(description_text)
        
        # Sample completion section with controls only if not collected yet
        self.status_group = QGroupBox("Статус изготовления образцов")
        status_layout = QFormLayout(self.status_group)
        
        if not self.request.is_collected:
            self.collected_check = QCheckBox("Образцы изготовлены")
            self.collected_check.setChecked(False)
            status_layout.addRow(self.collected_check)
            
            self.sent_check = QCheckBox("Образцы отправлены в лабораторию")
            self.sent_check.setChecked(False)
            status_layout.addRow(self.sent_check)
            
            self.sample_notes = QTextEdit()
            self.sample_notes.setPlaceholderText("Примечания по изготовленным образцам...")
            status_layout.addRow("Примечания:", self.sample_notes)
        else:
            # Display when the sample was collected and by whom
            db = SessionLocal()
            user = db.query(User).filter(User.id == self.request.created_by_id).first()
            db.close()
            
            collector_name = user.full_name if user else "Неизвестно"
            collected_date = self.request.collected_at.strftime("%d.%m.%Y %H:%M") if self.request.collected_at else "Неизвестно"
            
            status_layout.addRow("Статус:", QLabel("Образцы изготовлены"))
            status_layout.addRow("Отправлены в ЦЗЛ:", QLabel("Да" if self.request.is_sent_to_lab else "Нет"))
            status_layout.addRow("Дата изготовления:", QLabel(collected_date))
            status_layout.addRow("Изготовитель:", QLabel(collector_name))
        
        # Add groups to main layout
        layout.addWidget(request_group)
        layout.addWidget(diagram_group)
        layout.addWidget(self.status_group)
        
        # Buttons
        buttons = QDialogButtonBox()
        
        if not self.request.is_collected:
            self.save_btn = QPushButton("Сохранить")
            self.save_btn.clicked.connect(self.save_changes)
            buttons.addButton(self.save_btn, QDialogButtonBox.AcceptRole)
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.reject)
        buttons.addButton(self.close_btn, QDialogButtonBox.RejectRole)
        
        layout.addWidget(buttons)
    
    def save_changes(self):
        """Save changes to the sample request"""
        try:
            # Get session
            db = SessionLocal()
            
            # Get request by ID
            request = db.query(SampleRequest).filter(
                SampleRequest.id == self.request.id
            ).first()
            
            if not request:
                QMessageBox.warning(self, "Ошибка", "Заявка не найдена")
                db.close()
                return
            
            # Update request fields
            if hasattr(self, 'sample_location_combo') and self.sample_location_combo.currentText() != "Выберите место...":
                request.sample_location = self.sample_location_combo.currentText()
            
            if hasattr(self, 'sample_description') and self.sample_description.toPlainText():
                request.sample_description = self.sample_description.toPlainText()
            
            if hasattr(self, 'collected_check') and self.collected_check.isChecked():
                request.is_collected = True
                request.collected_at = datetime.datetime.utcnow()
                request.manufactured_by_id = self.user.id  # Store who manufactured the sample
                
                if hasattr(self, 'sent_check') and self.sent_check.isChecked():
                    request.is_sent_to_lab = True
                
                # Add notes if provided
                if hasattr(self, 'sample_notes') and self.sample_notes.toPlainText():
                    request.manufacturing_notes = self.sample_notes.toPlainText()
                    
                    # Add to sample description for backward compatibility
                    if request.sample_description:
                        request.sample_description += "\n\n--- Примечания по изготовлению ---\n" + self.sample_notes.toPlainText()
                    else:
                        request.sample_description = "--- Примечания по изготовлению ---\n" + self.sample_notes.toPlainText()
                
                # Update material status
                material = db.query(MaterialEntry).filter(
                    MaterialEntry.id == request.material_entry_id
                ).first()
                
                if material:
                    # Update material status to SAMPLES_COLLECTED if it's in SAMPLES_REQUESTED state
                    if material.status == MaterialStatus.SAMPLES_REQUESTED.value:
                        material.status = MaterialStatus.SAMPLES_COLLECTED.value
                        db.add(material)
            
            if hasattr(self, 'custom_scheme_check') and self.custom_scheme_check.isChecked():
                request.sample_cutting_scheme = True
            
            db.add(request)
            db.commit()
            db.close()
            
            QMessageBox.information(self, "Успех", "Информация об образцах сохранена")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}") 