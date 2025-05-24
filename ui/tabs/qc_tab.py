from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                             QFormLayout, QMessageBox, QFileDialog, QHeaderView,
                             QGroupBox, QCheckBox, QDialog, QTextEdit, QScrollArea,
                             QSplitter, QFrame, QMenu, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, QDateTime, QRegularExpression
from PySide6.QtGui import QFont, QColor, QBrush, QRegularExpressionValidator, QAction

from database.connection import SessionLocal
from models.models import User, MaterialEntry, Supplier, MaterialType, MaterialStatus, QCCheck
from sqlalchemy import desc
import os
import shutil
import datetime
from utils.material_utils import clean_material_grade, get_material_type_display, get_status_display_name
from ui.icons.icon_provider import IconProvider
from ui.themes import theme_manager
from ui.styles import apply_button_style

class QCCheckForm(QDialog):
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
        """Initialize the UI components for the QC check form"""
        self.setWindowTitle("Проверка сертификата ОТК")
        self.setMinimumSize(1000, 700)
        
        main_layout = QVBoxLayout(self)
        
        # Material details
        details_group = QGroupBox("Информация о материале")
        details_layout = QHBoxLayout()  # Используем горизонтальное расположение для равномерного распределения
        
        # Левая колонка информации
        left_form = QFormLayout()
        left_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.material_grade_label = QLabel()
        left_form.addRow("Марка материала:", self.material_grade_label)
        
        self.material_type_label = QLabel()
        left_form.addRow("Тип материала:", self.material_type_label)
        
        self.batch_number_label = QLabel()
        left_form.addRow("Номер партии:", self.batch_number_label)
        
        # Добавляем контейнер для левой колонки
        left_widget = QWidget()
        left_widget.setLayout(left_form)
        details_layout.addWidget(left_widget)
        
        # Правая колонка информации
        right_form = QFormLayout()
        right_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.melt_number_label = QLabel()
        right_form.addRow("Номер плавки:", self.melt_number_label)
        
        self.supplier_label = QLabel()
        right_form.addRow("Поставщик:", self.supplier_label)
        
        # Добавляем контейнер для правой колонки
        right_widget = QWidget()
        right_widget.setLayout(right_form)
        details_layout.addWidget(right_widget)
        
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        
        # Create splitter for certificate and comments sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Certificate group
        certificate_group = QGroupBox("Сертификат")
        certificate_layout = QVBoxLayout()
        
        upload_layout = QHBoxLayout()
        self.certificate_path_label = QLabel("Сертификат не загружен")
        upload_layout.addWidget(self.certificate_path_label)
        
        self.upload_btn = QPushButton("Загрузить")
        self.upload_btn.clicked.connect(self.upload_certificate)
        upload_layout.addWidget(self.upload_btn)
        
        self.view_btn = QPushButton("Просмотреть")
        self.view_btn.clicked.connect(self.view_certificate)
        self.view_btn.setEnabled(False)
        upload_layout.addWidget(self.view_btn)
        
        certificate_layout.addLayout(upload_layout)
        
        # Используем нижнюю область для чекбоксов - разбиваем на две колонки
        checks_container = QWidget()
        checks_grid = QHBoxLayout(checks_container)  # Горизонтальное расположение
        
        # Левая колонка - QC check options
        self.quality_checks = QGroupBox("Проверка качества")
        checks_layout = QVBoxLayout()
        
        self.certificate_readable = QCheckBox("Сертификат читаемый")
        checks_layout.addWidget(self.certificate_readable)
        
        self.material_matches = QCheckBox("Материал соответствует")
        checks_layout.addWidget(self.material_matches)
        
        self.dimensions_match = QCheckBox("Размеры соответствуют")
        checks_layout.addWidget(self.dimensions_match)
        
        self.certificate_data_correct = QCheckBox("Данные сертификата корректны")
        checks_layout.addWidget(self.certificate_data_correct)
        
        self.quality_checks.setLayout(checks_layout)
        checks_grid.addWidget(self.quality_checks)
        
        # Правая колонка - Issues checklist
        self.issues_group = QGroupBox("Замечания")
        issues_layout = QVBoxLayout()
        
        # Разделяем замечания на две колонки
        issues_box = QHBoxLayout()
        
        # Левая колонка замечаний
        left_issues = QVBoxLayout()
        self.issue_repurchase = QCheckBox("Перекуп")
        left_issues.addWidget(self.issue_repurchase)
        
        self.issue_poor_quality = QCheckBox("Плохое качество сертификата")
        left_issues.addWidget(self.issue_poor_quality)
        
        self.issue_no_stamp = QCheckBox("Нет печати")
        left_issues.addWidget(self.issue_no_stamp)
        
        self.issue_diameter_deviation = QCheckBox("Отклонение по диаметру")
        left_issues.addWidget(self.issue_diameter_deviation)
        
        # Правая колонка замечаний
        right_issues = QVBoxLayout()
        self.issue_cracks = QCheckBox("Трещины")
        right_issues.addWidget(self.issue_cracks)
        
        self.issue_no_melt = QCheckBox("Не набита плавка")
        right_issues.addWidget(self.issue_no_melt)
        
        self.issue_no_certificate = QCheckBox("Нет сертификата")
        right_issues.addWidget(self.issue_no_certificate)
        
        self.issue_copy = QCheckBox("Копия (без синей печати)")
        right_issues.addWidget(self.issue_copy)
        
        # Добавляем колонки в контейнер замечаний
        left_issues_widget = QWidget()
        left_issues_widget.setLayout(left_issues)
        issues_box.addWidget(left_issues_widget)
        
        right_issues_widget = QWidget()
        right_issues_widget.setLayout(right_issues)
        issues_box.addWidget(right_issues_widget)
        
        issues_layout.addLayout(issues_box)
        self.issues_group.setLayout(issues_layout)
        checks_grid.addWidget(self.issues_group)
        
        certificate_layout.addWidget(checks_container)
        
        # PPSD check - отдельный блок снизу
        ppsd_container = QWidget()
        ppsd_layout = QHBoxLayout(ppsd_container)
        
        self.requires_lab = QCheckBox("Требуется проведение ППСД")
        self.requires_lab.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        ppsd_layout.addWidget(self.requires_lab)
        ppsd_layout.addStretch(1)  # Добавляем растягивающийся элемент, чтобы checkbox был слева
        
        certificate_layout.addWidget(ppsd_container)
        
        # Chemical composition section
        chem_group = QGroupBox("Химический состав из сертификата (%)")
        chem_layout = QVBoxLayout()
        
        # Create grid layout for chemical elements
        chem_grid = QHBoxLayout()
        
        # Left column of chemical elements
        left_chem = QFormLayout()
        
        self.chem_c = QLineEdit()
        self.chem_c.setPlaceholderText("0.00")
        self.chem_c.setToolTip("Углерод: 0.08% макс.")
        self.chem_c.setMaximumWidth(80)
        left_chem.addRow("C (Углерод):", self.chem_c)
        
        self.chem_si = QLineEdit()
        self.chem_si.setPlaceholderText("0.00")
        self.chem_si.setToolTip("Кремний: 0.8% макс.")
        self.chem_si.setMaximumWidth(80)
        left_chem.addRow("Si (Кремний):", self.chem_si)
        
        self.chem_mn = QLineEdit()
        self.chem_mn.setPlaceholderText("0.00")
        self.chem_mn.setToolTip("Марганец: 2% макс.")
        self.chem_mn.setMaximumWidth(80)
        left_chem.addRow("Mn (Марганец):", self.chem_mn)
        
        self.chem_s = QLineEdit()
        self.chem_s.setPlaceholderText("0.00")
        self.chem_s.setToolTip("Сера: 0.02% макс.")
        self.chem_s.setMaximumWidth(80)
        left_chem.addRow("S (Сера):", self.chem_s)
        
        # Add left column to grid
        left_chem_widget = QWidget()
        left_chem_widget.setLayout(left_chem)
        chem_grid.addWidget(left_chem_widget)
        
        # Middle column of chemical elements
        middle_chem = QFormLayout()
        
        self.chem_p = QLineEdit()
        self.chem_p.setPlaceholderText("0.00")
        self.chem_p.setToolTip("Фосфор: 0.035% макс.")
        self.chem_p.setMaximumWidth(80)
        middle_chem.addRow("P (Фосфор):", self.chem_p)
        
        self.chem_cr = QLineEdit()
        self.chem_cr.setPlaceholderText("0.00")
        self.chem_cr.setToolTip("Хром: 17-19%")
        self.chem_cr.setMaximumWidth(80)
        middle_chem.addRow("Cr (Хром):", self.chem_cr)
        
        self.chem_ni = QLineEdit()
        self.chem_ni.setPlaceholderText("0.00")
        self.chem_ni.setToolTip("Никель: 9-11%")
        self.chem_ni.setMaximumWidth(80)
        middle_chem.addRow("Ni (Никель):", self.chem_ni)
        
        self.chem_cu = QLineEdit()
        self.chem_cu.setPlaceholderText("0.00")
        self.chem_cu.setToolTip("Медь: 0.3% макс.")
        self.chem_cu.setMaximumWidth(80)
        middle_chem.addRow("Cu (Медь):", self.chem_cu)
        
        # Add middle column to grid
        middle_chem_widget = QWidget()
        middle_chem_widget.setLayout(middle_chem)
        chem_grid.addWidget(middle_chem_widget)
        
        # Right column of chemical elements
        right_chem = QFormLayout()
        
        self.chem_ti = QLineEdit()
        self.chem_ti.setPlaceholderText("0.00")
        self.chem_ti.setToolTip("Титан: 0.4-0.8%")
        self.chem_ti.setMaximumWidth(80)
        right_chem.addRow("Ti (Титан):", self.chem_ti)
        
        self.chem_al = QLineEdit()
        self.chem_al.setPlaceholderText("0.00")
        self.chem_al.setToolTip("Алюминий")
        self.chem_al.setMaximumWidth(80)
        right_chem.addRow("Al (Алюминий):", self.chem_al)
        
        self.chem_mo = QLineEdit()
        self.chem_mo.setPlaceholderText("0.00")
        self.chem_mo.setToolTip("Молибден")
        self.chem_mo.setMaximumWidth(80)
        right_chem.addRow("Mo (Молибден):", self.chem_mo)
        
        self.chem_v = QLineEdit()
        self.chem_v.setPlaceholderText("0.00")
        self.chem_v.setToolTip("Ванадий")
        self.chem_v.setMaximumWidth(80)
        right_chem.addRow("V (Ванадий):", self.chem_v)
        
        # Add right column to grid
        right_chem_widget = QWidget()
        right_chem_widget.setLayout(right_chem)
        chem_grid.addWidget(right_chem_widget)
        
        # Extra column for less common elements
        extra_chem = QFormLayout()
        
        self.chem_nb = QLineEdit()
        self.chem_nb.setPlaceholderText("0.00")
        self.chem_nb.setToolTip("Ниобий")
        self.chem_nb.setMaximumWidth(80)
        extra_chem.addRow("Nb (Ниобий):", self.chem_nb)
        
        # Add extra column to grid
        extra_chem_widget = QWidget()
        extra_chem_widget.setLayout(extra_chem)
        chem_grid.addWidget(extra_chem_widget)
        
        # Add the grid to the chemical composition layout
        chem_layout.addLayout(chem_grid)
        
        chem_group.setLayout(chem_layout)
        certificate_layout.addWidget(chem_group)
        
        certificate_widget = QWidget()
        certificate_widget.setLayout(certificate_layout)
        splitter.addWidget(certificate_widget)
        
        # Comments section
        comments_group = QGroupBox("Комментарии")
        comments_layout = QVBoxLayout()
        
        # Comments history
        self.comments_display = QTextEdit()
        self.comments_display.setReadOnly(True)
        comments_layout.addWidget(self.comments_display)
        
        # New comment
        self.new_comment = QTextEdit()
        self.new_comment.setPlaceholderText("Введите комментарий...")
        self.new_comment.setMaximumHeight(80)
        comments_layout.addWidget(self.new_comment)
        
        # Add comment button
        self.add_comment_btn = QPushButton("Добавить комментарий")
        self.add_comment_btn.clicked.connect(self.add_comment)
        comments_layout.addWidget(self.add_comment_btn)
        
        comments_group.setLayout(comments_layout)
        splitter.addWidget(comments_group)
        
        # Устанавливаем начальные размеры сплиттера (60% / 40%)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)  # Добавляем растягивающийся элемент слева
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self.save_qc_check)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def load_material_data(self):
        """Load material data from database"""
        db = SessionLocal()
        try:
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            
            if not self.material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден")
                self.reject()
                return
            
            # Load material details - очищаем марку от стандарта
            clean_grade = clean_material_grade(self.material.material_grade)
            self.material_grade_label.setText(clean_grade)
            self.material_type_label.setText(get_material_type_display(self.material.material_type))
            self.batch_number_label.setText(self.material.batch_number or "Нет")
            self.melt_number_label.setText(self.material.melt_number)
            
            # Get supplier name
            supplier = db.query(Supplier).filter(Supplier.id == self.material.supplier_id).first()
            supplier_name = supplier.name if supplier else "Неизвестно"
            self.supplier_label.setText(supplier_name)
            
            # Check if certificate exists
            if self.material.certificate_file_path:
                self.certificate_path_label.setText(os.path.basename(self.material.certificate_file_path))
                self.view_btn.setEnabled(True)
            
            # Load existing QC check if available
            self.qc_check = db.query(QCCheck).filter(QCCheck.material_entry_id == self.material_id).first()
            
            if self.qc_check:
                # Set checkboxes based on existing data
                self.certificate_readable.setChecked(self.qc_check.certificate_readable)
                self.material_matches.setChecked(self.qc_check.material_matches)
                self.dimensions_match.setChecked(self.qc_check.dimensions_match)
                self.certificate_data_correct.setChecked(self.qc_check.certificate_data_correct)
                self.requires_lab.setChecked(self.qc_check.requires_lab_verification)
                
                # Set issue checkboxes
                self.issue_repurchase.setChecked(self.qc_check.issue_repurchase)
                self.issue_poor_quality.setChecked(self.qc_check.issue_poor_quality)
                self.issue_no_stamp.setChecked(self.qc_check.issue_no_stamp)
                self.issue_diameter_deviation.setChecked(self.qc_check.issue_diameter_deviation)
                self.issue_cracks.setChecked(self.qc_check.issue_cracks)
                self.issue_no_melt.setChecked(self.qc_check.issue_no_melt)
                self.issue_no_certificate.setChecked(self.qc_check.issue_no_certificate)
                self.issue_copy.setChecked(self.qc_check.issue_copy)
                
                # Set chemical composition values
                if self.qc_check.chem_c is not None:
                    self.chem_c.setText(str(self.qc_check.chem_c))
                if self.qc_check.chem_si is not None:
                    self.chem_si.setText(str(self.qc_check.chem_si))
                if self.qc_check.chem_mn is not None:
                    self.chem_mn.setText(str(self.qc_check.chem_mn))
                if self.qc_check.chem_s is not None:
                    self.chem_s.setText(str(self.qc_check.chem_s))
                if self.qc_check.chem_p is not None:
                    self.chem_p.setText(str(self.qc_check.chem_p))
                if self.qc_check.chem_cr is not None:
                    self.chem_cr.setText(str(self.qc_check.chem_cr))
                if self.qc_check.chem_ni is not None:
                    self.chem_ni.setText(str(self.qc_check.chem_ni))
                if self.qc_check.chem_cu is not None:
                    self.chem_cu.setText(str(self.qc_check.chem_cu))
                if self.qc_check.chem_ti is not None:
                    self.chem_ti.setText(str(self.qc_check.chem_ti))
                if self.qc_check.chem_al is not None:
                    self.chem_al.setText(str(self.qc_check.chem_al))
                if self.qc_check.chem_mo is not None:
                    self.chem_mo.setText(str(self.qc_check.chem_mo))
                if self.qc_check.chem_v is not None:
                    self.chem_v.setText(str(self.qc_check.chem_v))
                if self.qc_check.chem_nb is not None:
                    self.chem_nb.setText(str(self.qc_check.chem_nb))
                
                # Load comments
                if self.qc_check.notes:
                    self.comments_display.setHtml(self.qc_check.notes)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def upload_certificate(self):
        """Upload certificate file"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]
                
                # Create necessary directories
                reception_dir = os.path.join("docs_storage", "certificates", "На приемке")
                os.makedirs(reception_dir, exist_ok=True)
                
                # Generate certificate filename based on material data
                # Determine size and product type
                size = str(self.material.diameter or self.material.thickness or '')
                if not size:
                    size = "0"
                    
                product_type = self.material.material_type
                # Преобразование типа проката на русский для имени файла
                product_type_map = {
                    "rod": "Круг",
                    "sheet": "Лист",
                    "pipe": "Труба",
                    "angle": "Уголок",
                    "channel": "Швеллер",
                    "other": "Другое"
                }
                product_type_ru = product_type_map.get(product_type, product_type)
                
                # Для типа проката "Круг" (rod) не добавляем тип в имя файла
                if product_type == "rod":
                    size_prefix = f"{size}_"
                else:
                    size_prefix = f"{size}_{product_type_ru}_"
                
                # Очищаем марку от стандарта для имени файла
                grade = clean_material_grade(self.material.material_grade)
                melt = f"пл.{self.material.melt_number}"
                cert_num = f"серт.№{self.material.certificate_number}"
                
                # Get supplier name
                db = SessionLocal()
                supplier = db.query(Supplier).filter(Supplier.id == self.material.supplier_id).first()
                supplier_name = supplier.name if supplier else "Unknown"
                db.close()
                
                # Format date
                cert_date = self.material.certificate_date or datetime.datetime.now()
                date_str = cert_date.strftime("%d.%m.%Y")
                
                # Create certificate filename
                supplier_date = f"{supplier_name}_{date_str}"
                filename = f"{size_prefix}{grade}_{melt}_{cert_num}_({supplier_date}).pdf"
                filename = filename.replace("/", "-").replace("\\", "-").replace(":", "-")
                
                # Save to reception directory
                target_path = os.path.join(reception_dir, filename)
                
                try:
                    shutil.copy2(source_path, target_path)
                    self.certificate_path_label.setText(filename)
                    self.view_btn.setEnabled(True)
                    
                    # Update material certificate path
                    db = SessionLocal()
                    material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
                    material.certificate_file_path = target_path
                    db.commit()
                    
                    # Обновляем локальный объект материала
                    self.material.certificate_file_path = target_path
                    
                    db.close()
                    
                    QMessageBox.information(self, "Успех", "Сертификат успешно загружен")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке сертификата: {str(e)}")
    
    def view_certificate(self):
        """View certificate file"""
        # Получаем актуальный путь к файлу из базы данных
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if not material or not material.certificate_file_path:
                QMessageBox.warning(self, "Предупреждение", "Файл сертификата не найден в базе данных")
                return
                
            certificate_path = material.certificate_file_path
            
            if not os.path.exists(certificate_path):
                QMessageBox.warning(self, "Предупреждение", 
                                  f"Файл сертификата не найден по пути {certificate_path}")
                return
                
            # Open certificate using system default PDF viewer
            os.startfile(certificate_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии сертификата: {str(e)}")
        finally:
            db.close()
    
    def add_comment(self):
        """Add a new comment to the comments history"""
        comment_text = self.new_comment.toPlainText().strip()
        if not comment_text:
            QMessageBox.warning(self, "Предупреждение", "Введите текст комментария")
            return
        
        # Format the comment with user info and timestamp
        timestamp = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")
        formatted_comment = f"<p><b>{self.user.full_name} ({timestamp}):</b><br>{comment_text}</p>"
        
        # Add to display
        current_content = self.comments_display.toHtml()
        new_content = current_content + formatted_comment
        self.comments_display.setHtml(new_content)
        
        # Clear input
        self.new_comment.clear()
    
    def save_qc_check(self):
        """Save QC check data to database"""
        db = SessionLocal()
        try:
            # Check if we have a certificate
            if not self.material.certificate_file_path and not self.issue_no_certificate.isChecked():
                reply = QMessageBox.question(self, "Предупреждение", 
                                          "Сертификат не загружен. Продолжить без сертификата?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            # Create or update QC check
            if not self.qc_check:
                self.qc_check = QCCheck(
                    material_entry_id=self.material_id,
                    checked_by_id=self.user.id
                )
                db.add(self.qc_check)
            
            # Update check data
            self.qc_check.certificate_readable = self.certificate_readable.isChecked()
            self.qc_check.material_matches = self.material_matches.isChecked()
            self.qc_check.dimensions_match = self.dimensions_match.isChecked()
            self.qc_check.certificate_data_correct = self.certificate_data_correct.isChecked()
            self.qc_check.requires_lab_verification = self.requires_lab.isChecked()
            
            # Update issue flags
            self.qc_check.issue_repurchase = self.issue_repurchase.isChecked()
            self.qc_check.issue_poor_quality = self.issue_poor_quality.isChecked()
            self.qc_check.issue_no_stamp = self.issue_no_stamp.isChecked()
            self.qc_check.issue_diameter_deviation = self.issue_diameter_deviation.isChecked()
            self.qc_check.issue_cracks = self.issue_cracks.isChecked()
            self.qc_check.issue_no_melt = self.issue_no_melt.isChecked()
            self.qc_check.issue_no_certificate = self.issue_no_certificate.isChecked()
            self.qc_check.issue_copy = self.issue_copy.isChecked()
            
            # Update chemical composition data
            try:
                # Обрабатываем значения для полей химического состава
                # Принимаем как точку, так и запятую в качестве разделителя
                def parse_float(text):
                    if not text or text.strip() == "":
                        return None
                    try:
                        return float(text.replace(',', '.'))
                    except ValueError:
                        return None
                
                self.qc_check.chem_c = parse_float(self.chem_c.text())
                self.qc_check.chem_si = parse_float(self.chem_si.text())
                self.qc_check.chem_mn = parse_float(self.chem_mn.text())
                self.qc_check.chem_s = parse_float(self.chem_s.text())
                self.qc_check.chem_p = parse_float(self.chem_p.text())
                self.qc_check.chem_cr = parse_float(self.chem_cr.text())
                self.qc_check.chem_ni = parse_float(self.chem_ni.text())
                self.qc_check.chem_cu = parse_float(self.chem_cu.text())
                self.qc_check.chem_ti = parse_float(self.chem_ti.text())
                self.qc_check.chem_al = parse_float(self.chem_al.text())
                self.qc_check.chem_mo = parse_float(self.chem_mo.text())
                self.qc_check.chem_v = parse_float(self.chem_v.text())
                self.qc_check.chem_nb = parse_float(self.chem_nb.text())
            except Exception as e:
                QMessageBox.warning(self, "Предупреждение", f"Ошибка при обработке химического состава: {str(e)}")
                # Продолжаем сохранение даже при ошибке в химическом составе
            
            self.qc_check.notes = self.comments_display.toHtml()
            self.qc_check.checked_at = datetime.datetime.now()
            
            # Update material status
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            material.status = MaterialStatus.QC_CHECKED.value
            
            # If lab verification is required, update status
            if self.requires_lab.isChecked():
                material.requires_lab_verification = True
                material.status = MaterialStatus.LAB_TESTING.value
            
            # Move certificate to final location if QC check is successful
            if (material.certificate_file_path and 
                self.certificate_readable.isChecked() and 
                self.material_matches.isChecked() and 
                self.dimensions_match.isChecked() and 
                self.certificate_data_correct.isChecked()):
                self.move_certificate_to_final_location(material)
            
            db.commit()
            QMessageBox.information(self, "Успех", "Проверка сертификата успешно сохранена")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении данных: {str(e)}")
        finally:
            db.close()
    
    def move_certificate_to_final_location(self, material):
        """Move certificate file to final location after successful QC check"""
        if not material.certificate_file_path or not os.path.exists(material.certificate_file_path):
            return
            
        try:
            # Get certificate filename
            filename = os.path.basename(material.certificate_file_path)
            
            # Create directories for order-based storage
            order_dir = os.path.join("docs_storage", "certificates", "Сертификаты по заказам")
            order_number = material.order_number or "Без заказа"
            order_number = order_number.replace("/", "-")
            
            # Determine product type string
            size = str(material.diameter or material.thickness or "")
            if not size:
                size = "0"
                
            product_type = material.material_type
            # Преобразование типа проката на русский
            product_type_map = {
                "rod": "Круг",
                "sheet": "Лист",
                "pipe": "Труба",
                "angle": "Уголок",
                "channel": "Швеллер",
                "other": "Другое"
            }
            product_type_ru = product_type_map.get(product_type, product_type)
            
            # Создаем директории - используем очищенную марку
            clean_grade = clean_material_grade(material.material_grade)
            grade_dir = os.path.join(order_dir, order_number, clean_grade)
            size_type_dir = os.path.join(grade_dir, f"{size} {product_type_ru}")
            os.makedirs(size_type_dir, exist_ok=True)
            
            # Copy to order directory
            order_target = os.path.join(size_type_dir, filename)
            shutil.copy2(material.certificate_file_path, order_target)
            
            # Create directories for all certificates storage
            all_certs_dir = os.path.join("docs_storage", "certificates", "Все сертификаты")
            all_grade_dir = os.path.join(all_certs_dir, clean_grade)
            all_size_type_dir = os.path.join(all_grade_dir, f"{size} {product_type_ru}")
            os.makedirs(all_size_type_dir, exist_ok=True)
            
            # Copy to all certificates directory
            all_target = os.path.join(all_size_type_dir, filename)
            shutil.copy2(material.certificate_file_path, all_target)
            
            # Update material certificate path to the final location
            material.certificate_file_path = order_target
            
            # Удаляем файл из папки "На приемке"
            try:
                if os.path.exists(material.certificate_file_path) and "На приемке" in material.certificate_file_path:
                    os.remove(material.certificate_file_path)
            except Exception as e:
                print(f"Ошибка при удалении файла из папки На приемке: {e}")
            
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", 
                              f"Ошибка при перемещении сертификата: {str(e)}")

class QCTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.parent = parent
        self.viewed_materials = set()  # Track viewed materials
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create title with modern стиль
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Проверка качества материалов")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {theme_manager.get_color('primary')};")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"background-color: {theme_manager.get_color('border')};")
        main_layout.addWidget(separator)
        
        # Create toolbar with spacing and padding
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(f"""
            background-color: {theme_manager.get_color('card')};
            border-radius: 8px;
            padding: 8px;
        """)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(8, 8, 8, 8)
        toolbar_layout.setSpacing(10)  # Увеличиваем расстояние между кнопками
        
        # Check button
        self.check_btn = QPushButton("Проверить материал")
        self.check_btn.setIcon(IconProvider.create_qc_icon())
        self.check_btn.setMinimumWidth(150)
        apply_button_style(self.check_btn, 'primary')
        self.check_btn.clicked.connect(self.show_check_dialog)
        toolbar_layout.addWidget(self.check_btn)
        
        # View check details button
        self.view_btn = QPushButton("Просмотр проверки")
        self.view_btn.setIcon(IconProvider.create_view_icon())
        self.view_btn.setMinimumWidth(150)
        apply_button_style(self.view_btn, 'secondary')
        self.view_btn.clicked.connect(self.view_check_details)
        toolbar_layout.addWidget(self.view_btn)
        
        # Сертификаты - кнопка просмотра сертификатов
        self.cert_btn = QPushButton("Сертификаты")
        self.cert_btn.setIcon(IconProvider.create_certificate_icon())
        self.cert_btn.setMinimumWidth(120)
        apply_button_style(self.cert_btn, 'primary')
        self.cert_btn.clicked.connect(self.open_certificate_browser)
        toolbar_layout.addWidget(self.cert_btn)
        
        # Search field with icon
        search_layout = QHBoxLayout()
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_icon_label = QLabel()
        search_icon_label.setPixmap(IconProvider.create_search_icon().pixmap(16, 16))
        search_layout.addWidget(search_icon_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по марке, партии, плавке...")
        self.search_input.setStyleSheet(theme_manager.get_input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.filter_materials)
        search_layout.addWidget(self.search_input)
        
        toolbar_layout.addWidget(search_widget)
        
        # Status filter with icon
        filter_layout = QHBoxLayout()
        filter_widget = QWidget()
        filter_widget.setLayout(filter_layout)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        filter_icon_label = QLabel()
        filter_icon_label.setPixmap(IconProvider.create_filter_icon().pixmap(16, 16))
        filter_layout.addWidget(filter_icon_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", "")
        self.status_filter.addItem("На проверке", MaterialStatus.PENDING_QC.value)
        self.status_filter.addItem("Проверка пройдена", MaterialStatus.QC_PASSED.value)
        self.status_filter.addItem("Проверка не пройдена", MaterialStatus.QC_FAILED.value)
        self.status_filter.addItem("На лабораторных", MaterialStatus.LAB_TESTING.value)
        self.status_filter.addItem("Редактирование", MaterialStatus.EDIT_REQUESTED.value)
        self.status_filter.setStyleSheet(theme_manager.get_input_style())
        self.status_filter.setMinimumWidth(150)
        self.status_filter.currentIndexChanged.connect(self.filter_materials)
        filter_layout.addWidget(self.status_filter)
        
        toolbar_layout.addWidget(filter_widget)
        
        # Refresh button
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setIcon(IconProvider.create_refresh_icon())
        self.refresh_btn.setMinimumWidth(100)
        apply_button_style(self.refresh_btn, 'neutral')
        self.refresh_btn.clicked.connect(self.load_materials)
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(toolbar_widget)
        
        # Container for table with frame and spacing
        table_container = QFrame()
        table_container.setFrameShape(QFrame.Shape.StyledPanel)
        table_container.setStyleSheet(f"""
            background-color: {theme_manager.get_color('card')};
            border: 1px solid {theme_manager.get_color('border')};
            border-radius: 8px;
            padding: 8px;
        """)
        
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(8, 8, 8, 8)
        
        # Table title
        table_title = QLabel("Материалы на проверке")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        table_title.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        table_layout.addWidget(table_title)
        
        # Create pending materials table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(9)
        self.materials_table.setHorizontalHeaderLabels([
            "ID", "Марка материала", "Вид проката", "Размер", "Плавка", 
            "Партия", "Сертификат", "Поставщик", "Статус"
        ])
        
        # Set column widths
        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Марка материала
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Вид проката
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Размер
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Плавка
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Партия
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Сертификат
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Поставщик
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Статус
        
        # Устанавливаем минимальные размеры для важных колонок
        self.materials_table.horizontalHeader().setMinimumSectionSize(60)
        
        # Включаем нумерацию строк с минимальной шириной
        self.materials_table.verticalHeader().setVisible(True)
        self.materials_table.verticalHeader().setMinimumWidth(40)
        self.materials_table.verticalHeader().setDefaultSectionSize(36)
        
        # Включаем выделение строк
        self.materials_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.materials_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Улучшаем читаемость границ и отображение
        self.materials_table.setShowGrid(True)
        self.materials_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        # Стили для таблицы с улучшенной подсветкой выбранной строки и четкими границами
        self.materials_table.setStyleSheet(f"""
            {theme_manager.get_table_style()}
            QTableWidget {{
                gridline-color: {theme_manager.get_color('border')};
                border: 1px solid {theme_manager.get_color('border')};
                padding: 5px;
            }}
            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {theme_manager.get_color('border')};
            }}
            QTableWidget::item:selected {{
                background-color: {theme_manager.get_color('primary')};
                color: white;
            }}
            QTableWidget::item:hover:!selected {{
                background-color: {theme_manager.get_color('hover')};
            }}
            QHeaderView::section {{
                background-color: {theme_manager.get_color('header')};
                color: {theme_manager.get_color('text_primary')};
                font-weight: bold;
                padding: 6px;
                border: 1px solid {theme_manager.get_color('border')};
            }}
        """)
        
        # Включаем чередование строк для лучшей читаемости
        self.materials_table.setAlternatingRowColors(True)
        
        # Настраиваем контекстное меню для таблицы
        self.materials_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.materials_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Двойной клик по строке для просмотра деталей
        self.materials_table.cellDoubleClicked.connect(self.view_check_details)
        
        table_layout.addWidget(self.materials_table)
        
        # Add table status row
        status_layout = QHBoxLayout()
        
        self.table_status_label = QLabel("Загрузка данных...")
        self.table_status_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        status_layout.addWidget(self.table_status_label)
        
        status_layout.addStretch()
        
        self.records_count_label = QLabel("Записей: 0")
        self.records_count_label.setStyleSheet(f"color: {theme_manager.get_color('primary')}; font-weight: bold;")
        status_layout.addWidget(self.records_count_label)
        
        table_layout.addLayout(status_layout)
        
        main_layout.addWidget(table_container, 1)  # 1 = stretch factor
        
        # Load materials that need QC
        self.load_materials()
        
    def open_certificate_browser(self):
        """Открыть диалог просмотра сертификатов"""
        from ui.dialogs.certificate_browser_dialog import CertificateBrowserDialog
        dialog = CertificateBrowserDialog(self)
        dialog.exec()
    
    def load_materials(self):
        """Load materials that need QC check"""
        db = SessionLocal()
        try:
            # Get status filter
            status_filter = self.status_filter.currentData()
            
            # Get materials that need QC check
            query = db.query(MaterialEntry).filter(MaterialEntry.is_deleted == False)
            
            if status_filter:
                query = query.filter(MaterialEntry.status == status_filter)
            
            materials = query.order_by(desc(MaterialEntry.created_at)).all()
            
            # Clear table
            self.materials_table.setRowCount(0)
            
            # Add materials to table
            for row, material in enumerate(materials):
                self.materials_table.insertRow(row)
                
                # Сохраняем ID как данные (UserRole), но не отображаем
                # Очищаем марку материала от стандарта
                clean_grade = clean_material_grade(material.material_grade)
                grade_item = QTableWidgetItem(clean_grade)
                grade_item.setData(Qt.UserRole, material.id)
                self.materials_table.setItem(row, 0, grade_item)
                
                self.materials_table.setItem(row, 1, QTableWidgetItem(get_material_type_display(material.material_type)))
                self.materials_table.setItem(row, 2, QTableWidgetItem(material.batch_number or ""))
                self.materials_table.setItem(row, 3, QTableWidgetItem(material.melt_number))
                
                # Get supplier name
                supplier = db.query(Supplier).filter(Supplier.id == material.supplier_id).first()
                supplier_name = supplier.name if supplier else "Неизвестно"
                self.materials_table.setItem(row, 4, QTableWidgetItem(supplier_name))
                
                # Status
                status_item = QTableWidgetItem(get_status_display_name(material.status))
                self.materials_table.setItem(row, 5, status_item)
                
                # New/viewed mark
                mark_text = ""
                mark_color = None
                
                if material.id not in self.viewed_materials:
                    mark_text = "Новая"
                    mark_color = QColor(255, 255, 0)  # Yellow
                
                # Добавляем иконку запроса на редактирование если есть запрос
                if material.edit_requested:
                    mark_text = "⚠️ Запрос изменений"
                    mark_color = QColor(255, 165, 0)  # Orange
                
                mark_item = QTableWidgetItem(mark_text)
                if mark_color:
                    mark_item.setBackground(QBrush(mark_color))
                self.materials_table.setItem(row, 6, mark_item)
                
                # Color row by status
                row_color = None
                if material.status == MaterialStatus.RECEIVED.value:
                    row_color = QColor(255, 255, 200)  # Light yellow
                elif material.status == MaterialStatus.QC_CHECKED.value:
                    row_color = QColor(200, 255, 200)  # Light green
                elif material.status == MaterialStatus.LAB_TESTING.value:
                    row_color = QColor(200, 200, 255)  # Light blue
                elif material.status == MaterialStatus.EDIT_REQUESTED.value:
                    row_color = QColor(255, 230, 200)  # Light orange
                
                if row_color:
                    self.color_row(row, row_color)
            
            # Update status
            self.parent.status_bar.showMessage(f"Загружено {len(materials)} материалов")
            
            # После заполнения таблицы данными:
            self.materials_table.resizeColumnsToContents()
            
            # Ограничим максимальную ширину колонок и установим минимальную
            min_widths = {
                0: 60,   # ID
                1: 120,  # Марка материала 
                2: 80,   # Вид проката
                3: 80,   # Размер
                4: 80,   # Плавка
                5: 80,   # Партия
                6: 100,  # Сертификат
                7: 100,  # Поставщик
                8: 100   # Статус
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
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке материалов: {str(e)}")
        finally:
            db.close()
    
    def color_row(self, row, color):
        """Set background color for entire row"""
        for col in range(self.materials_table.columnCount()):
            item = self.materials_table.item(row, col)
            if item:
                item.setBackground(QBrush(color))
    
    def filter_materials(self):
        """Filter materials by search text"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.materials_table.rowCount()):
            show_row = True
            
            # Check if row matches search text
            if search_text:
                match_found = False
                for col in range(1, 5):  # Check columns 1-4 (material info)
                    item = self.materials_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                if not match_found:
                    show_row = False
            
            # Show/hide row
            self.materials_table.setRowHidden(row, not show_row)
    
    def show_qc_check_form(self, row, column):
        """Show form to check material certificate"""
        # Получаем ID из данных ячейки
        material_id = self.materials_table.item(row, 0).data(Qt.UserRole)
        
        # Mark as viewed
        self.viewed_materials.add(material_id)
        
        # Проверяем, есть ли запрос на редактирование
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            if material and material.edit_requested:
                # Есть запрос на редактирование - спрашиваем подтверждение
                reply = QMessageBox.question(
                    self, 
                    "Запрос на редактирование", 
                    f"Кладовщик запрашивает разрешение на редактирование материала.\n\n"
                    f"Причина: {material.edit_comment}\n\n"
                    f"Разрешить редактирование?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Подтверждаем запрос - сбрасываем статус до RECEIVED
                    material.status = MaterialStatus.RECEIVED.value
                    db.commit()
                    QMessageBox.information(
                        self, 
                        "Запрос подтвержден", 
                        "Вы разрешили редактирование материала. "
                        "Кладовщик теперь может внести изменения."
                    )
                    self.load_materials()
                    return
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке запроса: {str(e)}")
        finally:
            db.close()
        
        # Create and show QC check form
        qc_form = QCCheckForm(material_id, self.user, self)
        result = qc_form.exec()
        
        # Refresh materials list if form was accepted
        if result == QDialog.Accepted:
            self.load_materials()
    
    def show_check_dialog(self):
        """Показать диалог проверки для выбранного материала"""
        # Проверяем, выбран ли материал
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите материал для проверки")
            return
        
        # Получаем строку выбранного материала
        row = selected_items[0].row()
        
        # Вызываем форму проверки
        self.show_qc_check_form(row, 0)
    
    def view_check_details(self):
        """Просмотр деталей проверки выбранного материала"""
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите материал для просмотра")
            return
        
        row = selected_items[0].row()
        material_id = self.materials_table.item(row, 0).data(Qt.UserRole)
        
        # Проверяем, есть ли данные проверки для этого материала
        db = SessionLocal()
        try:
            qc_check = db.query(QCCheck).filter(QCCheck.material_id == material_id).first()
            
            if not qc_check:
                QMessageBox.information(self, "Информация", "Для данного материала проверка еще не проводилась")
                return
            
            # Создаем форму в режиме просмотра
            qc_form = QCCheckForm(material_id, self.user, self)
            qc_form.setWindowTitle(f"Просмотр проверки материала #{material_id}")
            
            # Делаем форму только для чтения
            for widget in qc_form.findChildren((QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox)):
                widget.setEnabled(False)
            
            # Скрываем кнопки сохранения
            if hasattr(qc_form, 'save_btn'):
                qc_form.save_btn.hide()
            
            qc_form.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных проверки: {str(e)}")
        finally:
            db.close()
    
    def show_context_menu(self, position):
        """Показать контекстное меню для таблицы материалов"""
        selected_items = self.materials_table.selectedItems()
        if not selected_items:
            return
            
        menu = QMenu(self)
        
        # Пункт меню "Проверить"
        check_action = QAction(IconProvider.create_qc_icon(), "Провести проверку", self)
        check_action.triggered.connect(self.show_check_dialog)
        menu.addAction(check_action)
        
        # Пункт меню "Просмотреть проверку"
        view_action = QAction(IconProvider.create_view_icon(), "Просмотреть проверку", self)
        view_action.triggered.connect(self.view_check_details)
        menu.addAction(view_action)
        
        # Показываем меню
        menu.exec(self.materials_table.mapToGlobal(position)) 