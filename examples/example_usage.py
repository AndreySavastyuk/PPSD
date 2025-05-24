"""
Примеры использования расширенной функциональности PPSD
"""

# Пример 1: Генерация QR-кода для образца
from utils.qr import save_qr_code

def example_qr_generation():
    sample_code = "001-ПЛ123456-01"
    qr_path = save_qr_code(sample_code, "sample_qr.png")
    print(f"QR-код создан: {qr_path}")

# Пример 2: Экспорт материалов в Excel
from utils.excel_export import export_materials_to_excel
from datetime import datetime, timedelta

def example_excel_export():
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    excel_path = export_materials_to_excel("materials_report.xlsx", start_date, end_date)
    print(f"Excel отчет создан: {excel_path}")

# Пример 3: Использование StatusManager для безопасного изменения статуса
from utils.status_manager import StatusManager
from models.models import MaterialStatus, UserRole

def example_status_transition():
    # Проверка возможности перехода
    can_transition = StatusManager.can_transition(
        MaterialStatus.RECEIVED.value, 
        MaterialStatus.QC_CHECK_PENDING.value
    )
    print(f"Можно перейти из RECEIVED в QC_CHECK_PENDING: {can_transition}")
    
    # Получение доступных переходов для пользователя
    available = StatusManager.get_available_transitions(
        MaterialStatus.RECEIVED.value, 
        UserRole.WAREHOUSE.value
    )
    print(f"Доступные переходы для кладовщика: {available}")
    
    # Выполнение перехода (пример)
    success, message = StatusManager.transition_material(
        material_id=1,
        target_status=MaterialStatus.QC_CHECK_PENDING.value,
        user_id=1,
        user_role=UserRole.WAREHOUSE.value,
        comment="Материал готов к проверке ОТК"
    )
    print(f"Результат перехода: {success}, {message}")

# Пример 4: Логирование действий пользователя
from utils.audit import log_action

def example_audit_logging():
    log_action(
        user_id=1,
        action="Создание нового материала",
        details="Марка: 08Х18Н10Т, Плавка: ПЛ123456, Поставщик: ММК"
    )
    print("Действие записано в журнал аудита")

# Пример 5: Запуск планировщика задач
from utils.scheduler import task_scheduler

def example_scheduler():
    # Запуск планировщика
    task_scheduler.start()
    print("Планировщик задач запущен")
    
    # Остановка планировщика (обычно при завершении приложения)
    # task_scheduler.stop()

# Пример 6: Генерация PDF отчета с QR-кодом
from utils.reports import ReportGenerator
from io import BytesIO

def example_pdf_with_qr():
    try:
        # Создаем отчет по образцу с QR-кодом
        pdf_buffer = ReportGenerator().generate_sample_report_with_qr(sample_id=1)
        
        # Сохраняем в файл
        with open("sample_report_with_qr.pdf", "wb") as f:
            f.write(pdf_buffer.read())
        
        print("PDF отчет с QR-кодом создан: sample_report_with_qr.pdf")
    except Exception as e:
        print(f"Ошибка создания отчета: {e}")

# Пример 7: Работа с REST API (через requests)
import requests

def example_api_usage():
    base_url = "http://localhost:8000"
    
    # Получение списка материалов
    materials_response = requests.get(f"{base_url}/materials")
    if materials_response.status_code == 200:
        materials = materials_response.json()
        print(f"Получено материалов: {len(materials)}")
    
    # Получение PDF отчета по образцу
    try:
        report_response = requests.get(f"{base_url}/sample_report/1")
        if report_response.status_code == 200:
            with open("api_sample_report.pdf", "wb") as f:
                f.write(report_response.content)
            print("PDF отчет получен через API")
    except Exception as e:
        print(f"Ошибка получения отчета через API: {e}")

if __name__ == "__main__":
    print("Примеры использования PPSD:")
    print("1. Генерация QR-кода")
    example_qr_generation()
    
    print("\n2. Экспорт в Excel")
    example_excel_export()
    
    print("\n3. Управление статусами")
    example_status_transition()
    
    print("\n4. Аудит действий")
    example_audit_logging()
    
    print("\n5. PDF отчет с QR-кодом")
    example_pdf_with_qr()
    
    print("\n6. Планировщик задач")
    example_scheduler()
    
    # API примеры требуют запущенного сервера
    # print("\n7. Работа с API")
    # example_api_usage() 