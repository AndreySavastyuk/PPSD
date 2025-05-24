"""
Модуль для отправки уведомлений пользователям
Поддерживает Telegram и внутренние уведомления
"""
import os
import logging
from typing import List, Optional
from datetime import datetime

import telegram
from telegram import Bot
from telegram.error import TelegramError

from database.connection import SessionLocal
from models.models import User, MaterialEntry, MaterialStatus, UserRole

# Настройка логгера
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """Инициализация сервиса уведомлений"""
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot = None
        
        if self.telegram_bot_token:
            try:
                self.bot = Bot(token=self.telegram_bot_token)
                logger.info("Telegram бот успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации Telegram бота: {e}")
                self.bot = None
    
    def send_telegram_message(self, telegram_id: str, message: str) -> bool:
        """
        Отправить сообщение через Telegram
        
        Args:
            telegram_id: Telegram ID пользователя
            message: Текст сообщения
        
        Returns:
            True если сообщение отправлено успешно
        """
        if not self.bot or not telegram_id:
            return False
        
        try:
            self.bot.send_message(chat_id=telegram_id, text=message, parse_mode='HTML')
            logger.info(f"Telegram сообщение отправлено пользователю {telegram_id}")
            return True
        except TelegramError as e:
            logger.error(f"Ошибка отправки Telegram сообщения: {e}")
            return False
    
    def notify_status_change(self, material_id: int, old_status: str, new_status: str):
        """
        Уведомить соответствующих пользователей об изменении статуса материала
        
        Args:
            material_id: ID материала
            old_status: Предыдущий статус
            new_status: Новый статус
        """
        db = SessionLocal()
        try:
            # Получаем информацию о материале
            material = db.query(MaterialEntry).filter(
                MaterialEntry.id == material_id
            ).first()
            
            if not material:
                return
            
            # Определяем, кого нужно уведомить
            notify_roles = []
            
            if new_status == MaterialStatus.QC_CHECK_PENDING.value:
                notify_roles = [UserRole.QC.value]
                message = f"🔔 <b>Новый материал для проверки ОТК</b>\n\n" \
                         f"Марка: {material.material_grade}\n" \
                         f"Плавка: {material.melt_number}\n" \
                         f"Поставщик: {material.supplier.name}"
            
            elif new_status == MaterialStatus.LAB_CHECK_PENDING.value:
                notify_roles = [UserRole.LAB.value]
                message = f"🔬 <b>Новый материал для проверки в лаборатории</b>\n\n" \
                         f"Марка: {material.material_grade}\n" \
                         f"Плавка: {material.melt_number}\n" \
                         f"Требуется проверка сертификатных данных"
            
            elif new_status == MaterialStatus.SAMPLES_REQUESTED.value:
                notify_roles = [UserRole.PRODUCTION.value]
                message = f"⚙️ <b>Запрос на изготовление образцов</b>\n\n" \
                         f"Марка: {material.material_grade}\n" \
                         f"Плавка: {material.melt_number}\n" \
                         f"Проверьте запрос в системе"
            
            elif new_status == MaterialStatus.EDIT_REQUESTED.value:
                notify_roles = [UserRole.WAREHOUSE.value]
                message = f"✏️ <b>Запрос на редактирование материала</b>\n\n" \
                         f"Марка: {material.material_grade}\n" \
                         f"Плавка: {material.melt_number}\n" \
                         f"Комментарий: {material.edit_comment}"
            
            elif new_status in [MaterialStatus.APPROVED.value, MaterialStatus.REJECTED.value]:
                # Уведомляем всех причастных
                notify_roles = [UserRole.WAREHOUSE.value, UserRole.QC.value]
                status_text = "✅ ОДОБРЕН" if new_status == MaterialStatus.APPROVED.value else "❌ ОТКЛОНЕН"
                message = f"<b>Материал {status_text}</b>\n\n" \
                         f"Марка: {material.material_grade}\n" \
                         f"Плавка: {material.melt_number}\n" \
                         f"Партия: {material.batch_number or 'Не указана'}"
            
            else:
                return  # Для других статусов уведомления не отправляем
            
            # Получаем пользователей для уведомления
            users_to_notify = db.query(User).filter(
                User.role.in_(notify_roles),
                User.telegram_id.isnot(None),
                User.is_active == True
            ).all()
            
            # Отправляем уведомления
            for user in users_to_notify:
                self.send_telegram_message(user.telegram_id, message)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")
        finally:
            db.close()
    
    def notify_test_results(self, material_id: int, test_type: str, passed: bool):
        """
        Уведомить о результатах испытаний
        
        Args:
            material_id: ID материала
            test_type: Тип испытания
            passed: Результат (True - годен, False - брак)
        """
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(
                MaterialEntry.id == material_id
            ).first()
            
            if not material:
                return
            
            # Определяем тип испытания
            test_type_names = {
                'mechanical': 'Механические испытания',
                'chemical': 'Химический анализ',
                'metallographic': 'Металлография'
            }
            test_name = test_type_names.get(test_type, test_type)
            
            # Формируем сообщение
            result_text = "✅ ПРОЙДЕНЫ" if passed else "❌ НЕ ПРОЙДЕНЫ"
            message = f"📊 <b>Результаты испытаний</b>\n\n" \
                     f"Материал: {material.material_grade}\n" \
                     f"Плавка: {material.melt_number}\n" \
                     f"Испытание: {test_name}\n" \
                     f"Результат: {result_text}"
            
            # Уведомляем ОТК и склад
            users_to_notify = db.query(User).filter(
                User.role.in_([UserRole.QC.value, UserRole.WAREHOUSE.value]),
                User.telegram_id.isnot(None),
                User.is_active == True
            ).all()
            
            for user in users_to_notify:
                self.send_telegram_message(user.telegram_id, message)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о результатах: {e}")
        finally:
            db.close()
    
    def send_daily_summary(self):
        """
        Отправить ежедневную сводку администраторам
        """
        db = SessionLocal()
        try:
            # Получаем статистику за день
            today = datetime.now().date()
            
            # Подсчитываем материалы по статусам
            status_counts = {}
            for status in MaterialStatus:
                count = db.query(MaterialEntry).filter(
                    MaterialEntry.status == status.value,
                    MaterialEntry.is_deleted == False
                ).count()
                if count > 0:
                    status_counts[status.value] = count
            
            # Формируем сообщение
            message = f"📈 <b>Ежедневная сводка на {today.strftime('%d.%m.%Y')}</b>\n\n"
            
            if status_counts:
                message += "📦 <b>Материалы по статусам:</b>\n"
                for status, count in status_counts.items():
                    status_name = self._get_status_name(status)
                    message += f"• {status_name}: {count}\n"
            else:
                message += "Нет активных материалов в системе\n"
            
            # Отправляем администраторам
            admins = db.query(User).filter(
                User.role == UserRole.ADMIN.value,
                User.telegram_id.isnot(None),
                User.is_active == True
            ).all()
            
            for admin in admins:
                self.send_telegram_message(admin.telegram_id, message)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневной сводки: {e}")
        finally:
            db.close()
    
    def _get_status_name(self, status_code: str) -> str:
        """Получить отображаемое имя статуса"""
        status_names = {
            MaterialStatus.RECEIVED.value: "Получен на склад",
            MaterialStatus.QC_CHECK_PENDING.value: "Ожидает проверки ОТК",
            MaterialStatus.QC_CHECKED.value: "Проверен ОТК",
            MaterialStatus.LAB_CHECK_PENDING.value: "Ожидает проверки в ЦЗЛ",
            MaterialStatus.SAMPLES_REQUESTED.value: "Запрошены пробы",
            MaterialStatus.SAMPLES_COLLECTED.value: "Пробы отобраны",
            MaterialStatus.TESTING.value: "На испытаниях",
            MaterialStatus.TESTING_COMPLETED.value: "Испытания завершены",
            MaterialStatus.APPROVED.value: "Одобрен",
            MaterialStatus.REJECTED.value: "Отклонен",
            MaterialStatus.ARCHIVED.value: "В архиве",
            MaterialStatus.EDIT_REQUESTED.value: "Запрос на редактирование"
        }
        return status_names.get(status_code, status_code)

# Глобальный экземпляр сервиса
notification_service = NotificationService() 