import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from database.connection import Base

class UserRole(enum.Enum):
    ADMIN = "admin"           # Администратор
    WAREHOUSE = "warehouse"   # Кладовщик
    QC = "qc"                 # Сотрудник ОТК
    LAB = "lab"               # Инженер ЦЗЛ
    PRODUCTION = "production" # Производство

class MaterialType(enum.Enum):
    SHEET = "sheet"           # Лист
    PIPE = "pipe"             # Труба
    ROD = "rod"               # Пруток
    ANGLE = "angle"           # Уголок
    CHANNEL = "channel"       # Швеллер
    OTHER = "other"           # Другое

class MaterialStatus(enum.Enum):
    RECEIVED = "received"          # Принят на склад
    PENDING_QC = "pending_qc"      # Ожидает проверки ОТК
    QC_PASSED = "qc_passed"        # Проверка ОТК пройдена
    QC_FAILED = "qc_failed"        # Проверка ОТК не пройдена
    QC_CHECKED = "qc_checked"      # Проверен ОТК (общий статус)
    QC_CHECK_PENDING = "qc_check_pending"  # Ожидает проверки ОТК (альтернативное название)
    LAB_TESTING = "lab_testing"    # На лабораторных испытаниях
    LAB_CHECK_PENDING = "lab_check_pending"  # Ожидает проверки в лаборатории
    SAMPLES_REQUESTED = "samples_requested"  # Запрошены образцы
    SAMPLES_COLLECTED = "samples_collected"  # Образцы отобраны
    TESTING = "testing"            # На испытаниях
    TESTING_COMPLETED = "testing_completed"  # Испытания завершены
    APPROVED = "approved"          # Одобрен
    READY_FOR_USE = "ready_for_use"  # Готов к использованию
    IN_USE = "in_use"              # В производстве
    REJECTED = "rejected"          # Забракован
    ARCHIVED = "archived"          # В архиве
    EDIT_REQUESTED = "edit_requested"  # Запрос на редактирование

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    telegram_id = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Разрешения для пользователя
    can_edit = Column(Boolean, default=False)
    can_view = Column(Boolean, default=True)
    can_delete = Column(Boolean, default=False)
    can_admin = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Отношения
    material_entries = relationship("MaterialEntry", back_populates="created_by_user")
    qc_checks = relationship("QCCheck", back_populates="checked_by_user")
    sample_requests = relationship("SampleRequest", back_populates="created_by_user", foreign_keys="SampleRequest.created_by_id")
    manufactured_sample_requests = relationship("SampleRequest", foreign_keys="SampleRequest.manufactured_by_id")
    lab_tests = relationship("LabTest", back_populates="performed_by_user")
    samples = relationship("Sample", back_populates="created_by_user")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_direct = Column(Boolean, default=True)  # Прямой или непрямой поставщик
    address = Column(String(200), nullable=True)
    contact_info = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Отношения
    material_entries = relationship("MaterialEntry", back_populates="supplier")

class MaterialGrade(Base):
    __tablename__ = "material_grades"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # Марка
    standard = Column(String(50), nullable=True)            # Стандарт
    density = Column(Float, nullable=True)                  # Плотность, кг/м3
    note = Column(String(200), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Отношения
    material_entries = relationship("MaterialEntry", back_populates="grade_ref")

class ProductType(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # Вид проката
    note = Column(String(200), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Отношения
    material_entries = relationship("MaterialEntry", back_populates="type_ref")

class TestType(Base):
    __tablename__ = "test_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Название испытания
    code = Column(String(20), unique=True, nullable=False)   # Код испытания
    description = Column(Text, nullable=True)                # Описание испытания
    standard = Column(String(100), nullable=True)            # Стандарт/ГОСТ/методика
    equipment = Column(String(200), nullable=True)           # Используемое оборудование
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Отношения
    lab_tests = relationship("LabTest", back_populates="test_type_ref")

class MaterialSize(Base):
    __tablename__ = "material_sizes"
    id = Column(Integer, primary_key=True, index=True)
    material_entry_id = Column(Integer, ForeignKey("material_entries.id"), nullable=False)
    length = Column(Float, nullable=False)  # мм
    quantity = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Отношения
    material_entry = relationship("MaterialEntry", back_populates="sizes")

class MaterialEntry(Base):
    __tablename__ = "material_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация о материале
    material_grade = Column(String(50), nullable=False)  # Марка материала
    material_type = Column(String(20), nullable=False)   # Вид проката (enum)
    
    # Размеры в зависимости от типа материала
    # Для листов: thickness, width, length
    # Для труб: diameter, wall_thickness, length
    # Для прутков: diameter, length
    thickness = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    diameter = Column(Float, nullable=True)
    wall_thickness = Column(Float, nullable=True)
    
    quantity = Column(Float, nullable=False)  # Количество
    unit = Column(String(10), default="кг")   # Единица измерения
    
    # Информация о сертификатах
    certificate_number = Column(String(100), nullable=False)
    certificate_date = Column(DateTime, nullable=True)  # Дата сертификата
    batch_number = Column(String(100), nullable=True)   # Теперь необязательное поле
    melt_number = Column(String(100), nullable=False)
    no_melt_number = Column(Boolean, default=False)     # Флаг "нет номера плавки"
    
    # Информация о заказе
    order_number = Column(String(100), nullable=True)
    
    # Пути к файлам
    certificate_file_path = Column(String(255), nullable=True)
    
    # Статус и флаги
    status = Column(String(30), default=MaterialStatus.RECEIVED.value)
    requires_lab_verification = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    edit_requested = Column(Boolean, default=False)  # Запрос на редактирование
    edit_comment = Column(String(255), nullable=True)  # Комментарий к запросу на редактирование
    
    # Foreign keys
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Отношения
    supplier = relationship("Supplier", back_populates="material_entries")
    created_by_user = relationship("User", back_populates="material_entries")
    qc_check = relationship("QCCheck", back_populates="material_entry", uselist=False)
    sample_requests = relationship("SampleRequest", back_populates="material_entry")
    lab_tests = relationship("LabTest", back_populates="material_entry")
    
    # В MaterialEntry добавим связи:
    # grade_id, type_id, sizes
    grade_id = Column(Integer, ForeignKey("material_grades.id"), nullable=True)
    type_id = Column(Integer, ForeignKey("product_types.id"), nullable=True)
    grade_ref = relationship("MaterialGrade", back_populates="material_entries")
    type_ref = relationship("ProductType", back_populates="material_entries")
    sizes = relationship("MaterialSize", back_populates="material_entry", cascade="all, delete-orphan")

class QCCheck(Base):
    __tablename__ = "qc_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    material_entry_id = Column(Integer, ForeignKey("material_entries.id"), nullable=False)
    checked_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Результаты проверки ОТК
    certificate_readable = Column(Boolean, default=False)
    material_matches = Column(Boolean, default=False)
    dimensions_match = Column(Boolean, default=False)
    certificate_data_correct = Column(Boolean, default=False)
    
    # Химический состав из сертификата (%)
    chem_c = Column(Float, nullable=True)  # Углерод
    chem_si = Column(Float, nullable=True)  # Кремний
    chem_mn = Column(Float, nullable=True)  # Марганец
    chem_s = Column(Float, nullable=True)  # Сера
    chem_p = Column(Float, nullable=True)  # Фосфор
    chem_cr = Column(Float, nullable=True)  # Хром
    chem_ni = Column(Float, nullable=True)  # Никель
    chem_cu = Column(Float, nullable=True)  # Медь
    chem_ti = Column(Float, nullable=True)  # Титан
    chem_al = Column(Float, nullable=True)  # Алюминий
    chem_mo = Column(Float, nullable=True)  # Молибден
    chem_v = Column(Float, nullable=True)  # Ванадий
    chem_nb = Column(Float, nullable=True)  # Ниобий
    
    # Замечания
    issue_repurchase = Column(Boolean, default=False)  # Перекуп
    issue_poor_quality = Column(Boolean, default=False)  # Плохое качество сертификата
    issue_no_stamp = Column(Boolean, default=False)  # Нет печати
    issue_diameter_deviation = Column(Boolean, default=False)  # Отклонение по диаметру
    issue_cracks = Column(Boolean, default=False)  # Трещины
    issue_no_melt = Column(Boolean, default=False)  # Не набита плавка
    issue_no_certificate = Column(Boolean, default=False)  # Нет сертификата
    issue_copy = Column(Boolean, default=False)  # Копия (без синей печати)
    
    # Нужна ли проверка в лаборатории
    requires_lab_verification = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # Отношения
    material_entry = relationship("MaterialEntry", back_populates="qc_check")
    checked_by_user = relationship("User", back_populates="qc_checks")

class SampleRequest(Base):
    __tablename__ = "sample_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    material_entry_id = Column(Integer, ForeignKey("material_entries.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Параметры запроса на пробы
    sample_size = Column(Float, nullable=False)
    sample_unit = Column(String(10), default="шт")
    sample_description = Column(Text, nullable=True)
    
    # Информация о месте отбора пробы
    sample_location = Column(String(100), nullable=True)  # Например, "С торца", "Из середины листа"
    sample_cutting_scheme = Column(String(255), nullable=True)  # Ссылка на схему разделки или описание
    
    # Информация об изготовлении образцов
    manufactured_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто изготовил образцы
    manufacturing_notes = Column(Text, nullable=True)  # Примечания по изготовлению
    
    # Список тестов, которые нужно провести
    mechanical_test = Column(Boolean, default=False)  # Механические испытания
    chemical_test = Column(Boolean, default=False)    # Химический анализ
    metallographic_test = Column(Boolean, default=False) # Металлографический анализ
    
    # Статус
    is_collected = Column(Boolean, default=False)
    is_sent_to_lab = Column(Boolean, default=False)
    
    request_pdf_path = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    collected_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    # Отношения
    material_entry = relationship("MaterialEntry", back_populates="sample_requests")
    created_by_user = relationship("User", back_populates="sample_requests", foreign_keys=[created_by_id])
    manufactured_by_user = relationship("User", foreign_keys=[manufactured_by_id], overlaps="manufactured_sample_requests")
    samples = relationship("Sample", back_populates="sample_request", cascade="all, delete-orphan")

class Sample(Base):
    """Модель для хранения информации об отдельных образцах"""
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    sample_request_id = Column(Integer, ForeignKey("sample_requests.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто создал образец
    
    # Идентификация образца
    sample_code = Column(String(50), nullable=False, unique=True)  # Уникальный код образца
    sample_type = Column(String(50), nullable=False)  # Тип образца (например, "Растяжение", "Удар", "Химия")
    
    # Размеры образца
    length = Column(Float, nullable=True)  # Длина, мм
    width = Column(Float, nullable=True)   # Ширина, мм
    thickness = Column(Float, nullable=True)  # Толщина, мм
    diameter = Column(Float, nullable=True)  # Диаметр (для круглых образцов), мм
    
    # Место отбора
    location_description = Column(String(200), nullable=True)  # Описание места отбора
    
    # Статус образца
    status = Column(String(30), default="created")  # created, prepared, testing, tested, archived
    
    # Дополнительная информация
    notes = Column(Text, nullable=True)
    photo_path = Column(String(255), nullable=True)  # Путь к фото образца
    
    # Даты
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    prepared_at = Column(DateTime, nullable=True)  # Когда образец был подготовлен
    tested_at = Column(DateTime, nullable=True)    # Когда образец был испытан
    
    is_deleted = Column(Boolean, default=False)
    
    # Отношения
    sample_request = relationship("SampleRequest", back_populates="samples")
    created_by_user = relationship("User", back_populates="samples")
    lab_tests = relationship("LabTestSample", back_populates="sample")

class LabTestSample(Base):
    """Связующая таблица между испытаниями и образцами"""
    __tablename__ = "lab_test_samples"
    
    id = Column(Integer, primary_key=True, index=True)
    lab_test_id = Column(Integer, ForeignKey("lab_tests.id"), nullable=False)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    
    # Результаты для конкретного образца
    individual_result = Column(Text, nullable=True)
    individual_passed = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Отношения
    lab_test = relationship("LabTest", back_populates="test_samples")
    sample = relationship("Sample", back_populates="lab_tests")

class LabTest(Base):
    __tablename__ = "lab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    material_entry_id = Column(Integer, ForeignKey("material_entries.id"), nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Тип теста
    test_type = Column(String(30), nullable=False)  # mechanical, chemical, metallographic
    
    # Связь с справочником видов испытаний
    test_type_id = Column(Integer, ForeignKey("test_types.id"), nullable=True)
    
    # Результаты
    results = Column(Text, nullable=True)
    is_passed = Column(Boolean, nullable=True)  # Null = не завершен, True = годно, False = брак
    
    report_file_path = Column(String(255), nullable=True)
    
    performed_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    # Отношения
    material_entry = relationship("MaterialEntry", back_populates="lab_tests")
    performed_by_user = relationship("User", back_populates="lab_tests")
    test_type_ref = relationship("TestType", back_populates="lab_tests")
    test_samples = relationship("LabTestSample", back_populates="lab_test", cascade="all, delete-orphan") 