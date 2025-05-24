from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QDateEdit, QMessageBox, QFormLayout, QDialog, QTableWidget, QTableWidgetItem, QGroupBox, QFrame, QSpinBox, QDoubleSpinBox, QHeaderView, QCheckBox)
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from database.connection import SessionLocal
from models.models import MaterialGrade, ProductType, Supplier, MaterialEntry, MaterialSize, MaterialType, MaterialStatus
from ui.icons.icon_provider import IconProvider
import re, datetime

class OrderNumberValidator(QRegularExpressionValidator):
    """Валидатор для поля номера заказа с автоматической вставкой слеша"""
    def __init__(self, parent=None):
        # Разрешаем только цифры и один слеш в нужной позиции
        regex = QRegularExpression("^[0-9]{0,4}(/[0-9]{0,3})?$")
        super().__init__(regex, parent)

class WarehouseEntryForm(QDialog):
    def __init__(self, parent=None, user=None, material_id=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление материала")
        self.setWindowIcon(IconProvider.create_material_entry_icon())
        self.user = user  # Сохраняем пользователя
        self.material_id = material_id  # ID материала для редактирования
        self.editing_mode = material_id is not None  # Режим редактирования
        self.init_ui()
        
        if self.editing_mode:
            self.load_material_data()
            self.setWindowTitle(f"Редактирование материала #{material_id}")
            
        self.resize(800, 600)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Заголовок формы
        title_label = QLabel("Добавление нового материала на склад")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Группа основных данных
        basic_group = QGroupBox("Основная информация")
        basic_layout = QFormLayout()
        basic_group.setLayout(basic_layout)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        basic_layout.addRow("Дата прихода:", self.date_input)

        self.grade_combo = QComboBox()
        self.grade_combo.setToolTip("Выберите марку материала из справочника")
        self.load_grades()
        basic_layout.addRow(QLabel("Марка:"), self.grade_combo)

        self.type_combo = QComboBox()
        self.type_combo.setToolTip("Выберите вид проката из справочника")
        self.load_types()
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        basic_layout.addRow(QLabel("Вид проката:"), self.type_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setToolTip("Выберите поставщика из справочника")
        self.load_suppliers()
        basic_layout.addRow(QLabel("Поставщик:"), self.supplier_combo)
        
        main_layout.addWidget(basic_group)
        
        # Группа документов
        docs_group = QGroupBox("Документы")
        docs_layout = QFormLayout()
        docs_group.setLayout(docs_layout)

        self.order_input = QLineEdit()
        self.order_input.setPlaceholderText("0000/000")
        # Настройка валидатора для номера заказа
        self.order_input.setValidator(OrderNumberValidator())
        self.order_input.textChanged.connect(self.format_order_number)
        docs_layout.addRow("№ заказа:", self.order_input)

        self.cert_input = QLineEdit()
        self.cert_input.setPlaceholderText("123/45-67")
        docs_layout.addRow("№ сертификата:", self.cert_input)
        
        # Добавляем дату сертификата
        self.cert_date_input = QDateEdit(QDate.currentDate())
        self.cert_date_input.setCalendarPopup(True)
        docs_layout.addRow("Дата сертификата:", self.cert_date_input)

        self.melt_input = QLineEdit()
        self.melt_input.setPlaceholderText("A123456")
        
        # Добавляем чекбокс "В сертификате нет плавки"
        melt_layout = QHBoxLayout()
        melt_layout.addWidget(self.melt_input)
        self.no_melt_checkbox = QCheckBox("В сертификате нет плавки")
        self.no_melt_checkbox.stateChanged.connect(self.toggle_melt_input)
        melt_layout.addWidget(self.no_melt_checkbox)
        docs_layout.addRow("№ плавки:", melt_layout)

        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("B123456")
        docs_layout.addRow("№ партии (необязательно):", self.batch_input)
        
        main_layout.addWidget(docs_group)
        
        # Группа размеров
        size_group = QGroupBox("Размеры и количество")
        size_layout = QVBoxLayout()
        size_group.setLayout(size_layout)
        
        # Форма с размерами в зависимости от типа материала
        self.dimensions_widget = QWidget()
        self.dimensions_layout = QFormLayout(self.dimensions_widget)
        
        # Поля для размеров
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.1, 500)
        self.thickness_spin.setDecimals(1)
        self.thickness_spin.setSuffix(" мм")
        
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(10, 3000)
        self.width_spin.setDecimals(1)
        self.width_spin.setSuffix(" мм")
        
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(3, 1000)
        self.diameter_spin.setDecimals(1)
        self.diameter_spin.setSuffix(" мм")
        
        self.wall_thickness_spin = QDoubleSpinBox()
        self.wall_thickness_spin.setRange(0.5, 100)
        self.wall_thickness_spin.setDecimals(1)
        self.wall_thickness_spin.setSuffix(" мм")
        
        size_layout.addWidget(self.dimensions_widget)
        
        # Добавляем кнопку для ввода размеров
        sizes_btn_layout = QHBoxLayout()
        self.sizes_btn = QPushButton("Добавить размеры и количество")
        self.sizes_btn.setIcon(IconProvider.create_material_entry_icon())
        self.sizes_btn.clicked.connect(self.open_sizes_dialog)
        sizes_btn_layout.addWidget(self.sizes_btn)
        size_layout.addLayout(sizes_btn_layout)
        
        # Таблица размеров
        self.sizes_table = QTableWidget()
        self.sizes_table.setColumnCount(2)
        self.sizes_table.setHorizontalHeaderLabels(["Длина (мм)", "Количество (шт)"])
        # Растягиваем колонки
        header = self.sizes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        size_layout.addWidget(self.sizes_table)
        
        # Создаем компоновку для отображения веса и общей длины
        stats_layout = QHBoxLayout()
        
        # Общий вес
        self.weight_label = QLabel("Вес: 0 т")
        self.weight_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.weight_label)
        
        # Общая длина
        self.total_length_label = QLabel("Общая длина: 0 мм")
        self.total_length_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.total_length_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.total_length_label)
        
        size_layout.addLayout(stats_layout)
        
        main_layout.addWidget(size_group)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить приход")
        self.save_btn.setIcon(IconProvider.create_material_entry_icon())
        self.save_btn.clicked.connect(self.save_entry)
        
        self.clear_btn = QPushButton("Очистить форму")
        self.clear_btn.clicked.connect(self.clear_form)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(actions_layout)
        
        # Инициализация данных
        self.sizes = []  # [(length, qty)]
        self.total_weight = 0
        self.total_length = 0  # Общая длина
        
        # Находим и выбираем "круг" в списке типов проката
        self.select_round_by_default()
        self.on_type_changed()

    def toggle_melt_input(self, state):
        """Переключение доступности поля ввода номера плавки"""
        self.melt_input.setEnabled(not state)
        if state:
            self.melt_input.clear()

    def format_order_number(self, text):
        """Форматирует номер заказа, добавляя слеш после ввода 4 цифр"""
        if len(text) == 4 and not text.endswith('/'):
            self.order_input.setText(text + '/')
    
    def select_round_by_default(self):
        """Находит и выбирает тип проката 'круг' по умолчанию"""
        round_index = -1
        for i in range(self.type_combo.count()):
            if "круг" in self.type_combo.itemText(i).lower():
                round_index = i
                break
        
        if round_index >= 0:
            self.type_combo.setCurrentIndex(round_index)
        else:
            # Если "круг" не найден, установить первый элемент
            if self.type_combo.count() > 0:
                self.type_combo.setCurrentIndex(0)

    def on_type_changed(self):
        """Обновление полей размеров в зависимости от типа материала"""
        # Очищаем текущие поля размеров
        while self.dimensions_layout.rowCount() > 0:
            self.dimensions_layout.removeRow(0)
        
        material_type = self.type_combo.currentText().lower()
        
        if "лист" in material_type:
            self.dimensions_layout.addRow("Толщина:", self.thickness_spin)
            self.dimensions_layout.addRow("Ширина:", self.width_spin)
        elif "труб" in material_type:
            self.dimensions_layout.addRow("Диаметр:", self.diameter_spin)
            self.dimensions_layout.addRow("Толщина стенки:", self.wall_thickness_spin)
        elif "пруток" in material_type or "круг" in material_type:
            self.dimensions_layout.addRow("Диаметр:", self.diameter_spin)
        elif "уголок" in material_type:
            self.dimensions_layout.addRow("Толщина:", self.thickness_spin)
            self.dimensions_layout.addRow("Ширина полки:", self.width_spin)
        elif "швеллер" in material_type:
            self.dimensions_layout.addRow("Высота стенки:", self.thickness_spin)
            self.dimensions_layout.addRow("Ширина полки:", self.width_spin)
            self.dimensions_layout.addRow("Толщина стенки:", self.wall_thickness_spin)
        else:
            # Для неизвестных типов показываем все поля
            self.dimensions_layout.addRow("Толщина:", self.thickness_spin)
            self.dimensions_layout.addRow("Ширина:", self.width_spin)
            self.dimensions_layout.addRow("Диаметр:", self.diameter_spin)
    
    def load_grades(self):
        try:
            self.grade_combo.clear()
            db = SessionLocal()
            for g in db.query(MaterialGrade).filter(MaterialGrade.is_deleted == False).all():
                self.grade_combo.addItem(f"{g.name} ({g.standard or ''})", g.id)
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке марок материалов: {str(e)}")

    def load_types(self):
        try:
            self.type_combo.clear()
            db = SessionLocal()
            for t in db.query(ProductType).filter(ProductType.is_deleted == False).all():
                # Добавляем соответствующую иконку в зависимости от типа
                icon = self.get_product_type_icon(t.name)
                self.type_combo.addItem(icon, t.name, t.id)
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке видов проката: {str(e)}")
    
    def get_product_type_icon(self, type_name):
        """Возвращает соответствующую иконку для типа продукции"""
        type_lower = type_name.lower()
        if "круг" in type_lower or "пруток" in type_lower:
            return IconProvider.create_round_product_icon()
        elif "лист" in type_lower:
            return IconProvider.create_sheet_product_icon()
        elif "труб" in type_lower:
            return IconProvider.create_pipe_product_icon()
        elif "уголок" in type_lower:
            return IconProvider.create_angle_product_icon()
        elif "швеллер" in type_lower:
            return IconProvider.create_channel_product_icon()
        else:
            return IconProvider.create_product_type_icon()

    def load_suppliers(self):
        try:
            self.supplier_combo.clear()
            db = SessionLocal()
            for s in db.query(Supplier).filter(Supplier.is_deleted == False).all():
                self.supplier_combo.addItem(s.name, s.id)
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке поставщиков: {str(e)}")

    def open_sizes_dialog(self):
        dialog = SizesDialog(self, self.grade_combo.currentData())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sizes = dialog.get_sizes()
            self.total_weight = dialog.get_total_weight()
            self.total_length = dialog.get_total_length()
            # Отображаем вес в тоннах с 3 знаками после запятой
            tons = self.total_weight / 1000  # конвертируем из кг в тонны
            self.format_weight_label(tons)
            # Обновляем отображение общей длины
            self.total_length_label.setText(f"Общая длина: {self.total_length} мм")
            self.update_sizes_table()

    def format_weight_label(self, tons):
        """Форматирует вес в тоннах, убирая лишние нули после запятой"""
        # Форматируем с 3 знаками после запятой
        formatted = f"{tons:.3f}".rstrip('0').rstrip('.') if '.' in f"{tons:.3f}" else f"{tons:.3f}"
        self.weight_label.setText(f"Вес: {formatted} т")

    def update_sizes_table(self):
        """Обновляет таблицу размеров"""
        self.sizes_table.setRowCount(0)
        for row, (length, qty) in enumerate(self.sizes):
            self.sizes_table.insertRow(row)
            self.sizes_table.setItem(row, 0, QTableWidgetItem(str(length)))
            self.sizes_table.setItem(row, 1, QTableWidgetItem(str(qty)))

    def load_material_data(self):
        """Загружает данные материала в форму для редактирования"""
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            if not material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден")
                self.reject()
                return
                
            # Загружаем дату
            if material.created_at:
                date = QDate(material.created_at.year, material.created_at.month, material.created_at.day)
                self.date_input.setDate(date)
            
            # Выбираем марку
            index = self.grade_combo.findText(material.material_grade)
            if index >= 0:
                self.grade_combo.setCurrentIndex(index)
            else:
                self.grade_combo.setEditText(material.material_grade)
            
            # Выбираем тип материала
            index = -1
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == material.material_type:
                    index = i
                    break
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            
            # Выбираем поставщика
            index = -1
            for i in range(self.supplier_combo.count()):
                if self.supplier_combo.itemData(i) == material.supplier_id:
                    index = i
                    break
            if index >= 0:
                self.supplier_combo.setCurrentIndex(index)
            
            # Заполняем данные документов
            self.order_input.setText(material.order_number or "")
            self.cert_input.setText(material.certificate_number or "")
            
            # Дата сертификата
            if material.certificate_date:
                cert_date = QDate(material.certificate_date.year, material.certificate_date.month, material.certificate_date.day)
                self.cert_date_input.setDate(cert_date)
            
            # Номер плавки и флаг отсутствия плавки
            self.no_melt_checkbox.setChecked(material.no_melt_number)
            if not material.no_melt_number:
                self.melt_input.setText(material.melt_number or "")
            
            # Номер партии
            self.batch_input.setText(material.batch_number or "")
            
            # Размеры в зависимости от типа материала
            if material.material_type == MaterialType.SHEET.value:
                self.thickness_spin.setValue(material.thickness or 0)
                self.width_spin.setValue(material.width or 0)
            elif material.material_type == MaterialType.PIPE.value:
                self.diameter_spin.setValue(material.diameter or 0)
                self.wall_thickness_spin.setValue(material.wall_thickness or 0)
            elif material.material_type == MaterialType.ROD.value:
                self.diameter_spin.setValue(material.diameter or 0)
            
            # Загружаем размеры из связанной таблицы
            self.sizes = [(size.length, size.quantity) for size in material.sizes]
            self.update_sizes_table()
            
            # Обновляем общий вес и длину
            total_weight_tons = material.quantity / 1000.0 if material.quantity else 0
            self.total_weight = material.quantity
            self.weight_label.setText(self.format_weight_label(total_weight_tons))
            
            # Обновляем надпись кнопки сохранения
            self.save_btn.setText("Сохранить изменения")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
        
    def save_entry(self):
        """Сохранение записи о материале"""
        # Проверка обязательных полей
        
        # Марка материала
        material_grade = self.grade_combo.currentText().strip()
        if not material_grade:
            QMessageBox.warning(self, "Предупреждение", "Введите марку материала")
            return
        
        # Номер сертификата
        cert_number = self.cert_input.text().strip()
        if not cert_number:
            QMessageBox.warning(self, "Предупреждение", "Введите номер сертификата")
            return
        
        # Номер плавки (если не отмечен чекбокс)
        melt_number = self.melt_input.text().strip()
        no_melt_number = self.no_melt_checkbox.isChecked()
        if not no_melt_number and not melt_number:
            QMessageBox.warning(self, "Предупреждение", "Введите номер плавки или отметьте, что его нет")
            return
        
        # Проверка размеров
        if not self.sizes:
            QMessageBox.warning(self, "Предупреждение", "Добавьте хотя бы один размер")
            return
        
        # Создаем или получаем запись материала
        db = SessionLocal()
        try:
            if self.editing_mode:
                # Редактирование существующего материала
                material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
                if not material:
                    QMessageBox.critical(self, "Ошибка", "Материал не найден")
                    return
            else:
                # Создание нового материала
                material = MaterialEntry()
                material.created_by_id = self.user.id
                material.status = MaterialStatus.RECEIVED.value
                
            # Установка данных материала
            material.material_grade = material_grade
            material.material_type = self.get_material_type()
            material.supplier_id = self.supplier_combo.currentData()
            
            # Размеры по типу материала
            if material.material_type == MaterialType.SHEET.value:
                material.thickness = self.thickness_spin.value()
                material.width = self.width_spin.value()
                material.diameter = None
                material.wall_thickness = None
            elif material.material_type == MaterialType.PIPE.value:
                material.thickness = None
                material.width = None
                material.diameter = self.diameter_spin.value()
                material.wall_thickness = self.wall_thickness_spin.value()
            elif material.material_type == MaterialType.ROD.value:
                material.thickness = None
                material.width = None
                material.diameter = self.diameter_spin.value()
                material.wall_thickness = None
            
            # Данные документов
            order_number = self.order_input.text().strip()
            material.order_number = order_number if order_number else None
            
            material.certificate_number = cert_number
            
            cert_date = self.cert_date_input.date().toPython()
            material.certificate_date = cert_date
            
            batch_number = self.batch_input.text().strip()
            material.batch_number = batch_number if batch_number else None
            
            material.no_melt_number = no_melt_number
            material.melt_number = "Н/Д" if no_melt_number else melt_number
            
            # Количество
            material.quantity = self.total_weight
            material.unit = "кг"
            
            # Если редактирование, удаляем старые размеры
            if self.editing_mode and material.sizes:
                for size in material.sizes:
                    db.delete(size)
                material.sizes = []
                
            # Добавляем новые размеры
            for length, qty in self.sizes:
                size = MaterialSize(material_entry=material, length=length, quantity=qty)
                db.add(size)
            
            # Сохраняем данные
            if not self.editing_mode:
                db.add(material)
            db.commit()
            
            QMessageBox.information(
                self, 
                "Успех", 
                "Материал успешно сохранен" if not self.editing_mode else "Изменения успешно сохранены"
            )
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении материала: {str(e)}")
        finally:
            db.close()

    def get_material_type(self):
        """Определяет тип материала на основе выбранного значения в combobox"""
        material_type_text = self.type_combo.currentText().lower()
        
        if "лист" in material_type_text:
            return MaterialType.SHEET.value
        elif "труб" in material_type_text:
            return MaterialType.PIPE.value
        elif "пруток" in material_type_text or "круг" in material_type_text:
            return MaterialType.ROD.value
        elif "уголок" in material_type_text:
            return MaterialType.ANGLE.value
        elif "швеллер" in material_type_text:
            return MaterialType.CHANNEL.value
        else:
            return MaterialType.OTHER.value

    def clear_form(self):
        self.order_input.clear()
        self.cert_input.clear()
        self.melt_input.clear()
        self.batch_input.clear()
        self.no_melt_checkbox.setChecked(False)
        self.thickness_spin.setValue(0)
        self.width_spin.setValue(0)
        self.diameter_spin.setValue(0)
        self.wall_thickness_spin.setValue(0)
        self.sizes = []
        self.weight_label.setText("Вес: 0 т")
        self.total_length_label.setText("Общая длина: 0 мм")
        self.sizes_table.setRowCount(0)

class SizesDialog(QDialog):
    def __init__(self, parent=None, grade_id=None):
        super().__init__(parent)
        self.setWindowTitle("Ввод размеров и количества")
        self.setWindowIcon(IconProvider.create_material_entry_icon())
        self.grade_id = grade_id
        self.sizes = []
        self.total_weight = 0
        self.total_length = 0  # Общая длина
        
        layout = QVBoxLayout(self)
        
        # Инструкция
        instruction_label = QLabel("Укажите длины и количество единиц материала")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction_label)
        
        # Формула ввода
        formula_group = QGroupBox("Ввод через формулу")
        formula_layout = QVBoxLayout()
        formula_group.setLayout(formula_layout)
        
        formula_help = QLabel("Формат: длина*количество+длина*количество\nПример: 2540*10+485+8769*3")
        formula_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formula_layout.addWidget(formula_help)
        
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Пример: 2540*10+485+8769*3")
        formula_layout.addWidget(self.formula_input)
        
        parse_btn = QPushButton("Рассчитать")
        parse_btn.clicked.connect(self.parse_formula)
        formula_layout.addWidget(parse_btn)
        
        layout.addWidget(formula_group)
        
        # Таблица размеров
        table_group = QGroupBox("Размеры")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Длина (мм)", "Количество (шт)"])
        
        # Растягиваем колонки
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        table_layout.addWidget(self.table)
        
        # Создаем компоновку для отображения веса и общей длины
        stats_layout = QHBoxLayout()
        
        # Отображаем вес в тоннах с 3 знаками после запятой
        self.weight_label = QLabel("Вес: 0 т")
        self.weight_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.weight_label)
        
        # Общая длина
        self.length_label = QLabel("Общая длина: 0 мм")
        self.length_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.length_label)
        
        table_layout.addLayout(stats_layout)
        
        layout.addWidget(table_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Сохранить")
        self.ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Устанавливаем минимальный размер окна
        self.resize(500, 400)

    def parse_formula(self):
        try:
            formula = self.formula_input.text()
            self.sizes = []
            for part in formula.split('+'):
                m = re.match(r'(\d+)(\*(\d+))?', part.strip())
                if m:
                    length = int(m.group(1))
                    qty = int(m.group(3)) if m.group(3) else 1
                    self.sizes.append((length, qty))
            
            if not self.sizes:
                QMessageBox.warning(self, "Ошибка", "Не удалось распознать формулу размеров.\nУбедитесь, что формат соответствует примеру.")
                return
                
            self.update_table()
            self.calc_weight()
            self.update_total_length()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при разборе формулы: {str(e)}")

    def update_table(self):
        self.table.setRowCount(0)
        for row, (length, qty) in enumerate(self.sizes):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(length)))
            self.table.setItem(row, 1, QTableWidgetItem(str(qty)))

    def update_total_length(self):
        """Обновляет информацию об общей длине"""
        self.total_length = sum(length * qty for length, qty in self.sizes)
        self.length_label.setText(f"Общая длина: {self.total_length} мм")

    def calc_weight(self):
        try:
            # Получаем плотность марки
            db = SessionLocal()
            density = None
            if self.grade_id:
                grade = db.query(MaterialGrade).filter(MaterialGrade.id == self.grade_id).first()
                if grade:
                    density = grade.density
            db.close()
            
            # Пример расчета веса для круга: вес = π/4 * d^2 * L * ρ * qty / 1e9 (d, L в мм, ρ в кг/м3)
            # Для простоты считаем d = длина (можно доработать под тип проката)
            self.total_weight = 0
            if density:
                for length, qty in self.sizes:
                    # Пример: для круга длина — это длина прутка, диаметр надо бы брать из отдельного поля
                    # Здесь просто length*qty*density/1000 (упрощённо)
                    self.total_weight += length * qty * density / 1000
            else:
                self.total_weight = sum(length * qty for length, qty in self.sizes) / 1000  # Примерный вес
                
            # Отображаем вес в тоннах с форматированием
            tons = self.total_weight / 1000  # кг в тонны
            formatted = f"{tons:.3f}".rstrip('0').rstrip('.') if '.' in f"{tons:.3f}" else f"{tons:.3f}"
            self.weight_label.setText(f"Вес: {formatted} т")
            
            # Обновляем общую длину
            self.update_total_length()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете веса: {str(e)}")

    def get_sizes(self):
        return self.sizes
    
    def get_total_weight(self):
        return self.total_weight
    
    def get_total_length(self):
        return self.total_length 