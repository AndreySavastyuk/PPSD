from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QLabel, QMessageBox, QHeaderView, QCheckBox)
from PySide6.QtCore import Qt
from database.connection import SessionLocal
from models.models import Supplier
from ui.icons.icon_provider import IconProvider
from ui.reference.base_reference_dialog import BaseReferenceDialog

class SupplierReference(BaseReferenceDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочник: Поставщики")
        self.setWindowIcon(IconProvider.create_supplier_icon())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Поставщик", "Прямой", "Адрес", "Контакты"])
        
        # Растягиваем колонки по ширине таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setIcon(IconProvider.create_supplier_icon())
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить (флаг)")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_supplier)
        self.edit_btn.clicked.connect(self.edit_supplier)
        self.delete_btn.clicked.connect(self.flag_delete_supplier)

        # Добавляем кнопку "Закрыть"
        close_btn_layout = QHBoxLayout()
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        close_btn_layout.addStretch()
        close_btn_layout.addWidget(self.close_btn)
        layout.addLayout(close_btn_layout)

        self.load_data()
        
        # Устанавливаем минимальный размер окна
        self.resize(800, 500)

    def load_data(self):
        try:
            self.table.setRowCount(0)
            db = SessionLocal()
            suppliers = db.query(Supplier).filter(Supplier.is_deleted == False).all()
            for row, supplier in enumerate(suppliers):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(supplier.name))
                is_direct_item = QTableWidgetItem()
                is_direct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                is_direct_item.setText("Да" if supplier.is_direct else "Нет")
                self.table.setItem(row, 1, is_direct_item)
                self.table.setItem(row, 2, QTableWidgetItem(supplier.address or ""))
                self.table.setItem(row, 3, QTableWidgetItem(supplier.contact_info or ""))
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")

    def add_supplier(self):
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                db = SessionLocal()
                name = dialog.name_input.text().strip()
                if db.query(Supplier).filter(Supplier.name == name, Supplier.is_deleted == False).first():
                    QMessageBox.warning(self, "Ошибка", "Такой поставщик уже существует!")
                    db.close()
                    return
                supplier = Supplier(
                    name=name,
                    is_direct=dialog.is_direct_checkbox.isChecked(),
                    address=dialog.address_input.text().strip(),
                    contact_info=dialog.contact_input.text().strip()
                )
                db.add(supplier)
                db.commit()
                db.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def edit_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поставщика для редактирования")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            supplier = db.query(Supplier).filter(Supplier.name == name, Supplier.is_deleted == False).first()
            if not supplier:
                QMessageBox.warning(self, "Ошибка", "Поставщик не найден")
                db.close()
                return
            dialog = SupplierDialog(self, supplier)
            if dialog.exec() == QDialog.Accepted:
                supplier.is_direct = dialog.is_direct_checkbox.isChecked()
                supplier.address = dialog.address_input.text().strip()
                supplier.contact_info = dialog.contact_input.text().strip()
                db.commit()
                db.close()
                self.load_data()
            else:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании: {str(e)}")

    def flag_delete_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поставщика для удаления")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            supplier = db.query(Supplier).filter(Supplier.name == name, Supplier.is_deleted == False).first()
            if not supplier:
                QMessageBox.warning(self, "Ошибка", "Поставщик не найден")
                db.close()
                return
            supplier.is_deleted = True
            db.commit()
            db.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

class SupplierDialog(BaseReferenceDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.setWindowTitle("Поставщик")
        self.setWindowIcon(IconProvider.create_supplier_icon())
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.is_direct_checkbox = QCheckBox("Прямой поставщик")
        self.address_input = QLineEdit()
        self.contact_input = QLineEdit()
        layout.addRow("Название:", self.name_input)
        layout.addRow(self.is_direct_checkbox)
        layout.addRow("Адрес:", self.address_input)
        layout.addRow("Контакты:", self.contact_input)
        if supplier:
            self.name_input.setText(supplier.name)
            self.name_input.setReadOnly(True)
            self.is_direct_checkbox.setChecked(supplier.is_direct)
            self.address_input.setText(supplier.address or "")
            self.contact_input.setText(supplier.contact_info or "")
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns) 