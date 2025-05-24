from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox, QFileDialog,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from utils.qr import generate_qr_code, save_qr_code
import tempfile
import os
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider
import qrcode
from io import BytesIO

class QRDialog(QDialog):
    """Диалог для генерации QR-кодов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Генератор QR-кодов")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Генератор QR-кодов")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Поле ввода текста
        input_layout = QVBoxLayout()
        
        input_label = QLabel("Введите текст для кодирования:")
        input_label.setFont(QFont("Segoe UI", 11))
        input_layout.addWidget(input_label)
        
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(100)
        self.text_input.setPlaceholderText("Например: https://example.com или любой текст")
        input_layout.addWidget(self.text_input)
        
        layout.addLayout(input_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Генерировать QR-код")
        self.generate_btn.setIcon(IconProvider.create_qr_code_icon())
        self.generate_btn.clicked.connect(self.generate_qr)
        button_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setIcon(IconProvider.create_excel_icon())  # Используем иконку сохранения
        self.save_btn.clicked.connect(self.save_qr)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Область для отображения QR-кода
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumHeight(200)
        self.qr_label.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {theme_manager.get_color('border')};
                border-radius: 8px;
                background-color: {theme_manager.get_color('surface')};
            }}
        """)
        self.qr_label.setText("QR-код появится здесь")
        layout.addWidget(self.qr_label)
        
        # Кнопка закрытия
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
        
        self.qr_image = None
    
    def apply_styles(self):
        """Применение стилей"""
        self.setStyleSheet(theme_manager.generate_stylesheet())
        
        # Стили для кнопок
        self.generate_btn.setStyleSheet(theme_manager.get_button_style('primary'))
        self.save_btn.setStyleSheet(theme_manager.get_button_style('secondary'))
        
        # Стили для полей ввода
        self.text_input.setStyleSheet(theme_manager.get_input_style())
    
    def generate_qr(self):
        """Генерация QR-кода"""
        text = self.text_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Введите текст для генерации QR-кода")
            return
        
        try:
            # Создаем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            # Создаем изображение
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в QPixmap
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Масштабируем для отображения
            scaled_pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            
            self.qr_label.setPixmap(scaled_pixmap)
            self.qr_image = qr_img
            self.save_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать QR-код:\n{str(e)}")
    
    def save_qr(self):
        """Сохранение QR-кода в файл"""
        if not self.qr_image:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить QR-код",
            "qr_code.png",
            "PNG файлы (*.png);;Все файлы (*)"
        )
        
        if filename:
            try:
                self.qr_image.save(filename)
                QMessageBox.information(self, "Успех", f"QR-код сохранен в файл:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")


class QRViewerDialog(QDialog):
    """Простой диалог для просмотра уже сгенерированного QR-кода"""
    
    def __init__(self, qr_image, sample_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"QR-код образца: {sample_code}")
        self.setMinimumSize(300, 350)
        self.qr_image = qr_image
        self.sample_code = sample_code
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel(f"QR-код образца: {self.sample_code}")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Область просмотра QR-кода
        graphics_view = QGraphicsView()
        graphics_scene = QGraphicsScene()
        graphics_view.setScene(graphics_scene)
        
        # Конвертируем PIL Image в QPixmap
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        self.qr_image.save(temp_file.name)
        pixmap = QPixmap(temp_file.name)
        graphics_scene.addPixmap(pixmap)
        graphics_view.fitInView(graphics_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Удаляем временный файл
        os.unlink(temp_file.name)
        
        layout.addWidget(graphics_view)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn) 