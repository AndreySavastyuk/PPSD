"""
Система автоматического резервного копирования для ППСД
Создает резервные копии базы данных и важных файлов
"""

import os
import shutil
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QTextEdit, QGroupBox,
                              QSpinBox, QCheckBox, QFileDialog, QMessageBox,
                              QComboBox, QListWidget, QListWidgetItem)
from PySide6.QtCore import QTimer, Signal, QThread, QSettings
from PySide6.QtGui import QFont
from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider

class BackupWorker(QThread):
    """Рабочий поток для создания резервных копий"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    backup_completed = Signal(bool, str)  # success, message
    
    def __init__(self, backup_config):
        super().__init__()
        self.config = backup_config
    
    def run(self):
        """Выполнение резервного копирования"""
        try:
            self.status_updated.emit("Начинаем резервное копирование...")
            self.progress_updated.emit(10)
            
            # Создаем директорию для резервных копий
            backup_dir = Path(self.config['backup_path'])
            backup_dir.mkdir(exist_ok=True)
            
            # Генерируем имя файла резервной копии
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"ppsd_backup_{timestamp}.zip"
            backup_filepath = backup_dir / backup_filename
            
            self.status_updated.emit("Создаем архив...")
            self.progress_updated.emit(20)
            
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Резервная копия базы данных
                if self.config['include_database']:
                    self.backup_database(backup_zip)
                    self.progress_updated.emit(40)
                
                # Резервная копия документов
                if self.config['include_documents']:
                    self.backup_documents(backup_zip)
                    self.progress_updated.emit(60)
                
                # Резервная копия конфигурации
                if self.config['include_config']:
                    self.backup_config_files(backup_zip)
                    self.progress_updated.emit(80)
            
            self.status_updated.emit("Проверяем резервную копию...")
            # Проверяем целостность архива
            if self.verify_backup(backup_filepath):
                self.progress_updated.emit(90)
                
                # Удаляем старые резервные копии при необходимости
                if self.config['auto_cleanup']:
                    self.cleanup_old_backups(backup_dir)
                
                self.progress_updated.emit(100)
                self.status_updated.emit(f"Резервная копия создана: {backup_filename}")
                self.backup_completed.emit(True, str(backup_filepath))
            else:
                self.backup_completed.emit(False, "Ошибка проверки целостности резервной копии")
                
        except Exception as e:
            self.backup_completed.emit(False, f"Ошибка создания резервной копии: {str(e)}")
    
    def backup_database(self, backup_zip):
        """Резервная копия базы данных"""
        self.status_updated.emit("Копируем базу данных...")
        
        # Путь к базе данных
        db_path = "database/ppsd.db"
        if os.path.exists(db_path):
            backup_zip.write(db_path, "database/ppsd.db")
    
    def backup_documents(self, backup_zip):
        """Резервная копия документов"""
        self.status_updated.emit("Копируем документы...")
        
        docs_dirs = ["docs_storage", "logs"]
        for docs_dir in docs_dirs:
            if os.path.exists(docs_dir):
                for root, dirs, files in os.walk(docs_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, ".")
                        backup_zip.write(file_path, archive_path)
    
    def backup_config_files(self, backup_zip):
        """Резервная копия конфигурационных файлов"""
        self.status_updated.emit("Копируем конфигурацию...")
        
        config_files = [".env", "requirements.txt", "README.md"]
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_zip.write(config_file, config_file)
    
    def verify_backup(self, backup_path):
        """Проверка целостности резервной копии"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Проверяем, что архив не поврежден
                backup_zip.testzip()
                return True
        except:
            return False
    
    def cleanup_old_backups(self, backup_dir):
        """Удаление старых резервных копий"""
        self.status_updated.emit("Удаляем старые резервные копии...")
        
        # Получаем список всех резервных копий
        backup_files = list(backup_dir.glob("ppsd_backup_*.zip"))
        
        # Сортируем по времени создания (новые сначала)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Оставляем только указанное количество резервных копий
        max_backups = self.config.get('max_backups', 10)
        for old_backup in backup_files[max_backups:]:
            try:
                old_backup.unlink()
            except:
                pass  # Игнорируем ошибки удаления

class BackupScheduler:
    """Планировщик автоматических резервных копий"""
    
    def __init__(self, backup_system):
        self.backup_system = backup_system
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_scheduled_backup)
        self.settings = QSettings('PPSD', 'BackupSystem')
    
    def start_scheduler(self):
        """Запуск планировщика"""
        interval_hours = self.settings.value('backup_interval', 24, type=int)
        if self.settings.value('auto_backup_enabled', False, type=bool):
            self.timer.start(interval_hours * 60 * 60 * 1000)  # Конвертируем в миллисекунды
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.timer.stop()
    
    def run_scheduled_backup(self):
        """Выполнение запланированной резервной копии"""
        if self.backup_system:
            self.backup_system.start_automatic_backup()

class BackupSystemWidget(QWidget):
    """Виджет системы резервного копирования"""
    
    backup_started = Signal()
    backup_finished = Signal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.scheduler = BackupScheduler(self)
        self.settings = QSettings('PPSD', 'BackupSystem')
        self.init_ui()
        self.load_settings()
        self.scheduler.start_scheduler()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Заголовок
        title_label = QLabel("Система резервного копирования")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Настройки резервного копирования
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout(settings_group)
        
        # Путь для резервных копий
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Путь для резервных копий:"))
        self.backup_path = QLabel("./backups")
        self.backup_path.setStyleSheet(f"padding: 4px; border: 1px solid {theme_manager.get_color('border')}; border-radius: 4px;")
        path_layout.addWidget(self.backup_path)
        
        self.browse_btn = QPushButton("Обзор...")
        self.browse_btn.clicked.connect(self.browse_backup_path)
        self.browse_btn.setStyleSheet(theme_manager.get_button_style('neutral'))
        path_layout.addWidget(self.browse_btn)
        
        settings_layout.addLayout(path_layout)
        
        # Что включать в резервную копию
        content_layout = QHBoxLayout()
        
        self.include_database = QCheckBox("База данных")
        self.include_database.setChecked(True)
        content_layout.addWidget(self.include_database)
        
        self.include_documents = QCheckBox("Документы")
        self.include_documents.setChecked(True)
        content_layout.addWidget(self.include_documents)
        
        self.include_config = QCheckBox("Конфигурация")
        self.include_config.setChecked(True)
        content_layout.addWidget(self.include_config)
        
        content_layout.addStretch()
        settings_layout.addLayout(content_layout)
        
        # Автоматическое резервное копирование
        auto_layout = QHBoxLayout()
        
        self.auto_backup = QCheckBox("Автоматическое резервное копирование")
        auto_layout.addWidget(self.auto_backup)
        
        auto_layout.addWidget(QLabel("каждые"))
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 168)
        self.backup_interval.setValue(24)
        self.backup_interval.setSuffix(" часов")
        auto_layout.addWidget(self.backup_interval)
        
        auto_layout.addStretch()
        settings_layout.addLayout(auto_layout)
        
        # Очистка старых резервных копий
        cleanup_layout = QHBoxLayout()
        
        self.auto_cleanup = QCheckBox("Удалять старые резервные копии (оставлять")
        cleanup_layout.addWidget(self.auto_cleanup)
        
        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 100)
        self.max_backups.setValue(10)
        cleanup_layout.addWidget(self.max_backups)
        
        cleanup_layout.addWidget(QLabel("последних)"))
        cleanup_layout.addStretch()
        settings_layout.addLayout(cleanup_layout)
        
        layout.addWidget(settings_group)
        
        # Управление резервными копиями
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout(control_group)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.create_backup_btn = QPushButton("Создать резервную копию")
        self.create_backup_btn.setIcon(IconProvider.create_backup_icon())
        self.create_backup_btn.clicked.connect(self.create_backup)
        self.create_backup_btn.setStyleSheet(theme_manager.get_button_style('primary'))
        buttons_layout.addWidget(self.create_backup_btn)
        
        self.restore_backup_btn = QPushButton("Восстановить из копии")
        self.restore_backup_btn.setIcon(IconProvider.create_restore_icon())
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        self.restore_backup_btn.setStyleSheet(theme_manager.get_button_style('warning'))
        buttons_layout.addWidget(self.restore_backup_btn)
        
        self.save_settings_btn = QPushButton("Сохранить настройки")
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.save_settings_btn.setStyleSheet(theme_manager.get_button_style('secondary'))
        buttons_layout.addWidget(self.save_settings_btn)
        
        buttons_layout.addStretch()
        control_layout.addLayout(buttons_layout)
        
        # Прогресс резервного копирования
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("Готов к созданию резервной копии")
        self.status_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        
        # Список существующих резервных копий
        backups_group = QGroupBox("Существующие резервные копии")
        backups_layout = QVBoxLayout(backups_group)
        
        refresh_layout = QHBoxLayout()
        self.refresh_list_btn = QPushButton("Обновить список")
        self.refresh_list_btn.clicked.connect(self.refresh_backup_list)
        self.refresh_list_btn.setStyleSheet(theme_manager.get_button_style('neutral'))
        refresh_layout.addWidget(self.refresh_list_btn)
        refresh_layout.addStretch()
        backups_layout.addLayout(refresh_layout)
        
        self.backups_list = QListWidget()
        self.backups_list.setMaximumHeight(150)
        backups_layout.addWidget(self.backups_list)
        
        layout.addWidget(backups_group)
        
        layout.addStretch()
        
        # Загружаем список резервных копий
        self.refresh_backup_list()
    
    def browse_backup_path(self):
        """Выбор пути для резервных копий"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для резервных копий")
        if path:
            self.backup_path.setText(path)
    
    def create_backup(self):
        """Создание резервной копии"""
        if self.worker and self.worker.isRunning():
            return  # Уже выполняется резервное копирование
        
        config = {
            'backup_path': self.backup_path.text(),
            'include_database': self.include_database.isChecked(),
            'include_documents': self.include_documents.isChecked(),
            'include_config': self.include_config.isChecked(),
            'auto_cleanup': self.auto_cleanup.isChecked(),
            'max_backups': self.max_backups.value()
        }
        
        self.worker = BackupWorker(config)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.backup_completed.connect(self.on_backup_completed)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.create_backup_btn.setEnabled(False)
        
        self.backup_started.emit()
        self.worker.start()
    
    def start_automatic_backup(self):
        """Запуск автоматической резервной копии"""
        if self.auto_backup.isChecked():
            self.create_backup()
    
    def on_backup_completed(self, success, message):
        """Обработка завершения резервного копирования"""
        self.progress_bar.setVisible(False)
        self.create_backup_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"Резервная копия создана успешно")
            self.refresh_backup_list()
        else:
            self.status_label.setText(f"Ошибка: {message}")
        
        self.backup_finished.emit(success, message)
    
    def restore_backup(self):
        """Восстановление из резервной копии"""
        selected_items = self.backups_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите резервную копию для восстановления")
            return
        
        backup_name = selected_items[0].text()
        backup_path = os.path.join(self.backup_path.text(), backup_name)
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Вы уверены, что хотите восстановить данные из резервной копии?\n"
            f"Текущие данные будут заменены!\n\n"
            f"Файл: {backup_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.perform_restore(backup_path)
                QMessageBox.information(self, "Успех", "Данные восстановлены успешно.\nПерезапустите приложение.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка восстановления: {str(e)}")
    
    def perform_restore(self, backup_path):
        """Выполнение восстановления"""
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            # Создаем временную папку для извлечения
            extract_path = "./temp_restore"
            backup_zip.extractall(extract_path)
            
            # Восстанавливаем базу данных
            if os.path.exists(f"{extract_path}/database/ppsd.db"):
                shutil.copy2(f"{extract_path}/database/ppsd.db", "database/ppsd.db")
            
            # Восстанавливаем документы
            if os.path.exists(f"{extract_path}/docs_storage"):
                if os.path.exists("docs_storage"):
                    shutil.rmtree("docs_storage")
                shutil.copytree(f"{extract_path}/docs_storage", "docs_storage")
            
            # Удаляем временную папку
            shutil.rmtree(extract_path)
    
    def refresh_backup_list(self):
        """Обновление списка резервных копий"""
        self.backups_list.clear()
        
        backup_dir = Path(self.backup_path.text())
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("ppsd_backup_*.zip"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                # Получаем информацию о файле
                stat = backup_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                
                # Создаем элемент списка с информацией
                item_text = f"{backup_file.name} ({size_mb:.1f} МБ, {mod_time.strftime('%d.%m.%Y %H:%M')})"
                item = QListWidgetItem(item_text)
                item.setData(0, backup_file.name)  # Сохраняем имя файла
                self.backups_list.addItem(item)
    
    def save_settings(self):
        """Сохранение настроек"""
        self.settings.setValue('backup_path', self.backup_path.text())
        self.settings.setValue('include_database', self.include_database.isChecked())
        self.settings.setValue('include_documents', self.include_documents.isChecked())
        self.settings.setValue('include_config', self.include_config.isChecked())
        self.settings.setValue('auto_backup_enabled', self.auto_backup.isChecked())
        self.settings.setValue('backup_interval', self.backup_interval.value())
        self.settings.setValue('auto_cleanup', self.auto_cleanup.isChecked())
        self.settings.setValue('max_backups', self.max_backups.value())
        
        # Перезапускаем планировщик с новыми настройками
        self.scheduler.stop_scheduler()
        self.scheduler.start_scheduler()
        
        self.status_label.setText("Настройки сохранены")
    
    def load_settings(self):
        """Загрузка настроек"""
        self.backup_path.setText(self.settings.value('backup_path', './backups'))
        self.include_database.setChecked(self.settings.value('include_database', True, type=bool))
        self.include_documents.setChecked(self.settings.value('include_documents', True, type=bool))
        self.include_config.setChecked(self.settings.value('include_config', True, type=bool))
        self.auto_backup.setChecked(self.settings.value('auto_backup_enabled', False, type=bool))
        self.backup_interval.setValue(self.settings.value('backup_interval', 24, type=int))
        self.auto_cleanup.setChecked(self.settings.value('auto_cleanup', True, type=bool))
        self.max_backups.setValue(self.settings.value('max_backups', 10, type=int)) 