"""
Модуль для исправления проблем с QPainter в PySide6.
Решает ошибку: 'PySide6.QtGui.QPainter' object has no attribute 'path'
"""
from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtCore import QPointF

def patch_painter():
    """
    Создает monkey-patch для QPainter, добавляя отсутствующие методы или атрибуты.
    
    Это решает проблему с отсутствующим атрибутом 'path'.
    """
    # Проверка, есть ли уже атрибут path у QPainter
    if not hasattr(QPainter, 'path'):
        # Добавляем метод path, который возвращает новый пустой QPainterPath
        def path_method(self):
            return QPainterPath()
        
        # Добавляем метод к QPainter
        QPainter.path = path_method
        
        print("QPainter patched: added 'path' method")

# Альтернативная функция для использования вместо QPainter.path()
def create_path():
    """
    Создает и возвращает новый пустой QPainterPath.
    Используйте эту функцию вместо QPainter.path().
    
    Пример использования:
    from utils.painter_fix import create_path
    
    # Вместо: path = painter.path()
    path = create_path()
    """
    return QPainterPath()

# Использование:
# В начале программы (например, в main.py):
# from utils.painter_fix import patch_painter
# patch_painter()
#
# Или, альтернативно, используйте create_path() вместо painter.path() 