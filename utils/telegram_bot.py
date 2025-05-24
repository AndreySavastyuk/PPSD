"""
Telegram бот для отправки уведомлений ППСД
Отправляет сообщения о результатах ОТК и лабораторных испытаний
"""

import asyncio
import logging
from typing import Optional, List, Dict
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class PPSDTelegramBot:
    """Telegram бот для уведомлений ППСД"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        
        self.logger = logger
        
        # Эмодзи для разных типов сообщений
        self.emojis = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'material': '🔩',
            'test': '🧪',
            'qc': '🔍',
            'approved': '👍',
            'rejected': '👎'
        }
    
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Отправка сообщения в Telegram"""
        if not self.bot or not text:
            return False
        
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            self.logger.warning("Не указан chat_id для отправки сообщения")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=text,
                parse_mode='HTML'
            )
            return True
        except TelegramError as e:
            self.logger.error(f"Ошибка отправки Telegram сообщения: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при отправке: {e}")
            return False
    
    def format_material_info(self, material_data: Dict) -> str:
        """Форматирование информации о материале"""
        return (
            f"{self.emojis['material']} <b>Материал:</b> {material_data.get('grade', 'Н/Д')}\n"
            f"📦 <b>Партия:</b> {material_data.get('batch', 'Н/Д')}\n"
            f"🔥 <b>Плавка:</b> {material_data.get('melt', 'Н/Д')}\n"
            f"🏢 <b>Поставщик:</b> {material_data.get('supplier', 'Н/Д')}\n"
            f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
    
    async def send_qc_approval(self, material_data: Dict, qc_operator: str) -> bool:
        """Отправка уведомления об одобрении ОТК"""
        message = (
            f"{self.emojis['success']} <b>МАТЕРИАЛ ОДОБРЕН ОТК</b>\n\n"
            f"{self.format_material_info(material_data)}\n\n"
            f"{self.emojis['qc']} <b>Сотрудник ОТК:</b> {qc_operator}\n"
            f"{self.emojis['approved']} <b>Статус:</b> Одобрен для использования"
        )
        return await self.send_message(message)
    
    async def send_qc_rejection(self, material_data: Dict, qc_operator: str, defects: List[str]) -> bool:
        """Отправка уведомления об отклонении ОТК с замечаниями"""
        defects_text = "\n".join([f"• {defect}" for defect in defects])
        
        message = (
            f"{self.emojis['error']} <b>МАТЕРИАЛ ОТКЛОНЕН ОТК</b>\n\n"
            f"{self.format_material_info(material_data)}\n\n"
            f"{self.emojis['qc']} <b>Сотрудник ОТК:</b> {qc_operator}\n"
            f"{self.emojis['rejected']} <b>Статус:</b> Отклонен\n\n"
            f"<b>🔍 Список замечаний:</b>\n{defects_text}"
        )
        return await self.send_message(message)
    
    async def send_lab_test_failure(self, material_data: Dict, test_data: Dict, discrepancies: List[str]) -> bool:
        """Отправка уведомления о браке в лаборатории ЦЗЛ"""
        discrepancies_text = "\n".join([f"• {disc}" for disc in discrepancies])
        
        message = (
            f"{self.emojis['error']} <b>БРАК ЛАБОРАТОРИИ ЦЗЛ</b>\n\n"
            f"{self.format_material_info(material_data)}\n\n"
            f"{self.emojis['test']} <b>Тип испытания:</b> {test_data.get('test_type', 'Н/Д')}\n"
            f"🔬 <b>Образец:</b> {test_data.get('sample_code', 'Н/Д')}\n"
            f"👨‍🔬 <b>Инженер ЦЗЛ:</b> {test_data.get('engineer', 'Н/Д')}\n\n"
            f"<b>⚡ Несоответствия:</b>\n{discrepancies_text}"
        )
        return await self.send_message(message)
    
    async def send_final_acceptance(self, material_data: Dict, responsible_person: str, acceptance_type: str = "ППСД") -> bool:
        """Отправка уведомления о окончательной приемке"""
        message = (
            f"{self.emojis['success']} <b>ОКОНЧАТЕЛЬНАЯ ПРИЕМКА {acceptance_type}</b>\n\n"
            f"{self.format_material_info(material_data)}\n\n"
            f"👤 <b>Ответственный:</b> {responsible_person}\n"
            f"{self.emojis['approved']} <b>Статус:</b> Материал принят в эксплуатацию\n"
            f"📋 <b>Заключение:</b> Все проверки пройдены успешно"
        )
        return await self.send_message(message)
    
    async def send_urgent_notification(self, title: str, message: str) -> bool:
        """Отправка срочного уведомления"""
        formatted_message = (
            f"{self.emojis['warning']} <b>СРОЧНОЕ УВЕДОМЛЕНИЕ</b>\n\n"
            f"<b>{title}</b>\n\n"
            f"{message}\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        return await self.send_message(formatted_message)
    
    async def send_status_change(self, material_data: Dict, old_status: str, new_status: str, changed_by: str) -> bool:
        """Отправка уведомления об изменении статуса"""
        message = (
            f"{self.emojis['info']} <b>ИЗМЕНЕНИЕ СТАТУСА МАТЕРИАЛА</b>\n\n"
            f"{self.format_material_info(material_data)}\n\n"
            f"📊 <b>Было:</b> {old_status}\n"
            f"📊 <b>Стало:</b> {new_status}\n"
            f"👤 <b>Изменил:</b> {changed_by}"
        )
        return await self.send_message(message)
    
    def send_message_sync(self, text: str, chat_id: Optional[str] = None) -> bool:
        """Синхронная версия отправки сообщения"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_message(text, chat_id))
        except RuntimeError:
            # Если нет активного event loop, создаем новый
            return asyncio.run(self.send_message(text, chat_id))
    
    def send_qc_approval_sync(self, material_data: Dict, qc_operator: str) -> bool:
        """Синхронная версия отправки одобрения ОТК"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_qc_approval(material_data, qc_operator))
        except RuntimeError:
            return asyncio.run(self.send_qc_approval(material_data, qc_operator))
    
    def send_qc_rejection_sync(self, material_data: Dict, qc_operator: str, defects: List[str]) -> bool:
        """Синхронная версия отправки отклонения ОТК"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_qc_rejection(material_data, qc_operator, defects))
        except RuntimeError:
            return asyncio.run(self.send_qc_rejection(material_data, qc_operator, defects))
    
    def send_lab_test_failure_sync(self, material_data: Dict, test_data: Dict, discrepancies: List[str]) -> bool:
        """Синхронная версия отправки брака лаборатории"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_lab_test_failure(material_data, test_data, discrepancies))
        except RuntimeError:
            return asyncio.run(self.send_lab_test_failure(material_data, test_data, discrepancies))
    
    def send_final_acceptance_sync(self, material_data: Dict, responsible_person: str, acceptance_type: str = "ППСД") -> bool:
        """Синхронная обертка для отправки уведомления о финальном одобрении материала"""
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            return event_loop.run_until_complete(
                self.send_final_acceptance(material_data, responsible_person, acceptance_type)
            )
        finally:
            event_loop.close()

    def send_error_sync(self, error_message: str, error_details: str = None) -> bool:
        """Синхронная обертка для отправки уведомления об ошибке"""
        message = f"⚠️ ОШИБКА: {error_message}"
        if error_details:
            message += f"\n\nДетали: {error_details}"
        
        return self.send_message_sync(message)
    
    def send_system_event_sync(self, event_type: str, details: str = None) -> bool:
        """Синхронная обертка для отправки уведомления о системном событии"""
        event_type_map = {
            "startup": "🟢 Система запущена",
            "shutdown": "🔴 Система остановлена",
            "backup": "💾 Резервное копирование",
            "migration": "🔄 Миграция базы данных",
            "error": "⚠️ Системная ошибка"
        }
        
        title = event_type_map.get(event_type, f"ℹ️ {event_type}")
        message = f"{title}"
        if details:
            message += f"\n\n{details}"
        
        return self.send_message_sync(message)
    
    def send_status_change_notification_sync(self, material_id: int, old_status: str, new_status: str, 
                                          changed_by: str) -> bool:
        """Синхронная функция для отправки уведомления об изменении статуса материала"""
        from models.models import MaterialStatus
        from utils.material_utils import get_status_display_name
        
        old_status_display = get_status_display_name(old_status)
        new_status_display = get_status_display_name(new_status)
        
        message = f"🔄 Изменение статуса материала #{material_id}\n\n"
        message += f"Старый статус: {old_status_display}\n"
        message += f"Новый статус: {new_status_display}\n"
        message += f"Изменил: {changed_by}"
        
        return self.send_message_sync(message)

# Глобальный экземпляр бота
telegram_bot = PPSDTelegramBot()

def send_qc_approval_notification(material_data: Dict, qc_operator: str) -> bool:
    """Отправить уведомление об одобрении материала ОТК"""
    return telegram_bot.send_qc_approval_sync(material_data, qc_operator)

def send_qc_rejection_notification(material_data: Dict, qc_operator: str, defects: List[str]) -> bool:
    """Отправить уведомление о забраковке материала ОТК"""
    return telegram_bot.send_qc_rejection_sync(material_data, qc_operator, defects)

def send_lab_test_failure_notification(material_data: Dict, test_data: Dict, discrepancies: List[str]) -> bool:
    """Отправить уведомление о негативных результатах лабораторных испытаний"""
    return telegram_bot.send_lab_test_failure_sync(material_data, test_data, discrepancies)

def send_final_acceptance_notification(material_data: Dict, responsible_person: str, acceptance_type: str = "ППСД") -> bool:
    """Отправить уведомление о финальном одобрении материала"""
    return telegram_bot.send_final_acceptance_sync(material_data, responsible_person, acceptance_type)

def send_error_notification(error_message: str, error_details: str = None) -> bool:
    """Отправить уведомление об ошибке"""
    return telegram_bot.send_error_sync(error_message, error_details)

def send_system_event_notification(event_type: str, details: str = None) -> bool:
    """Отправить уведомление о системном событии"""
    return telegram_bot.send_system_event_sync(event_type, details)

def send_status_change_notification(material_id: int, old_status: str, new_status: str, changed_by: str) -> bool:
    """Отправить уведомление об изменении статуса материала"""
    return telegram_bot.send_status_change_notification_sync(material_id, old_status, new_status, changed_by)

# Примеры использования
def send_qc_approval_notification(material):
    """Отправка уведомления о положительном результате проверки ОТК"""
    from database.connection import SessionLocal
    db = SessionLocal()
    try:
        # Формируем минимальные данные для уведомления
        material_data = {
            "id": material.id,
            "material_grade": material.material_grade,
            "batch_number": material.batch_number,
            "melt_number": material.melt_number
        }
        
        # Получаем имя пользователя
        user = db.query(User).filter(User.id == material.created_by_id).first()
        operator_name = user.full_name if user else "Неизвестный пользователь"
        
        send_qc_approval_notification(material_data, operator_name)
    finally:
        db.close()

def send_qc_rejection_notification(material, comment=None):
    """Отправка уведомления о негативном результате проверки ОТК"""
    material_data = {
        "id": material.id,
        "material_grade": material.material_grade,
        "batch_number": material.batch_number or "Нет",
        "melt_number": material.melt_number
    }
    
    defects = ["Несоответствие сертификата"]
    if comment:
        defects.append(comment)
    
    send_qc_rejection_notification(material_data, "Инспектор ОТК", defects)

def send_lab_test_failure_notification(material, comment=None):
    """Отправка уведомления о негативном результате лабораторных испытаний"""
    material_data = {
        "id": material.id,
        "material_grade": material.material_grade,
        "batch_number": material.batch_number or "Нет",
        "melt_number": material.melt_number
    }
    
    test_data = {"test_type": "Химический анализ"}
    discrepancies = ["Несоответствие химического состава"]
    if comment:
        discrepancies.append(comment)
    
    send_lab_test_failure_notification(material_data, test_data, discrepancies)

def send_final_acceptance_notification(material):
    """Отправка уведомления о финальном одобрении материала"""
    material_data = {
        "id": material.id,
        "material_grade": material.material_grade,
        "batch_number": material.batch_number or "Нет",
        "melt_number": material.melt_number
    }
    
    send_final_acceptance_notification(material_data, "Инспектор ЦЗЛ") 