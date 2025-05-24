import os
import bcrypt
from sqlalchemy.orm import Session
from database.connection import engine, SessionLocal, Base
from models.models import User, UserRole, Supplier, TestType
from database.migrate_db import migrate_database
from sqlalchemy import Table, Column, Integer, String, DateTime, Text, MetaData

def init_database():
    """
    Initialize the database by creating all tables and adding default data.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Run migrations
    migrate_database()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if we need to create default admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Create default admin user
            password_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                username="admin",
                password_hash=password_hash,
                full_name="Администратор системы",
                role=UserRole.ADMIN.value,
                can_edit=True,
                can_view=True,
                can_delete=True,
                can_admin=True
            )
            db.add(admin_user)
        
        # Add default users for each role if they don't exist
        roles_to_create = [
            {
                "username": "warehouse",
                "password": "warehouse",
                "full_name": "Кладовщик",
                "role": UserRole.WAREHOUSE.value,
                "can_edit": True,
                "can_view": True
            },
            {
                "username": "qc",
                "password": "qc",
                "full_name": "Сотрудник ОТК",
                "role": UserRole.QC.value,
                "can_edit": True,
                "can_view": True
            },
            {
                "username": "lab",
                "password": "lab",
                "full_name": "Инженер ЦЗЛ",
                "role": UserRole.LAB.value,
                "can_edit": True,
                "can_view": True
            },
        ]
        
        for user_data in roles_to_create:
            user = db.query(User).filter(User.username == user_data["username"]).first()
            if not user:
                password_hash = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                new_user = User(
                    username=user_data["username"],
                    password_hash=password_hash,
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    can_edit=user_data["can_edit"],
                    can_view=user_data["can_view"],
                )
                db.add(new_user)
        
        # Add some example suppliers if they don't exist
        example_suppliers = [
            {"name": "ММК", "is_direct": True},
            {"name": "НЛМК", "is_direct": True},
            {"name": "Северсталь", "is_direct": True},
            {"name": "ТМК", "is_direct": True},
            {"name": "ОМЗ", "is_direct": True},
            {"name": "Металлторг", "is_direct": False},
        ]
        
        for supplier_data in example_suppliers:
            supplier = db.query(Supplier).filter(Supplier.name == supplier_data["name"]).first()
            if not supplier:
                new_supplier = Supplier(
                    name=supplier_data["name"],
                    is_direct=supplier_data["is_direct"],
                )
                db.add(new_supplier)
        
        # Add basic test types if they don't exist
        example_test_types = [
            {
                "name": "Испытание на растяжение", 
                "code": "MECH-TENS",
                "standard": "ГОСТ 1497-84",
                "equipment": "Разрывная машина ИР-5082",
                "description": "Испытание на растяжение образцов для определения механических свойств: предел текучести, предел прочности, относительное удлинение."
            },
            {
                "name": "Испытание на твердость по Бринеллю", 
                "code": "MECH-HB",
                "standard": "ГОСТ 9012-59",
                "equipment": "Твердомер ТБ-5004",
                "description": "Определение твердости металла методом вдавливания стального шарика."
            },
            {
                "name": "Испытание на ударную вязкость", 
                "code": "MECH-IMP",
                "standard": "ГОСТ 9454-78",
                "equipment": "Маятниковый копер КМ-30",
                "description": "Определение ударной вязкости при динамическом изгибе образца с надрезом."
            },
            {
                "name": "Спектральный анализ", 
                "code": "CHEM-SPEC",
                "standard": "ГОСТ 18895-97",
                "equipment": "Спектрометр SPECTROMAXx",
                "description": "Определение химического состава материала методом оптико-эмиссионной спектрометрии."
            },
            {
                "name": "Анализ содержания углерода", 
                "code": "CHEM-C",
                "standard": "ГОСТ 12344-2003",
                "equipment": "Анализатор CS-230",
                "description": "Определение массовой доли углерода методом ИК-абсорбции."
            },
            {
                "name": "Анализ макроструктуры", 
                "code": "MET-MACRO",
                "standard": "ГОСТ 10243-75",
                "equipment": "Металлографический микроскоп MET-2",
                "description": "Анализ макроструктуры металла для выявления дефектов: неоднородность, ликвация, пористость."
            },
            {
                "name": "Анализ микроструктуры", 
                "code": "MET-MICRO",
                "standard": "ГОСТ 5639-82",
                "equipment": "Металлографический микроскоп MET-2",
                "description": "Анализ микроструктуры для выявления структурных составляющих, определения размера зерна."
            },
        ]
        
        for test_type_data in example_test_types:
            test_type = db.query(TestType).filter(TestType.code == test_type_data["code"]).first()
            if not test_type:
                new_test_type = TestType(
                    name=test_type_data["name"],
                    code=test_type_data["code"],
                    standard=test_type_data["standard"],
                    equipment=test_type_data["equipment"],
                    description=test_type_data["description"]
                )
                db.add(new_test_type)
        
        # Commit changes
        db.commit()
    
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()

def create_audit_log_table(engine):
    metadata = MetaData()
    Table(
        'audit_log', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, nullable=False),
        Column('action', String(128), nullable=False),
        Column('details', Text),
        Column('timestamp', DateTime, nullable=False)
    )
    metadata.create_all(engine)

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.") 