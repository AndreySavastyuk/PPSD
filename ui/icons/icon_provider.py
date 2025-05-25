from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QFont, QPainterPath
from PySide6.QtCore import Qt, QSize, QRect, QPoint, QPointF

class IconProvider:
    """Provides standard grayscale icons for the application"""
    
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
    def create_round_product_icon(size=32):
        """Creates an icon for round product (circle)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle shape
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        painter.drawEllipse(6, 6, size-12, size-12)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_sheet_product_icon(size=32):
        """Creates an icon for sheet product (rectangle)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw sheet shape
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        painter.drawRect(6, 8, size-12, size-16)
        
        # Draw some lines to represent layers
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawLine(8, 12, size-8, 12)
        painter.drawLine(8, 16, size-8, 16)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_pipe_product_icon(size=32):
        """Creates an icon for pipe product (circle with hole)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw outer circle
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        painter.drawEllipse(6, 6, size-12, size-12)
        
        # Draw inner circle (hole)
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        innerSize = size - 20
        painter.drawEllipse(size/2 - innerSize/2, size/2 - innerSize/2, innerSize, innerSize)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_angle_product_icon(size=32):
        """Creates an icon for angle product (L-shape)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw L-shaped angle
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        
        # Create L-shape
        path = QPainterPath()
        path.moveTo(6, 6)
        path.lineTo(6, size-6)
        path.lineTo(size-6, size-6)
        path.lineTo(size-6, size-12)
        path.lineTo(12, size-12)
        path.lineTo(12, 6)
        path.closeSubpath()
        painter.drawPath(path)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_channel_product_icon(size=32):
        """Creates an icon for channel product (U-shape)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw U-shaped channel
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        
        # Create U-shape
        path = QPainterPath()
        path.moveTo(8, 6)
        path.lineTo(8, size-6)
        path.lineTo(size-8, size-6)
        path.lineTo(size-8, 6)
        path.lineTo(size-14, 6)
        path.lineTo(size-14, size-12)
        path.lineTo(14, size-12)
        path.lineTo(14, 6)
        path.closeSubpath()
        painter.drawPath(path)
        
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
    def create_test_type_icon(size=32):
        """Creates an icon for test types (shows a flask/test tube)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw flask
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(230, 230, 230, 180)))
        
        # Test tube shape
        # Neck
        painter.drawRect(size//2-2, 4, 4, 6)
        
        # Body - a rounded bottom test tube
        path = QPainterPath()
        path.moveTo(size//2-2, 10)
        path.lineTo(size//2-6, 10)
        path.lineTo(size//2-10, size-10)
        path.arcTo(size//2-10, size-15, 20, 10, 180, 180)
        path.lineTo(size//2+6, 10)
        path.lineTo(size//2+2, 10)
        painter.drawPath(path)
        
        # Liquid in tube
        painter.setBrush(QBrush(QColor(100, 180, 220, 180)))
        painter.drawEllipse(size//2-6, size-14, 12, 8)
        painter.drawRect(size//2-6, size-20, 12, 10)
        
        # Bubbles
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.drawEllipse(size//2-3, size-18, 3, 3)
        painter.drawEllipse(size//2+2, size-13, 2, 2)
        
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
        
        # Document shape
        painter.drawRoundedRect(6, 4, size-12, size-8, 3, 3)
        
        # Fold in top right corner
        path = QPainterPath()
        path.moveTo(size-6, 4)
        path.lineTo(size-6, 10)
        path.lineTo(size-12, 4)
        path.closeSubpath()
        painter.drawPath(path)
        
        # Plus symbol
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawLine(size//2, 12, size//2, size-14)  # Vertical
        painter.drawLine(12, size//2, size-12, size//2)  # Horizontal
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_edit_icon(size=32):
        """Creates an icon for editing (shows a pencil)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pencil body
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(240, 220, 160)))
        
        # Draw pencil body
        pencil_points = [
            QPoint(size-8, 8),
            QPoint(size-14, 2),
            QPoint(8, size-14),
            QPoint(14, size-8)
        ]
        painter.drawPolygon(pencil_points)
        
        # Pencil tip
        tip_points = [
            QPoint(8, size-14),
            QPoint(2, size-8),
            QPoint(8, size-2),
            QPoint(14, size-8)
        ]
        painter.setBrush(QBrush(QColor(220, 160, 160)))
        painter.drawPolygon(tip_points)
        
        # Eraser
        painter.setBrush(QBrush(QColor(255, 180, 180)))
        eraser_points = [
            QPoint(size-8, 8),
            QPoint(size-14, 2),
            QPoint(size-8, size-4),
            QPoint(size-2, size-10)
        ]
        painter.drawPolygon(eraser_points)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_status_change_icon(size=32):
        """Creates an icon for status change (shows circular arrows)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular arrows
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # First arc (upper)
        painter.drawArc(6, 6, size-12, size-12, 45*16, 180*16)
        
        # Arrow head 1
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        arrow1_points = [
            QPoint(size-8, size//2-3),
            QPoint(size-8, size//2+3),
            QPoint(size-4, size//2)
        ]
        painter.drawPolygon(arrow1_points)
        
        # Second arc (lower)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(6, 6, size-12, size-12, 225*16, 180*16)
        
        # Arrow head 2
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        arrow2_points = [
            QPoint(8, size//2-3),
            QPoint(8, size//2+3),
            QPoint(4, size//2)
        ]
        painter.drawPolygon(arrow2_points)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_qr_code_icon(size=32):
        """Creates an icon for QR code (shows QR pattern)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw QR code pattern
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        
        # Border
        painter.drawRect(4, 4, size-8, size-8)
        
        # White background
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(6, 6, size-12, size-12)
        
        # Black squares pattern
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        
        # Corner squares
        painter.drawRect(8, 8, 6, 6)
        painter.drawRect(size-14, 8, 6, 6)
        painter.drawRect(8, size-14, 6, 6)
        
        # Random pattern to simulate QR
        painter.drawRect(10, 16, 2, 2)
        painter.drawRect(14, 16, 2, 2)
        painter.drawRect(18, 16, 2, 2)
        painter.drawRect(12, 20, 2, 2)
        painter.drawRect(16, 20, 2, 2)
        painter.drawRect(10, 24, 2, 2)
        painter.drawRect(14, 24, 2, 2)
        painter.drawRect(18, 24, 2, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_excel_icon(size=32):
        """Creates an icon for Excel export (shows spreadsheet)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw spreadsheet
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setBrush(QBrush(QColor(220, 255, 220, 180)))
        
        # Main rectangle
        painter.drawRoundedRect(4, 4, size-8, size-8, 2, 2)
        
        # Grid lines
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        
        # Vertical lines
        for i in range(1, 4):
            x = 4 + (size-8) * i // 4
            painter.drawLine(x, 4, x, size-4)
        
        # Horizontal lines
        for i in range(1, 4):
            y = 4 + (size-8) * i // 4
            painter.drawLine(4, y, size-4, y)
        
        # Excel "X" in top left
        painter.setPen(QPen(QColor(40, 120, 40), 2))
        painter.drawLine(6, 6, 12, 12)
        painter.drawLine(12, 6, 6, 12)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_refresh_icon(size=32):
        """Creates an icon for refresh (shows circular arrow)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular arrow
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Arc
        painter.drawArc(6, 6, size-12, size-12, 30*16, 300*16)
        
        # Arrow head
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        arrow_points = [
            QPoint(size//2+6, 8),
            QPoint(size//2+6, 14),
            QPoint(size//2+12, 11)
        ]
        painter.drawPolygon(arrow_points)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_search_icon(size=32):
        """Creates an icon for search (shows magnifying glass)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw magnifying glass
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Glass circle
        painter.drawEllipse(4, 4, 18, 18)
        
        # Handle
        painter.drawLine(18, 18, size-4, size-4)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_scheduler_icon(size=32):
        """Creates an icon for task scheduler (shows clock with gears)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clock face
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
        painter.drawEllipse(6, 6, size-12, size-12)
        
        # Clock hands
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        center = size // 2
        # Hour hand
        painter.drawLine(center, center, center, center-6)
        # Minute hand
        painter.drawLine(center, center, center+4, center-2)
        
        # Clock center
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawEllipse(center-2, center-2, 4, 4)
        
        # Small gear
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        painter.drawEllipse(size-12, 2, 8, 8)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_api_icon(size=32):
        """Creates an icon for API (shows connected nodes)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw network nodes
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(180, 220, 255, 180)))
        
        # Central node
        painter.drawEllipse(size//2-4, size//2-4, 8, 8)
        
        # Outer nodes
        painter.drawEllipse(6, 6, 6, 6)
        painter.drawEllipse(size-12, 6, 6, 6)
        painter.drawEllipse(6, size-12, 6, 6)
        painter.drawEllipse(size-12, size-12, 6, 6)
        
        # Connection lines
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawLine(size//2, size//2, 9, 9)
        painter.drawLine(size//2, size//2, size-9, 9)
        painter.drawLine(size//2, size//2, 9, size-9)
        painter.drawLine(size//2, size//2, size-9, size-9)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_audit_icon(size=32):
        """Creates an icon for audit log (shows document with check)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Document
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(255, 255, 240, 180)))
        painter.drawRoundedRect(4, 4, size-8, size-8, 3, 3)
        
        # Text lines
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLine(8, 10, size-8, 10)
        painter.drawLine(8, 14, size-8, 14)
        painter.drawLine(8, 18, size-8, 18)
        painter.drawLine(8, 22, size-12, 22)
        
        # Checkmark
        painter.setPen(QPen(QColor(60, 150, 60), 3))
        painter.drawLine(size-16, size-8, size-12, size-4)
        painter.drawLine(size-12, size-4, size-6, size-12)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_backup_icon(size=32):
        """Creates an icon for backup (shows database with arrow)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Database cylinders
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 220, 255, 180)))
        
        # Top ellipse
        painter.drawEllipse(4, 6, size//2-2, 8)
        # Middle ellipse
        painter.drawEllipse(4, 12, size//2-2, 8)
        # Bottom ellipse
        painter.drawEllipse(4, 18, size//2-2, 8)
        
        # Connecting lines
        painter.drawLine(4, 10, 4, 22)
        painter.drawLine(size//2+2, 10, size//2+2, 22)
        
        # Arrow pointing to backup
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(size//2+4, size//2, size-6, size//2)
        
        # Arrow head
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        arrow_points = [
            QPoint(size-6, size//2),
            QPoint(size-10, size//2-3),
            QPoint(size-10, size//2+3)
        ]
        painter.drawPolygon(arrow_points)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_filter_icon(size=32):
        """Creates an icon for filter (shows funnel)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Funnel shape
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Top wide part
        painter.drawLine(6, 8, size-6, 8)
        
        # Funnel sides
        painter.drawLine(6, 8, size//2-3, size//2+2)
        painter.drawLine(size-6, 8, size//2+3, size//2+2)
        
        # Narrow bottom
        painter.drawLine(size//2-3, size//2+2, size//2-3, size-6)
        painter.drawLine(size//2+3, size//2+2, size//2+3, size-6)
        
        # Bottom opening
        painter.drawLine(size//2-3, size-6, size//2+3, size-6)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_sample_icon(size=32):
        """Creates an icon for samples (shows test tube with label)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Test tube
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
        
        # Tube body
        painter.drawRoundedRect(8, 6, 8, size-12, 4, 4)
        
        # Sample inside
        painter.setBrush(QBrush(QColor(100, 150, 200, 180)))
        painter.drawRoundedRect(10, size-10, 4, 6, 2, 2)
        
        # Label
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawRect(18, 8, 8, 6)
        
        # Label text
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        font = QFont("Arial", 6)
        painter.setFont(font)
        painter.drawText(19, 12, "01")
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_production_icon(size=32):
        """Creates an icon for production (shows gear and hammer)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gear
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        
        # Simplified gear shape
        painter.drawEllipse(4, 4, 12, 12)
        painter.drawRect(2, 8, 16, 4)
        painter.drawRect(8, 2, 4, 16)
        
        # Center hole
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(8, 8, 4, 4)
        
        # Hammer
        painter.setPen(QPen(QColor(100, 60, 40), 2))
        painter.setBrush(QBrush(QColor(160, 120, 80)))
        
        # Hammer head
        painter.drawRect(18, 12, 8, 4)
        # Handle
        painter.drawRect(20, 16, 2, 12)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_lab_icon(size=32):
        """Creates an icon for laboratory (shows microscope)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Microscope base
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Base
        painter.drawRect(6, size-8, size-12, 4)
        
        # Stand
        painter.drawRect(size//2-1, 8, 2, size-12)
        
        # Eyepiece
        painter.drawEllipse(size//2-3, 6, 6, 6)
        
        # Objective
        painter.drawEllipse(size//2-2, size-14, 4, 4)
        
        # Stage
        painter.drawRect(size//2-6, size-16, 12, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_warehouse_icon(size=32):
        """Creates an icon for warehouse (shows boxes)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Boxes
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 180, 160, 180)))
        
        # Box 1
        painter.drawRect(4, 12, 10, 8)
        painter.drawLine(4, 12, 9, 7)
        painter.drawLine(14, 12, 19, 7)
        painter.drawLine(9, 7, 19, 7)
        painter.drawLine(19, 7, 19, 15)
        
        # Box 2
        painter.drawRect(16, 16, 8, 6)
        painter.drawLine(16, 16, 20, 12)
        painter.drawLine(24, 16, 28, 12)
        painter.drawLine(20, 12, 28, 12)
        painter.drawLine(28, 12, 28, 18)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_qc_icon(size=32):
        """Creates an icon for quality control (shows magnifying glass with checkmark)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Magnifying glass
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Glass circle
        painter.drawEllipse(4, 4, 18, 18)
        
        # Handle
        painter.drawLine(18, 18, size-4, size-4)
        
        # Checkmark inside
        painter.setPen(QPen(QColor(60, 150, 60), 3))
        painter.drawLine(8, 13, 11, 16)
        painter.drawLine(11, 16, 18, 9)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_report_icon(size=32):
        """Creates an icon for reports (shows document with chart)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Document
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.drawRoundedRect(4, 4, size-8, size-8, 3, 3)
        
        # Chart bars
        painter.setBrush(QBrush(QColor(100, 150, 200, 180)))
        painter.drawRect(8, 18, 3, 6)
        painter.drawRect(12, 14, 3, 10)
        painter.drawRect(16, 16, 3, 8)
        painter.drawRect(20, 12, 3, 12)
        
        # Title line
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawLine(8, 10, size-8, 10)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_notification_icon(size=32):
        """Creates an icon for notifications (shows bell)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bell shape
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(255, 220, 100, 180)))
        
        # Bell body
        path = QPainterPath()
        path.moveTo(size//2, 6)
        path.quadTo(8, 10, 8, 18)
        path.lineTo(size-8, 18)
        path.quadTo(size-8, 10, size//2, 6)
        painter.drawPath(path)
        
        # Bell bottom
        painter.drawLine(8, 18, size-8, 18)
        
        # Clapper
        painter.setBrush(QBrush(QColor(120, 120, 120)))
        painter.drawEllipse(size//2-2, 16, 4, 4)
        
        # Top
        painter.drawLine(size//2-2, 6, size//2+2, 6)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_settings_icon(size=32):
        """Creates an icon for settings (shows gear)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gear
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200, 180)))
        
        # Main circle
        painter.drawEllipse(8, 8, size-16, size-16)
        
        # Gear teeth
        for i in range(8):
            angle = i * 45
            x1 = size//2 + 10 * (angle % 90 == 0 and 1 or 0.7) * (1 if angle < 180 else -1) * (1 if angle % 180 < 90 else -1)
            y1 = size//2 + 10 * (angle % 90 == 0 and 1 or 0.7) * (1 if 90 <= angle < 270 else -1) * (1 if angle < 90 or angle >= 270 else -1)
            painter.drawLine(size//2, size//2, x1, y1)
        
        # Center hole
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(size//2-4, size//2-4, 8, 8)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_success_icon(size=32):
        """Creates a success icon (checkmark in circle)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle
        painter.setPen(QPen(QColor(76, 175, 80), 2))
        painter.setBrush(QBrush(QColor(76, 175, 80, 50)))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw checkmark
        painter.setPen(QPen(QColor(76, 175, 80), 3))
        painter.drawLine(size//4, size//2, size//2-2, size*3//4-2)
        painter.drawLine(size//2-2, size*3//4-2, size*3//4, size//4+2)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_error_icon(size=32):
        """Creates an error icon (X in circle)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle
        painter.setPen(QPen(QColor(244, 67, 54), 2))
        painter.setBrush(QBrush(QColor(244, 67, 54, 50)))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw X
        painter.setPen(QPen(QColor(244, 67, 54), 3))
        painter.drawLine(size//4, size//4, size*3//4, size*3//4)
        painter.drawLine(size*3//4, size//4, size//4, size*3//4)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_warning_icon(size=32):
        """Creates a warning icon (triangle with exclamation)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw triangle
        painter.setPen(QPen(QColor(255, 152, 0), 2))
        painter.setBrush(QBrush(QColor(255, 152, 0, 50)))
        
        points = [
            QPoint(size//2, 4),
            QPoint(size-4, size-4),
            QPoint(4, size-4)
        ]
        painter.drawPolygon(points)
        
        # Draw exclamation mark
        painter.setPen(QPen(QColor(255, 152, 0), 3))
        painter.drawLine(size//2, size//3, size//2, size*2//3-2)
        painter.drawPoint(size//2, size*3//4)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_info_icon(size=32):
        """Creates an info icon (i in circle)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle
        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QBrush(QColor(33, 150, 243, 50)))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw 'i'
        painter.setPen(QPen(QColor(33, 150, 243), 3))
        painter.drawPoint(size//2, size//3-2)
        painter.drawLine(size//2, size//2, size//2, size*3//4)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_certificate_icon(size=32):
        """Creates a certificate icon (document with seal)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw document
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.drawRect(6, 4, size-12, size-8)
        
        # Draw horizontal lines (text)
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        line_y = 10
        for _ in range(4):
            painter.drawLine(9, line_y, size-9, line_y)
            line_y += 4
        
        # Draw seal
        painter.setPen(QPen(QColor(120, 60, 60), 1))
        painter.setBrush(QBrush(QColor(220, 150, 150, 180)))
        painter.drawEllipse(size-16, size-16, 10, 10)
        
        # Draw ribbon
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(60, 120, 180)))
        points = [
            QPoint(size-14, size-6),
            QPoint(size-10, size-4),
            QPoint(size-6, size-6),
            QPoint(size-10, size-2)
        ]
        painter.drawPolygon(points)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_copy_icon(size=32):
        """Creates a copy icon (two overlapping documents)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw back document
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawRect(10, 8, size-16, size-16)
        
        # Draw front document
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.drawRect(6, 4, size-16, size-16)
        
        # Draw horizontal lines (text)
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        line_y = 10
        for _ in range(3):
            painter.drawLine(9, line_y, size-13, line_y)
            line_y += 4
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_view_icon(size=32):
        """Creates an icon for viewing/preview (shows an eye)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw eye outline
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Draw eye shape (oval)
        painter.drawEllipse(4, size//2-6, size-8, 12)
        
        # Draw pupil (circle)
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawEllipse(size//2-4, size//2-4, 8, 8)
        
        # Draw highlight in pupil
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawEllipse(size//2-2, size//2-3, 3, 3)
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_delete_icon(size=32):
        """Creates an icon for delete action (shows a trash can)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw trash can
        painter.setPen(QPen(QColor(120, 120, 120), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Draw can body
        painter.drawRect(8, 10, size-16, size-14)
        
        # Draw lid
        painter.drawRect(6, 8, size-12, 4)
        
        # Draw handle
        painter.setPen(QPen(QColor(120, 120, 120), 2))
        painter.setBrush(QBrush(Qt.GlobalColor.transparent))
        painter.drawRect(10, 6, size-20, 4)
        
        # Draw vertical lines on can
        painter.setPen(QPen(QColor(140, 140, 140), 1))
        painter.drawLine(12, 12, 12, size-6)
        painter.drawLine(size//2, 12, size//2, size-6)
        painter.drawLine(size-12, 12, size-12, size-6)
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_add_icon(size=32):
        """Creates an icon for add action (shows a plus sign)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw plus sign
        painter.setPen(QPen(QColor(80, 80, 80), 3))
        
        # Horizontal line
        painter.drawLine(8, size//2, size-8, size//2)
        
        # Vertical line
        painter.drawLine(size//2, 8, size//2, size-8)
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_save_icon(size=32):
        """Creates an icon for save action (shows a floppy disk)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw floppy disk outline
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        painter.drawRect(4, 4, size-8, size-8)
        
        # Draw label area
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawRect(6, 6, size-12, 8)
        
        # Draw metal slider
        painter.setBrush(QBrush(QColor(160, 160, 160)))
        painter.drawRect(size-10, 6, 4, 8)
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_cancel_icon(size=32):
        """Creates an icon for cancel action (shows an X)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw X
        painter.setPen(QPen(QColor(120, 120, 120), 3))
        
        # Draw diagonal lines
        painter.drawLine(8, 8, size-8, size-8)
        painter.drawLine(size-8, 8, 8, size-8)
        
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def create_dashboard_icon(size=32):
        """Creates a dashboard icon (shows grid layout)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid layout
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Top row
        painter.drawRoundedRect(6, 6, 8, 8, 2, 2)
        painter.drawRoundedRect(18, 6, 8, 8, 2, 2)
        
        # Bottom row  
        painter.drawRoundedRect(6, 18, 8, 8, 2, 2)
        painter.drawRoundedRect(18, 18, 8, 8, 2, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_user_icon(size=32):
        """Creates an icon for users (shows a person silhouette)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw user silhouette
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(220, 220, 220, 180)))
        
        # Draw head (circle)
        head_size = size // 4
        head_x = size // 2 - head_size // 2
        head_y = size // 6
        painter.drawEllipse(head_x, head_y, head_size, head_size)
        
        # Draw body (rounded rectangle)
        body_width = size // 2
        body_height = size // 2
        body_x = size // 2 - body_width // 2
        body_y = head_y + head_size
        painter.drawRoundedRect(body_x, body_y, body_width, body_height, 4, 4)
        
        painter.end()
        return QIcon(pixmap) 