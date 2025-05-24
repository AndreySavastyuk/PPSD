#!/usr/bin/env python3
"""
Система уведомлений для ППСД
Поддерживает Email, Telegram и веб push-уведомления
"""

import os
import sys
import smtplib
import logging
from datetime import datetime
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import json

# Добавляем корневую директорию в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.connection import SessionLocal
from models.models import MaterialEntry, User, UserRole, MaterialStatus

# Настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@ppsd.local')
        }
        
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_bot = None
        
        if self.telegram_token:
            self.init_telegram_bot()
    
    def init_telegram_bot(self):
        """Инициализация Telegram бота"""
        try:
            self.telegram_bot = telegram.Bot(token=self.telegram_token)
            logger.info("Telegram бот инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
    
    async def send_email(self, to_email: str, subject: str, body: str, attachments: List[str] = None):
        """Отправка email уведомления"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Добавляем вложения
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email отправлен на {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
            return False
    
    async def send_telegram_message(self, chat_id: str, message: str, parse_mode: str = 'HTML'):
        """Отправка сообщения в Telegram"""
        if not self.telegram_bot:
            logger.warning("Telegram бот не инициализирован")
            return False
        
        try:
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"Telegram сообщение отправлено в чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram сообщения: {e}")
            return False
    
    def send_web_push(self, user_id: int, title: str, body: str, data: Dict = None):
        """Отправка web push уведомления (заглушка для будущей реализации)"""
        logger.info(f"Web push уведомление для пользователя {user_id}: {title}")
        # TODO: Реализовать с помощью WebPush API
        return True
    
    async def notify_material_status_change(self, material_id: int, old_status: str, new_status: str, user_id: int):
        """Уведомление об изменении статуса материала"""
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            if not material:
                return
            
            # Получаем пользователей для уведомления
            users_to_notify = self.get_users_for_status_notification(db, old_status, new_status)
            
            subject = f"ППСД: Изменение статуса материала #{material_id}"
            
            message = self.create_status_change_message(material, old_status, new_status)
            
            for user in users_to_notify:
                if user.email:
                    await self.send_email(user.email, subject, message)
                
                if user.telegram_chat_id:
                    telegram_message = self.create_telegram_status_message(material, old_status, new_status)
                    await self.send_telegram_message(user.telegram_chat_id, telegram_message)
                
                # Web push уведомление
                self.send_web_push(
                    user.id,
                    f"Статус материала изменен",
                    f"Материал #{material_id} переведен в статус: {self.get_status_display_name(new_status)}",
                    {'material_id': material_id, 'status': new_status}
                )
        
        finally:
            db.close()
    
    async def notify_new_material(self, material_id: int):
        """Уведомление о новом материале"""
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            if not material:
                return
            
            # Уведомляем ОТК о новом материале
            qc_users = db.query(User).filter(User.role == UserRole.QC.value).all()
            
            subject = f"ППСД: Новый материал для проверки #{material_id}"
            
            for user in qc_users:
                message = self.create_new_material_message(material)
                
                if user.email:
                    await self.send_email(user.email, subject, message)
                
                if user.telegram_chat_id:
                    telegram_message = self.create_telegram_new_material_message(material)
                    await self.send_telegram_message(user.telegram_chat_id, telegram_message)
        
        finally:
            db.close()
    
    async def notify_critical_event(self, event_type: str, message: str, affected_material_id: int = None):
        """Уведомление о критическом событии"""
        db = SessionLocal()
        try:
            # Уведомляем администраторов
            admins = db.query(User).filter(User.role == UserRole.ADMIN.value).all()
            
            subject = f"ППСД: КРИТИЧЕСКОЕ СОБЫТИЕ - {event_type}"
            
            for admin in admins:
                if admin.email:
                    email_message = self.create_critical_event_message(event_type, message, affected_material_id)
                    await self.send_email(admin.email, subject, email_message)
                
                if admin.telegram_chat_id:
                    telegram_message = f"🚨 <b>КРИТИЧЕСКОЕ СОБЫТИЕ</b>\n\n" \
                                     f"<b>Тип:</b> {event_type}\n" \
                                     f"<b>Описание:</b> {message}\n" \
                                     f"<b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                    
                    if affected_material_id:
                        telegram_message += f"\n<b>Материал:</b> #{affected_material_id}"
                    
                    await self.send_telegram_message(admin.telegram_chat_id, telegram_message)
        
        finally:
            db.close()
    
    def get_users_for_status_notification(self, db, old_status: str, new_status: str) -> List[User]:
        """Получение списка пользователей для уведомления об изменении статуса"""
        users = []
        
        # Логика определения кого уведомлять в зависимости от изменения статуса
        if new_status == MaterialStatus.QC_CHECK_PENDING.value:
            # Уведомляем ОТК
            users.extend(db.query(User).filter(User.role == UserRole.QC.value).all())
        
        elif new_status == MaterialStatus.LAB_CHECK_PENDING.value:
            # Уведомляем лабораторию
            users.extend(db.query(User).filter(User.role == UserRole.LAB.value).all())
        
        elif new_status in [MaterialStatus.APPROVED.value, MaterialStatus.REJECTED.value]:
            # Уведомляем склад и производство
            users.extend(db.query(User).filter(
                User.role.in_([UserRole.WAREHOUSE.value, UserRole.PRODUCTION.value])
            ).all())
        
        return users
    
    def create_status_change_message(self, material: MaterialEntry, old_status: str, new_status: str) -> str:
        """Создание сообщения об изменении статуса для email"""
        return f"""
        <html>
        <body>
            <h2>Изменение статуса материала</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><b>ID материала:</b></td><td>#{material.id}</td></tr>
                <tr><td><b>Марка:</b></td><td>{material.material_grade}</td></tr>
                <tr><td><b>Плавка:</b></td><td>{material.melt_number}</td></tr>
                <tr><td><b>Старый статус:</b></td><td>{self.get_status_display_name(old_status)}</td></tr>
                <tr><td><b>Новый статус:</b></td><td>{self.get_status_display_name(new_status)}</td></tr>
                <tr><td><b>Время изменения:</b></td><td>{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</td></tr>
            </table>
            
            <p><a href="http://localhost:5000">Перейти в систему ППСД</a></p>
        </body>
        </html>
        """
    
    def create_telegram_status_message(self, material: MaterialEntry, old_status: str, new_status: str) -> str:
        """Создание сообщения об изменении статуса для Telegram"""
        return f"""
📋 <b>Изменение статуса материала</b>

🔢 <b>ID:</b> #{material.id}
⚡ <b>Марка:</b> {material.material_grade}
🔥 <b>Плавка:</b> {material.melt_number}

📊 <b>Статус изменен:</b>
• Было: {self.get_status_display_name(old_status)}
• Стало: {self.get_status_display_name(new_status)}

🕒 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        """
    
    def create_new_material_message(self, material: MaterialEntry) -> str:
        """Создание сообщения о новом материале для email"""
        return f"""
        <html>
        <body>
            <h2>Новый материал для проверки</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><b>ID материала:</b></td><td>#{material.id}</td></tr>
                <tr><td><b>Марка:</b></td><td>{material.material_grade}</td></tr>
                <tr><td><b>Тип:</b></td><td>{material.material_type}</td></tr>
                <tr><td><b>Плавка:</b></td><td>{material.melt_number}</td></tr>
                <tr><td><b>Партия:</b></td><td>{material.batch_number or 'Не указана'}</td></tr>
                <tr><td><b>Дата поступления:</b></td><td>{material.created_at.strftime('%d.%m.%Y %H:%M:%S')}</td></tr>
            </table>
            
            <p><b>Требуется проверка ОТК</b></p>
            <p><a href="http://localhost:5000">Перейти в систему ППСД</a></p>
        </body>
        </html>
        """
    
    def create_telegram_new_material_message(self, material: MaterialEntry) -> str:
        """Создание сообщения о новом материале для Telegram"""
        return f"""
🆕 <b>Новый материал для проверки</b>

🔢 <b>ID:</b> #{material.id}
⚡ <b>Марка:</b> {material.material_grade}
📦 <b>Тип:</b> {material.material_type}
🔥 <b>Плавка:</b> {material.melt_number}
📋 <b>Партия:</b> {material.batch_number or 'Не указана'}

⏰ <b>Поступил:</b> {material.created_at.strftime('%d.%m.%Y %H:%M:%S')}

✅ <b>Требуется проверка ОТК</b>
        """
    
    def create_critical_event_message(self, event_type: str, message: str, material_id: int = None) -> str:
        """Создание сообщения о критическом событии для email"""
        material_info = ""
        if material_id:
            material_info = f"<tr><td><b>Затронутый материал:</b></td><td>#{material_id}</td></tr>"
        
        return f"""
        <html>
        <body>
            <h2 style="color: red;">КРИТИЧЕСКОЕ СОБЫТИЕ</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><b>Тип события:</b></td><td>{event_type}</td></tr>
                <tr><td><b>Описание:</b></td><td>{message}</td></tr>
                {material_info}
                <tr><td><b>Время:</b></td><td>{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</td></tr>
            </table>
            
            <p><b>Требуется немедленное внимание!</b></p>
            <p><a href="http://localhost:5000">Перейти в систему ППСД</a></p>
        </body>
        </html>
        """
    
    def get_status_display_name(self, status_code: str) -> str:
        """Получение отображаемого имени статуса"""
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

# Singleton instance
notification_manager = NotificationManager()

class TelegramBotHandler:
    """Обработчик команд Telegram бота"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.nm = notification_manager
        self.user_chats = {}  # Словарь для хранения связей пользователей с чатами
        
    async def start_command(self, update, context):
        """Команда /start"""
        chat_id = update.effective_chat.id
        message = """
🏭 <b>Добро пожаловать в бот ППСД!</b>

Этот бот уведомляет о важных событиях в системе проверки сертификатных данных.

<b>Доступные команды:</b>
/start - Показать это сообщение
/status - Текущий статус системы
/stats - Статистика материалов
/help - Помощь

Для получения уведомлений обратитесь к администратору системы для связки вашего аккаунта с этим чатом.
        """
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
    
    async def status_command(self, update, context):
        """Команда /status"""
        chat_id = update.effective_chat.id
        
        db = SessionLocal()
        try:
            total_materials = db.query(MaterialEntry).filter(MaterialEntry.is_deleted == False).count()
            pending_qc = db.query(MaterialEntry).filter(
                MaterialEntry.status == MaterialStatus.QC_CHECK_PENDING.value,
                MaterialEntry.is_deleted == False
            ).count()
            
            message = f"""
📊 <b>Статус системы ППСД</b>

📦 <b>Всего материалов:</b> {total_materials}
⏳ <b>Ожидают проверки ОТК:</b> {pending_qc}
🕒 <b>Время проверки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

✅ Система работает в штатном режиме
            """
            
        except Exception as e:
            message = f"❌ Ошибка получения статуса: {str(e)}"
        
        finally:
            db.close()
        
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
    
    async def help_command(self, update, context):
        """Команда /help"""
        chat_id = update.effective_chat.id
        message = """
🆘 <b>Помощь по боту ППСД</b>

<b>Назначение:</b>
Бот предназначен для получения уведомлений о важных событиях в системе контроля качества материалов.

<b>Типы уведомлений:</b>
• 📦 Новые материалы для проверки
• 🔄 Изменения статусов материалов
• 🚨 Критические события
• ⚠️ Системные предупреждения

<b>Настройка уведомлений:</b>
Для получения персональных уведомлений обратитесь к администратору системы. Он свяжет ваш аккаунт ППСД с этим Telegram чатом.

<b>Техническая поддержка:</b>
Если у вас есть вопросы или проблемы, обратитесь в IT-отдел.
        """
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

def run_telegram_bot():
    """Запуск Telegram бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен. Telegram бот не будет запущен.")
        return
    
    application = Application.builder().token(token).build()
    handler = TelegramBotHandler(notification_manager)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("status", handler.status_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    
    logger.info("Запуск Telegram бота...")
    application.run_polling()

if __name__ == '__main__':
    # Запускаем Telegram бота
    run_telegram_bot() 