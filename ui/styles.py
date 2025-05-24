"""
Общие стили для приложения ППСД
"""

from ui.themes import theme_manager
from PySide6.QtWidgets import QHeaderView, QTableWidget
from PySide6.QtCore import Qt

# Функция для применения стилей к кнопкам
def apply_button_style(button, style_type='default'):
    """
    Применить стиль к кнопке
    
    Args:
        button: Кнопка (QPushButton)
        style_type: Тип стиля ('default')
    """
    try:
        # Устанавливаем минимальные размеры кнопки для предотвращения наложения
        button.setMinimumWidth(80)
        button.setMinimumHeight(30)
        
        # Используем цветные стили из theme_manager
        if style_type == 'default':
            style_type = 'primary'  # Для обратной совместимости
        button.setStyleSheet(theme_manager.get_button_style(style_type))
    except Exception:
        # Фолбек на случай ошибки
        button.setStyleSheet('''
            QPushButton {
                font-size: 14px;
                padding: 5px 12px;
                border-radius: 4px;
                color: #222;
                background: #f8f8f8;
                border: 1px solid #bbb;
                text-shadow: 1px 1px 2px #fff;
                min-width: 80px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        ''')

# Функция для применения стилей к полям ввода
def apply_input_style(input_widget, style_type='default'):
    """
    Применить стиль к полю ввода
    
    Args:
        input_widget: Поле ввода (QLineEdit, QTextEdit, QPlainTextEdit)
        style_type: Тип стиля ('default', 'search')
    """
    try:
        # Используем стили из theme_manager
        input_widget.setStyleSheet(theme_manager.get_input_style())
    except Exception:
        # Фолбек на случай ошибки
        input_widget.setStyleSheet("""
            QLineEdit, QTextEdit, QPlainTextEdit {
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #2196F3;
            }
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
                background-color: #F5F5F5;
                color: #757575;
            }
        """)

# Функция для применения стилей к комбобоксам
def apply_combobox_style(combobox, style_type='default'):
    """
    Применить стиль к комбобоксу
    
    Args:
        combobox: Комбобокс (QComboBox)
        style_type: Тип стиля ('default')
    """
    try:
        # Используем стили из theme_manager
        combobox.setStyleSheet(theme_manager.get_input_style())
    except Exception:
        # Фолбек на случай ошибки
        combobox.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 150px;
                background-color: #FFFFFF;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #757575;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E0E0E0;
                background-color: #FFFFFF;
                selection-background-color: #BBDEFB;
            }
        """)

# Функция для применения стилей к таблицам
def apply_table_style(table, style_type='default'):
    """
    Применить стиль к таблице
    
    Args:
        table: Таблица (QTableWidget, QTableView)
        style_type: Тип стиля ('default')
    """
    try:
        # Настройка вертикального заголовка (номера строк)
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultSectionSize(40)  # Высота строк
        table.verticalHeader().setMinimumWidth(50)  # Ширина столбца с номерами
        table.verticalHeader().setFixedWidth(50)
        
        # Настройка горизонтального заголовка
        header = table.horizontalHeader()
        header.setMinimumHeight(45)  # Увеличенная высота заголовка
        header.setDefaultSectionSize(120)  # Стандартная ширина колонок
        header.setMinimumSectionSize(80)  # Минимальная ширина колонок
        
        # Отключаем изменение размеров пользователем для определенности
        header.setSectionsMovable(False)
        
        # Улучшение стиля таблицы
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Стили CSS для улучшения внешнего вида
        table.setStyleSheet(f'''
            QTableWidget, QTableView {{
                gridline-color: {theme_manager.get_color('border')};
                border: 1px solid {theme_manager.get_color('border')};
                selection-background-color: {theme_manager.get_color('primary')};
                selection-color: white;
                alternate-background-color: {theme_manager.get_color('table_alternate')};
                background-color: {theme_manager.get_color('table_background')};
            }}
            
            QTableWidget::item, QTableView::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {theme_manager.get_color('border')};
                text-shadow: 1px 1px 1px #fff;
                font-size: 14px;
            }}
            
            QHeaderView::section {{
                background-color: {theme_manager.get_color('table_header')};
                color: {theme_manager.get_color('table_header_text')};
                font-weight: bold;
                padding: 8px;
                border: 1px solid {theme_manager.get_color('border')};
                min-height: 45px;
                font-size: 14px;
                text-shadow: 1px 1px 1px #fff;
            }}
            
            QHeaderView::section:vertical {{
                min-width: 50px;
                background-color: {theme_manager.get_color('header')};
                color: {theme_manager.get_color('text_secondary')};
                text-align: center;
            }}
        ''')
        
        # Настройка авторазмера для всех колонок
        table.resizeColumnsToContents()
        
        # Ограничение максимальной ширины колонок
        max_width = 300
        for col in range(table.columnCount()):
            width = table.columnWidth(col)
            if width > max_width:
                table.setColumnWidth(col, max_width)
        
    except Exception as e:
        print(f"Ошибка при настройке таблицы: {e}")
        table.setStyleSheet('''
            QTableWidget, QTableView {
                gridline-color: #E0E0E0;
                background-color: #FFFFFF;
                alternate-background-color: #F9F9F9;
                selection-background-color: #BBDEFB;
                border: 1px solid #E0E0E0;
            }
            QTableWidget::item, QTableView::item {
                padding: 8px;
                border-bottom: 1px solid #EEEEEE;
                text-shadow: 1px 1px 2px #fff;
                font-size: 14px;
            }
            QTableWidget::item:selected, QTableView::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 8px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                color: #212121;
                min-height: 45px;
                min-width: 60px;
                font-size: 14px;
                text-shadow: 1px 1px 1px #fff;
            }
            QHeaderView::section:vertical {
                min-width: 50px;
                background-color: #EEEEEE;
                color: #757575;
            }
        ''')
        
        # Применяем базовые настройки даже в случае ошибки
        table.verticalHeader().setDefaultSectionSize(40)
        table.verticalHeader().setMinimumWidth(50)
        table.horizontalHeader().setMinimumHeight(45)
        table.setAlternatingRowColors(True)

# Функция для применения стилей к диалогам
def apply_dialog_style(dialog):
    """
    Применить стиль к диалогу
    
    Args:
        dialog: Диалоговое окно (QDialog)
    """
    try:
        # Используем стили из theme_manager
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {theme_manager.get_color('background')};
                color: {theme_manager.get_color('text_primary')};
            }}
            QLabel {{
                color: {theme_manager.get_color('text_primary')};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme_manager.get_color('border')};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
    except Exception:
        # Фолбек на случай ошибки
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
                color: #212121;
            }
            QLabel {
                color: #212121;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

# Функция для применения стилей к вкладкам
def apply_tab_style(tab_widget):
    """
    Применить стиль к виджету вкладок
    
    Args:
        tab_widget: Виджет вкладок (QTabWidget)
    """
    try:
        # Используем стили из theme_manager
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme_manager.get_color('border')};
                background-color: {theme_manager.get_color('surface')};
            }}
            QTabBar::tab {{
                background-color: #F5F5F5;
                border: 1px solid {theme_manager.get_color('border')};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme_manager.get_color('primary')};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {theme_manager.get_color('primary_light')};
            }}
        """)
    except Exception:
        # Фолбек на случай ошибки
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #BBDEFB;
            }
        """)

# Функция для получения общих стилей приложения
def get_application_styles():
    """
    Получить общие стили для приложения
    
    Returns:
        str: CSS стили для приложения
    """
    try:
        # Используем стили из theme_manager
        return f"""
            QMainWindow {{
                background-color: {theme_manager.get_color('background')};
            }}
            QWidget {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: {theme_manager.get_color('text_primary')};
            }}
            QStatusBar {{
                background-color: {theme_manager.get_color('surface')};
                border-top: 1px solid {theme_manager.get_color('border')};
            }}
            QMenuBar {{
                background-color: {theme_manager.get_color('surface')};
                border-bottom: 1px solid {theme_manager.get_color('border')};
            }}
            QMenuBar::item {{
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme_manager.get_color('primary_light')};
            }}
            QMenu {{
                background-color: {theme_manager.get_color('surface')};
                border: 1px solid {theme_manager.get_color('border')};
            }}
            QMenu::item {{
                padding: 4px 20px;
            }}
            QMenu::item:selected {{
                background-color: {theme_manager.get_color('primary_light')};
            }}
        """
    except Exception:
        # Фолбек на случай ошибки
        return """
            QMainWindow {
                background-color: #F5F5F5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #212121;
            }
            QStatusBar {
                background-color: #FFFFFF;
                border-top: 1px solid #E0E0E0;
            }
            QMenuBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E0E0E0;
            }
            QMenuBar::item {
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #BBDEFB;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #BBDEFB;
            }
        """ 