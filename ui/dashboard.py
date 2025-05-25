"""Дашборд для отображения общей информации и метрик системы ППСД"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QGridLayout, QFrame, QScrollArea, QPushButton,
                              QTabWidget, QSplitter, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPainter, QBrush, QColor, QPen
from database.connection import SessionLocal
from models.models import MaterialEntry, Sample, User, MaterialStatus, LabTest
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider
from ui.styles import apply_button_style

try:
    from ui.components.charts import MetricsPanel, BarChart, DonutChart
    from ui.components.advanced_search import QuickSearchBar
except ImportError:
    # Fallback if components are not available yet
    MetricsPanel = None
    BarChart = None
    DonutChart = None
    QuickSearchBar = None

class MetricCard(QFrame):
    """Карточка с метрикой - адаптивная версия"""
    
    clicked = Signal()
    
    def __init__(self, title: str, value: str, subtitle: str = "", icon=None, color_accent: str = None):
        super().__init__()
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.icon = icon
        self.color_accent = color_accent or theme_manager.get_color('primary')
        
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        """Инициализация интерфейса карточки"""
        # Убираем фиксированный размер, используем гибкие политики
        self.setMinimumSize(200, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Заголовок и иконка
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 11))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        if self.icon:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon.pixmap(20, 20))
            header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Значение
        self.value_label = QLabel(self.value)
        self.value_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(self.value_label)
        
        # Подзаголовок
        if self.subtitle:
            self.subtitle_label = QLabel(self.subtitle)
            self.subtitle_label.setFont(QFont("Segoe UI", 9))
            layout.addWidget(self.subtitle_label)
        
        layout.addStretch()
    
    def apply_styles(self):
        """Применение стилей к карточке через QSS"""
        # Устанавливаем свойства для QSS селекторов
        self.setProperty("card_type", "metric")
        self.setProperty("accent_color", self.color_accent)
    
    def mousePressEvent(self, event):
        """Обработка клика по карточке"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_value(self, new_value: str, new_subtitle: str = None):
        """Обновление значения в карточке"""
        self.value_label.setText(new_value)
        if new_subtitle and hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(new_subtitle)

class Dashboard(QWidget):
    """Главный виджет дашборда с современным дизайном"""
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.metric_cards = {}
        
        self.init_ui()
        self.setup_timer()
        self.load_metrics()
    
    def refresh_styles(self):
        """Обновить стили после смены темы"""
        try:
            # Обновляем стили карточек
            for card in self.metric_cards.values():
                if hasattr(card, 'apply_styles'):
                    card.apply_styles()
            
            # Обновляем весь виджет
            self.update()
        except Exception as e:
            print(f"Ошибка обновления стилей в dashboard: {e}")
    
    def init_ui(self):
        """Инициализация интерфейса дашборда"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Заголовок с адаптивным layout
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Дашборд системы контроля качества")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setIcon(IconProvider.create_refresh_icon())
        refresh_btn.clicked.connect(self.load_metrics)
        apply_button_style(refresh_btn, 'default')
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Создаем прокручиваемую область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setSpacing(20)
        
        # Основные метрики
        main_metrics_layout = self.create_main_metrics_section()
        scroll_layout.addLayout(main_metrics_layout)
        
        # Метрики по статусам
        status_metrics_layout = self.create_status_metrics_section()
        scroll_layout.addLayout(status_metrics_layout)
        
        # Активность
        activity_layout = self.create_activity_section()
        scroll_layout.addLayout(activity_layout)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
    
    def create_main_metrics_section(self) -> QVBoxLayout:
        """Создание секции основных метрик с адаптивным grid"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        section_label = QLabel("Общие показатели")
        section_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(section_label)
        
        # Адаптивная сетка карточек
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setRowStretch(0, 1)  # Позволяем строкам растягиваться
        
        # Карточка общего количества материалов
        self.metric_cards['total_materials'] = MetricCard(
            "Всего материалов", "0", "в системе",
            IconProvider.create_warehouse_icon(),
            theme_manager.get_color('primary')
        )
        grid_layout.addWidget(self.metric_cards['total_materials'], 0, 0)
        
        # Карточка активных образцов
        self.metric_cards['active_samples'] = MetricCard(
            "Активные образцы", "0", "в испытаниях",
            IconProvider.create_sample_icon(),
            theme_manager.get_color('secondary')
        )
        grid_layout.addWidget(self.metric_cards['active_samples'], 0, 1)
        
        # Карточка пользователей
        self.metric_cards['total_users'] = MetricCard(
            "Пользователи", "0", "зарегистрировано",
            IconProvider.create_user_icon(),
            theme_manager.get_color('info')
        )
        grid_layout.addWidget(self.metric_cards['total_users'], 0, 2)
        
        # Карточка за сегодня
        self.metric_cards['today_entries'] = MetricCard(
            "За сегодня", "0", "новых записей",
            IconProvider.create_material_entry_icon(),
            theme_manager.get_color('success')
        )
        grid_layout.addWidget(self.metric_cards['today_entries'], 0, 3)
        
        # Устанавливаем равные веса колонок для адаптивности
        for col in range(4):
            grid_layout.setColumnStretch(col, 1)
        
        layout.addLayout(grid_layout)
        return layout
    
    def create_status_metrics_section(self) -> QVBoxLayout:
        """Создание секции метрик по статусам"""
        layout = QVBoxLayout()
        
        section_label = QLabel("Распределение по статусам")
        section_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        section_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        layout.addWidget(section_label)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        
        # Карточки для разных статусов
        statuses = [
            ("RECEIVED", "На поступлении", theme_manager.get_color('warning')),
            ("QC_CHECK_PENDING", "Ожидает ОТК", theme_manager.get_color('info')),
            ("QC_CHECKED", "Одобрено ОТК", theme_manager.get_color('success')),
            ("TESTING", "В лаборатории", theme_manager.get_color('primary')),
            ("APPROVED", "Завершено", theme_manager.get_color('secondary'))
        ]
        
        for i, (status, title, color) in enumerate(statuses):
            self.metric_cards[f'status_{status}'] = MetricCard(
                title, "0", "материалов",
                IconProvider.create_qc_icon(),
                color
            )
            grid_layout.addWidget(self.metric_cards[f'status_{status}'], i // 3, i % 3)
        
        layout.addLayout(grid_layout)
        return layout
    
    def create_activity_section(self) -> QVBoxLayout:
        """Создание секции активности"""
        layout = QVBoxLayout()
        
        section_label = QLabel("Активность за сегодня")
        section_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        section_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        layout.addWidget(section_label)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        
        # Новые материалы сегодня
        self.metric_cards['today_materials'] = MetricCard(
            "Новые материалы", "0", "сегодня",
            IconProvider.create_material_entry_icon(),
            theme_manager.get_color('accent')
        )
        grid_layout.addWidget(self.metric_cards['today_materials'], 0, 0)
        
        # Изменения статусов
        self.metric_cards['status_changes'] = MetricCard(
            "Изменения статусов", "0", "сегодня",
            IconProvider.create_status_change_icon(),
            theme_manager.get_color('warning')
        )
        grid_layout.addWidget(self.metric_cards['status_changes'], 0, 1)
        
        # Созданные образцы
        self.metric_cards['today_samples'] = MetricCard(
            "Новые образцы", "0", "сегодня",
            IconProvider.create_sample_icon(),
            theme_manager.get_color('info')
        )
        grid_layout.addWidget(self.metric_cards['today_samples'], 0, 2)
        
        layout.addLayout(grid_layout)
        return layout
    
    def setup_timer(self):
        """Настройка таймера для автообновления"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_metrics)
        self.update_timer.start(30000)  # Обновление каждые 30 секунд
    
    def load_metrics(self):
        """Загрузка метрик из базы данных"""
        try:
            with SessionLocal() as session:
                # Общие метрики
                total_materials = session.query(MaterialEntry).count()
                self.metric_cards['total_materials'].update_value(str(total_materials))
                
                active_samples = session.query(Sample).filter(
                    Sample.status.in_(['created', 'prepared', 'testing'])
                ).count()
                self.metric_cards['active_samples'].update_value(str(active_samples))
                
                # Пользователи (общее количество)
                total_users = session.query(User).count()
                self.metric_cards['total_users'].update_value(str(total_users))
                
                # Записи за сегодня
                today = datetime.now().date()
                today_start = datetime.combine(today, datetime.min.time())
                
                today_entries = session.query(MaterialEntry).filter(
                    MaterialEntry.created_at >= today_start
                ).count()
                self.metric_cards['today_entries'].update_value(str(today_entries))
                
                # Метрики по статусам
                for status in ['RECEIVED', 'QC_CHECK_PENDING', 'QC_CHECKED', 'TESTING', 'APPROVED']:
                    count = session.query(MaterialEntry).filter(MaterialEntry.status == status).count()
                    if f'status_{status}' in self.metric_cards:
                        self.metric_cards[f'status_{status}'].update_value(str(count))
                
                # Активность за сегодня
                today_materials = session.query(MaterialEntry).filter(
                    MaterialEntry.created_at >= today_start
                ).count()
                self.metric_cards['today_materials'].update_value(str(today_materials))
                
                today_samples = session.query(Sample).filter(
                    Sample.created_at >= today_start
                ).count()
                self.metric_cards['today_samples'].update_value(str(today_samples))
                
                # Примерное количество изменений статусов (можно улучшить с audit log)
                self.metric_cards['status_changes'].update_value("N/A", "недоступно")
                
        except Exception as e:
            print(f"Ошибка загрузки метрик: {e}")
    
    def apply_theme(self):
        """Применение текущей темы"""
        self.setStyleSheet(theme_manager.generate_stylesheet())
        for card in self.metric_cards.values():
            card.apply_styles() 