"""
Скрипт для инициализации базы данных с тестовыми данными
"""
import os
import sys
import datetime

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import Base, engine, SessionLocal
from models.models import *
import bcrypt

def init_database():
    """Инициализация базы данных"""
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Проверяем, есть ли пользователи в базе
    users_count = db.query(User).count()
    if users_count > 0:
        print(f"В базе данных уже есть {users_count} пользователя(ей). Пропускаем создание администратора.")
        db.close()
        return
    
    # Создаем администратора
    admin_password = "admin"
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin = User(
        username="admin",
        password_hash=hashed_password,
        full_name="Администратор системы",
        role="admin",
        can_edit=True,
        can_view=True,
        can_delete=True,
        can_admin=True
    )
    db.add(admin)
    
    # Создаем тестовых пользователей
    warehouse_user = User(
        username="warehouse",
        password_hash=hashed_password,
        full_name="Кладовщик",
        role="warehouse",
        can_edit=True,
        can_view=True,
        can_delete=False,
        can_admin=False
    )
    db.add(warehouse_user)
    
    qc_user = User(
        username="qc",
        password_hash=hashed_password,
        full_name="Сотрудник ОТК",
        role="qc",
        can_edit=True,
        can_view=True,
        can_delete=False,
        can_admin=False
    )
    db.add(qc_user)
    
    lab_user = User(
        username="lab",
        password_hash=hashed_password,
        full_name="Инженер ЦЗЛ",
        role="lab",
        can_edit=True,
        can_view=True,
        can_delete=False,
        can_admin=False
    )
    db.add(lab_user)
    
    # Сохраняем пользователей
    db.commit()
    print("Пользователи созданы")
    
    # Создаем тестовых поставщиков
    suppliers = [
        Supplier(name="ММК", is_direct=True, address="г. Магнитогорск"),
        Supplier(name="НЛМК", is_direct=True, address="г. Липецк"),
        Supplier(name="Северсталь", is_direct=True, address="г. Череповец"),
        Supplier(name="ОМК", is_direct=True, address="г. Выкса"),
        Supplier(name="ТД Металлтрейд", is_direct=False, address="г. Санкт-Петербург")
    ]
    
    for supplier in suppliers:
        db.add(supplier)
    
    db.commit()
    print("Поставщики созданы")
    
    # Создаем марки материалов
    material_grades = [
        MaterialGrade(name="08Х18Н10Т", standard="ГОСТ 5632-2014", density=7900),
        MaterialGrade(name="12Х18Н10Т", standard="ГОСТ 5632-2014", density=7900),
        MaterialGrade(name="10Х17Н13М2Т", standard="ГОСТ 5632-2014", density=7900),
        MaterialGrade(name="Ст3сп", standard="ГОСТ 380-2005", density=7850),
        MaterialGrade(name="09Г2С", standard="ГОСТ 19281-2014", density=7850)
    ]
    
    for grade in material_grades:
        db.add(grade)
    
    db.commit()
    print("Марки материалов созданы")
    
    # Создаем виды проката
    product_types = [
        ProductType(name="Круг"),
        ProductType(name="Лист"),
        ProductType(name="Труба"),
        ProductType(name="Уголок"),
        ProductType(name="Швеллер")
    ]
    
    for product_type in product_types:
        db.add(product_type)
    
    db.commit()
    print("Виды проката созданы")
    
    # Создаем типы испытаний
    test_types = [
        TestType(name="Испытание на растяжение", code="GOST1497", 
                standard="ГОСТ 1497-84", equipment="Разрывная машина ИР-5082"),
        TestType(name="Испытание на твердость по Бринеллю", code="GOST9012", 
                standard="ГОСТ 9012-59", equipment="Твердомер ТБ-5006"),
        TestType(name="Спектральный анализ", code="SPECTRAL", 
                standard="ГОСТ 18895-97", equipment="Спектрометр SPECTROMAXx"),
        TestType(name="Ударная вязкость", code="GOST9454", 
                standard="ГОСТ 9454-78", equipment="Маятниковый копер КМ-300")
    ]
    
    for test_type in test_types:
        db.add(test_type)
    
    db.commit()
    print("Типы испытаний созданы")
    
    # Создаем тестовые материалы
    materials = [
        MaterialEntry(
            material_grade="08Х18Н10Т",
            material_type="rod",
            diameter=12.5,
            quantity=100,
            unit="кг",
            certificate_number="45612",
            certificate_date=datetime.datetime(2023, 5, 15),
            batch_number="9888989",
            melt_number="562221",
            order_number="2023-023",
            supplier_id=1,
            created_by_id=2,
            status=MaterialStatus.RECEIVED.value,
            grade_id=1,
            type_id=1
        ),
        MaterialEntry(
            material_grade="12Х18Н10Т",
            material_type="sheet",
            thickness=3.0,
            width=1000,
            length=2000,
            quantity=200,
            unit="кг",
            certificate_number="78945",
            certificate_date=datetime.datetime(2023, 6, 10),
            batch_number="L789456",
            melt_number="745236",
            order_number="2023-045",
            supplier_id=2,
            created_by_id=2,
            status=MaterialStatus.RECEIVED.value,
            grade_id=2,
            type_id=2
        )
    ]
    
    for material in materials:
        db.add(material)
    
    db.commit()
    print("Тестовые материалы созданы")
    
    # Закрываем сессию
    db.close()
    print("Инициализация базы данных завершена успешно")

if __name__ == "__main__":
    print("Запуск инициализации базы данных...")
    init_database()
    print("Инициализация завершена.") 