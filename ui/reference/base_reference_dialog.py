from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt

class BaseReferenceDialog(QDialog):
    """
    Базовый класс для всех диалогов-справочников, который добавляет кнопки управления окном
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Устанавливаем флаги, чтобы окно имело кнопки закрытия, сворачивания и разворачивания
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        ) 