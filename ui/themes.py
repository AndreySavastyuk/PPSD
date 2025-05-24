"""
Система тем для приложения ППСД
Поддержка светлой и темной тем
"""

from enum import Enum
from typing import Dict, Any

class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"

class ThemeManager:
    """Менеджер тем приложения"""
    
    def __init__(self):
        self.current_theme = ThemeType.LIGHT
        self._themes = self._initialize_themes()
    
    def _initialize_themes(self) -> Dict[str, Dict[str, Any]]:
        """Инициализация всех тем"""
        return {
            ThemeType.LIGHT.value: {
                'colors': {
                    'primary': '#2196F3',
                    'primary_dark': '#1976D2',
                    'primary_light': '#BBDEFB',
                    'secondary': '#4CAF50',
                    'secondary_dark': '#388E3C',
                    'accent': '#FF9800',
                    'accent_dark': '#F57C00',
                    'error': '#F44336',
                    'warning': '#FF9800',
                    'info': '#2196F3',
                    'success': '#4CAF50',
                    'background': '#F5F5F5',
                    'surface': '#FFFFFF',
                    'card': '#FFFFFF',
                    'text_primary': '#212121',
                    'text_secondary': '#757575',
                    'text_disabled': '#BDBDBD',
                    'border': '#E0E0E0',
                    'border_focus': '#2196F3',
                    'hover': '#F5F5F5',
                    'pressed': '#EEEEEE',
                    'shadow': 'rgba(0, 0, 0, 0.1)',
                    # Цвета для таблиц
                    'table_background': '#FFFFFF',
                    'table_alternate': '#F8F9FA',
                    'table_header': '#E3F2FD',
                    'table_header_text': '#1565C0',
                    'table_border': '#DEE2E6',
                    'table_selected': '#E1F5FE',
                    'table_hover': '#F0F8FF',
                    # Цвета для полей ввода
                    'input_background': '#FFFFFF',
                    'input_border': '#CED4DA',
                    'input_focus': '#80BDFF',
                    'input_text': '#495057',
                    'header': '#F0F0F0'
                },
                'fonts': {
                    'family': 'Segoe UI',
                    'size_small': '11px',
                    'size_normal': '13px',
                    'size_large': '15px',
                    'size_xlarge': '17px',
                    'weight_normal': '400',
                    'weight_bold': '600'
                }
            },
            ThemeType.DARK.value: {
                'colors': {
                    'primary': '#64B5F6',
                    'primary_dark': '#42A5F5',
                    'primary_light': '#90CAF9',
                    'secondary': '#81C784',
                    'secondary_dark': '#66BB6A',
                    'accent': '#FFB74D',
                    'accent_dark': '#FFA726',
                    'error': '#EF5350',
                    'warning': '#FFB74D',
                    'info': '#64B5F6',
                    'success': '#81C784',
                    'background': '#1E1E1E',
                    'surface': '#2D2D2D',
                    'card': '#3E3E3E',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#B0BEC5',
                    'text_disabled': '#666666',
                    'border': '#4A4A4A',
                    'border_focus': '#64B5F6',
                    'hover': '#404040',
                    'pressed': '#505050',
                    'shadow': 'rgba(0, 0, 0, 0.4)',
                    # Цвета для таблиц (темная тема)
                    'table_background': '#2D2D2D',
                    'table_alternate': '#363636',
                    'table_header': '#404040',
                    'table_header_text': '#E0E0E0',
                    'table_border': '#4A4A4A',
                    'table_selected': '#1565C0',
                    'table_hover': '#424242',
                    # Цвета для полей ввода (темная тема)
                    'input_background': '#3E3E3E',
                    'input_border': '#5A5A5A',
                    'input_focus': '#64B5F6',
                    'input_text': '#FFFFFF',
                    'header': '#3D3D3D'
                },
                'fonts': {
                    'family': 'Segoe UI',
                    'size_small': '11px',
                    'size_normal': '13px',
                    'size_large': '15px',
                    'size_xlarge': '17px',
                    'weight_normal': '400',
                    'weight_bold': '600'
                }
            }
        }
    
    def set_theme(self, theme_type: ThemeType):
        """Установить текущую тему"""
        self.current_theme = theme_type
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Получить данные текущей темы"""
        return self._themes[self.current_theme.value]
    
    def get_color(self, color_name: str) -> str:
        """Получить цвет из текущей темы"""
        return self.get_current_theme()['colors'].get(color_name, '#000000')
    
    def get_font(self, font_property: str) -> str:
        """Получить свойство шрифта из текущей темы"""
        return self.get_current_theme()['fonts'].get(font_property, '14px')
    
    def generate_stylesheet(self) -> str:
        """Генерация основного стиля приложения"""
        theme = self.get_current_theme()
        colors = theme['colors']
        fonts = theme['fonts']
        
        return f"""
        /* Основные стили приложения */
        QWidget {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            font-weight: {fonts['weight_normal']};
        }}
        
        /* Главное окно */
        QMainWindow {{
            background-color: {colors['background']};
        }}
        
        /* Центральный виджет */
        QMainWindow::centralWidget {{
            background-color: {colors['background']};
        }}
        
        /* Меню */
        QMenuBar {{
            background-color: {colors['surface']};
            border-bottom: 1px solid {colors['border']};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['hover']};
        }}
        
        QMenu {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 8px;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['hover']};
        }}
        
        /* Вкладки */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-radius: 8px;
            background-color: {colors['surface']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['card']};
            border: 1px solid {colors['border']};
            border-bottom: none;
            padding: 12px 16px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['surface']};
            border-bottom: 2px solid {colors['primary']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors['hover']};
        }}
        
        /* Панели и фреймы */
        QFrame {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
        }}
        
        /* Диалоги */
        QDialog {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
        }}
        
        /* Статусная строка */
        QStatusBar {{
            background-color: {colors['surface']};
            border-top: 1px solid {colors['border']};
            color: {colors['text_secondary']};
        }}
        
        /* Прокрутка */
        QScrollBar:vertical {{
            background: {colors['background']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['border']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors['text_secondary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* Тултипы */
        QToolTip {{
            background-color: {colors['card']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
            font-size: {fonts['size_small']};
        }}
        
        /* Подсказки для элементов списка */
        QListView::item {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
        }}
        
        QListView::item:selected {{
            background-color: {colors['primary']};
            color: white;
        }}
        """
    
    def get_button_style(self, style_type: str = 'primary') -> str:
        """Получить стиль кнопки для текущей темы"""
        colors = self.get_current_theme()['colors']
        
        button_configs = {
            'primary': {
                'bg': colors['primary'],
                'bg_hover': colors['primary_dark'],
                'bg_pressed': colors['primary_dark'],
                'text': '#FFFFFF'
            },
            'secondary': {
                'bg': colors['secondary'],
                'bg_hover': colors['secondary_dark'],
                'bg_pressed': colors['secondary_dark'],
                'text': '#FFFFFF'
            },
            'warning': {
                'bg': colors['warning'],
                'bg_hover': colors['accent_dark'],
                'bg_pressed': colors['accent_dark'],
                'text': '#FFFFFF'
            },
            'danger': {
                'bg': colors['error'],
                'bg_hover': '#D32F2F',
                'bg_pressed': '#C62828',
                'text': '#FFFFFF'
            },
            'neutral': {
                'bg': colors['text_secondary'],
                'bg_hover': colors['text_primary'],
                'bg_pressed': colors['text_primary'],
                'text': colors['surface']
            },
            'special': {
                'bg': '#9C27B0',
                'bg_hover': '#7B1FA2',
                'bg_pressed': '#6A1B9A',
                'text': '#FFFFFF'
            }
        }
        
        config = button_configs.get(style_type, button_configs['primary'])
        
        return f"""
        QPushButton {{
            background-color: {config['bg']};
            color: {config['text']};
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            min-height: 20px;
            min-width: 100px;
            margin: 2px 4px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {config['bg_hover']};
        }}
        QPushButton:pressed {{
            background-color: {config['bg_pressed']};
        }}
        QPushButton:disabled {{
            background-color: {colors['text_disabled']};
            color: {colors['text_secondary']};
        }}
        """
    
    def get_input_style(self) -> str:
        """Получить стили для полей ввода с улучшенной контрастностью"""
        theme = self.get_current_theme()
        colors = theme['colors']
        fonts = theme['fonts']
        
        return f"""
        QLineEdit {{
            background-color: {colors['input_background']};
            border: 2px solid {colors['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            color: {colors['input_text']};
        }}
        
        QLineEdit:focus {{
            border-color: {colors['input_focus']};
            background-color: {colors['input_background']};
        }}
        
        QLineEdit:disabled {{
            background-color: {colors['hover']};
            color: {colors['text_disabled']};
            border-color: {colors['border']};
        }}
        
        QComboBox {{
            background-color: {colors['input_background']};
            border: 2px solid {colors['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            color: {colors['input_text']};
            min-width: 80px;
        }}
        
        QComboBox:focus {{
            border-color: {colors['input_focus']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {colors['input_border']};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: {colors['hover']};
        }}
        
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['input_background']};
            border: 1px solid {colors['input_border']};
            border-radius: 6px;
            color: {colors['input_text']};
            selection-background-color: {colors['table_selected']};
        }}
        
        QDateEdit {{
            background-color: {colors['input_background']};
            border: 2px solid {colors['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            color: {colors['input_text']};
        }}
        
        QDateEdit:focus {{
            border-color: {colors['input_focus']};
        }}
        
        QTextEdit {{
            background-color: {colors['input_background']};
            border: 2px solid {colors['input_border']};
            border-radius: 6px;
            padding: 8px;
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            color: {colors['input_text']};
        }}
        
        QTextEdit:focus {{
            border-color: {colors['input_focus']};
        }}
        """
    
    def get_table_style(self) -> str:
        """Получить стили для таблиц с улучшенной контрастностью"""
        theme = self.get_current_theme()
        colors = theme['colors']
        fonts = theme['fonts']
        
        return f"""
        QTableWidget {{
            background-color: {colors['table_background']};
            alternate-background-color: {colors['table_alternate']};
            color: {colors['text_primary']};
            border: 1px solid {colors['table_border']};
            border-radius: 6px;
            font-family: {fonts['family']};
            font-size: {fonts['size_normal']};
            gridline-color: {colors['table_border']};
            selection-background-color: {colors['table_selected']};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors['table_border']};
            background-color: {colors['table_background']};
            color: {colors['text_primary']};
        }}
        
        QTableWidget::item:alternate {{
            background-color: {colors['table_alternate']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors['table_selected']};
            color: {colors['text_primary']};
        }}
        
        QTableWidget::item:hover {{
            background-color: {colors['table_hover']};
        }}
        
        QHeaderView::section {{
            background-color: {colors['table_header']};
            color: {colors['table_header_text']};
            font-weight: {fonts['weight_bold']};
            padding: 10px;
            border: 1px solid {colors['table_border']};
            border-left: none;
            border-bottom: 2px solid {colors['primary']};
        }}
        
        QHeaderView::section:first {{
            border-left: 1px solid {colors['table_border']};
            border-top-left-radius: 6px;
        }}
        
        QHeaderView::section:last {{
            border-top-right-radius: 6px;
        }}
        
        QScrollBar:vertical {{
            background: {colors['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['border']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors['primary']};
        }}
        """

# Глобальный экземпляр менеджера тем
theme_manager = ThemeManager() 