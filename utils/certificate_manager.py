"""
Утилиты для работы с сертификатами материалов в ППСД
"""

import os
import shutil
import datetime
from pathlib import Path
import re
from utils.material_utils import clean_material_grade

class CertificateManager:
    """Класс для управления сертификатами материалов"""
    
    BASE_DIR = "docs_storage/certificates"
    RECEPTION_DIR = os.path.join(BASE_DIR, "На_приемке")
    ORDERS_DIR = os.path.join(BASE_DIR, "Сертификаты_по_заказам")
    ALL_CERTS_DIR = os.path.join(BASE_DIR, "Все_сертификаты")
    
    @classmethod
    def ensure_directories(cls):
        """Создает необходимые директории для хранения сертификатов"""
        os.makedirs(cls.RECEPTION_DIR, exist_ok=True)
        os.makedirs(cls.ORDERS_DIR, exist_ok=True)
        os.makedirs(cls.ALL_CERTS_DIR, exist_ok=True)
    
    @classmethod
    def format_certificate_filename(cls, material):
        """
        Формирует имя файла сертификата на основе данных о материале
        
        Args:
            material: Объект материала с атрибутами
            
        Returns:
            str: Отформатированное имя файла
        """
        # Determine size and product type
        size = str(material.diameter or material.thickness or '')
        if not size:
            size = "0"
            
        product_type = material.material_type
        # Преобразование типа проката на русский для имени файла
        product_type_map = {
            "rod": "Круг",
            "sheet": "Лист",
            "pipe": "Труба",
            "angle": "Уголок",
            "channel": "Швеллер",
            "other": "Другое"
        }
        product_type_ru = product_type_map.get(product_type, product_type)
        
        # Для типа проката "Круг" (rod) не добавляем тип в имя файла
        if product_type == "rod":
            size_prefix = f"{size}_"
        else:
            size_prefix = f"{size}_{product_type_ru}_"
        
        # Очищаем марку от стандарта для имени файла
        grade = clean_material_grade(material.material_grade)
        melt = f"пл.{material.melt_number}" if material.melt_number else ""
        cert_num = f"серт.№{material.certificate_number}" if material.certificate_number else ""
        
        # Format date
        cert_date = material.certificate_date or datetime.datetime.now()
        date_str = cert_date.strftime("%d.%m.%Y")
        
        # Create certificate filename
        supplier_date = f"{material.supplier_name}_{date_str}"
        filename = f"{size_prefix}{grade}_{melt}_{cert_num}_({supplier_date}).pdf"
        
        # Заменяем недопустимые символы
        filename = filename.replace("/", "-").replace("\\", "-").replace(":", "-")
        filename = re.sub(r'[<>"|?*]', '', filename)  # Удаляем недопустимые символы Windows
        
        return filename
    
    @classmethod
    def upload_certificate(cls, source_path, material):
        """
        Загружает сертификат во временную директорию На приемке
        
        Args:
            source_path (str): Путь к исходному файлу
            material: Объект материала
            
        Returns:
            str: Путь к загруженному файлу
        """
        cls.ensure_directories()
        
        # Генерируем имя файла
        filename = cls.format_certificate_filename(material)
        
        # Путь для временного хранения (на приемке)
        target_path = os.path.join(cls.RECEPTION_DIR, filename)
        
        # Копируем файл
        shutil.copy2(source_path, target_path)
        
        return target_path
    
    @classmethod
    def move_to_final_location(cls, material):
        """
        Перемещает сертификат из временной директории в постоянное хранилище
        
        Args:
            material: Объект материала с certificate_file_path
            
        Returns:
            str: Новый путь к файлу
        """
        if not material.certificate_file_path or not os.path.exists(material.certificate_file_path):
            return None
            
        # Получаем имя файла
        filename = os.path.basename(material.certificate_file_path)
        
        # Создаем директории для хранения по заказам
        order_number = material.order_number or "Без заказа"
        order_number = order_number.replace("/", "-")
        
        # Получаем размер и тип продукта
        size = str(material.diameter or material.thickness or "")
        if not size:
            size = "0"
            
        product_type = material.material_type
        # Преобразование типа проката на русский
        product_type_map = {
            "rod": "Круг",
            "sheet": "Лист",
            "pipe": "Труба",
            "angle": "Уголок",
            "channel": "Швеллер",
            "other": "Другое"
        }
        product_type_ru = product_type_map.get(product_type, product_type)
        
        # Создаем директории - используем очищенную марку
        clean_grade = clean_material_grade(material.material_grade)
        
        # Путь для хранения по заказам
        grade_dir = os.path.join(cls.ORDERS_DIR, order_number, clean_grade)
        size_type_dir = os.path.join(grade_dir, f"{size} {product_type_ru}")
        os.makedirs(size_type_dir, exist_ok=True)
        order_target = os.path.join(size_type_dir, filename)
        
        # Путь для общего хранилища по маркам
        all_grade_dir = os.path.join(cls.ALL_CERTS_DIR, clean_grade)
        all_size_type_dir = os.path.join(all_grade_dir, f"{size} {product_type_ru}")
        os.makedirs(all_size_type_dir, exist_ok=True)
        all_target = os.path.join(all_size_type_dir, filename)
        
        # Копируем файл в оба места
        shutil.copy2(material.certificate_file_path, order_target)
        shutil.copy2(material.certificate_file_path, all_target)
        
        # Удаляем файл из временного хранилища если он там
        if "На приемке" in material.certificate_file_path and os.path.exists(material.certificate_file_path):
            os.remove(material.certificate_file_path)
        
        return order_target
    
    @classmethod
    def search_certificates(cls, search_text=None, material_grade=None, supplier=None, 
                          melt_number=None, date_from=None, date_to=None, 
                          order_number=None, product_type=None):
        """
        Поиск сертификатов по различным критериям
        
        Args:
            search_text (str): Текст для поиска в имени файла
            material_grade (str): Марка материала
            supplier (str): Наименование поставщика
            melt_number (str): Номер плавки
            date_from (datetime): Начальная дата
            date_to (datetime): Конечная дата
            order_number (str): Номер заказа
            product_type (str): Тип продукции
            
        Returns:
            list: Список путей к найденным сертификатам
        """
        results = []
        
        # Функция для проверки соответствия файла критериям поиска
        def matches_criteria(filepath):
            filename = os.path.basename(filepath)
            
            # Поиск по тексту в имени файла
            if search_text and search_text.lower() not in filename.lower():
                return False
                
            # Поиск по марке материала
            if material_grade:
                clean_grade_pattern = f"_{clean_material_grade(material_grade)}_"
                if clean_grade_pattern.lower() not in filename.lower():
                    return False
            
            # Поиск по поставщику
            if supplier and supplier.lower() not in filename.lower():
                return False
                
            # Поиск по номеру плавки
            if melt_number:
                melt_pattern = f"пл.{melt_number}"
                if melt_pattern.lower() not in filename.lower():
                    return False
            
            # Поиск по типу продукции
            if product_type:
                product_type_map = {
                    "rod": "Круг",
                    "sheet": "Лист",
                    "pipe": "Труба",
                    "angle": "Уголок",
                    "channel": "Швеллер",
                    "other": "Другое"
                }
                product_type_ru = product_type_map.get(product_type, product_type)
                if product_type_ru.lower() not in filename.lower():
                    return False
            
            # TODO: Добавить проверку даты
            
            return True
        
        # Обходим директории с сертификатами
        search_dirs = [cls.ALL_CERTS_DIR]
        
        # Если указан номер заказа, ищем только в директории этого заказа
        if order_number:
            order_dir = os.path.join(cls.ORDERS_DIR, order_number)
            if os.path.exists(order_dir):
                search_dirs = [order_dir]
        
        # Обходим все подходящие директории
        for search_dir in search_dirs:
            for root, _, files in os.walk(search_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        filepath = os.path.join(root, file)
                        if matches_criteria(filepath):
                            results.append(filepath)
        
        return results
    
    @classmethod
    def get_certificates_by_material(cls, material_id, material_grade, melt_number=None):
        """
        Получить сертификаты для конкретного материала
        
        Args:
            material_id (int): ID материала
            material_grade (str): Марка материала
            melt_number (str): Номер плавки
            
        Returns:
            list: Список путей к найденным сертификатам
        """
        # Очищаем марку от стандарта
        clean_grade = clean_material_grade(material_grade)
        
        # Ищем в директории общих сертификатов
        grade_dir = os.path.join(cls.ALL_CERTS_DIR, clean_grade)
        
        results = []
        
        if os.path.exists(grade_dir):
            for root, _, files in os.walk(grade_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        filepath = os.path.join(root, file)
                        
                        # Если указан номер плавки, проверяем его наличие в имени файла
                        if melt_number:
                            melt_pattern = f"пл.{melt_number}"
                            if melt_pattern.lower() not in file.lower():
                                continue
                        
                        results.append(filepath)
        
        return results
    
    @classmethod
    def list_certificates_by_material_grade(cls):
        """
        Получить список всех марок материалов с сертификатами
        
        Returns:
            dict: Словарь марок материалов с количеством сертификатов
        """
        result = {}
        
        if os.path.exists(cls.ALL_CERTS_DIR):
            # Обходим все папки марок материалов
            for material_grade in os.listdir(cls.ALL_CERTS_DIR):
                grade_dir = os.path.join(cls.ALL_CERTS_DIR, material_grade)
                if os.path.isdir(grade_dir):
                    # Считаем все файлы PDF внутри директории и поддиректорий
                    count = 0
                    for root, _, files in os.walk(grade_dir):
                        for file in files:
                            if file.lower().endswith('.pdf'):
                                count += 1
                    
                    if count > 0:
                        result[material_grade] = count
        
        return result

def open_certificate(file_path):
    """
    Открывает файл сертификата в системном приложении для просмотра PDF
    
    Args:
        file_path (str): Путь к файлу сертификата
    """
    import os
    import platform
    import subprocess
    
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', file_path))
        else:  # Linux и другие Unix-подобные
            subprocess.call(('xdg-open', file_path))
        return True
    except Exception as e:
        print(f"Ошибка при открытии файла: {e}")
        return False 