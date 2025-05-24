"""
Система уведомлений для приложения ППСД
Красивые всплывающие уведомления с анимацией
"""

from PySide6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                             QGraphicsEffect, QGraphicsDropShadowEffect,
                             QApplication)
from PySide6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                          QRect, QPoint, Signal)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from enum import Enum
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider

class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class NotificationWidget(QWidget):
    """Виджет уведомления с анимацией"""
    
    closed = Signal()
    
    def __init__(self, message: str, notification_type: NotificationType, duration: int = 3000):
        super().__init__()
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
        self.setup_animations()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setFixedSize(350, 80)
        
        # Основной layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Иконка
        self.icon_label = QLabel()
        icon = self.get_notification_icon()
        if icon:
            self.icon_label.setPixmap(icon.pixmap(24, 24))
        layout.addWidget(self.icon_label)
        
        # Текст
        self.text_label = QLabel(self.message)
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.text_label, 1)
        
        # Кнопка закрытия
        self.close_label = QLabel("×")
        self.close_label.setFixedSize(20, 20)
        self.close_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.close_label.setStyleSheet("QLabel:hover { background-color: rgba(255,255,255,0.2); border-radius: 10px; }")
        self.close_label.mousePressEvent = self.close_notification
        layout.addWidget(self.close_label)
        
        # Добавляем тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Таймер автозакрытия
        # Убедимся, что duration - это число и оно больше 0
        try:
            duration_int = int(self.duration)
            if duration_int > 0:
                self.timer = QTimer()
                self.timer.timeout.connect(self.close_notification)
                self.timer.start(duration_int)
        except (ValueError, TypeError):
            # Если duration не число или его нельзя преобразовать в число,
            # просто не создаем таймер автозакрытия
            pass
    
    def get_notification_icon(self):
        """Получить иконку для типа уведомления"""
        if self.notification_type == NotificationType.SUCCESS:
            return IconProvider.create_success_icon()
        elif self.notification_type == NotificationType.ERROR:
            return IconProvider.create_error_icon()
        elif self.notification_type == NotificationType.WARNING:
            return IconProvider.create_warning_icon()
        elif self.notification_type == NotificationType.INFO:
            return IconProvider.create_info_icon()
        return None
    
    def setup_animations(self):
        """Настройка анимаций"""
        # Анимация появления
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(300)
        self.show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Анимация исчезновения
        self.hide_animation = QPropertyAnimation(self, b"geometry")
        self.hide_animation.setDuration(200)
        self.hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.hide_animation.finished.connect(self.close)
        self.hide_animation.finished.connect(self.closed.emit)
    
    def paintEvent(self, event):
        """Отрисовка фона уведомления"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Определяем цвет фона в зависимости от типа
        colors = theme_manager.get_current_theme()['colors']
        
        if self.notification_type == NotificationType.SUCCESS:
            bg_color = QColor(colors['success'])
        elif self.notification_type == NotificationType.ERROR:
            bg_color = QColor(colors['error'])
        elif self.notification_type == NotificationType.WARNING:
            bg_color = QColor(colors['warning'])
        else:  # INFO
            bg_color = QColor(colors['info'])
        
        # Рисуем фон с скругленными углами
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        # Рисуем прогресс-бар (если есть таймер)
        if hasattr(self, 'timer') and self.timer.isActive():
            remaining_time = self.timer.remainingTime()
            try:
                duration_int = int(self.duration)
                if duration_int > 0:
                    progress = remaining_time / duration_int
                    
                    # Фон прогресс-бара
                    progress_rect = QRect(0, self.height() - 3, self.width(), 3)
                    painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
                    painter.drawRoundedRect(progress_rect, 1, 1)
                    
                    # Сам прогресс-бар
                    progress_width = int(self.width() * progress)
                    progress_rect.setWidth(progress_width)
                    painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
                    painter.drawRoundedRect(progress_rect, 1, 1)
            except (ValueError, TypeError):
                # Если duration не может быть преобразовано в int, не рисуем прогресс-бар
                pass
    
    def show_notification(self, parent_rect: QRect):
        """Показать уведомление с анимацией"""
        # Позиция справа сверху
        x = parent_rect.right() - self.width() - 20
        y = parent_rect.top() + 20
        
        # Начальная позиция (справа от экрана)
        start_rect = QRect(parent_rect.right(), y, self.width(), self.height())
        end_rect = QRect(x, y, self.width(), self.height())
        
        self.setGeometry(start_rect)
        self.show()
        
        self.show_animation.setStartValue(start_rect)
        self.show_animation.setEndValue(end_rect)
        self.show_animation.start()
    
    def close_notification(self, event=None):
        """Закрыть уведомление с анимацией"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        current_rect = self.geometry()
        end_rect = QRect(current_rect.right(), current_rect.y(), 
                        current_rect.width(), current_rect.height())
        
        self.hide_animation.setStartValue(current_rect)
        self.hide_animation.setEndValue(end_rect)
        self.hide_animation.start()


class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.notifications = []
        self.max_notifications = 5
        
    def show_notification(self, message: str, notification_type: NotificationType, 
                         duration: int = 3000, parent_widget=None):
        """Показать уведомление"""
        # Определяем родительский виджет
        if parent_widget is None:
            parent_widget = QApplication.activeWindow()
        
        if parent_widget is None:
            return
        
        # Удаляем старые уведомления если их слишком много
        while len(self.notifications) >= self.max_notifications:
            old_notification = self.notifications.pop(0)
            old_notification.close_notification()
        
        # Создаем новое уведомление
        notification = NotificationWidget(message, notification_type, duration)
        notification.closed.connect(lambda: self.remove_notification(notification))
        
        # Вычисляем позицию с учетом других уведомлений
        parent_rect = parent_widget.geometry()
        y_offset = 20 + len(self.notifications) * 90
        
        notification_rect = QRect(
            parent_rect.right() - notification.width() - 20,
            parent_rect.top() + y_offset,
            notification.width(),
            notification.height()
        )
        
        notification.show_notification(QRect(
            parent_rect.x(), parent_rect.y() + y_offset,
            parent_rect.width(), notification.height()
        ))
        
        self.notifications.append(notification)
    
    def remove_notification(self, notification):
        """Удалить уведомление из списка"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            self.reposition_notifications()
    
    def reposition_notifications(self):
        """Перепозиционировать уведомления после удаления"""
        for i, notification in enumerate(self.notifications):
            current_rect = notification.geometry()
            new_y = 20 + i * 90
            
            if current_rect.y() != new_y:
                # Анимация перемещения
                animation = QPropertyAnimation(notification, b"geometry")
                animation.setDuration(200)
                animation.setStartValue(current_rect)
                animation.setEndValue(QRect(current_rect.x(), new_y, 
                                          current_rect.width(), current_rect.height()))
                animation.start()
    
    def show_success(self, message: str, duration: int = 3000, parent_widget=None):
        """Показать уведомление об успехе"""
        self.show_notification(message, NotificationType.SUCCESS, duration, parent_widget)
    
    def show_error(self, message: str, duration: int = 5000, parent_widget=None):
        """Показать уведомление об ошибке"""
        self.show_notification(message, NotificationType.ERROR, duration, parent_widget)
    
    def show_warning(self, message: str, duration: int = 4000, parent_widget=None):
        """Показать предупреждение"""
        self.show_notification(message, NotificationType.WARNING, duration, parent_widget)
    
    def show_info(self, message: str, duration: int = 3000, parent_widget=None):
        """Показать информационное уведомление"""
        self.show_notification(message, NotificationType.INFO, duration, parent_widget)
    
    def clear_all(self):
        """Закрыть все уведомления"""
        for notification in self.notifications[:]:
            notification.close_notification()

# Глобальный экземпляр менеджера уведомлений
notification_manager = NotificationManager() 