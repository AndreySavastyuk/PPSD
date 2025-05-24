from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QLabel, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from database.connection import SessionLocal
from models.models import ProductType
from ui.icons.icon_provider import IconProvider
from ui.reference.base_reference_dialog import BaseReferenceDialog

class ProductTypeReference(BaseReferenceDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочник: Виды проката")
        self.setWindowIcon(IconProvider.create_product_type_icon())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Вид проката", "Примечание"])
        
        # Растягиваем колонки по ширине таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setIcon(IconProvider.create_product_type_icon())
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить (флаг)")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_type)
        self.edit_btn.clicked.connect(self.edit_type)
        self.delete_btn.clicked.connect(self.flag_delete_type)

        # Добавляем кнопку "Закрыть"
        close_btn_layout = QHBoxLayout()
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        close_btn_layout.addStretch()
        close_btn_layout.addWidget(self.close_btn)
        layout.addLayout(close_btn_layout)

        self.load_data()
        
        # Устанавливаем минимальный размер окна
        self.resize(600, 400)

    def load_data(self):
        try:
            self.table.setRowCount(0)
            db = SessionLocal()
            types = db.query(ProductType).filter(ProductType.is_deleted == False).all()
            for row, type_item in enumerate(types):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(type_item.name))
                self.table.setItem(row, 1, QTableWidgetItem(type_item.note or ""))
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")

    def add_type(self):
        dialog = ProductTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                db = SessionLocal()
                name = dialog.name_input.text().strip()
                if db.query(ProductType).filter(ProductType.name == name, ProductType.is_deleted == False).first():
                    QMessageBox.warning(self, "Ошибка", "Такой вид проката уже существует!")
                    db.close()
                    return
                type_item = ProductType(
                    name=name,
                    note=dialog.note_input.text().strip()
                )
                db.add(type_item)
                db.commit()
                db.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def edit_type(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите вид проката для редактирования")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            type_item = db.query(ProductType).filter(ProductType.name == name, ProductType.is_deleted == False).first()
            if not type_item:
                QMessageBox.warning(self, "Ошибка", "Вид проката не найден")
                db.close()
                return
            dialog = ProductTypeDialog(self, type_item)
            if dialog.exec() == QDialog.Accepted:
                type_item.note = dialog.note_input.text().strip()
                db.commit()
                db.close()
                self.load_data()
            else:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании: {str(e)}")

    def flag_delete_type(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите вид проката для удаления")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            type_item = db.query(ProductType).filter(ProductType.name == name, ProductType.is_deleted == False).first()
            if not type_item:
                QMessageBox.warning(self, "Ошибка", "Вид проката не найден")
                db.close()
                return
            type_item.is_deleted = True
            db.commit()
            db.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

class ProductTypeDialog(BaseReferenceDialog):
    def __init__(self, parent=None, type_item=None):
        super().__init__(parent)
        self.setWindowTitle("Вид проката")
        self.setWindowIcon(IconProvider.create_product_type_icon())
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.note_input = QLineEdit()
        layout.addRow("Название:", self.name_input)
        layout.addRow("Примечание:", self.note_input)
        if type_item:
            self.name_input.setText(type_item.name)
            self.name_input.setReadOnly(True)
            self.note_input.setText(type_item.note or "")
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns) 