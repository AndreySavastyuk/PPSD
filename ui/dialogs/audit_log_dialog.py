from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                             QDateEdit, QComboBox, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from database.connection import SessionLocal
from models.models import User
from sqlalchemy import text
from datetime import datetime, timedelta

class AuditLogDialog(QDialog):
    """Диалог для просмотра журнала действий пользователей"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Журнал действий пользователей")
        self.setMinimumSize(900, 600)
        self.init_ui()
        self.load_audit_log()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Журнал действий пользователей (Audit Trail)")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Панель фильтров
        filter_layout = QHBoxLayout()
        
        # Фильтр по дате
        filter_layout.addWidget(QLabel("С:"))
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("По:"))
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.date_to)
        
        # Фильтр по пользователю
        filter_layout.addWidget(QLabel("Пользователь:"))
        self.user_filter = QComboBox()
        self.user_filter.addItem("Все пользователи", None)
        self.load_users()
        filter_layout.addWidget(self.user_filter)
        
        # Поиск по действию
        filter_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по действию или деталям...")
        filter_layout.addWidget(self.search_input)
        
        # Кнопка фильтрации
        self.filter_btn = QPushButton("Фильтровать")
        self.filter_btn.clicked.connect(self.load_audit_log)
        filter_layout.addWidget(self.filter_btn)
        
        layout.addLayout(filter_layout)
        
        # Таблица журнала
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels([
            "Дата/Время", "Пользователь", "Действие", "Детали", "ID"
        ])
        
        # Настройка размеров колонок
        header = self.audit_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Пользователь
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Действие
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Детали
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # ID
        
        layout.addWidget(self.audit_table)
        
        # Статистика
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.stats_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.load_audit_log)
        button_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Экспорт в Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def load_users(self):
        """Загрузка списка пользователей для фильтра"""
        db = SessionLocal()
        try:
            users = db.query(User).all()
            for user in users:
                self.user_filter.addItem(f"{user.full_name} ({user.username})", user.id)
        finally:
            db.close()
    
    def load_audit_log(self):
        """Загрузка журнала аудита"""
        db = SessionLocal()
        try:
            # Создаем таблицу audit_log если её нет
            from database.init_db import create_audit_log_table
            from database.connection import engine
            create_audit_log_table(engine)
            
            # Формируем запрос с фильтрами
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            date_to = datetime.combine(date_to, datetime.max.time())  # До конца дня
            
            query = """
                SELECT a.timestamp, u.full_name, u.username, a.action, a.details, a.id
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE a.timestamp BETWEEN :date_from AND :date_to
            """
            
            params = {
                'date_from': date_from,
                'date_to': date_to
            }
            
            # Фильтр по пользователю
            selected_user_id = self.user_filter.currentData()
            if selected_user_id:
                query += " AND a.user_id = :user_id"
                params['user_id'] = selected_user_id
            
            # Фильтр по тексту
            search_text = self.search_input.text().strip()
            if search_text:
                query += " AND (a.action LIKE :search OR a.details LIKE :search)"
                params['search'] = f"%{search_text}%"
            
            query += " ORDER BY a.timestamp DESC LIMIT 1000"
            
            result = db.execute(text(query), params).fetchall()
            
            # Заполняем таблицу
            self.audit_table.setRowCount(len(result))
            
            for row_idx, record in enumerate(result):
                timestamp, full_name, username, action, details, log_id = record
                
                # Форматируем время
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                # Заполняем ячейки
                self.audit_table.setItem(row_idx, 0, QTableWidgetItem(
                    timestamp.strftime('%d.%m.%Y %H:%M:%S') if timestamp else ""
                ))
                
                user_display = full_name or username or "Неизвестен"
                self.audit_table.setItem(row_idx, 1, QTableWidgetItem(user_display))
                
                self.audit_table.setItem(row_idx, 2, QTableWidgetItem(action or ""))
                self.audit_table.setItem(row_idx, 3, QTableWidgetItem(details or ""))
                self.audit_table.setItem(row_idx, 4, QTableWidgetItem(str(log_id)))
            
            # Обновляем статистику
            self.stats_label.setText(f"Показано записей: {len(result)} (максимум 1000)")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить журнал аудита:\n{str(e)}")
        finally:
            db.close()
    
    def export_to_excel(self):
        """Экспорт журнала в Excel"""
        from PySide6.QtWidgets import QFileDialog
        import openpyxl
        from openpyxl.styles import Font
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить журнал аудита", 
            f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel файлы (*.xlsx)"
        )
        
        if filename:
            try:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Журнал аудита"
                
                # Заголовки
                headers = ["Дата/Время", "Пользователь", "Действие", "Детали", "ID"]
                ws.append(headers)
                
                # Стилизация заголовков
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                
                # Данные
                for row in range(self.audit_table.rowCount()):
                    row_data = []
                    for col in range(self.audit_table.columnCount()):
                        item = self.audit_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    ws.append(row_data)
                
                wb.save(filename)
                QMessageBox.information(self, "Экспорт завершен", 
                                      f"Журнал аудита сохранен в файл:\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать данные:\n{str(e)}") 