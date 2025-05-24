"""
Компоненты для визуализации данных в системе ППСД
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QComboBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QLinearGradient
import math
from datetime import datetime, timedelta
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider

class AnimatedProgressBar(QWidget):
    """Анимированная полоса прогресса"""
    
    def __init__(self, value=0, maximum=100, color=None, height=8):
        super().__init__()
        self.value = value
        self.maximum = maximum
        self.animated_value = 0
        self.color = color or theme_manager.get_color('primary')
        self.bar_height = height
        
        self.setFixedHeight(height + 4)
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def set_value(self, value):
        """Установка значения с анимацией"""
        self.value = min(max(0, value), self.maximum)
        self.animation.setStartValue(self.animated_value)
        self.animation.setEndValue(self.value)
        self.animation.start()
    
    def get_animated_value(self):
        return self._animated_value
    
    def set_animated_value(self, value):
        self._animated_value = value
        self.update()
    
    animated_value = property(get_animated_value, set_animated_value)
    
    def paintEvent(self, event):
        """Отрисовка полосы прогресса"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        bar_rect = rect.adjusted(2, 2, -2, -2)
        
        # Фон
        painter.setBrush(QBrush(QColor(theme_manager.get_color('border'))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, self.bar_height // 2, self.bar_height // 2)
        
        # Прогресс
        if self.animated_value > 0:
            progress_width = int((self.animated_value / self.maximum) * bar_rect.width())
            progress_rect = bar_rect.adjusted(0, 0, -bar_rect.width() + progress_width, 0)
            
            # Градиент
            gradient = QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
            base_color = QColor(self.color)
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color)
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(progress_rect, self.bar_height // 2, self.bar_height // 2)

class CircularProgressWidget(QWidget):
    """Круговой индикатор прогресса"""
    
    def __init__(self, value=0, maximum=100, size=120, thickness=12):
        super().__init__()
        self.value = value
        self.maximum = maximum
        self.animated_value = 0
        self.size = size
        self.thickness = thickness
        
        self.setFixedSize(size, size)
        
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(1500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def set_value(self, value):
        """Установка значения с анимацией"""
        self.value = min(max(0, value), self.maximum)
        self.animation.setStartValue(self.animated_value)
        self.animation.setEndValue(self.value)
        self.animation.start()
    
    def get_animated_value(self):
        return self._animated_value
    
    def set_animated_value(self, value):
        self._animated_value = value
        self.update()
    
    animated_value = property(get_animated_value, set_animated_value)
    
    def paintEvent(self, event):
        """Отрисовка кругового прогресса"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(self.thickness // 2, self.thickness // 2, 
                                  -self.thickness // 2, -self.thickness // 2)
        
        # Фон
        pen = QPen(QColor(theme_manager.get_color('border')))
        pen.setWidth(self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # Прогресс
        if self.animated_value > 0:
            progress_angle = int((self.animated_value / self.maximum) * 360 * 16)
            
            # Определяем цвет в зависимости от процента
            percentage = self.animated_value / self.maximum
            if percentage < 0.5:
                color = theme_manager.get_color('error')
            elif percentage < 0.8:
                color = theme_manager.get_color('warning')
            else:
                color = theme_manager.get_color('success')
            
            pen = QPen(QColor(color))
            pen.setWidth(self.thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, -progress_angle)
        
        # Текст в центре
        painter.setPen(QPen(QColor(theme_manager.get_color('text_primary'))))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        percentage_text = f"{int((self.animated_value / self.maximum) * 100)}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, percentage_text)

class BarChart(QWidget):
    """Простая столбчатая диаграмма"""
    
    def __init__(self, data=None, labels=None, colors=None):
        super().__init__()
        self.data = data or []
        self.labels = labels or []
        self.colors = colors or []
        self.animated_data = [0] * len(self.data)
        
        self.setMinimumHeight(200)
        
        # Анимация для каждого столбца
        self.animations = []
        for i in range(len(self.data)):
            animation = QPropertyAnimation(self, f"animated_value_{i}".encode())
            animation.setDuration(1000 + i * 100)  # Каскадная анимация
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animations.append(animation)
    
    def set_data(self, data, labels=None, colors=None):
        """Установка данных с анимацией"""
        self.data = data
        if labels:
            self.labels = labels
        if colors:
            self.colors = colors
        
        # Обновляем анимации
        self.animated_data = [0] * len(data)
        self.animations.clear()
        
        for i in range(len(data)):
            animation = QPropertyAnimation(self, f"animated_value_{i}".encode())
            animation.setDuration(1000 + i * 100)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.setStartValue(0)
            animation.setEndValue(data[i])
            
            # Создаем функцию обновления для каждого индекса
            def make_updater(index):
                def update_value(value):
                    self.animated_data[index] = value
                    self.update()
                return update_value
            
            animation.valueChanged.connect(make_updater(i))
            animation.start()
            self.animations.append(animation)
    
    def paintEvent(self, event):
        """Отрисовка столбчатой диаграммы"""
        if not self.animated_data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(40, 20, -20, -40)  # Отступы для подписей
        
        max_value = max(self.data) if self.data else 1
        bar_width = rect.width() // len(self.animated_data) - 10
        
        for i, value in enumerate(self.animated_data):
            # Позиция столбца
            x = rect.left() + i * (bar_width + 10)
            bar_height = int((value / max_value) * rect.height()) if max_value > 0 else 0
            y = rect.bottom() - bar_height
            
            # Цвет столбца
            if i < len(self.colors):
                color = QColor(self.colors[i])
            else:
                # Используем цвета темы по умолчанию
                theme_colors = [
                    theme_manager.get_color('primary'),
                    theme_manager.get_color('secondary'),
                    theme_manager.get_color('success'),
                    theme_manager.get_color('warning'),
                    theme_manager.get_color('error')
                ]
                color = QColor(theme_colors[i % len(theme_colors)])
            
            # Градиент для столбца
            gradient = QLinearGradient(x, y, x, y + bar_height)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 4, 4)
            
            # Значение над столбцом
            painter.setPen(QPen(QColor(theme_manager.get_color('text_primary'))))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(x, y - 5, bar_width, 20, Qt.AlignmentFlag.AlignCenter, str(int(value)))
            
            # Подпись под столбцом
            if i < len(self.labels):
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(x, rect.bottom() + 5, bar_width, 20, 
                               Qt.AlignmentFlag.AlignCenter, self.labels[i])

class DonutChart(QWidget):
    """Кольцевая диаграмма"""
    
    def __init__(self, data=None, labels=None, colors=None, size=200):
        super().__init__()
        self.data = data or []
        self.labels = labels or []
        self.colors = colors or []
        self.animated_angles = [0] * len(self.data)
        
        self.setFixedSize(size, size)
        
        # Анимация для каждого сегмента
        self.animations = []
        self.setup_animations()
    
    def setup_animations(self):
        """Настройка анимаций для сегментов"""
        total = sum(self.data) if self.data else 1
        start_angle = 0
        
        for i, value in enumerate(self.data):
            target_angle = int((value / total) * 360) if total > 0 else 0
            
            animation = QPropertyAnimation(self, f"animated_angle_{i}".encode())
            animation.setDuration(1500 + i * 200)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.setStartValue(0)
            animation.setEndValue(target_angle)
            
            def make_updater(index):
                def update_angle(angle):
                    self.animated_angles[index] = angle
                    self.update()
                return update_angle
            
            animation.valueChanged.connect(make_updater(i))
            self.animations.append(animation)
    
    def set_data(self, data, labels=None, colors=None):
        """Установка данных с анимацией"""
        self.data = data
        if labels:
            self.labels = labels
        if colors:
            self.colors = colors
        
        self.animated_angles = [0] * len(data)
        
        # Останавливаем старые анимации
        for animation in self.animations:
            animation.stop()
        
        self.animations.clear()
        self.setup_animations()
        
        # Запускаем анимации
        for animation in self.animations:
            animation.start()
    
    def paintEvent(self, event):
        """Отрисовка кольцевой диаграммы"""
        if not self.animated_angles:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(20, 20, -20, -20)
        inner_rect = rect.adjusted(40, 40, -40, -40)
        
        start_angle = 0
        
        for i, angle in enumerate(self.animated_angles):
            if angle <= 0:
                continue
            
            # Цвет сегмента
            if i < len(self.colors):
                color = QColor(self.colors[i])
            else:
                theme_colors = [
                    theme_manager.get_color('primary'),
                    theme_manager.get_color('secondary'),
                    theme_manager.get_color('success'),
                    theme_manager.get_color('warning'),
                    theme_manager.get_color('error')
                ]
                color = QColor(theme_colors[i % len(theme_colors)])
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(theme_manager.get_color('background')), 2))
            
            # Рисуем сегмент
            painter.drawPie(rect, start_angle * 16, angle * 16)
            
            # Вырезаем внутренний круг
            painter.setBrush(QBrush(QColor(theme_manager.get_color('background'))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(inner_rect)
            
            start_angle += angle

class MetricsPanel(QFrame):
    """Панель с метриками и диаграммами"""
    
    def __init__(self, title="Метрики"):
        super().__init__()
        self.title = title
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton()
        refresh_btn.setIcon(IconProvider.create_refresh_icon())
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("Обновить данные")
        refresh_btn.setStyleSheet(theme_manager.get_button_style('neutral'))
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Контейнер для диаграмм
        self.charts_container = QGridLayout()
        layout.addLayout(self.charts_container)
        
        layout.addStretch()
    
    def add_progress_metric(self, title, value, maximum=100, row=0, col=0):
        """Добавление метрики с прогресс-баром"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        container_layout.addWidget(title_label)
        
        # Значение
        value_label = QLabel(f"{value}/{maximum}")
        value_label.setFont(QFont("Segoe UI", 10))
        value_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        container_layout.addWidget(value_label)
        
        # Прогресс-бар
        progress = AnimatedProgressBar(value, maximum)
        progress.set_value(value)
        container_layout.addWidget(progress)
        
        self.charts_container.addWidget(container, row, col)
        return progress
    
    def add_circular_metric(self, title, value, maximum=100, row=0, col=0):
        """Добавление метрики с круговым индикатором"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Круговой прогресс
        circular = CircularProgressWidget(value, maximum, 100, 8)
        circular.set_value(value)
        container_layout.addWidget(circular)
        
        self.charts_container.addWidget(container, row, col)
        return circular
    
    def add_bar_chart(self, title, data, labels=None, colors=None, row=0, col=0, colspan=1):
        """Добавление столбчатой диаграммы"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        container_layout.addWidget(title_label)
        
        # Диаграмма
        chart = BarChart(data, labels, colors)
        chart.set_data(data, labels, colors)
        container_layout.addWidget(chart)
        
        self.charts_container.addWidget(container, row, col, 1, colspan)
        return chart
    
    def add_donut_chart(self, title, data, labels=None, colors=None, row=0, col=0):
        """Добавление кольцевой диаграммы"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Диаграмма
        chart = DonutChart(data, labels, colors, 150)
        chart.set_data(data, labels, colors)
        container_layout.addWidget(chart)
        
        # Легенда
        if labels:
            legend_layout = QHBoxLayout()
            legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            for i, label in enumerate(labels):
                if i >= len(data):
                    break
                
                color = colors[i] if i < len(colors) else theme_manager.get_color('primary')
                
                # Цветной квадратик
                color_label = QLabel()
                color_label.setFixedSize(12, 12)
                color_label.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
                legend_layout.addWidget(color_label)
                
                # Текст
                text_label = QLabel(f"{label}: {data[i]}")
                text_label.setFont(QFont("Segoe UI", 9))
                legend_layout.addWidget(text_label)
                
                if i < len(labels) - 1:
                    legend_layout.addSpacing(16)
            
            container_layout.addLayout(legend_layout)
        
        self.charts_container.addWidget(container, row, col)
        return chart
    
    def apply_styles(self):
        """Применение стилей"""
        colors = theme_manager.get_current_theme()['colors']
        
        self.setStyleSheet(f"""
        MetricsPanel {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
        }}
        """)