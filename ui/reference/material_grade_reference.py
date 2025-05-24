from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QLabel, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from database.connection import SessionLocal
from models.models import MaterialGrade
from ui.icons.icon_provider import IconProvider
from ui.reference.base_reference_dialog import BaseReferenceDialog

class MaterialGradeReference(BaseReferenceDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочник: Марки материалов")
        self.setWindowIcon(IconProvider.create_material_grade_icon())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Марка", "Плотность, кг/м3", "Примечание"])
        
        # Растягиваем колонки по ширине таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setIcon(IconProvider.create_material_grade_icon())
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить (флаг)")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_grade)
        self.edit_btn.clicked.connect(self.edit_grade)
        self.delete_btn.clicked.connect(self.flag_delete_grade)

        # Добавляем кнопку "Закрыть"
        close_btn_layout = QHBoxLayout()
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        close_btn_layout.addStretch()
        close_btn_layout.addWidget(self.close_btn)
        layout.addLayout(close_btn_layout)

        self.load_data()
        
        # Устанавливаем минимальный размер окна
        self.resize(800, 600)

    def load_data(self):
        try:
            self.table.setRowCount(0)
            db = SessionLocal()
            grades = db.query(MaterialGrade).filter(MaterialGrade.is_deleted == False).all()
            for row, grade in enumerate(grades):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(grade.name))
                self.table.setItem(row, 1, QTableWidgetItem(str(grade.density) if grade.density else ""))
                self.table.setItem(row, 2, QTableWidgetItem(grade.note or ""))
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")

    def add_grade(self):
        dialog = MaterialGradeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                db = SessionLocal()
                name = dialog.name_input.text().strip()
                if db.query(MaterialGrade).filter(MaterialGrade.name == name, MaterialGrade.is_deleted == False).first():
                    QMessageBox.warning(self, "Ошибка", "Такая марка уже существует!")
                    db.close()
                    return
                grade = MaterialGrade(
                    name=name,
                    density=float(dialog.density_input.text()) if dialog.density_input.text() else None,
                    note=dialog.note_input.text().strip()
                )
                db.add(grade)
                db.commit()
                db.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def edit_grade(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите марку для редактирования")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            grade = db.query(MaterialGrade).filter(MaterialGrade.name == name, MaterialGrade.is_deleted == False).first()
            if not grade:
                QMessageBox.warning(self, "Ошибка", "Марка не найдена")
                db.close()
                return
            dialog = MaterialGradeDialog(self, grade)
            if dialog.exec() == QDialog.Accepted:
                grade.density = float(dialog.density_input.text()) if dialog.density_input.text() else None
                grade.note = dialog.note_input.text().strip()
                db.commit()
                db.close()
                self.load_data()
            else:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании: {str(e)}")

    def flag_delete_grade(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите марку для удаления")
            return
        name = self.table.item(row, 0).text()
        try:
            db = SessionLocal()
            grade = db.query(MaterialGrade).filter(MaterialGrade.name == name, MaterialGrade.is_deleted == False).first()
            if not grade:
                QMessageBox.warning(self, "Ошибка", "Марка не найдена")
                db.close()
                return
            grade.is_deleted = True
            db.commit()
            db.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

class MaterialGradeDialog(BaseReferenceDialog):
    def __init__(self, parent=None, grade=None):
        super().__init__(parent)
        self.setWindowTitle("Марка материала")
        self.setWindowIcon(IconProvider.create_material_grade_icon())
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.density_input = QLineEdit()
        self.note_input = QLineEdit()
        layout.addRow("Марка:", self.name_input)
        layout.addRow("Плотность, кг/м3:", self.density_input)
        layout.addRow("Примечание:", self.note_input)
        if grade:
            self.name_input.setText(grade.name)
            self.name_input.setReadOnly(True)
            self.density_input.setText(str(grade.density) if grade.density else "")
            self.note_input.setText(grade.note or "")
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns) 