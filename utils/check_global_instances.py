"""
Утилита для проверки глобальных экземпляров в кодовой базе ППСД.
Проверяет, что все необходимые глобальные экземпляры созданы и доступны.
"""

import sys
import os
import importlib
import importlib.util
import traceback
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Список классов и их ожидаемых глобальных экземпляров
EXPECTED_GLOBALS = {
    "ui.themes.ThemeManager": "theme_manager",
    "ui.notifications.NotificationManager": "notification_manager"
}

def check_module_exports(module_path, class_name, instance_name):
    """
    Проверяет, экспортирует ли модуль экземпляр указанного класса
    
    Args:
        module_path (str): Путь к модулю (например, 'ui.themes')
        class_name (str): Имя класса (например, 'ThemeManager')
        instance_name (str): Ожидаемое имя экземпляра (например, 'theme_manager')
        
    Returns:
        bool: True если экземпляр существует, иначе False
    """
    try:
        # Импортируем модуль
        module = importlib.import_module(module_path)
        
        # Проверяем, что класс существует
        if not hasattr(module, class_name):
            print(f"[ERROR] Модуль {module_path} не содержит класс {class_name}")
            return False
        
        # Проверяем, что экземпляр существует
        if not hasattr(module, instance_name):
            print(f"[ERROR] Модуль {module_path} не содержит глобальный экземпляр {instance_name}")
            return False
        
        # Проверяем, что экземпляр является экземпляром ожидаемого класса
        instance = getattr(module, instance_name)
        expected_class = getattr(module, class_name)
        
        if not isinstance(instance, expected_class):
            print(f"[ERROR] {instance_name} не является экземпляром класса {class_name}")
            return False
            
        print(f"[OK] Модуль {module_path} содержит экземпляр {instance_name} класса {class_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке модуля {module_path}: {str(e)}")
        traceback.print_exc()
        return False

def check_imports(file_path, module_path, instance_name):
    """
    Проверяет, правильно ли импортируется глобальный экземпляр в файле
    
    Args:
        file_path (str): Путь к файлу для проверки
        module_path (str): Путь к модулю (например, 'ui.themes')
        instance_name (str): Имя глобального экземпляра (например, 'theme_manager')
        
    Returns:
        bool: True если импорт корректен, иначе False
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем различные варианты импорта
        import_patterns = [
            f"from {module_path} import {instance_name}",
            f"from {module_path} import {instance_name} as",
            f"import {module_path}"  # Может использовать как module_path.instance_name
        ]
        
        for pattern in import_patterns:
            if pattern in content:
                return True
                
        return False
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке импортов в файле {file_path}: {str(e)}")
        return False

def find_files_using_instance(instance_name):
    """
    Находит файлы, которые потенциально используют указанный глобальный экземпляр
    
    Args:
        instance_name (str): Имя глобального экземпляра
        
    Returns:
        list: Список путей к файлам
    """
    files_using_instance = []
    project_dir = str(project_root)
    
    for root, dirs, files in os.walk(project_dir):
        # Пропускаем виртуальное окружение и другие ненужные директории
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Ищем использование экземпляра
                    if f"{instance_name}." in content or f"{instance_name}(" in content:
                        files_using_instance.append(file_path)
                except Exception as e:
                    print(f"Ошибка при чтении файла {file_path}: {str(e)}")
    
    return files_using_instance

def check_all_globals():
    """
    Проверяет все ожидаемые глобальные экземпляры
    
    Returns:
        bool: True если все проверки прошли успешно
    """
    all_ok = True
    
    for class_path, instance_name in EXPECTED_GLOBALS.items():
        module_path, class_name = class_path.rsplit('.', 1)
        
        print(f"\n--- Проверка {class_name} и {instance_name} ---")
        
        # Проверяем, что модуль экспортирует экземпляр
        if not check_module_exports(module_path, class_name, instance_name):
            all_ok = False
            continue
            
        # Находим файлы, использующие экземпляр
        print(f"\nПоиск файлов, использующих {instance_name}...")
        files = find_files_using_instance(instance_name)
        
        if not files:
            print(f"Не найдено файлов, использующих {instance_name}")
            continue
            
        # Проверяем импорты в найденных файлах
        print(f"\nПроверка импортов в файлах, использующих {instance_name}:")
        
        for file_path in files:
            if check_imports(file_path, module_path, instance_name):
                print(f"[OK] {file_path} - правильно импортирует {instance_name}")
            else:
                print(f"[WARNING] {file_path} - возможно неправильно импортирует {instance_name}")
                # Не считаем это ошибкой, так как могут быть другие способы импорта
    
    return all_ok

if __name__ == "__main__":
    print("=== Проверка глобальных экземпляров в кодовой базе ППСД ===\n")
    
    success = check_all_globals()
    
    if success:
        print("\n✅ Все проверки прошли успешно.")
        sys.exit(0)
    else:
        print("\n❌ Обнаружены проблемы с глобальными экземплярами.")
        sys.exit(1) 