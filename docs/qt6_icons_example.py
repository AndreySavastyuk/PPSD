"""
Пример реализации IconProvider с использованием PySide6 (Qt6)
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QSize, QRect, QPoint, QPointF
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QLabel
from PySide6.QtGui import QAction

class IconProvider:
    """Provides standard grayscale icons for the application (Qt6 version)"""
    
    @staticmethod
    def create_material_grade_icon(size=32):
        """Creates an icon for material grades (shows M letter in a box)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw rounded rectangle
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        painter.drawRoundedRect(4, 4, size-8, size-8, 4, 4)
        
        # Draw 'M' letter
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        font = QFont("Arial", 16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "M")
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_product_type_icon(size=32):
        """Creates an icon for product types (shows a shape icon)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw profile shape
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        
        # Draw a rod/pipe shape
        painter.drawRoundedRect(6, 8, size-12, size-16, 2, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_supplier_icon(size=32):
        """Creates an icon for suppliers (shows a factory/company)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw factory outline
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Draw building
        painter.drawRect(8, 14, size-16, size-18)
        # Draw roof
        points = [
            QPoint(8, 14),
            QPoint(size-8, 14),
            QPoint(size-8-4, 6),
            QPoint(8+4, 6)
        ]
        painter.drawPolygon(points)
        
        # Draw chimney
        painter.drawRect(size-15, 2, 4, 8)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_material_entry_icon(size=32):
        """Creates an icon for material entry (shows a document with plus)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw document
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
        painter.drawRect(6, 4, size-12, size-8)
        
        # Draw lines for text
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        y_pos = 10
        for _ in range(3):
            painter.drawLine(10, y_pos, size-10, y_pos)
            y_pos += 5
        
        # Draw plus sign
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.drawLine(size//2, 20, size//2, 28)
        painter.drawLine(size//2-4, 24, size//2+4, 24)
        
        painter.end()
        return QIcon(pixmap)


# Пример использования с Qt6:
def qt6_example():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Qt6 Icons Example")
    
    toolbar = QToolBar()
    window.addToolBar(toolbar)
    
    # Добавление иконок в тулбар
    action1 = QAction(IconProvider.create_material_grade_icon(), "Материалы", window)
    action2 = QAction(IconProvider.create_product_type_icon(), "Прокат", window)
    action3 = QAction(IconProvider.create_supplier_icon(), "Поставщики", window)
    action4 = QAction(IconProvider.create_material_entry_icon(), "Приход", window)
    
    toolbar.addAction(action1)
    toolbar.addAction(action2)
    toolbar.addAction(action3)
    toolbar.addAction(action4)
    
    window.setMinimumSize(400, 300)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    qt6_example() 