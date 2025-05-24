"""
Система оповещений в реальном времени для ППСД
Отслеживает изменения в базе данных и показывает уведомления
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
from PySide6.QtCore import QTimer, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPixmap
from datetime import datetime, timedelta
from database.connection import SessionLocal
from models.models import MaterialEntry, Sample, LabTest, QCCheck, MaterialStatus
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider
from ui.notifications import notification_manager
from sqlalchemy import desc

class DatabaseWatcher(QThread):
    """Наблюдатель за изменениями в базе данных"""
    
    new_material = Signal(dict)
    status_changed = Signal(dict)
    test_completed = Signal(dict)
    urgent_notification = Signal(str, str)  # title, message
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_check = datetime.now()
        self.known_materials = set()
        self.known_tests = set()
    
    def run(self):
        """Основной цикл наблюдения"""
        while self.running:
            try:
                self.check_database_changes()
                self.msleep(5000)  # Проверяем каждые 5 секунд
            except Exception as e:
                print(f"Ошибка в DatabaseWatcher: {e}")
                self.msleep(10000)  # Ждем 10 секунд при ошибке
    
    def check_database_changes(self):
        """Проверка изменений в базе данных"""
        db = SessionLocal()
        try:
            current_time = datetime.now()
            
            # Проверяем новые материалы
            new_materials = db.query(MaterialEntry).filter(
                MaterialEntry.created_at >= self.last_check,
                MaterialEntry.is_deleted == False
            ).all()
            
            for material in new_materials:
                if material.id not in self.known_materials:
                    self.known_materials.add(material.id)
                    self.new_material.emit({
                        'id': material.id,
                        'grade': material.material_grade,
                        'batch': material.batch_number,
                        'supplier': material.supplier_id
                    })
            
            # Проверяем изменения статусов
            materials_with_status_changes = db.query(MaterialEntry).filter(
                MaterialEntry.updated_at >= self.last_check,
                MaterialEntry.is_deleted == False
            ).all()
            
            for material in materials_with_status_changes:
                if material.id in self.known_materials:
                    self.status_changed.emit({
                        'id': material.id,
                        'grade': material.material_grade,
                        'status': material.status,
                        'batch': material.batch_number
                    })
            
            # Проверяем завершенные испытания
            completed_tests = db.query(LabTest).filter(
                LabTest.completed_at >= self.last_check,
                LabTest.completed_at != None
            ).all()
            
            for test in completed_tests:
                if test.id not in self.known_tests:
                    self.known_tests.add(test.id)
                    self.test_completed.emit({
                        'id': test.id,
                        'sample_id': test.sample_id,
                        'passed': test.is_passed,
                        'test_type': test.test_type_id
                    })
            
            # Проверяем критические ситуации
            self.check_urgent_situations(db)
            
            self.last_check = current_time
            
        finally:
            db.close()
    
    def check_urgent_situations(self, db):
        """Проверка критических ситуаций"""
        # Материалы, ожидающие проверки более 3 дней
        three_days_ago = datetime.now() - timedelta(days=3)
        overdue_materials = db.query(MaterialEntry).filter(
            MaterialEntry.status == MaterialStatus.QC_CHECK_PENDING.value,
            MaterialEntry.created_at <= three_days_ago,
            MaterialEntry.is_deleted == False
        ).count()
        
        if overdue_materials > 0:
            self.urgent_notification.emit(
                "Просроченные проверки",
                f"Материалов ожидает проверки ОТК более 3 дней: {overdue_materials}"
            )
        
        # Испытания, превысившие срок
        overdue_tests = db.query(LabTest).filter(
            LabTest.started_at <= three_days_ago,
            LabTest.completed_at == None
        ).count()
        
        if overdue_tests > 0:
            self.urgent_notification.emit(
                "Просроченные испытания", 
                f"Испытаний превысили стандартный срок: {overdue_tests}"
            )
    
    def stop(self):
        """Остановить наблюдение"""
        self.running = False

class NotificationWidget(QFrame):
    """Виджет уведомления в панели"""
    
    def __init__(self, title, message, notification_type="info"):
        super().__init__()
        self.notification_type = notification_type
        self.init_ui(title, message)
    
    def init_ui(self, title, message):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Иконка
        icon_label = QLabel()
        if self.notification_type == "success":
            icon = IconProvider.create_success_icon()
        elif self.notification_type == "warning":
            icon = IconProvider.create_warning_icon()
        elif self.notification_type == "error":
            icon = IconProvider.create_error_icon()
        else:
            icon = IconProvider.create_info_icon()
        
        icon_label.setPixmap(icon.pixmap(24, 24))
        layout.addWidget(icon_label)
        
        # Текст
        text_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        text_layout.addWidget(title_label)
        
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setWordWrap(True)
        text_layout.addWidget(message_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Кнопка закрытия
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close_notification)
        layout.addWidget(close_btn)
        
        self.apply_styles()
    
    def apply_styles(self):
        """Применение стилей"""
        colors = theme_manager.get_current_theme()['colors']
        
        if self.notification_type == "success":
            bg_color = colors['success']
        elif self.notification_type == "warning":
            bg_color = colors['warning']
        elif self.notification_type == "error":
            bg_color = colors['error']
        else:
            bg_color = colors['info']
        
        self.setStyleSheet(f"""
        NotificationWidget {{
            background-color: {bg_color}20;
            border-left: 4px solid {bg_color};
            border-radius: 6px;
            margin: 2px 0;
        }}
        QLabel {{
            color: {colors['text_primary']};
        }}
        QPushButton {{
            background-color: transparent;
            border: none;
            color: {colors['text_secondary']};
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {colors['hover']};
        }}
        """)
    
    def close_notification(self):
        """Закрыть уведомление"""
        self.setParent(None)
        self.deleteLater()

class RealTimeNotificationPanel(QWidget):
    """Панель уведомлений в реальном времени"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.watcher = DatabaseWatcher()
        self.init_ui()
        self.setup_connections()
        self.start_watching()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Уведомления")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Кнопка очистки
        clear_btn = QPushButton("Очистить")
        clear_btn.setStyleSheet(theme_manager.get_button_style('neutral'))
        clear_btn.clicked.connect(self.clear_notifications)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Область прокрутки для уведомлений
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(300)
        
        self.notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_widget)
        self.notifications_layout.addStretch()
        
        self.scroll_area.setWidget(self.notifications_widget)
        layout.addWidget(self.scroll_area)
        
        self.apply_styles()
    
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.watcher.new_material.connect(self.on_new_material)
        self.watcher.status_changed.connect(self.on_status_changed)
        self.watcher.test_completed.connect(self.on_test_completed)
        self.watcher.urgent_notification.connect(self.on_urgent_notification)
    
    def start_watching(self):
        """Запуск наблюдения"""
        self.watcher.start()
    
    def stop_watching(self):
        """Остановка наблюдения"""
        self.watcher.stop()
        self.watcher.wait()
    
    def add_notification(self, title, message, notification_type="info"):
        """Добавить уведомление"""
        widget = NotificationWidget(title, message, notification_type)
        
        # Вставляем в начало списка (последние уведомления сверху)
        self.notifications_layout.insertWidget(0, widget)
        
        # Ограничиваем количество уведомлений
        if self.notifications_layout.count() > 10:
            old_widget = self.notifications_layout.itemAt(9).widget()
            if old_widget:
                old_widget.setParent(None)
                old_widget.deleteLater()
        
        # Прокручиваем вверх
        self.scroll_area.verticalScrollBar().setValue(0)
    
    def on_new_material(self, data):
        """Обработка нового материала"""
        title = "Новый материал"
        message = f"Поступил материал {data['grade']}, партия {data['batch']}"
        self.add_notification(title, message, "success")
    
    def on_status_changed(self, data):
        """Обработка изменения статуса"""
        title = "Изменение статуса"
        message = f"Материал {data['grade']} (партия {data['batch']}) изменил статус"
        self.add_notification(title, message, "info")
    
    def on_test_completed(self, data):
        """Обработка завершения испытания"""
        title = "Испытание завершено"
        result = "пройдено" if data['passed'] else "не пройдено"
        message = f"Испытание образца #{data['sample_id']} {result}"
        notification_type = "success" if data['passed'] else "warning"
        self.add_notification(title, message, notification_type)
    
    def on_urgent_notification(self, title, message):
        """Обработка критического уведомления"""
        self.add_notification(title, message, "error")
        # Также показываем системное уведомление
        notification_manager.show_error(f"{title}: {message}")
    
    def clear_notifications(self):
        """Очистить все уведомления"""
        for i in reversed(range(self.notifications_layout.count())):
            item = self.notifications_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
    
    def apply_styles(self):
        """Применение стилей"""
        colors = theme_manager.get_current_theme()['colors']
        
        self.setStyleSheet(f"""
        RealTimeNotificationPanel {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
        }}
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        """)
    
    def closeEvent(self, event):
        """Обработка закрытия виджета"""
        self.stop_watching()
        super().closeEvent(event) 