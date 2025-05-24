import os
import shutil
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.connection import SessionLocal
from models.models import MaterialEntry, MaterialStatus
from utils.notifications import notification_service
from utils.reports import ReportGenerator

class TaskScheduler:
    """Планировщик автоматических задач для PPSD"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Настройка автоматических задач"""
        # Ежедневная сводка в 09:00
        self.scheduler.add_job(
            func=self.send_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_summary',
            name='Ежедневная сводка'
        )
        
        # Резервное копирование в 23:00
        self.scheduler.add_job(
            func=self.backup_database,
            trigger=CronTrigger(hour=23, minute=0),
            id='daily_backup',
            name='Резервное копирование БД'
        )
        
        # Проверка просроченных задач каждый час
        self.scheduler.add_job(
            func=self.check_overdue_tasks,
            trigger=CronTrigger(minute=0),
            id='check_overdue',
            name='Проверка просроченных задач'
        )
    
    def send_daily_summary(self):
        """Отправка ежедневной сводки"""
        try:
            notification_service.send_daily_summary()
            print(f"[{datetime.now()}] Ежедневная сводка отправлена")
        except Exception as e:
            print(f"[{datetime.now()}] Ошибка отправки сводки: {e}")
    
    def backup_database(self):
        """Резервное копирование базы данных"""
        try:
            source = "ppsd.db"
            if os.path.exists(source):
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                backup_name = f"ppsd_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                destination = os.path.join(backup_dir, backup_name)
                shutil.copy2(source, destination)
                print(f"[{datetime.now()}] Резервная копия создана: {destination}")
                
                # Удаляем старые копии (оставляем последние 30)
                self.cleanup_old_backups(backup_dir, keep_count=30)
        except Exception as e:
            print(f"[{datetime.now()}] Ошибка создания резервной копии: {e}")
    
    def cleanup_old_backups(self, backup_dir: str, keep_count: int = 30):
        """Удаление старых резервных копий"""
        try:
            backups = []
            for file in os.listdir(backup_dir):
                if file.startswith("ppsd_backup_") and file.endswith(".db"):
                    file_path = os.path.join(backup_dir, file)
                    backups.append((file_path, os.path.getctime(file_path)))
            
            # Сортируем по времени создания (новые сначала)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Удаляем лишние
            for backup_path, _ in backups[keep_count:]:
                os.remove(backup_path)
                print(f"[{datetime.now()}] Удалена старая копия: {backup_path}")
                
        except Exception as e:
            print(f"[{datetime.now()}] Ошибка очистки старых копий: {e}")
    
    def check_overdue_tasks(self):
        """Проверка просроченных задач"""
        db = SessionLocal()
        try:
            # Материалы, которые долго висят в одном статусе
            cutoff_date = datetime.now() - timedelta(days=7)
            
            pending_materials = db.query(MaterialEntry).filter(
                MaterialEntry.status.in_([
                    MaterialStatus.QC_CHECK_PENDING.value,
                    MaterialStatus.LAB_CHECK_PENDING.value,
                    MaterialStatus.TESTING.value
                ]),
                MaterialEntry.updated_at < cutoff_date,
                MaterialEntry.is_deleted == False
            ).all()
            
            if pending_materials:
                message = f"⚠️ <b>Найдены просроченные задачи ({len(pending_materials)})</b>\n\n"
                for material in pending_materials[:5]:  # Показываем первые 5
                    days_overdue = (datetime.now() - material.updated_at).days
                    message += f"• {material.material_grade} (плавка {material.melt_number})\n"
                    message += f"  Статус: {material.status}, просрочено на {days_overdue} дней\n\n"
                
                # Отправляем администраторам
                from models.models import User, UserRole
                admins = db.query(User).filter(
                    User.role == UserRole.ADMIN.value,
                    User.telegram_id.isnot(None),
                    User.is_active == True
                ).all()
                
                for admin in admins:
                    notification_service.send_telegram_message(admin.telegram_id, message)
                
                print(f"[{datetime.now()}] Найдено просроченных задач: {len(pending_materials)}")
            
        except Exception as e:
            print(f"[{datetime.now()}] Ошибка проверки просроченных задач: {e}")
        finally:
            db.close()
    
    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
        print("Планировщик задач запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        print("Планировщик задач остановлен")

# Глобальный экземпляр планировщика
task_scheduler = TaskScheduler() 