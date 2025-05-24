#!/usr/bin/env python
"""
Скрипт автоматической миграции PyQt5 → PySide6
"""

import os
import re
import sys
from pathlib import Path

def find_python_files(base_path):
    """Ищет все Python файлы в директории"""
    found_files = []
    for root, dirs, files in os.walk(base_path):
        # Пропускаем venv и .git директории
        if "venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                found_files.append(os.path.join(root, file))
    return found_files

def update_import_statements(file_path):
    """Обновляет импорты PyQt5 на PySide6"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Заменяем импорты
    updated_content = re.sub(r'from PyQt5\.([a-zA-Z.]+) import (.+)', 
                             r'from PySide6.\1 import \2', content)
    updated_content = re.sub(r'import PyQt5\.([a-zA-Z.]+)', 
                             r'import PySide6.\1', updated_content)
    
    # Проверяем, были ли сделаны изменения
    if content != updated_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return True
    return False

def update_constants(file_path):
    """Обновляем константы Qt для Qt6"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Словарь преобразований
    replacements = {
        # Выравнивание
        r'Qt\.AlignCenter': 'Qt.AlignmentFlag.AlignCenter',
        r'Qt\.AlignLeft': 'Qt.AlignmentFlag.AlignLeft',
        r'Qt\.AlignRight': 'Qt.AlignmentFlag.AlignRight',
        r'Qt\.AlignTop': 'Qt.AlignmentFlag.AlignTop',
        r'Qt\.AlignBottom': 'Qt.AlignmentFlag.AlignBottom',
        r'Qt\.AlignVCenter': 'Qt.AlignmentFlag.AlignVCenter',
        r'Qt\.AlignHCenter': 'Qt.AlignmentFlag.AlignHCenter',
        
        # Цвета
        r'Qt\.transparent': 'Qt.GlobalColor.transparent',
        r'Qt\.black': 'Qt.GlobalColor.black',
        r'Qt\.white': 'Qt.GlobalColor.white',
        r'Qt\.red': 'Qt.GlobalColor.red',
        r'Qt\.green': 'Qt.GlobalColor.green',
        r'Qt\.blue': 'Qt.GlobalColor.blue',
        
        # Флаги окон
        r'Qt\.WindowStaysOnTopHint': 'Qt.WindowType.WindowStaysOnTopHint',
        r'Qt\.WindowCloseButtonHint': 'Qt.WindowType.WindowCloseButtonHint',
        r'Qt\.Dialog': 'Qt.WindowType.Dialog',
        
        # Ориентация
        r'Qt\.Horizontal': 'Qt.Orientation.Horizontal',
        r'Qt\.Vertical': 'Qt.Orientation.Vertical',
        
        # QFrame
        r'QFrame\.HLine': 'QFrame.Shape.HLine',
        r'QFrame\.VLine': 'QFrame.Shape.VLine',
        r'QFrame\.Sunken': 'QFrame.Shadow.Sunken',
        r'QFrame\.Raised': 'QFrame.Shadow.Raised',
        
        # QPainter
        r'QPainter\.Antialiasing': 'QPainter.RenderHint.Antialiasing',
        
        # QFont
        r'QFont\.Bold': 'QFont.Weight.Bold',
        r'QFont\.Normal': 'QFont.Weight.Normal',
        
        # QMessageBox
        r'QMessageBox\.Yes': 'QMessageBox.StandardButton.Yes',
        r'QMessageBox\.No': 'QMessageBox.StandardButton.No',
        r'QMessageBox\.Ok': 'QMessageBox.StandardButton.Ok',
        r'QMessageBox\.Cancel': 'QMessageBox.StandardButton.Cancel',
        r'QMessageBox\.Question': 'QMessageBox.Icon.Question',
        r'QMessageBox\.Information': 'QMessageBox.Icon.Information',
        r'QMessageBox\.Warning': 'QMessageBox.Icon.Warning',
        r'QMessageBox\.Critical': 'QMessageBox.Icon.Critical',
    }
    
    updated_content = content
    for old, new in replacements.items():
        updated_content = re.sub(old, new, updated_content)
    
    # Проверяем, были ли сделаны изменения
    if content != updated_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return True
    return False

def update_exec_to_exec_(file_path):
    """Заменяет app.exec() на app.exec() для совместимости"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Ищем вызовы app.exec() и заменяем на app.exec()
    # Исправлено: правильно ищем и заменяем метод exec_()
    updated_content = re.sub(r'app\.exec_\(\)', 'app.exec()', content)
    
    # Проверяем, были ли сделаны изменения
    if content != updated_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return True
    return False

def migrate_requirements():
    """Обновляет requirements.txt"""
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Заменяем PyQt5 на PySide6
        if 'PyQt5' in content:
            # Находим версию PyQt5
            pyqt_match = re.search(r'PyQt5==([0-9.]+)', content)
            if pyqt_match:
                version = pyqt_match.group(1)
                print(f"Найдена версия PyQt5: {version}")
                print("Заменяем на PySide6==6.5.2")
                content = content.replace(f'PyQt5=={version}', 'PySide6==6.5.2')
            else:
                print("Заменяем PyQt5 на PySide6==6.5.2")
                content = content.replace('PyQt5', 'PySide6==6.5.2')
            
            with open('requirements.txt', 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Создаем бэкап файла
            with open('requirements.txt.bak', 'w', encoding='utf-8') as file:
                file.write(content)
            
            return True
    return False

def main():
    # Определяем базовую директорию проекта
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    print(f"Начинаем миграцию в директории: {base_path}")
    
    # Обновляем requirements.txt
    if migrate_requirements():
        print("✅ requirements.txt успешно обновлен")
    else:
        print("⚠️ requirements.txt не найден или не содержит PyQt5")
    
    # Находим все Python файлы
    python_files = find_python_files(base_path)
    print(f"Найдено {len(python_files)} Python файлов")
    
    files_with_import_changes = 0
    files_with_constant_changes = 0
    files_with_exec_changes = 0
    
    # Обрабатываем каждый файл
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, base_path)
        
        # Обновляем импорты
        if update_import_statements(file_path):
            files_with_import_changes += 1
            print(f"📄 Обновлены импорты в: {rel_path}")
        
        # Обновляем константы
        if update_constants(file_path):
            files_with_constant_changes += 1
            print(f"🔄 Обновлены константы в: {rel_path}")
        
        # Обновляем exec_() на exec()
        if update_exec_to_exec_(file_path):
            files_with_exec_changes += 1
            print(f"🔄 Обновлен app.exec() в: {rel_path}")
    
    print("\n--- Результаты миграции ---")
    print(f"Обработано файлов: {len(python_files)}")
    print(f"Файлов с изменениями импортов: {files_with_import_changes}")
    print(f"Файлов с изменениями констант: {files_with_constant_changes}")
    print(f"Файлов с изменениями exec_(): {files_with_exec_changes}")
    print("\n⚠️ Внимание! После миграции требуется ручная проверка и тестирование.")
    print("Особое внимание уделите файлам, где используются QPainter, QFont, QMessageBox.")

if __name__ == "__main__":
    main() 