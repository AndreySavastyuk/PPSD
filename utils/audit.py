"""
Модуль для аудита действий пользователей и системных событий.
Записывает все действия в базу данных для последующего анализа.
"""

import logging
import datetime
import traceback
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base, SessionLocal
from typing import Optional, Dict, Any, Union

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Добавляем обработчик для вывода в файл
file_handler = logging.FileHandler('logs/audit.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class AuditLog(Base):
    """Модель для хранения аудита в базе данных"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Отношения
    user = relationship("User", backref="audit_logs")

def log_action(user_id: Optional[int], action: str, details: Optional[str] = None) -> None:
    """
    Записывает действие пользователя в журнал аудита
    
    Args:
        user_id: ID пользователя (может быть None для системных действий)
        action: Название действия (например, "login", "create_material", "edit_material")
        details: Дополнительные детали (например, ID материала, описание действия)
    """
    try:
        db = SessionLocal()
        audit_entry = AuditLog(user_id=user_id, action=action, details=details)
        db.add(audit_entry)
        db.commit()
        logger.info(f"Audit: User {user_id} - {action} - {details}")
    except Exception as e:
        logger.error(f"Failed to log audit entry: {str(e)}")
    finally:
        db.close()

def log_material_action(user_id: int, action: str, material_id: int, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Записывает действие пользователя с материалом
    
    Args:
        user_id: ID пользователя
        action: Тип действия (create, edit, delete, status_change)
        material_id: ID материала
        data: Дополнительные данные о действии
    """
    details = f"Material ID: {material_id}"
    if data:
        # Добавляем информацию о изменениях или другие данные
        details += f", Data: {str(data)}"
    
    log_action(user_id, f"material_{action}", details)

def log_qc_action(user_id: int, action: str, material_id: int, qc_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Записывает действие ОТК
    
    Args:
        user_id: ID пользователя (сотрудника ОТК)
        action: Тип действия (check, approve, reject)
        material_id: ID материала
        qc_data: Данные проверки ОТК
    """
    details = f"Material ID: {material_id}"
    if qc_data:
        # Добавляем информацию о проверке
        details += f", QC Data: {str(qc_data)}"
    
    log_action(user_id, f"qc_{action}", details)

def log_lab_action(user_id: int, action: str, material_id: int, sample_id: Optional[int] = None, 
                  test_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Записывает действие лаборатории
    
    Args:
        user_id: ID пользователя (инженера ЦЗЛ)
        action: Тип действия (sample_request, sample_collect, test_start, test_complete)
        material_id: ID материала
        sample_id: ID образца (если применимо)
        test_data: Данные испытания
    """
    details = f"Material ID: {material_id}"
    if sample_id:
        details += f", Sample ID: {sample_id}"
    if test_data:
        details += f", Test Data: {str(test_data)}"
    
    log_action(user_id, f"lab_{action}", details)

def log_status_change(user_id: int, material_id: int, old_status: str, new_status: str) -> None:
    """
    Записывает изменение статуса материала
    
    Args:
        user_id: ID пользователя
        material_id: ID материала
        old_status: Предыдущий статус
        new_status: Новый статус
    """
    details = f"Material ID: {material_id}, Old Status: {old_status}, New Status: {new_status}"
    log_action(user_id, "status_change", details)

def log_error(error: Exception, user_id: Optional[int] = None, context: Optional[str] = None) -> None:
    """
    Записывает ошибку в журнал аудита
    
    Args:
        error: Объект исключения
        user_id: ID пользователя (если доступен)
        context: Контекст, в котором произошла ошибка
    """
    error_type = type(error).__name__
    error_message = str(error)
    stack_trace = traceback.format_exc()
    
    details = f"Error Type: {error_type}, Message: {error_message}"
    if context:
        details += f", Context: {context}"
    details += f"\nStack Trace: {stack_trace}"
    
    log_action(user_id, "error", details)
    logger.error(f"Error logged: {error_type} - {error_message} (User: {user_id})")

def log_login_attempt(username: str, success: bool, ip_address: Optional[str] = None) -> None:
    """
    Записывает попытку входа в систему
    
    Args:
        username: Имя пользователя
        success: Успешная попытка или нет
        ip_address: IP-адрес, с которого выполнялась попытка
    """
    details = f"Username: {username}, Success: {success}"
    if ip_address:
        details += f", IP: {ip_address}"
    
    log_action(None, "login_attempt", details)
    
    if not success:
        logger.warning(f"Failed login attempt for user {username} from IP {ip_address}")

def log_data_export(user_id: int, export_type: str, data_description: str) -> None:
    """
    Записывает экспорт данных
    
    Args:
        user_id: ID пользователя
        export_type: Тип экспорта (excel, pdf, csv)
        data_description: Описание экспортируемых данных
    """
    details = f"Export Type: {export_type}, Data: {data_description}"
    log_action(user_id, "data_export", details)

def log_system_event(event_type: str, details: Optional[str] = None) -> None:
    """
    Записывает системное событие
    
    Args:
        event_type: Тип события (startup, shutdown, backup, etc)
        details: Дополнительные детали
    """
    log_action(None, f"system_{event_type}", details)
    logger.info(f"System event: {event_type} - {details}")

def get_user_audit_history(user_id: int, limit: int = 100) -> list:
    """
    Получает историю действий пользователя
    
    Args:
        user_id: ID пользователя
        limit: Максимальное количество записей
        
    Returns:
        list: Список записей аудита
    """
    db = SessionLocal()
    try:
        audit_entries = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return audit_entries
    finally:
        db.close()

def get_material_audit_history(material_id: int, limit: int = 100) -> list:
    """
    Получает историю действий с материалом
    
    Args:
        material_id: ID материала
        limit: Максимальное количество записей
        
    Returns:
        list: Список записей аудита
    """
    db = SessionLocal()
    try:
        # Ищем записи, где в деталях упоминается ID материала
        material_id_str = f"Material ID: {material_id}"
        audit_entries = db.query(AuditLog).filter(
            AuditLog.details.like(f"%{material_id_str}%")
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return audit_entries
    finally:
        db.close()

def get_recent_activity(limit: int = 100) -> list:
    """
    Получает последние действия в системе
    
    Args:
        limit: Максимальное количество записей
        
    Returns:
        list: Список записей аудита
    """
    db = SessionLocal()
    try:
        audit_entries = db.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        return audit_entries
    finally:
        db.close()

def search_audit_log(query: str, limit: int = 100) -> list:
    """
    Поиск в журнале аудита
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество записей
        
    Returns:
        list: Список записей аудита
    """
    db = SessionLocal()
    try:
        audit_entries = db.query(AuditLog).filter(
            AuditLog.details.like(f"%{query}%") | AuditLog.action.like(f"%{query}%")
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return audit_entries
    finally:
        db.close() 