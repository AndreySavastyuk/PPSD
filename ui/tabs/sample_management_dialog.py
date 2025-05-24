from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
                               QFormLayout, QMessageBox, QGroupBox, QHeaderView,
                               QDoubleSpinBox, QTextEdit, QCheckBox, QDialogButtonBox,
                               QInputDialog, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QBrush, QIcon, QPixmap

from database.connection import SessionLocal
from models.models import Sample, SampleRequest, MaterialEntry, User, MaterialStatus
import datetime
import os
import shutil


class SampleManagementDialog(QDialog):
    """Диалог для управления образцами"""
    samples_updated = Signal()  # Сигнал об обновлении образцов
    
    def __init__(self, sample_request_id, user, parent=None):
        super().__init__(parent)
        self.sample_request_id = sample_request_id
        self.user = user
        self.parent = parent
        self.sample_request = None
        self.material = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Управление образцами")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Информация о материале и заявке
        info_group = QGroupBox("Информация о заявке")
        info_layout = QFormLayout()
        
        self.material_label = QLabel()
        info_layout.addRow("Материал:", self.material_label)
        
        self.request_info_label = QLabel()
        info_layout.addRow("Заявка:", self.request_info_label)
        
        self.tests_label = QLabel()
        info_layout.addRow("Требуемые испытания:", self.tests_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Панель инструментов
        toolbar_layout = QHBoxLayout()
        
        self.add_sample_btn = QPushButton("Добавить образец")
        self.add_sample_btn.setIcon(QIcon("ui/icons/add_icon.png"))
        self.add_sample_btn.clicked.connect(self.add_sample)
        toolbar_layout.addWidget(self.add_sample_btn)
        
        self.generate_codes_btn = QPushButton("Генерировать коды")
        self.generate_codes_btn.setIcon(QIcon("ui/icons/generate_icon.png"))
        self.generate_codes_btn.clicked.connect(self.generate_sample_codes)
        toolbar_layout.addWidget(self.generate_codes_btn)
        
        self.import_photo_btn = QPushButton("Импорт фото")
        self.import_photo_btn.setIcon(QIcon("ui/icons/photo_icon.png"))
        self.import_photo_btn.clicked.connect(self.import_photo)
        toolbar_layout.addWidget(self.import_photo_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setIcon(QIcon("ui/icons/refresh_icon.png"))
        self.refresh_btn.clicked.connect(self.load_samples)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Таблица образцов
        self.samples_table = QTableWidget()
        self.samples_table.setColumnCount(9)
        self.samples_table.setHorizontalHeaderLabels([
            "Код", "Тип", "Размеры", "Место отбора", "Статус", "Подготовлен", "Испытан", "Фото", ""
        ])
        
        header = self.samples_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Код
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Тип
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Размеры
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Место отбора
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Статус
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Подготовлен
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Испытан
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Фото
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Действия
        
        self.samples_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.samples_table.cellDoubleClicked.connect(self.edit_sample)
        
        layout.addWidget(self.samples_table)
        
        # Кнопки диалога
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
    
    def load_data(self):
        """Загрузка данных о заявке и материале"""
        db = SessionLocal()
        try:
            self.sample_request = db.query(SampleRequest).filter(
                SampleRequest.id == self.sample_request_id
            ).first()
            
            if not self.sample_request:
                QMessageBox.critical(self, "Ошибка", "Заявка не найдена")
                self.reject()
                return
            
            self.material = db.query(MaterialEntry).filter(
                MaterialEntry.id == self.sample_request.material_entry_id
            ).first()
            
            # Обновляем информацию
            self.material_label.setText(f"{self.material.material_grade} - {self.material.melt_number}")
            self.request_info_label.setText(f"№{self.sample_request.id} от {self.sample_request.created_at.strftime('%d.%m.%Y')}")
            
            # Формируем список испытаний
            tests = []
            if self.sample_request.mechanical_test:
                tests.append("Механические")
            if self.sample_request.chemical_test:
                tests.append("Химический анализ")
            if self.sample_request.metallographic_test:
                tests.append("Металлография")
            
            self.tests_label.setText(", ".join(tests) if tests else "Не указано")
            
            # Загружаем образцы
            self.load_samples()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def load_samples(self):
        """Загрузка списка образцов"""
        db = SessionLocal()
        try:
            # Очищаем таблицу
            self.samples_table.setRowCount(0)
            
            # Получаем образцы
            samples = db.query(Sample).filter(
                Sample.sample_request_id == self.sample_request_id,
                Sample.is_deleted == False
            ).order_by(Sample.created_at).all()
            
            # Добавляем в таблицу
            for row, sample in enumerate(samples):
                self.samples_table.insertRow(row)
                
                # Код образца
                code_item = QTableWidgetItem(sample.sample_code)
                code_item.setData(Qt.UserRole, sample.id)
                self.samples_table.setItem(row, 0, code_item)
                
                # Тип образца
                self.samples_table.setItem(row, 1, QTableWidgetItem(sample.sample_type))
                
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
                
                self.samples_table.setItem(row, 2, QTableWidgetItem(" × ".join(sizes)))
                
                # Место отбора
                self.samples_table.setItem(row, 3, QTableWidgetItem(sample.location_description or "-"))
                
                # Статус
                status_item = QTableWidgetItem(self.get_status_display(sample.status))
                status_color = self.get_status_color(sample.status)
                status_item.setBackground(QBrush(status_color))
                self.samples_table.setItem(row, 4, status_item)
                
                # Даты
                prepared = sample.prepared_at.strftime("%d.%m.%Y") if sample.prepared_at else "-"
                self.samples_table.setItem(row, 5, QTableWidgetItem(prepared))
                
                tested = sample.tested_at.strftime("%d.%m.%Y") if sample.tested_at else "-"
                self.samples_table.setItem(row, 6, QTableWidgetItem(tested))
                
                # Фото
                photo_item = QTableWidgetItem("Есть" if sample.photo_path else "-")
                self.samples_table.setItem(row, 7, photo_item)
                
                # Кнопки действий
                action_layout = QHBoxLayout()
                action_widget = QPushButton("Действия")
                action_widget.clicked.connect(lambda checked=False, s_id=sample.id: self.show_sample_actions(s_id))
                self.samples_table.setCellWidget(row, 8, action_widget)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке образцов: {str(e)}")
        finally:
            db.close()
    
    def add_sample(self):
        """Добавление нового образца"""
        dialog = AddSampleDialog(self.sample_request_id, self.user, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_samples()
            self.samples_updated.emit()
    
    def edit_sample(self, row, column):
        """Редактирование образца"""
        sample_id = self.samples_table.item(row, 0).data(Qt.UserRole)
        dialog = EditSampleDialog(sample_id, self.user, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_samples()
            self.samples_updated.emit()
    
    def generate_sample_codes(self):
        """Автоматическая генерация кодов образцов"""
        count, ok = QInputDialog.getInt(self, "Генерация кодов", 
                                        "Количество образцов для генерации:", 
                                        1, 1, 50)
        if not ok:
            return
        
        db = SessionLocal()
        try:
            # Получаем базовый код из материала и заявки
            base_code = f"{self.material.material_grade}_{self.material.melt_number}_{self.sample_request.id}"
            
            # Получаем максимальный номер существующих образцов
            existing_samples = db.query(Sample).filter(
                Sample.sample_request_id == self.sample_request_id,
                Sample.is_deleted == False
            ).all()
            
            max_num = 0
            for sample in existing_samples:
                parts = sample.sample_code.split('_')
                if parts[-1].isdigit():
                    max_num = max(max_num, int(parts[-1]))
            
            # Создаем новые образцы
            for i in range(count):
                sample_num = max_num + i + 1
                sample_code = f"{base_code}_{sample_num}"
                
                # Проверяем уникальность кода
                existing = db.query(Sample).filter(Sample.sample_code == sample_code).first()
                if existing:
                    continue
                
                # Создаем образец
                sample = Sample(
                    sample_request_id=self.sample_request_id,
                    created_by_id=self.user.id,
                    sample_code=sample_code,
                    sample_type="Не указан",  # Пользователь должен будет указать тип позже
                    status="created"
                )
                db.add(sample)
            
            db.commit()
            
            QMessageBox.information(self, "Успех", f"Создано {count} новых образцов")
            self.load_samples()
            self.samples_updated.emit()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации кодов: {str(e)}")
        finally:
            db.close()
    
    def import_photo(self):
        """Импорт фото для выбранных образцов"""
        selected_rows = set(item.row() for item in self.samples_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите образцы для импорта фото")
            return
        
        # Выбор файла
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите фото", 
            "", 
            "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if not file_path:
            return
        
        db = SessionLocal()
        try:
            # Создаем папку для фото образцов
            photos_dir = f"docs_storage/sample_photos/{self.sample_request_id}"
            os.makedirs(photos_dir, exist_ok=True)
            
            # Обрабатываем каждый выбранный образец
            for row in selected_rows:
                sample_id = self.samples_table.item(row, 0).data(Qt.UserRole)
                sample = db.query(Sample).filter(Sample.id == sample_id).first()
                
                if sample:
                    # Копируем файл
                    ext = os.path.splitext(file_path)[1]
                    new_filename = f"{sample.sample_code}{ext}"
                    new_path = os.path.join(photos_dir, new_filename)
                    
                    shutil.copy2(file_path, new_path)
                    
                    # Обновляем путь в базе
                    sample.photo_path = new_path
            
            db.commit()
            
            QMessageBox.information(self, "Успех", "Фото успешно импортировано")
            self.load_samples()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте фото: {str(e)}")
        finally:
            db.close()
    
    def show_sample_actions(self, sample_id):
        """Показать меню действий для образца"""
        # TODO: Реализовать контекстное меню с действиями
        pass
    
    def get_status_display(self, status):
        """Получить отображаемое название статуса"""
        status_map = {
            "created": "Создан",
            "prepared": "Подготовлен",
            "testing": "Испытывается",
            "tested": "Испытан",
            "archived": "В архиве"
        }
        return status_map.get(status, status)
    
    def get_status_color(self, status):
        """Получить цвет для статуса"""
        color_map = {
            "created": QColor(200, 200, 200),      # Серый
            "prepared": QColor(255, 255, 160),     # Желтый
            "testing": QColor(160, 200, 255),      # Голубой
            "tested": QColor(160, 255, 160),       # Зеленый
            "archived": QColor(220, 220, 220)      # Светло-серый
        }
        return color_map.get(status, QColor(255, 255, 255))


class AddSampleDialog(QDialog):
    """Диалог добавления нового образца"""
    
    def __init__(self, sample_request_id, user, parent=None):
        super().__init__(parent)
        self.sample_request_id = sample_request_id
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Добавление образца")
        self.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Форма ввода данных
        form_layout = QFormLayout()
        
        # Код образца
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Уникальный код образца")
        form_layout.addRow("Код образца:", self.code_input)
        
        # Тип образца
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Растяжение",
            "Ударная вязкость",
            "Твердость",
            "Химический анализ",
            "Металлография",
            "Изгиб",
            "Сжатие",
            "Другое"
        ])
        self.type_combo.setEditable(True)
        form_layout.addRow("Тип образца:", self.type_combo)
        
        # Размеры
        size_group = QGroupBox("Размеры образца (мм)")
        size_layout = QFormLayout()
        
        self.length_input = QDoubleSpinBox()
        self.length_input.setRange(0, 10000)
        self.length_input.setDecimals(1)
        size_layout.addRow("Длина:", self.length_input)
        
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0, 10000)
        self.width_input.setDecimals(1)
        size_layout.addRow("Ширина:", self.width_input)
        
        self.thickness_input = QDoubleSpinBox()
        self.thickness_input.setRange(0, 10000)
        self.thickness_input.setDecimals(1)
        size_layout.addRow("Толщина:", self.thickness_input)
        
        self.diameter_input = QDoubleSpinBox()
        self.diameter_input.setRange(0, 10000)
        self.diameter_input.setDecimals(1)
        size_layout.addRow("Диаметр:", self.diameter_input)
        
        size_group.setLayout(size_layout)
        form_layout.addRow(size_group)
        
        # Место отбора
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Например: С торца прутка")
        form_layout.addRow("Место отбора:", self.location_input)
        
        # Примечания
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        form_layout.addRow("Примечания:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_sample)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def save_sample(self):
        """Сохранение образца"""
        # Проверка обязательных полей
        if not self.code_input.text():
            QMessageBox.warning(self, "Предупреждение", "Введите код образца")
            return
        
        db = SessionLocal()
        try:
            # Проверяем уникальность кода
            existing = db.query(Sample).filter(
                Sample.sample_code == self.code_input.text()
            ).first()
            
            if existing:
                QMessageBox.warning(self, "Предупреждение", "Образец с таким кодом уже существует")
                return
            
            # Создаем новый образец
            sample = Sample(
                sample_request_id=self.sample_request_id,
                created_by_id=self.user.id,
                sample_code=self.code_input.text(),
                sample_type=self.type_combo.currentText(),
                length=self.length_input.value() if self.length_input.value() > 0 else None,
                width=self.width_input.value() if self.width_input.value() > 0 else None,
                thickness=self.thickness_input.value() if self.thickness_input.value() > 0 else None,
                diameter=self.diameter_input.value() if self.diameter_input.value() > 0 else None,
                location_description=self.location_input.text() or None,
                notes=self.notes_input.toPlainText() or None,
                status="created"
            )
            
            db.add(sample)
            db.commit()
            
            QMessageBox.information(self, "Успех", "Образец успешно добавлен")
            self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
        finally:
            db.close()


class EditSampleDialog(AddSampleDialog):
    """Диалог редактирования образца"""
    
    def __init__(self, sample_id, user, parent=None):
        self.sample_id = sample_id
        super().__init__(None, user, parent)
        self.setWindowTitle("Редактирование образца")
        self.load_sample_data()
    
    def load_sample_data(self):
        """Загрузка данных образца"""
        db = SessionLocal()
        try:
            sample = db.query(Sample).filter(Sample.id == self.sample_id).first()
            if sample:
                self.sample_request_id = sample.sample_request_id
                
                # Заполняем поля
                self.code_input.setText(sample.sample_code)
                self.code_input.setEnabled(False)  # Код нельзя менять
                
                index = self.type_combo.findText(sample.sample_type)
                if index >= 0:
                    self.type_combo.setCurrentIndex(index)
                else:
                    self.type_combo.setEditText(sample.sample_type)
                
                if sample.length:
                    self.length_input.setValue(sample.length)
                if sample.width:
                    self.width_input.setValue(sample.width)
                if sample.thickness:
                    self.thickness_input.setValue(sample.thickness)
                if sample.diameter:
                    self.diameter_input.setValue(sample.diameter)
                
                self.location_input.setText(sample.location_description or "")
                self.notes_input.setPlainText(sample.notes or "")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.close()
    
    def save_sample(self):
        """Сохранение изменений"""
        db = SessionLocal()
        try:
            sample = db.query(Sample).filter(Sample.id == self.sample_id).first()
            if sample:
                # Обновляем данные
                sample.sample_type = self.type_combo.currentText()
                sample.length = self.length_input.value() if self.length_input.value() > 0 else None
                sample.width = self.width_input.value() if self.width_input.value() > 0 else None
                sample.thickness = self.thickness_input.value() if self.thickness_input.value() > 0 else None
                sample.diameter = self.diameter_input.value() if self.diameter_input.value() > 0 else None
                sample.location_description = self.location_input.text() or None
                sample.notes = self.notes_input.toPlainText() or None
                
                db.commit()
                
                QMessageBox.information(self, "Успех", "Образец успешно обновлен")
                self.accept()
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")
        finally:
            db.close() 