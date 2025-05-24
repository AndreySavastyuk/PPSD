import openpyxl
from openpyxl.styles import Font
from database.connection import SessionLocal
from models.models import MaterialEntry, Supplier, MaterialStatus
from datetime import datetime

def export_materials_to_excel(filename: str, start_date: datetime = None, end_date: datetime = None) -> str:
    """
    Экспортирует список материалов в Excel-файл.
    Args:
        filename: Имя файла для сохранения (xlsx)
        start_date: Начальная дата (по умолчанию месяц назад)
        end_date: Конечная дата (по умолчанию сегодня)
    Returns:
        Путь к сохраненному файлу
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Материалы"
    # Заголовки
    headers = [
        "ID", "Марка", "Плавка", "Поставщик", "Статус", "Дата создания"
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    # Данные
    db = SessionLocal()
    try:
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            from datetime import timedelta
            start_date = end_date - timedelta(days=30)
        materials = db.query(MaterialEntry).filter(
            MaterialEntry.created_at.between(start_date, end_date),
            MaterialEntry.is_deleted == False
        ).all()
        for m in materials:
            ws.append([
                m.id,
                m.material_grade,
                m.melt_number,
                m.supplier.name if m.supplier else "-",
                m.status,
                m.created_at.strftime('%d.%m.%Y') if m.created_at else ""
            ])
    finally:
        db.close()
    wb.save(filename)
    return filename

# Пример использования
if __name__ == "__main__":
    out_file = "materials_export.xlsx"
    path = export_materials_to_excel(out_file)
    print(f"Экспортировано: {path}") 