"""
Общие стили для приложения ППСД
Теперь использует QSS файлы и гибкие размеры
"""

from ui.themes import theme_manager
from PySide6.QtWidgets import QHeaderView, QTableWidget, QSizePolicy
from PySide6.QtCore import Qt

# Функция для применения стилей к кнопкам
def apply_button_style(button, style_type='default'):
    """
    Применить стиль к кнопке с гибкими размерами
    
    Args:
        button: Кнопка (QPushButton)
        style_type: Тип стиля ('default', 'primary', 'secondary', 'danger')
    """
    try:
        # Убираем фиксированные размеры, используем минимальные для предотвращения наложения
        button.setMinimumSize(80, 32)
        
        # Устанавливаем гибкую политику размеров
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Применяем стили через theme_manager (используется QSS)
        if hasattr(button, 'setProperty'):
            button.setProperty("style_type", style_type)
            
        # QSS стили будут применены автоматически через основную тему
        
    except Exception as e:
        print(f"Ошибка применения стиля кнопки: {e}")

# Функция для применения стилей к полям ввода
def apply_input_style(input_widget, style_type='default'):
    """
    Применить стиль к полю ввода с гибкими размерами
    
    Args:
        input_widget: Поле ввода (QLineEdit, QTextEdit, QPlainTextEdit)
        style_type: Тип стиля ('default', 'search')
    """
    try:
        # Убираем фиксированные размеры
        input_widget.setMinimumHeight(32)
        
        # Устанавливаем гибкую политику размеров
        input_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # QSS стили применятся автоматически
        if hasattr(input_widget, 'setProperty'):
            input_widget.setProperty("input_type", style_type)
            
    except Exception as e:
        print(f"Ошибка применения стиля поля ввода: {e}")

# Функция для применения стилей к комбобоксам
def apply_combobox_style(combobox, style_type='default'):
    """
    Применить стиль к комбобоксу с гибкими размерами
    
    Args:
        combobox: Комбобокс (QComboBox)
        style_type: Тип стиля ('default')
    """
    try:
        # Убираем фиксированные размеры
        combobox.setMinimumSize(120, 32)
        
        # Устанавливаем гибкую политику размеров
        combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # QSS стили применятся автоматически
        if hasattr(combobox, 'setProperty'):
            combobox.setProperty("combo_type", style_type)
            
    except Exception as e:
        print(f"Ошибка применения стиля комбобокса: {e}")

# Функция для применения стилей к таблицам
def apply_table_style(table, style_type='default'):
    """
    Применить стиль к таблице с гибкими размерами и растяжением
    
    Args:
        table: Таблица (QTableWidget, QTableView)
        style_type: Тип стиля ('default')
    """
    try:
        # Убираем все фиксированные размеры, используем гибкие политики
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Настройка вертикального заголовка (номера строк)
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultSectionSize(48)  # Увеличенная высота строк для лучшей читаемости
        table.verticalHeader().setMinimumWidth(80)  # Увеличенная минимальная ширина столбца с номерами
        table.verticalHeader().setMinimumSectionSize(36)  # Минимальная высота = шрифт 14px + зазор
        # Убираем setFixedWidth - используем минимальную ширину
        
        # Настройка горизонтального заголовка с растяжением
        header = table.horizontalHeader()
        header.setMinimumHeight(48)  # Увеличенная минимальная высота заголовка
        header.setDefaultSectionSize(140)  # Увеличенная начальная ширина колонок
        header.setMinimumSectionSize(100)  # Увеличенная минимальная ширина колонок
        
        # Включаем растяжение последней колонки и пропорциональное изменение размеров
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Для лучшего поведения можно использовать ResizeToContents для некоторых колонок
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # Отключаем перемещение колонок для стабильности
        header.setSectionsMovable(False)
        
        # Улучшение настроек таблицы
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Улучшенные настройки для лучшей производительности
        table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # QSS стили применятся автоматически через тему
        
        # Автоматическое изменение размеров колонок под содержимое
        table.resizeColumnsToContents()
        
        # Ограничение максимальной ширины колонок для лучшего отображения
        max_width = 350  # Увеличиваем максимальную ширину
        for col in range(table.columnCount()):
            width = table.columnWidth(col)
            if width > max_width:
                table.setColumnWidth(col, max_width)
            elif width < 100:  # Устанавливаем минимальную ширину
                table.setColumnWidth(col, 100)
        
    except Exception as e:
        print(f"Ошибка при настройке таблицы: {e}")

# Добавляем метод для обновления стилей таблицы после изменения темы
def refresh_table_style(table):
    """
    Обновить стили таблицы после смены темы
    
    Args:
        table: Таблица (QTableWidget, QTableView)
    """
    try:
        # Принудительно обновляем размеры колонок
        table.resizeColumnsToContents()
        
        # Обновляем viewport для перерисовки
        table.viewport().update()
        
        # Применяем минимальные размеры заново
        for col in range(table.columnCount()):
            width = table.columnWidth(col)
            if width < 100:
                table.setColumnWidth(col, 100)
        
    except Exception as e:
        print(f"Ошибка обновления стилей таблицы: {e}")

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