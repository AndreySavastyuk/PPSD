"""
Утилиты для работы с материалами в ППСД
"""

import re

def clean_material_grade(grade_text):
    """
    Очищает марку материала от стандарта (ГОСТ и других обозначений)
    
    Args:
        grade_text (str): Исходная марка материала
        
    Returns:
        str: Очищенная марка материала
        
    Examples:
        clean_material_grade("08Х18Н10Т (ГОСТ 5632-2014)") -> "08Х18Н10Т"
        clean_material_grade("08Х18Н10Т ГОСТ5632-2014") -> "08Х18Н10Т"
        clean_material_grade("12Х18Н10Т") -> "12Х18Н10Т"
    """
    if not grade_text:
        return grade_text
    
    # Паттерны для удаления стандартов
    patterns = [
        r'\s*\(ГОСТ.*?\)',          # Удаляем (ГОСТ...)
        r'\s*\(гост.*?\)',          # Удаляем (гост...)
        r'\s*ГОСТ.*$',              # Удаляем ГОСТ в конце строки
        r'\s*гост.*$',              # Удаляем гост в конце строки
        r'\s*\([^)]*ГОСТ[^)]*\)',   # Удаляем любые скобки с ГОСТ
        r'\s*\([^)]*гост[^)]*\)',   # Удаляем любые скобки с гост
        r'\s*ТУ\s*[\d-]+.*$',       # Удаляем ТУ и номера
        r'\s*ОСТ\s*[\d-]+.*$',      # Удаляем ОСТ и номера
        r'\s*DIN\s*[\d-]+.*$',      # Удаляем DIN стандарты
        r'\s*EN\s*[\d-]+.*$',       # Удаляем EN стандарты
        r'\s*ISO\s*[\d-]+.*$',      # Удаляем ISO стандарты
    ]
    
    clean_text = grade_text.strip()
    
    for pattern in patterns:
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
    
    # Удаляем лишние пробелы и дефисы в конце
    clean_text = re.sub(r'[\s-]+$', '', clean_text)
    
    return clean_text.strip()

def get_material_type_display(type_code):
    """
    Получить отображаемое название типа материала
    
    Args:
        type_code (str): Код типа материала
        
    Returns:
        str: Человекочитаемое название
    """
    type_names = {
        "rod": "Круг",
        "sheet": "Лист", 
        "pipe": "Труба",
        "angle": "Уголок",
        "channel": "Швеллер",
        "other": "Другое"
    }
    return type_names.get(type_code, type_code)

def get_status_display_name(status_code):
    """
    Получить отображаемое название статуса материала
    
    Args:
        status_code (str): Код статуса
        
    Returns:
        str: Человекочитаемое название
    """
    from models.models import MaterialStatus
    
    status_names = {
        MaterialStatus.RECEIVED.value: "Получен на склад",
        MaterialStatus.PENDING_QC.value: "Ожидает проверки ОТК",
        MaterialStatus.QC_CHECK_PENDING.value: "Ожидает проверки ОТК",
        MaterialStatus.QC_CHECKED.value: "Проверен ОТК",
        MaterialStatus.QC_PASSED.value: "Проверка ОТК пройдена",
        MaterialStatus.QC_FAILED.value: "Проверка ОТК не пройдена",
        MaterialStatus.LAB_CHECK_PENDING.value: "Ожидает проверки ЦЗЛ",
        MaterialStatus.LAB_TESTING.value: "На лабораторных испытаниях",
        MaterialStatus.SAMPLES_REQUESTED.value: "Запрошены образцы",
        MaterialStatus.SAMPLES_COLLECTED.value: "Образцы отобраны",
        MaterialStatus.TESTING.value: "На испытаниях",
        MaterialStatus.TESTING_COMPLETED.value: "Испытания завершены",
        MaterialStatus.APPROVED.value: "Одобрен",
        MaterialStatus.READY_FOR_USE.value: "Готов к использованию",
        MaterialStatus.IN_USE.value: "В производстве",
        MaterialStatus.REJECTED.value: "Отклонен",
        MaterialStatus.ARCHIVED.value: "В архиве",
        MaterialStatus.EDIT_REQUESTED.value: "Запрос на редактирование"
    }
    return status_names.get(status_code, status_code) 