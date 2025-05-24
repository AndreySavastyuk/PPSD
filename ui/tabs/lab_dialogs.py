from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                               QTextEdit, QGroupBox, QMessageBox, QCheckBox, QFileDialog,
                               QTabWidget, QWidget, QInputDialog, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame, QScrollArea)
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtGui import QFont, QColor, QBrush, QIcon, QPixmap, QTextDocument

from database.connection import SessionLocal
from models.models import MaterialEntry, SampleRequest, LabTest, MaterialStatus, TestType, Supplier, User, QCCheck, Sample, LabTestSample
import os
import datetime
import shutil
from ui.tabs.sample_management_dialog import SampleManagementDialog
from ui.styles import apply_table_style

class MaterialDetailsDialog(QDialog):
    """Dialog to show details of a material pending lab check"""
    def __init__(self, material_id, user, parent=None):
        super().__init__(parent)
        self.material_id = material_id
        self.user = user
        self.parent = parent
        self.material = None
        self.qc_check = None
        self.init_ui()
        self.load_material_data()
        
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Детали материала")
        self.setMinimumSize(900, 650)
        
        layout = QVBoxLayout(self)
        
        # Material information section
        info_group = QGroupBox("Информация о материале")
        info_layout = QFormLayout()
        
        self.material_grade_label = QLabel()
        info_layout.addRow("Марка материала:", self.material_grade_label)
        
        self.material_type_label = QLabel()
        info_layout.addRow("Тип материала:", self.material_type_label)
        
        self.melt_number_label = QLabel()
        info_layout.addRow("Плавка:", self.melt_number_label)
        
        self.batch_number_label = QLabel()
        info_layout.addRow("Партия:", self.batch_number_label)
        
        self.certificate_number_label = QLabel()
        info_layout.addRow("Номер сертификата:", self.certificate_number_label)
        
        self.certificate_date_label = QLabel()
        info_layout.addRow("Дата сертификата:", self.certificate_date_label)
        
        self.order_number_label = QLabel()
        info_layout.addRow("Номер заказа:", self.order_number_label)
        
        self.supplier_label = QLabel()
        info_layout.addRow("Поставщик:", self.supplier_label)
        
        self.created_at_label = QLabel()
        info_layout.addRow("Дата поступления:", self.created_at_label)
        
        self.status_label = QLabel()
        info_layout.addRow("Статус:", self.status_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # QC check results section
        self.qc_results_group = QGroupBox("Результаты проверки ОТК")
        qc_layout = QVBoxLayout()
        
        # Таблица с основными параметрами проверки
        self.qc_main_checks = QTableWidget()
        self.qc_main_checks.setColumnCount(3)
        self.qc_main_checks.setHorizontalHeaderLabels(["Параметр", "Статус", ""])
        self.qc_main_checks.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.qc_main_checks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.qc_main_checks.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.qc_main_checks.setRowCount(4)
        
        # Зададим заголовки параметров
        self.qc_main_checks.setItem(0, 0, QTableWidgetItem("Сертификат читаемый"))
        self.qc_main_checks.setItem(1, 0, QTableWidgetItem("Материал соответствует"))
        self.qc_main_checks.setItem(2, 0, QTableWidgetItem("Размеры соответствуют"))
        self.qc_main_checks.setItem(3, 0, QTableWidgetItem("Данные сертификата корректны"))
        
        self.qc_main_checks.setMaximumHeight(150)
        qc_layout.addWidget(self.qc_main_checks)
        
        # Таблица с замечаниями
        self.issues_label = QLabel("Замечания ОТК:")
        self.issues_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        qc_layout.addWidget(self.issues_label)
        
        self.qc_issues = QTableWidget()
        self.qc_issues.setColumnCount(2)
        self.qc_issues.setHorizontalHeaderLabels(["Замечание", "Статус"])
        self.qc_issues.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.qc_issues.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.qc_issues.setRowCount(8)
        
        # Зададим заголовки замечаний
        self.qc_issues.setItem(0, 0, QTableWidgetItem("Перекуп"))
        self.qc_issues.setItem(1, 0, QTableWidgetItem("Плохое качество сертификата"))
        self.qc_issues.setItem(2, 0, QTableWidgetItem("Нет печати"))
        self.qc_issues.setItem(3, 0, QTableWidgetItem("Отклонение по диаметру"))
        self.qc_issues.setItem(4, 0, QTableWidgetItem("Трещины"))
        self.qc_issues.setItem(5, 0, QTableWidgetItem("Не набита плавка"))
        self.qc_issues.setItem(6, 0, QTableWidgetItem("Нет сертификата"))
        self.qc_issues.setItem(7, 0, QTableWidgetItem("Копия (без синей печати)"))
        
        self.qc_issues.setMaximumHeight(250)
        qc_layout.addWidget(self.qc_issues)
        
        # Химический состав
        self.chem_label = QLabel("Химический состав (%):")
        self.chem_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        qc_layout.addWidget(self.chem_label)
        
        self.chem_table = QTableWidget()
        self.chem_table.setColumnCount(7)
        self.chem_table.setHorizontalHeaderLabels(["C", "Si", "Mn", "S", "P", "Cr", "Ni"])
        self.chem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chem_table.setRowCount(1)
        
        # Еще одна таблица для остальных элементов
        self.chem_more_table = QTableWidget()
        self.chem_more_table.setColumnCount(6)
        self.chem_more_table.setHorizontalHeaderLabels(["Cu", "Ti", "Al", "Mo", "V", "Nb"])
        self.chem_more_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chem_more_table.setRowCount(1)
        
        self.chem_table.setMaximumHeight(80)
        self.chem_more_table.setMaximumHeight(80)
        
        qc_layout.addWidget(self.chem_table)
        qc_layout.addWidget(self.chem_more_table)
        
        # Комментарии
        self.comments_label = QLabel("Комментарии ОТК:")
        self.comments_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        qc_layout.addWidget(self.comments_label)
        
        self.comments_area = QTextEdit()
        self.comments_area.setReadOnly(True)
        self.comments_area.setMaximumHeight(120)
        qc_layout.addWidget(self.comments_area)
        
        self.qc_results_group.setLayout(qc_layout)
        layout.addWidget(self.qc_results_group)
        
        # Certificate actions
        cert_group = QGroupBox("Сертификат")
        cert_layout = QHBoxLayout()
        
        self.certificate_path_label = QLabel("Сертификат не загружен")
        cert_layout.addWidget(self.certificate_path_label)
        
        self.view_cert_btn = QPushButton("Просмотреть сертификат")
        self.view_cert_btn.clicked.connect(self.view_certificate)
        cert_layout.addWidget(self.view_cert_btn)
        
        cert_group.setLayout(cert_layout)
        layout.addWidget(cert_group)
        
        # Sample requests tab
        tabs = QTabWidget()
        
        # Sample requests tab
        samples_tab = QWidget()
        samples_layout = QVBoxLayout(samples_tab)
        
        self.samples_group = QGroupBox("Запросы на пробы")
        self.samples_layout = QVBoxLayout(self.samples_group)
        samples_layout.addWidget(self.samples_group)
        
        # New sample request button
        self.new_sample_btn = QPushButton("Новый запрос на пробу")
        self.new_sample_btn.clicked.connect(self.request_sample)
        samples_layout.addWidget(self.new_sample_btn)
        
        tabs.addTab(samples_tab, "Запросы на пробы")
        
        # Test results tab
        tests_tab = QWidget()
        tests_layout = QVBoxLayout(tests_tab)
        
        self.tests_group = QGroupBox("Результаты испытаний")
        self.tests_layout = QVBoxLayout(self.tests_group)
        tests_layout.addWidget(self.tests_group)
        
        # New test button
        self.new_test_btn = QPushButton("Новое испытание")
        self.new_test_btn.clicked.connect(self.start_test)
        tests_layout.addWidget(self.new_test_btn)
        
        tabs.addTab(tests_tab, "Испытания")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        buttons_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_material_data(self):
        """Load material data from the database"""
        db = SessionLocal()
        try:
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if not self.material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден")
                self.reject()
                return
            
            # Set material info
            self.material_grade_label.setText(self.material.material_grade)
            self.material_type_label.setText(self.get_material_type_display(self.material.material_type))
            self.melt_number_label.setText(self.material.melt_number)
            self.batch_number_label.setText(self.material.batch_number or "Н/Д")
            self.certificate_number_label.setText(self.material.certificate_number)
            
            # Certificate date
            if self.material.certificate_date:
                cert_date_str = self.material.certificate_date.strftime("%d.%m.%Y")
                self.certificate_date_label.setText(cert_date_str)
            else:
                self.certificate_date_label.setText("Н/Д")
            
            self.order_number_label.setText(self.material.order_number or "Н/Д")
            
            # Supplier
            supplier = db.query(Supplier).filter(Supplier.id == self.material.supplier_id).first()
            supplier_name = supplier.name if supplier else "Неизвестно"
            self.supplier_label.setText(supplier_name)
            
            # Created date
            created_str = self.material.created_at.strftime("%d.%m.%Y %H:%M")
            self.created_at_label.setText(created_str)
            
            # Status
            self.status_label.setText(self.get_status_display(self.material.status))
            
            # Применяем улучшения ко всем таблицам в диалоге
            for table in [self.qc_main_checks, self.qc_issues, self.chem_table, self.chem_more_table]:
                self.apply_table_improvements(table)
            
            # Load QC check data
            self.load_qc_check_data(db)
            
            # Check certificate
            if self.material.certificate_file_path:
                self.certificate_path_label.setText(os.path.basename(self.material.certificate_file_path))
                self.view_cert_btn.setEnabled(True)
            else:
                self.view_cert_btn.setEnabled(False)
            
            # Load sample requests
            self.load_sample_requests(db)
            
            # Load test results
            self.load_test_results(db)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def load_qc_check_data(self, db):
        """Загрузка данных о проверке ОТК"""
        self.qc_check = db.query(QCCheck).filter(QCCheck.material_entry_id == self.material_id).first()
        
        if not self.qc_check:
            # Нет данных о проверке ОТК
            for row in range(self.qc_main_checks.rowCount()):
                self.qc_main_checks.setItem(row, 1, QTableWidgetItem("Не проверено"))
                
                # Добавляем пустой статус
                status_item = QTableWidgetItem("")
                self.qc_main_checks.setItem(row, 2, status_item)
            
            for row in range(self.qc_issues.rowCount()):
                self.qc_issues.setItem(row, 1, QTableWidgetItem("Не проверено"))
            
            # Пустая таблица химического состава
            for col in range(self.chem_table.columnCount()):
                self.chem_table.setItem(0, col, QTableWidgetItem("—"))
            
            for col in range(self.chem_more_table.columnCount()):
                self.chem_more_table.setItem(0, col, QTableWidgetItem("—"))
            
            self.comments_area.setText("Нет комментариев от ОТК")
            return
        
        # Заполнение основных проверок
        check_fields = [
            (0, self.qc_check.certificate_readable),
            (1, self.qc_check.material_matches),
            (2, self.qc_check.dimensions_match),
            (3, self.qc_check.certificate_data_correct)
        ]
        
        for row, value in check_fields:
            status_text = "✓ Да" if value else "✗ Нет"
            status_item = QTableWidgetItem(status_text)
            
            # Устанавливаем цвет ячейки в зависимости от статуса
            if value:
                status_item.setBackground(QBrush(QColor(200, 255, 200)))  # Зеленый
            else:
                status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Красный
            
            self.qc_main_checks.setItem(row, 1, status_item)
            
            # Добавляем иконку статуса
            icon_item = QTableWidgetItem()
            if value:
                icon_item.setBackground(QBrush(QColor(200, 255, 200)))  # Зеленый
            else:
                icon_item.setBackground(QBrush(QColor(255, 200, 200)))  # Красный
            
            self.qc_main_checks.setItem(row, 2, icon_item)
        
        # Заполнение замечаний
        issue_fields = [
            (0, self.qc_check.issue_repurchase),
            (1, self.qc_check.issue_poor_quality),
            (2, self.qc_check.issue_no_stamp),
            (3, self.qc_check.issue_diameter_deviation),
            (4, self.qc_check.issue_cracks),
            (5, self.qc_check.issue_no_melt),
            (6, self.qc_check.issue_no_certificate),
            (7, self.qc_check.issue_copy)
        ]
        
        for row, value in issue_fields:
            # Если есть замечание (True), то это плохо
            status_text = "✗ Да" if value else "✓ Нет"
            status_item = QTableWidgetItem(status_text)
            
            # Устанавливаем цвет ячейки в зависимости от статуса (обратная логика)
            if value:
                status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Красный
            else:
                status_item.setBackground(QBrush(QColor(200, 255, 200)))  # Зеленый
                
            self.qc_issues.setItem(row, 1, status_item)
        
        # Заполнение химического состава
        chem_values = [
            self.qc_check.chem_c,
            self.qc_check.chem_si,
            self.qc_check.chem_mn,
            self.qc_check.chem_s,
            self.qc_check.chem_p,
            self.qc_check.chem_cr,
            self.qc_check.chem_ni
        ]
        
        for col, value in enumerate(chem_values):
            text = f"{value:.3f}" if value is not None else "—"
            self.chem_table.setItem(0, col, QTableWidgetItem(text))
        
        # Остальные элементы
        more_chem_values = [
            self.qc_check.chem_cu,
            self.qc_check.chem_ti,
            self.qc_check.chem_al,
            self.qc_check.chem_mo,
            self.qc_check.chem_v,
            self.qc_check.chem_nb
        ]
        
        for col, value in enumerate(more_chem_values):
            text = f"{value:.3f}" if value is not None else "—"
            self.chem_more_table.setItem(0, col, QTableWidgetItem(text))
        
        # Комментарии ОТК
        if self.qc_check.notes:
            # Преобразуем HTML-разметку в обычный текст для отображения
            doc = QTextDocument()
            doc.setHtml(self.qc_check.notes)
            plain_text = doc.toPlainText()
            self.comments_area.setPlainText(plain_text)
        else:
            self.comments_area.setText("Нет комментариев от ОТК")
        
        # После заполнения таблицы данными:
        self.qc_main_checks.resizeColumnsToContents()
        self.qc_issues.resizeColumnsToContents()
        self.chem_table.resizeColumnsToContents()
        self.chem_more_table.resizeColumnsToContents()
        max_width = 300
        for table in [self.qc_main_checks, self.qc_issues, self.chem_table, self.chem_more_table]:
            for col in range(table.columnCount()):
                w = table.columnWidth(col)
                if w > max_width:
                    table.setColumnWidth(col, max_width)
        # Минимальная ширина для первой колонки в каждой таблице
        for table in [self.qc_main_checks, self.qc_issues, self.chem_table, self.chem_more_table]:
            if table.columnCount() > 0:
                table.setColumnWidth(0, max(table.columnWidth(0), 60))
    
    def load_sample_requests(self, db):
        """Load sample requests for this material"""
        # Clear existing content
        while self.samples_layout.count():
            item = self.samples_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Get sample requests
        requests = db.query(SampleRequest).filter(
            SampleRequest.material_entry_id == self.material_id,
            SampleRequest.is_deleted == False
        ).order_by(SampleRequest.created_at.desc()).all()
        
        if not requests:
            self.samples_layout.addWidget(QLabel("Нет запросов на пробы"))
            return
        
        # Add each request
        for request in requests:
            # Create a group for each request
            request_group = QGroupBox(f"Запрос #{request.id} от {request.created_at.strftime('%d.%m.%Y')}")
            request_layout = QFormLayout()
            
            # Size
            size_info = f"{request.sample_size} {request.sample_unit}"
            request_layout.addRow("Размер пробы:", QLabel(size_info))
            
            # Description
            request_layout.addRow("Описание:", QLabel(request.sample_description or "-"))
            
            # Tests to perform
            tests = []
            if request.mechanical_test:
                tests.append("Механические испытания")
            if request.chemical_test:
                tests.append("Химический анализ")
            if request.metallographic_test:
                tests.append("Металлографический анализ")
            
            request_layout.addRow("Испытания:", QLabel(", ".join(tests) if tests else "-"))
            
            # Status
            status = "Отправлено в лабораторию" if request.is_sent_to_lab else \
                    "Отобрано" if request.is_collected else "Ожидает отбора"
            
            status_label = QLabel(status)
            request_layout.addRow("Статус:", status_label)
            
            # Created by
            creator = db.query(User).filter(User.id == request.created_by_id).first()
            creator_name = creator.full_name if creator else "Неизвестно"
            request_layout.addRow("Создал:", QLabel(creator_name))
            
            # Buttons row
            buttons_layout = QHBoxLayout()
            
            # Mark as collected button
            if not request.is_collected:
                collect_btn = QPushButton("Отметить как отобранную")
                collect_btn.clicked.connect(lambda checked=False, r_id=request.id: self.mark_sample_collected(r_id))
                buttons_layout.addWidget(collect_btn)
            
            # Mark as sent button
            if request.is_collected and not request.is_sent_to_lab:
                send_btn = QPushButton("Отправить в лабораторию")
                send_btn.clicked.connect(lambda checked=False, r_id=request.id: self.mark_sample_sent(r_id))
                buttons_layout.addWidget(send_btn)
            
            request_layout.addRow("", buttons_layout)
            
            request_group.setLayout(request_layout)
            self.samples_layout.addWidget(request_group)
    
    def load_test_results(self, db):
        """Load test results for this material"""
        # Clear existing content
        while self.tests_layout.count():
            item = self.tests_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Get test results
        tests = db.query(LabTest).filter(
            LabTest.material_entry_id == self.material_id,
            LabTest.is_deleted == False
        ).order_by(LabTest.performed_at.desc()).all()
        
        if not tests:
            self.tests_layout.addWidget(QLabel("Нет результатов испытаний"))
            return
        
        # Add each test
        for test in tests:
            # Create a group for each test
            test_group = QGroupBox(f"Испытание #{test.id} от {test.performed_at.strftime('%d.%m.%Y')}")
            test_layout = QFormLayout()
            
            # Test type
            test_type = ""
            if test.test_type_id:
                test_type_obj = db.query(TestType).filter(TestType.id == test.test_type_id).first()
                if test_type_obj:
                    test_type = test_type_obj.name
            else:
                test_type = test.test_type
            
            test_layout.addRow("Тип испытания:", QLabel(test_type))
            
            # Results
            result_label = QLabel(test.results or "-")
            result_label.setWordWrap(True)
            test_layout.addRow("Результаты:", result_label)
            
            # Status
            if test.is_passed is None:
                status = "В процессе"
            elif test.is_passed:
                status = "Годно"
            else:
                status = "Брак"
            
            test_layout.addRow("Статус:", QLabel(status))
            
            # Performed by
            performer = db.query(User).filter(User.id == test.performed_by_id).first()
            performer_name = performer.full_name if performer else "Неизвестно"
            test_layout.addRow("Выполнил:", QLabel(performer_name))
            
            # Performed date
            performed_str = test.performed_at.strftime("%d.%m.%Y %H:%M")
            test_layout.addRow("Начато:", QLabel(performed_str))
            
            # Completed date
            if test.completed_at:
                completed_str = test.completed_at.strftime("%d.%m.%Y %H:%M")
                test_layout.addRow("Завершено:", QLabel(completed_str))
            
            # Buttons row
            if test.is_passed is None:
                buttons_layout = QHBoxLayout()
                
                # Complete buttons
                pass_btn = QPushButton("Отметить как годное")
                pass_btn.clicked.connect(lambda checked=False, t_id=test.id, passed=True: self.complete_test(t_id, passed))
                buttons_layout.addWidget(pass_btn)
                
                fail_btn = QPushButton("Отметить как брак")
                fail_btn.clicked.connect(lambda checked=False, t_id=test.id, passed=False: self.complete_test(t_id, passed))
                buttons_layout.addWidget(fail_btn)
                
                test_layout.addRow("", buttons_layout)
            
            test_group.setLayout(test_layout)
            self.tests_layout.addWidget(test_group)
    
    def view_certificate(self):
        """View certificate file"""
        if not self.material or not self.material.certificate_file_path:
            QMessageBox.warning(self, "Предупреждение", "Файл сертификата не найден")
            return
        
        certificate_path = self.material.certificate_file_path
        if not os.path.exists(certificate_path):
            QMessageBox.warning(self, "Предупреждение", f"Файл сертификата не найден по пути {certificate_path}")
            return
        
        # Open certificate using system default PDF viewer
        os.startfile(certificate_path)
    
    def request_sample(self):
        """Create a new sample request"""
        dialog = SampleRequestDialog(None, self.user, self, self.material_id)
        if dialog.exec() == QDialog.Accepted:
            # Refresh material data
            self.load_material_data()
    
    def start_test(self):
        """Start a new test"""
        dialog = TestResultDialog(None, self.user, self, self.material_id)
        if dialog.exec() == QDialog.Accepted:
            # Refresh material data
            self.load_material_data()
    
    def mark_sample_collected(self, request_id):
        """Mark a sample as collected"""
        db = SessionLocal()
        try:
            request = db.query(SampleRequest).filter(SampleRequest.id == request_id).first()
            if not request:
                QMessageBox.warning(self, "Предупреждение", "Запрос не найден")
                return
            
            request.is_collected = True
            request.collected_at = datetime.datetime.now()
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == request.material_entry_id).first()
            if material:
                material.status = MaterialStatus.SAMPLES_COLLECTED.value
            
            db.commit()
            QMessageBox.information(self, "Успех", "Проба отмечена как отобранная")
            
            # Refresh data
            self.load_material_data()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")
        finally:
            db.close()
    
    def mark_sample_sent(self, request_id):
        """Mark a sample as sent to the lab"""
        db = SessionLocal()
        try:
            request = db.query(SampleRequest).filter(SampleRequest.id == request_id).first()
            if not request:
                QMessageBox.warning(self, "Предупреждение", "Запрос не найден")
                return
            
            request.is_sent_to_lab = True
            
            # Update material status if needed
            material = db.query(MaterialEntry).filter(MaterialEntry.id == request.material_entry_id).first()
            if material and material.status == MaterialStatus.SAMPLES_COLLECTED.value:
                material.status = MaterialStatus.TESTING.value
            
            db.commit()
            QMessageBox.information(self, "Успех", "Проба отмечена как отправленная в лабораторию")
            
            # Refresh data
            self.load_material_data()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")
        finally:
            db.close()
    
    def complete_test(self, test_id, is_passed):
        """Complete a test with result"""
        # Ask for test results
        results, ok = QInputDialog.getText(
            self, 
            "Результаты испытания", 
            "Введите результаты испытания:",
            QLineEdit.Normal, 
            ""
        )
        
        if not ok:
            return
        
        db = SessionLocal()
        try:
            test = db.query(LabTest).filter(LabTest.id == test_id).first()
            if not test:
                QMessageBox.warning(self, "Предупреждение", "Испытание не найдено")
                return
            
            test.is_passed = is_passed
            test.results = results
            test.completed_at = datetime.datetime.now()
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == test.material_entry_id).first()
            if material:
                if is_passed:
                    material.status = MaterialStatus.APPROVED.value
                else:
                    material.status = MaterialStatus.REJECTED.value
            
            db.commit()
            
            result_text = "годно" if is_passed else "брак"
            QMessageBox.information(self, "Успех", f"Испытание завершено с результатом: {result_text}")
            
            # Refresh data
            self.load_material_data()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при завершении испытания: {str(e)}")
        finally:
            db.close()
    
    def get_material_type_display(self, type_code):
        """Convert material type code to display name"""
        type_names = {
            "rod": "Круг",
            "sheet": "Лист",
            "pipe": "Труба",
            "angle": "Уголок",
            "channel": "Швеллер",
            "other": "Другое"
        }
        return type_names.get(type_code, type_code)
    
    def get_status_display(self, status_code):
        """Convert status code to display name"""
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

    def apply_table_improvements(self, table):
        """Применить улучшения к таблице для лучшей читаемости"""
        # Применяем общие стили
        apply_table_style(table)
        
        # Устанавливаем минимальные размеры
        table.horizontalHeader().setMinimumSectionSize(60)
        table.verticalHeader().setMinimumWidth(40)
        table.verticalHeader().setDefaultSectionSize(36)
        
        # Запрещаем редактирование
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Включаем чередование строк
        table.setAlternatingRowColors(True)
        
        # Отображаем сетку
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)


class SampleRequestDialog(QDialog):
    """Dialog to manage sample requests"""
    def __init__(self, request_id=None, user=None, parent=None, material_id=None):
        super().__init__(parent)
        self.request_id = request_id
        self.user = user
        self.parent = parent
        self.material_id = material_id
        self.editing_mode = request_id is not None
        self.request = None
        self.material = None
        
        self.init_ui()
        
        if self.editing_mode:
            self.setWindowTitle("Просмотр запроса на пробы")
            self.load_request_data()
        else:
            self.setWindowTitle("Новый запрос на пробы")
            self.load_material_data()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        self.setMinimumWidth(600)
        
        # Material information (read-only)
        material_group = QGroupBox("Информация о материале")
        material_layout = QFormLayout()
        
        self.material_label = QLabel()
        material_layout.addRow("Материал:", self.material_label)
        
        self.melt_label = QLabel()
        material_layout.addRow("Плавка:", self.melt_label)
        
        self.supplier_label = QLabel()
        material_layout.addRow("Поставщик:", self.supplier_label)
        
        material_group.setLayout(material_layout)
        layout.addWidget(material_group)
        
        # Sample request form
        request_group = QGroupBox("Данные запроса на пробы")
        request_layout = QFormLayout()
        
        # Sample size
        size_layout = QHBoxLayout()
        self.sample_size_spin = QDoubleSpinBox()
        self.sample_size_spin.setRange(0.1, 1000)
        self.sample_size_spin.setDecimals(1)
        size_layout.addWidget(self.sample_size_spin)
        
        self.sample_unit_combo = QComboBox()
        self.sample_unit_combo.addItem("шт")
        self.sample_unit_combo.addItem("кг")
        self.sample_unit_combo.addItem("г")
        self.sample_unit_combo.addItem("мм")
        size_layout.addWidget(self.sample_unit_combo)
        
        request_layout.addRow("Размер пробы:", size_layout)
        
        # Test types checkboxes
        tests_group = QGroupBox("Требуемые испытания")
        tests_layout = QVBoxLayout()
        
        self.mechanical_test_check = QCheckBox("Механические испытания")
        tests_layout.addWidget(self.mechanical_test_check)
        
        self.chemical_test_check = QCheckBox("Химический анализ")
        tests_layout.addWidget(self.chemical_test_check)
        
        self.metallographic_test_check = QCheckBox("Металлографический анализ")
        tests_layout.addWidget(self.metallographic_test_check)
        
        tests_group.setLayout(tests_layout)
        request_layout.addRow(tests_group)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Дополнительная информация о пробе...")
        request_layout.addRow("Описание:", self.description_edit)
        
        # Sample Location & Cutting Scheme
        sample_location_group = QGroupBox("Указания по отбору проб")
        sample_location_layout = QVBoxLayout()
        
        # Sample location
        location_layout = QFormLayout()
        self.sample_location_combo = QComboBox()
        self.sample_location_combo.addItem("Не указано")
        location_layout.addRow("Рекомендуемое место отбора:", self.sample_location_combo)
        sample_location_layout.addLayout(location_layout)
        
        # Diagram text
        self.cutting_diagram_text = QTextEdit()
        self.cutting_diagram_text.setReadOnly(True)
        self.cutting_diagram_text.setMaximumHeight(120)
        sample_location_layout.addWidget(QLabel("Рекомендуемая схема вырезки:"))
        sample_location_layout.addWidget(self.cutting_diagram_text)
        
        # Update sample locations and diagram based on material type
        if hasattr(self, 'material') and self.material:
            if self.material.material_type == "rod":
                self.sample_location_combo.clear()
                self.sample_location_combo.addItems(["Не указано", "С торца стержня", "Из середины стержня", "Произвольно"])
                
                diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                diagram_text += "• Для механических испытаний: отрезать от торца стержня образец длиной не менее 200 мм\n"
                diagram_text += "• Для химического анализа: стружка с любого участка или фрагмент Ø10×10 мм\n"
                diagram_text += "• Для металлографии: поперечный срез толщиной 10-15 мм\n"
                self.cutting_diagram_text.setText(diagram_text)
                
            elif self.material.material_type == "sheet":
                self.sample_location_combo.clear()
                self.sample_location_combo.addItems(["Не указано", "С края листа", "Из середины листа", "По диагонали"])
                
                diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                diagram_text += "• Для механических испытаний: вырезать образец размером 300×100 мм с середины листа\n"
                diagram_text += "• Для химического анализа: фрагмент 20×20 мм с любого участка\n"
                diagram_text += "• Для металлографии: образец 20×20 мм с края листа\n"
                self.cutting_diagram_text.setText(diagram_text)
                
            elif self.material.material_type == "pipe":
                self.sample_location_combo.clear()
                self.sample_location_combo.addItems(["Не указано", "С торца трубы", "Из середины трубы", "Произвольно"])
                
                diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                diagram_text += "• Для механических испытаний: отрезать кольцо шириной 50 мм\n"
                diagram_text += "• Для химического анализа: стружка или фрагмент 10×10 мм\n"
                diagram_text += "• Для металлографии: поперечный срез шириной 10-15 мм\n"
                self.cutting_diagram_text.setText(diagram_text)
        
        # Production notes
        self.cutting_notes = QTextEdit()
        self.cutting_notes.setPlaceholderText("Дополнительные указания для производства по изготовлению образцов...")
        sample_location_layout.addWidget(QLabel("Специальные указания:"))
        sample_location_layout.addWidget(self.cutting_notes)
        
        sample_location_group.setLayout(sample_location_layout)
        request_layout.addRow(sample_location_group)
        
        # Status (view mode only)
        self.status_group = QGroupBox("Статус")
        status_layout = QFormLayout()
        
        self.created_label = QLabel()
        status_layout.addRow("Запрос создан:", self.created_label)
        
        self.collected_label = QLabel("Не отобрано")
        status_layout.addRow("Проба отобрана:", self.collected_label)
        
        self.sent_label = QLabel("Не отправлено")
        status_layout.addRow("Отправлено в лабораторию:", self.sent_label)
        
        self.status_group.setLayout(status_layout)
        
        # Show only in view mode
        if self.editing_mode:
            request_layout.addRow(self.status_group)
        
        request_group.setLayout(request_layout)
        layout.addWidget(request_group)
        
        # Действия с пробой
        actions_group = QGroupBox("Действия")
        actions_layout = QHBoxLayout()
        
        self.mark_collected_btn = QPushButton("Отметить как отобранную")
        self.mark_collected_btn.clicked.connect(self.mark_collected)
        actions_layout.addWidget(self.mark_collected_btn)
        
        self.mark_sent_btn = QPushButton("Отправить в лабораторию")
        self.mark_sent_btn.clicked.connect(self.mark_sent)
        actions_layout.addWidget(self.mark_sent_btn)
        
        self.manage_samples_btn = QPushButton("Управление образцами")
        self.manage_samples_btn.clicked.connect(self.manage_samples)
        actions_layout.addWidget(self.manage_samples_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        if self.editing_mode:
            # View mode buttons
            if self.request_id:
                # Collection and sending buttons would be added dynamically based on status
                pass
            
            self.close_btn = QPushButton("Закрыть")
            self.close_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(self.close_btn)
        else:
            # Edit mode buttons
            self.save_btn = QPushButton("Создать запрос")
            self.save_btn.clicked.connect(self.save_request)
            buttons_layout.addWidget(self.save_btn)
            
            self.cancel_btn = QPushButton("Отмена")
            self.cancel_btn.clicked.connect(self.reject)
            buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_material_data(self):
        """Load material data for new request"""
        if not self.material_id:
            self.reject()
            return
        
        db = SessionLocal()
        try:
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if not self.material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден")
                self.reject()
                return
            
            # Set material info in the form
            self.material_label.setText(f"{self.material.material_grade} ({self.get_material_type_display(self.material.material_type)})")
            self.melt_label.setText(self.material.melt_number)
            
            # Supplier
            supplier = db.query(Supplier).filter(Supplier.id == self.material.supplier_id).first()
            supplier_name = supplier.name if supplier else "Неизвестно"
            self.supplier_label.setText(supplier_name)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def load_request_data(self):
        """Load request data for view/edit mode"""
        if not self.request_id:
            self.reject()
            return
        
        db = SessionLocal()
        try:
            self.request = db.query(SampleRequest).filter(SampleRequest.id == self.request_id).first()
            if not self.request:
                QMessageBox.critical(self, "Ошибка", "Запрос не найден")
                self.reject()
                return
            
            # Load material data
            self.material_id = self.request.material_entry_id
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            
            if self.material:
                # Set material info
                self.material_label.setText(f"{self.material.material_grade} ({self.get_material_type_display(self.material.material_type)})")
                self.melt_label.setText(self.material.melt_number)
                
                # Supplier
                supplier = db.query(Supplier).filter(Supplier.id == self.material.supplier_id).first()
                supplier_name = supplier.name if supplier else "Неизвестно"
                self.supplier_label.setText(supplier_name)
            
            # Set request data
            self.sample_size_spin.setValue(self.request.sample_size)
            
            # Set unit combo
            index = self.sample_unit_combo.findText(self.request.sample_unit)
            if index >= 0:
                self.sample_unit_combo.setCurrentIndex(index)
            
            # Set test checkboxes
            self.mechanical_test_check.setChecked(self.request.mechanical_test)
            self.chemical_test_check.setChecked(self.request.chemical_test)
            self.metallographic_test_check.setChecked(self.request.metallographic_test)
            
            # Set description
            self.description_edit.setText(self.request.sample_description or "")
            
            # Set sample location if available
            if self.request.sample_location:
                index = self.sample_location_combo.findText(self.request.sample_location)
                if index >= 0:
                    self.sample_location_combo.setCurrentIndex(index)
            
            # Set manufacturing notes if available
            if self.request.manufacturing_notes:
                self.cutting_notes.setText(self.request.manufacturing_notes)
            
            # Update cutting diagram text based on material type
            if self.material:
                if self.material.material_type == "rod":
                    diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                    diagram_text += "• Для механических испытаний: отрезать от торца стержня образец длиной не менее 200 мм\n"
                    diagram_text += "• Для химического анализа: стружка с любого участка или фрагмент Ø10×10 мм\n"
                    diagram_text += "• Для металлографии: поперечный срез толщиной 10-15 мм\n"
                    self.cutting_diagram_text.setText(diagram_text)
                    
                elif self.material.material_type == "sheet":
                    diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                    diagram_text += "• Для механических испытаний: вырезать образец размером 300×100 мм с середины листа\n"
                    diagram_text += "• Для химического анализа: фрагмент 20×20 мм с любого участка\n"
                    diagram_text += "• Для металлографии: образец 20×20 мм с края листа\n"
                    self.cutting_diagram_text.setText(diagram_text)
                    
                elif self.material.material_type == "pipe":
                    diagram_text = "Рекомендуемые схемы вырезки образцов:\n\n"
                    diagram_text += "• Для механических испытаний: отрезать кольцо шириной 50 мм\n"
                    diagram_text += "• Для химического анализа: стружка или фрагмент 10×10 мм\n"
                    diagram_text += "• Для металлографии: поперечный срез шириной 10-15 мм\n"
                    self.cutting_diagram_text.setText(diagram_text)
            
            # Set status info
            created_str = self.request.created_at.strftime("%d.%m.%Y %H:%M")
            self.created_label.setText(created_str)
            
            if self.request.is_collected:
                collected_str = self.request.collected_at.strftime("%d.%m.%Y %H:%M") if self.request.collected_at else "Да"
                self.collected_label.setText(collected_str)
            
            if self.request.is_sent_to_lab:
                self.sent_label.setText("Да")
            
            # In view mode, make fields read-only
            self.sample_size_spin.setEnabled(False)
            self.sample_unit_combo.setEnabled(False)
            self.mechanical_test_check.setEnabled(False)
            self.chemical_test_check.setEnabled(False)
            self.metallographic_test_check.setEnabled(False)
            self.description_edit.setReadOnly(True)
            
            # Add action buttons based on status
            buttons_layout = self.layout().itemAt(self.layout().count() - 1)
            
            if not self.request.is_collected:
                collect_btn = QPushButton("Отметить как отобранную")
                collect_btn.clicked.connect(self.mark_collected)
                buttons_layout.insertWidget(0, collect_btn)
            
            if self.request.is_collected and not self.request.is_sent_to_lab:
                send_btn = QPushButton("Отправить в лабораторию")
                send_btn.clicked.connect(self.mark_sent)
                buttons_layout.insertWidget(0, send_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def save_request(self):
        """Save new sample request"""
        # Validate input
        if self.sample_size_spin.value() <= 0:
            QMessageBox.warning(self, "Предупреждение", "Укажите размер пробы")
            return
        
        if not (self.mechanical_test_check.isChecked() or 
                self.chemical_test_check.isChecked() or 
                self.metallographic_test_check.isChecked()):
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один тип испытания")
            return
        
        db = SessionLocal()
        try:
            new_request = SampleRequest(
                material_entry_id=self.material_id,
                created_by_id=self.user.id,
                sample_size=self.sample_size_spin.value(),
                sample_unit=self.sample_unit_combo.currentText(),
                sample_description=self.description_edit.toPlainText() if self.description_edit.toPlainText() else None,
                mechanical_test=self.mechanical_test_check.isChecked(),
                chemical_test=self.chemical_test_check.isChecked(),
                metallographic_test=self.metallographic_test_check.isChecked(),
                sample_location=self.sample_location_combo.currentText() if self.sample_location_combo.currentText() != "Не указано" else None,
                manufacturing_notes=self.cutting_notes.toPlainText() if self.cutting_notes.toPlainText() else None
            )
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if material and material.status in [MaterialStatus.LAB_CHECK_PENDING.value, MaterialStatus.QC_CHECKED.value]:
                material.status = MaterialStatus.SAMPLES_REQUESTED.value
                db.add(material)
            
            db.add(new_request)
            db.commit()
            
            QMessageBox.information(self, "Успех", "Запрос на пробы создан")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать запрос: {str(e)}")
        finally:
            db.close()
    
    def mark_collected(self):
        """Mark sample as collected"""
        db = SessionLocal()
        try:
            self.request = db.query(SampleRequest).filter(SampleRequest.id == self.request_id).first()
            if not self.request:
                QMessageBox.warning(self, "Предупреждение", "Запрос не найден")
                return
            
            self.request.is_collected = True
            self.request.collected_at = datetime.datetime.now()
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.request.material_entry_id).first()
            if material:
                material.status = MaterialStatus.SAMPLES_COLLECTED.value
            
            db.commit()
            QMessageBox.information(self, "Успех", "Проба отмечена как отобранная")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")
        finally:
            db.close()
    
    def mark_sent(self):
        """Отметить пробы как отправленные в лабораторию"""
        db = SessionLocal()
        try:
            request = db.query(SampleRequest).filter(SampleRequest.id == self.request_id).first()
            if request:
                request.is_sent_to_lab = True
                
                # Обновляем статус материала
                material = db.query(MaterialEntry).filter(MaterialEntry.id == request.material_entry_id).first()
                if material and material.status == MaterialStatus.SAMPLES_COLLECTED.value:
                    material.status = MaterialStatus.TESTING.value
                
                db.commit()
                
                QMessageBox.information(self, "Успех", "Проба отправлена в лабораторию")
                self.load_request_data()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")
        finally:
            db.close()
    
    def manage_samples(self):
        """Управление образцами для данной заявки"""
        if not self.request_id:
            QMessageBox.warning(self, "Предупреждение", "Сначала сохраните заявку")
            return
        
        dialog = SampleManagementDialog(self.request_id, self.user, self)
        dialog.samples_updated.connect(self.load_request_data)  # Обновляем данные при изменении образцов
        dialog.exec()
    
    def get_material_type_display(self, type_code):
        """Convert material type code to display name"""
        type_names = {
            "rod": "Круг",
            "sheet": "Лист",
            "pipe": "Труба",
            "angle": "Уголок",
            "channel": "Швеллер",
            "other": "Другое"
        }
        return type_names.get(type_code, type_code)

    def apply_table_improvements(self, table):
        """Применить улучшения к таблице для лучшей читаемости"""
        # Применяем общие стили
        apply_table_style(table)
        
        # Устанавливаем минимальные размеры
        table.horizontalHeader().setMinimumSectionSize(60)
        table.verticalHeader().setMinimumWidth(40)
        table.verticalHeader().setDefaultSectionSize(36)
        
        # Запрещаем редактирование
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Включаем чередование строк
        table.setAlternatingRowColors(True)
        
        # Отображаем сетку
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)


class TestResultDialog(QDialog):
    """Dialog for entering and viewing test results"""
    def __init__(self, test_id=None, user=None, parent=None, material_id=None):
        super().__init__(parent)
        self.test_id = test_id
        self.user = user
        self.parent = parent
        self.material_id = material_id
        self.test = None
        self.material = None
        self.is_new = test_id is None
        self.init_ui()
        if self.material_id:
            self.load_material_data()
        if self.test_id:
            self.load_test_data()
            
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Результаты испытания")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Material information
        material_group = QGroupBox("Информация о материале")
        material_layout = QFormLayout()
        
        self.material_grade_label = QLabel()
        material_layout.addRow("Марка материала:", self.material_grade_label)
        
        self.melt_number_label = QLabel()
        material_layout.addRow("Плавка:", self.melt_number_label)
        
        self.batch_number_label = QLabel()
        material_layout.addRow("Партия:", self.batch_number_label)
        
        material_group.setLayout(material_layout)
        layout.addWidget(material_group)
        
        # Test information
        test_group = QGroupBox("Информация об испытании")
        test_layout = QFormLayout()
        
        # Test type
        self.test_type_combo = QComboBox()
        test_layout.addRow("Тип испытания:", self.test_type_combo)
        
        # Выбор образцов
        samples_group = QGroupBox("Образцы для испытания")
        samples_layout = QVBoxLayout()
        
        # Таблица образцов
        self.samples_table = QTableWidget()
        self.samples_table.setColumnCount(5)
        self.samples_table.setHorizontalHeaderLabels(["Выбрать", "Код", "Тип", "Размеры", "Статус"])
        self.samples_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        samples_layout.addWidget(self.samples_table)
        
        samples_group.setLayout(samples_layout)
        test_layout.addRow(samples_group)
        
        # Results
        self.results_text = QTextEdit()
        test_layout.addRow("Результаты:", self.results_text)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("В процессе", None)
        self.status_combo.addItem("Годно", True)
        self.status_combo.addItem("Брак", False)
        test_layout.addRow("Статус:", self.status_combo)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_test)
        buttons_layout.addWidget(self.save_btn)
        
        self.complete_btn = QPushButton("Завершить испытание")
        self.complete_btn.clicked.connect(lambda: self.complete_test(self.status_combo.currentData()))
        buttons_layout.addWidget(self.complete_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Load test types
        self.load_test_types()
    
    def load_material_data(self):
        """Load material data by ID"""
        if not self.material_id:
            return
            
        db = SessionLocal()
        try:
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if not self.material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден")
                return
            
            # Set material info in the form
            self.material_grade_label.setText(self.material.material_grade)
            self.melt_number_label.setText(self.material.melt_number)
            self.batch_number_label.setText(self.material.batch_number or "Н/Д")
            
            # Применяем улучшения к таблице образцов
            self.apply_table_improvements(self.samples_table)
            
            # Загружаем доступные образцы
            self.load_available_samples()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных материала: {str(e)}")
        finally:
            db.close()
    
    def load_test_data(self):
        """Load test data for view/edit mode"""
        if not self.test_id:
            self.reject()
            return
        
        db = SessionLocal()
        try:
            self.test = db.query(LabTest).filter(LabTest.id == self.test_id).first()
            if not self.test:
                QMessageBox.critical(self, "Ошибка", "Испытание не найдено")
                self.reject()
                return
            
            # Load material data
            self.material_id = self.test.material_entry_id
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            
            if self.material:
                # Set material info
                self.material_grade_label.setText(self.material.material_grade)
                self.melt_number_label.setText(self.material.melt_number)
                self.batch_number_label.setText(self.material.batch_number or "Н/Д")
            
            # Set test type
            if self.test.test_type_id:
                # Find by ID
                index = self.test_type_combo.findData(self.test.test_type_id)
            else:
                # Find by string type
                index = self.test_type_combo.findData(self.test.test_type)
            
            if index >= 0:
                self.test_type_combo.setCurrentIndex(index)
            
            # Set results
            self.results_text.setText(self.test.results or "")
            
            # Set status
            if self.test.is_passed is None:
                self.status_combo.setCurrentIndex(0)
            elif self.test.is_passed:
                self.status_combo.setCurrentIndex(1)
            else:
                self.status_combo.setCurrentIndex(2)
            
            # In view mode, make fields read-only
            self.test_type_combo.setEnabled(False)
            self.results_text.setReadOnly(True)
            
            # Add action buttons based on status
            if self.test.is_passed is None:
                buttons_layout = self.layout().itemAt(self.layout().count() - 1)
                
                pass_btn = QPushButton("Отметить как годное")
                pass_btn.clicked.connect(lambda: self.complete_test(True))
                buttons_layout.insertWidget(0, pass_btn)
                
                fail_btn = QPushButton("Отметить как брак")
                fail_btn.clicked.connect(lambda: self.complete_test(False))
                buttons_layout.insertWidget(1, fail_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def save_test(self):
        """Save new test"""
        # Validate input
        if not self.results_text.toPlainText().strip():
            QMessageBox.warning(self, "Предупреждение", "Введите результаты испытания")
            return
        
        # Проверка выбора образцов
        selected_samples = []
        for row in range(self.samples_table.rowCount()):
            checkbox = self.samples_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_samples.append(checkbox.data(Qt.UserRole))
        
        if not selected_samples:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один образец для испытания")
            return
        
        db = SessionLocal()
        try:
            # Create new test
            test = LabTest(
                material_entry_id=self.material_id,
                performed_by_id=self.user.id,
                test_type=self.test_type_combo.currentData() if isinstance(self.test_type_combo.currentData(), str) else None,
                test_type_id=self.test_type_combo.currentData() if isinstance(self.test_type_combo.currentData(), int) else None,
                results=self.results_text.toPlainText(),
                is_passed=self.status_combo.currentData(),
                performed_at=datetime.datetime.now()
            )
            
            db.add(test)
            db.flush()  # Получаем ID нового теста
            
            # Сохраняем связи с образцами
            self.save_selected_samples(test.id)
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if material:
                material.status = MaterialStatus.TESTING.value if self.status_combo.currentData() is None else MaterialStatus.TESTING_COMPLETED.value
            
            db.commit()
            QMessageBox.information(self, "Успех", "Результаты испытания сохранены")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении результатов испытания: {str(e)}")
        finally:
            db.close()
    
    def complete_test(self, is_passed):
        """Complete test with result"""
        if not self.test_id:
            # Update from current dialog if we're editing
            if not self.results_text.toPlainText().strip():
                QMessageBox.warning(self, "Предупреждение", "Введите результаты испытания")
                return
        
        db = SessionLocal()
        try:
            test = db.query(LabTest).filter(LabTest.id == self.test_id).first()
            if not test:
                QMessageBox.warning(self, "Предупреждение", "Испытание не найдено")
                return
            
            # Update results from dialog
            test.results = self.results_text.toPlainText()
            
            # Mark as completed
            test.is_passed = is_passed
            test.completed_at = datetime.datetime.now()
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == test.material_entry_id).first()
            if material:
                if is_passed:
                    material.status = MaterialStatus.APPROVED.value
                else:
                    material.status = MaterialStatus.REJECTED.value
            
            db.commit()
            
            result_text = "годно" if is_passed else "брак"
            QMessageBox.information(self, "Успех", f"Испытание завершено с результатом: {result_text}")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при завершении испытания: {str(e)}")
        finally:
            db.close()
    
    def load_test_types(self):
        """Load test types from the database"""
        db = SessionLocal()
        try:
            test_types = db.query(TestType).filter(TestType.is_deleted == False).all()
            for test_type in test_types:
                self.test_type_combo.addItem(test_type.name, test_type.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке типов испытаний: {str(e)}")
        finally:
            db.close()
    
    def load_available_samples(self):
        """Загрузка доступных образцов для испытания"""
        db = SessionLocal()
        try:
            # Очищаем таблицу
            self.samples_table.setRowCount(0)
            
            # Получаем все заявки на пробы для данного материала
            sample_requests = db.query(SampleRequest).filter(
                SampleRequest.material_entry_id == self.material_id,
                SampleRequest.is_deleted == False
            ).all()
            
            # Получаем все образцы для этих заявок
            row = 0
            for request in sample_requests:
                samples = db.query(Sample).filter(
                    Sample.sample_request_id == request.id,
                    Sample.is_deleted == False,
                    Sample.status.in_(["prepared", "testing", "tested"])  # Только подготовленные образцы
                ).all()
                
                for sample in samples:
                    self.samples_table.insertRow(row)
                    
                    # Чекбокс для выбора
                    checkbox = QCheckBox()
                    checkbox.setData(Qt.UserRole, sample.id)
                    
                    # Если редактируем существующий тест, отмечаем уже связанные образцы
                    if self.test_id:
                        existing_link = db.query(LabTestSample).filter(
                            LabTestSample.lab_test_id == self.test_id,
                            LabTestSample.sample_id == sample.id
                        ).first()
                        if existing_link:
                            checkbox.setChecked(True)
                    
                    self.samples_table.setCellWidget(row, 0, checkbox)
                    
                    # Код образца
                    self.samples_table.setItem(row, 1, QTableWidgetItem(sample.sample_code))
                    
                    # Тип образца
                    self.samples_table.setItem(row, 2, QTableWidgetItem(sample.sample_type))
                    
                    # Размеры
                    sizes = []
                    if sample.length:
                        sizes.append(f"L={sample.length}")
                    if sample.width:
                        sizes.append(f"W={sample.width}")
                    if sample.thickness:
                        sizes.append(f"T={sample.thickness}")
                    if sample.diameter:
                        sizes.append(f"Ø={sample.diameter}")
                    
                    self.samples_table.setItem(row, 3, QTableWidgetItem(" × ".join(sizes)))
                    
                    # Статус
                    status_map = {
                        "created": "Создан",
                        "prepared": "Подготовлен",
                        "testing": "Испытывается",
                        "tested": "Испытан",
                        "archived": "В архиве"
                    }
                    self.samples_table.setItem(row, 4, QTableWidgetItem(status_map.get(sample.status, sample.status)))
                    
                    row += 1
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке образцов: {str(e)}")
        finally:
            db.close()
    
    def save_selected_samples(self, test_id):
        """Сохранение связей между тестом и выбранными образцами"""
        db = SessionLocal()
        try:
            # Удаляем старые связи
            db.query(LabTestSample).filter(LabTestSample.lab_test_id == test_id).delete()
            
            # Создаем новые связи
            for row in range(self.samples_table.rowCount()):
                checkbox = self.samples_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    sample_id = checkbox.data(Qt.UserRole)
                    
                    # Создаем связь
                    link = LabTestSample(
                        lab_test_id=test_id,
                        sample_id=sample_id
                    )
                    db.add(link)
                    
                    # Обновляем статус образца
                    sample = db.query(Sample).filter(Sample.id == sample_id).first()
                    if sample and sample.status == "prepared":
                        sample.status = "testing"
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_material_type_display(self, type_code):
        """Convert material type code to display name"""
        type_names = {
            "rod": "Круг",
            "sheet": "Лист",
            "pipe": "Труба",
            "angle": "Уголок",
            "channel": "Швеллер",
            "other": "Другое"
        }
        return type_names.get(type_code, type_code)

    def apply_table_improvements(self, table):
        """Применить улучшения к таблице для лучшей читаемости"""
        # Применяем общие стили
        apply_table_style(table)
        
        # Устанавливаем минимальные размеры
        table.horizontalHeader().setMinimumSectionSize(60)
        table.verticalHeader().setMinimumWidth(40)
        table.verticalHeader().setDefaultSectionSize(36)
        
        # Запрещаем редактирование
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Включаем чередование строк
        table.setAlternatingRowColors(True)
        
        # Отображаем сетку
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine) 