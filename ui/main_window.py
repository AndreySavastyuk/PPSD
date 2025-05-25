import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTabWidget, QPushButton, 
                             QMessageBox, QFrame, QStatusBar, QMenu,
                             QToolBar, QSplitter, QDialog, QDialogButtonBox)
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtCore import Qt, QSize

from database.connection import SessionLocal
from models.models import UserRole
from ui.tabs.warehouse_tab import WarehouseTab
from ui.tabs.qc_tab import QCTab
from ui.tabs.lab_tab import LabTab
from ui.tabs.admin_tab import AdminTab
from ui.tabs.production_tab import ProductionTab
from ui.reference.material_grade_reference import MaterialGradeReference
from ui.reference.product_type_reference import ProductTypeReference
from ui.reference.supplier_reference import SupplierReference
from ui.reference.test_type_reference import TestTypeReference
from ui.icons.icon_provider import IconProvider
from ui.styles import apply_table_style, get_application_styles, apply_tab_style
from ui.themes import theme_manager, ThemeType
from ui.notifications import notification_manager
from ui.dashboard import Dashboard

try:
    from ui.components.real_time_notifications import RealTimeNotificationPanel
except ImportError:
    RealTimeNotificationPanel = None

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        # Создаем status_bar до инициализации UI
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        # Window properties
        self.setWindowTitle("ППСД - Система проверки сертификатных данных")
        self.setMinimumSize(1200, 800)  # Минимальный размер окна
        
        # Запуск в полноэкранном режиме
        self.showMaximized()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)  # Равномерные отступы
        main_layout.setSpacing(8)  # Разумные расстояния между элементами
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        
        # Create main content splitter с гибкими настройками
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.addWidget(self.tab_widget)
        
        # Add notification panel if available
        if RealTimeNotificationPanel:
            self.notification_panel = RealTimeNotificationPanel(self)
            # Убираем фиксированные размеры, используем size policy
            self.notification_panel.setSizePolicy(
                self.notification_panel.sizePolicy().horizontalPolicy(),
                self.notification_panel.sizePolicy().verticalPolicy()
            )
            content_splitter.addWidget(self.notification_panel)
            
            # Set splitter proportions (main content 75%, notifications 25%)
            content_splitter.setSizes([1200, 400])
            content_splitter.setCollapsible(1, True)  # Позволяем скрывать панель уведомлений
        
        main_layout.addWidget(content_splitter)
        
        # Add tabs based on user role
        self.add_tabs_for_user()
        
        # Установка сообщения в статусную строку
        self.status_bar.showMessage("Готово")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Применяем стили ПОСЛЕ создания всех компонентов
        self.apply_current_theme()
        
        # Запускаем планировщик задач
        self.start_scheduler()
    
    def add_tabs_for_user(self):
        """Add tabs based on user role and permissions"""
        # Everyone can see the dashboard if they can view
        if self.user.can_view:
            # Добавляем дашборд как первую вкладку
            self.dashboard = Dashboard(self.user)
            self.tab_widget.addTab(self.dashboard, "Дашборд")
            self.tab_widget.setTabIcon(0, IconProvider.create_report_icon())
            
            tab_index = 1  # Начинаем с индекса 1, так как дашборд уже добавлен
            
            # Add tabs based on role
            if self.user.role == UserRole.WAREHOUSE.value:
                # Warehouse interface
                self.warehouse_tab = WarehouseTab(self.user, self)
                self.tab_widget.addTab(self.warehouse_tab, "Склад")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_warehouse_icon())
            
            if self.user.role == UserRole.QC.value:
                # QC interface
                self.qc_tab = QCTab(self.user, self)
                self.tab_widget.addTab(self.qc_tab, "ОТК")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_qc_icon())
            
            if self.user.role == UserRole.LAB.value:
                # Lab interface
                self.lab_tab = LabTab(self.user, self)
                self.tab_widget.addTab(self.lab_tab, "Лаборатория")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_lab_icon())
            
            if self.user.role == UserRole.PRODUCTION.value:
                # Production interface
                self.production_tab = ProductionTab(self.user, self)
                self.tab_widget.addTab(self.production_tab, "Производство")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_production_icon())
            
            # Admin can see all tabs
            if self.user.role == UserRole.ADMIN.value:
                # tab_index уже равен 1 после дашборда
                
                self.warehouse_tab = WarehouseTab(self.user, self)
                self.tab_widget.addTab(self.warehouse_tab, "Склад")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_warehouse_icon())
                tab_index += 1
                
                self.qc_tab = QCTab(self.user, self)
                self.tab_widget.addTab(self.qc_tab, "ОТК")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_qc_icon())
                tab_index += 1
                
                self.lab_tab = LabTab(self.user, self)
                self.tab_widget.addTab(self.lab_tab, "Лаборатория")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_lab_icon())
                tab_index += 1
                
                # Admin tab is only for admins
                self.admin_tab = AdminTab(self.user, self)
                self.tab_widget.addTab(self.admin_tab, "Администрирование")
                self.tab_widget.setTabIcon(tab_index, IconProvider.create_settings_icon())
            
            # Перемещаем вкладку "Отладка" в конец, если она существует
            debug_tab_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Отладка":
                    debug_tab_index = i
                    break
            
            if debug_tab_index >= 0:
                # Сохраняем вкладку
                debug_tab = self.tab_widget.widget(debug_tab_index)
                debug_tab_icon = self.tab_widget.tabIcon(debug_tab_index)
                
                # Удаляем вкладку с текущей позиции (но не удаляем сам виджет)
                self.tab_widget.removeTab(debug_tab_index)
                
                # Добавляем вкладку отладки в конец
                new_index = self.tab_widget.addTab(debug_tab, debug_tab_icon, "Отладка")
                self.tab_widget.setTabToolTip(new_index, "Инструменты отладки")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menu_bar = self.menuBar()
        
        # Файл
        file_menu = menu_bar.addMenu("Файл")
        
        qr_action = QAction("Генератор QR-кодов", self)
        qr_action.setIcon(IconProvider.create_qr_code_icon())
        qr_action.setShortcut("Ctrl+Q")
        qr_action.triggered.connect(self.open_qr_generator)
        file_menu.addAction(qr_action)
        
        cert_action = QAction("Проводник сертификатов", self)
        cert_action.setIcon(IconProvider.create_certificate_icon())
        cert_action.setShortcut("Ctrl+E")
        cert_action.triggered.connect(self.open_certificate_browser)
        file_menu.addAction(cert_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Справочники
        reference_menu = menu_bar.addMenu("Справочники")
        
        material_grade_action = QAction("Марки материалов", self)
        material_grade_action.triggered.connect(self.show_material_grade_reference)
        reference_menu.addAction(material_grade_action)
        
        product_type_action = QAction("Виды проката", self)
        product_type_action.triggered.connect(self.show_product_type_reference)
        reference_menu.addAction(product_type_action)
        
        supplier_action = QAction("Поставщики", self)
        supplier_action.triggered.connect(self.show_supplier_reference)
        reference_menu.addAction(supplier_action)
        
        test_type_action = QAction("Виды испытаний", self)
        test_type_action.triggered.connect(self.show_test_type_reference)
        reference_menu.addAction(test_type_action)
        
        # Инструменты
        tools_menu = menu_bar.addMenu("Инструменты")
        settings_action = QAction("Настройки", self)
        settings_action.setIcon(IconProvider.create_settings_icon())
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Вид
        view_menu = menu_bar.addMenu("Вид")
        self.dark_theme_action = QAction("Темная тема", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.setChecked(theme_manager.current_theme == ThemeType.DARK)
        self.dark_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.dark_theme_action)
        self.notifications_action = QAction("Панель уведомлений", self)
        self.notifications_action.setCheckable(True)
        self.notifications_action.setChecked(True)
        self.notifications_action.triggered.connect(self.toggle_notifications)
        view_menu.addAction(self.notifications_action)
        
        # Справка
        help_menu = menu_bar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Вернем прежние отступы и стиль для main_layout/tab_widget
        self.centralWidget().layout().setContentsMargins(10, 10, 10, 10)
        self.centralWidget().layout().setSpacing(6)
        self.tab_widget.setStyleSheet("")
        self.setStyleSheet(theme_manager.generate_stylesheet())
    
    def show_material_grade_reference(self):
        """Show material grade reference window"""
        dialog = MaterialGradeReference(self)
        dialog.exec()
    
    def show_product_type_reference(self):
        """Show product type reference window"""
        dialog = ProductTypeReference(self)
        dialog.exec()
    
    def show_supplier_reference(self):
        """Show supplier reference window"""
        dialog = SupplierReference(self)
        dialog.exec()
    
    def show_test_type_reference(self):
        """Show test type reference window"""
        dialog = TestTypeReference(self)
        dialog.exec()
    
    def logout(self):
        """Handle user logout"""
        reply = QMessageBox.question(self, "Выход из системы", 
                                     "Вы уверены, что хотите выйти из системы?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Import here to avoid circular imports
            from ui.login_window import LoginWindow
            
            # Show login window
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()
    
    def show_about(self):
        """Show about dialog"""
        about_text = ("ППСД - Система проверки сертификатных данных\n"
                     f"Версия: 1.0.0\n\n"
                     f"Пользователь: {self.user.full_name}\n"
                     f"Роль: {self.get_role_display_name(self.user.role)}\n\n"
                     "© 2023 Все права защищены")
        
        QMessageBox.about(self, "О программе", about_text)
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Заглушка для настроек
        label = QLabel("Настройки находятся в разработке.\n\nДоступные функции:\n- Смена темы (Вид → Темная тема)\n- Панель уведомлений (Вид → Панель уведомлений)")
        layout.addWidget(label)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
    
    def get_role_display_name(self, role):
        """Get display name for user role"""
        role_map = {
            UserRole.ADMIN.value: "Администратор",
            UserRole.WAREHOUSE.value: "Кладовщик",
            UserRole.QC.value: "Сотрудник ОТК",
            UserRole.LAB.value: "Инженер ЦЗЛ",
            UserRole.PRODUCTION.value: "Производственный персонал"
        }
        return role_map.get(role, "Неизвестная роль")

    def start_scheduler(self):
        """Запуск планировщика автоматических задач"""
        try:
            from utils.scheduler import task_scheduler
            if not task_scheduler.scheduler.running:
                task_scheduler.start()
                self.status_bar.showMessage("Планировщик задач запущен", 3000)
            else:
                self.status_bar.showMessage("Планировщик задач уже активен", 3000)
        except Exception as e:
            print(f"Ошибка запуска планировщика: {e}")
            self.status_bar.showMessage(f"Ошибка планировщика: {e}", 5000)
    
    def export_materials_to_excel(self):
        """Экспорт материалов в Excel"""
        from PySide6.QtWidgets import QFileDialog
        from utils.excel_export import export_materials_to_excel
        import os
        
        # Выбор файла для сохранения
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить отчет Excel", 
            f"materials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel файлы (*.xlsx)"
        )
        
        if filename:
            try:
                export_materials_to_excel(filename)
                QMessageBox.information(self, "Экспорт завершен", 
                                      f"Материалы успешно экспортированы в файл:\n{filename}")
                # Предложить открыть файл
                reply = QMessageBox.question(self, "Открыть файл?", 
                                           "Хотите открыть созданный файл?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(filename)  # Windows
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать данные:\n{str(e)}")
    
    def show_scheduler_status(self):
        """Показать статус планировщика задач"""
        from utils.scheduler import task_scheduler
        
        try:
            if task_scheduler.scheduler.running:
                jobs_info = []
                for job in task_scheduler.scheduler.get_jobs():
                    next_run = job.next_run_time.strftime('%d.%m.%Y %H:%M:%S') if job.next_run_time else "Неизвестно"
                    jobs_info.append(f"• {job.name}: {next_run}")
                
                status_text = f"📊 Планировщик задач АКТИВЕН\n\nЗапланированные задачи:\n" + "\n".join(jobs_info)
            else:
                status_text = "❌ Планировщик задач НЕ АКТИВЕН"
            
            QMessageBox.information(self, "Статус планировщика", status_text)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить статус планировщика:\n{str(e)}")
    
    def manual_backup(self):
        """Создать резервную копию вручную"""
        from utils.scheduler import task_scheduler
        
        try:
            task_scheduler.backup_database()
            QMessageBox.information(self, "Резервное копирование", 
                                  "Резервная копия базы данных успешно создана!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать резервную копию:\n{str(e)}")
    
    def start_api_server(self):
        """Запуск API сервера"""
        import subprocess
        import sys
        
        try:
            # Запускаем API сервер в отдельном процессе
            subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--reload", "--port", "8000"])
            QMessageBox.information(self, "API Сервер", 
                                  "API сервер запускается...\n\n"
                                  "Адрес: http://localhost:8000\n"
                                  "Документация: http://localhost:8000/docs")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить API сервер:\n{str(e)}")
    
    def show_api_docs(self):
        """Показать документацию API"""
        import webbrowser
        
        try:
            webbrowser.open("http://localhost:8000/docs")
        except Exception as e:
            QMessageBox.information(self, "Документация API", 
                                  "API Эндпоинты:\n\n"
                                  "GET /materials - список материалов\n"
                                  "GET /samples - список образцов\n"
                                  "GET /sample_report/{id} - PDF отчет по образцу\n\n"
                                  "Для просмотра интерактивной документации\n"
                                  "запустите API сервер и перейдите по адресу:\n"
                                  "http://localhost:8000/docs")
    
    def show_audit_log(self):
        """Показать журнал действий пользователей"""
        from ui.dialogs.audit_log_dialog import AuditLogDialog
        
        try:
            dialog = AuditLogDialog(self)
            dialog.exec()
        except ImportError:
            # Если диалог еще не создан, показываем простое сообщение
            QMessageBox.information(self, "Журнал аудита", 
                                  "Функция просмотра журнала аудита в разработке.\n\n"
                                  "Все действия пользователей записываются в таблицу audit_log")
    
    def open_qr_generator(self):
        """Open QR code generator dialog"""
        try:
            from ui.dialogs.qr_dialog import QRDialog
            dialog = QRDialog(parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось открыть генератор QR-кодов: {str(e)}"
            )
    
    def open_certificate_browser(self):
        """Open certificate browser dialog"""
        from ui.dialogs.certificate_browser_dialog import CertificateBrowserDialog
        dialog = CertificateBrowserDialog(parent=self)
        dialog.exec()
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if theme_manager.current_theme == ThemeType.LIGHT:
            theme_manager.set_theme(ThemeType.DARK)
            self.dark_theme_action.setText("☀️ Светлая тема")
            self.dark_theme_action.setChecked(True)
            notification_manager.show_success("Темная тема активирована", parent_widget=self)
        else:
            theme_manager.set_theme(ThemeType.LIGHT)
            self.dark_theme_action.setText("🌙 Темная тема")
            self.dark_theme_action.setChecked(False)
            notification_manager.show_success("Светлая тема активирована", parent_widget=self)
        
        # Apply theme to all components
        self.apply_current_theme()
    
    def apply_current_theme(self):
        """Применение текущей темы ко всему приложению через QSS"""
        try:
            # Применяем QSS стили для текущей темы
            qss_content = theme_manager.get_current_stylesheet()
            self.setStyleSheet(qss_content)
            
            # Обновляем дашборд если он существует
            if hasattr(self, 'dashboard'):
                if hasattr(self.dashboard, 'apply_theme'):
                    self.dashboard.apply_theme()
                    
            # Обновляем другие вкладки - QSS применится автоматически
            # но для специфических виджетов может потребоваться дополнительная обработка
            self._update_tab_widgets()
            
        except Exception as e:
            print(f"Ошибка применения темы: {e}")
            # Fallback на старый метод
            self._apply_legacy_theme()
    
    def _update_tab_widgets(self):
        """Обновление специфических виджетов в вкладках"""
        # Проверяем, что tab_widget уже создан
        if not hasattr(self, 'tab_widget') or self.tab_widget is None:
            return
            
        # Обновляем таблицы в вкладках
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, 'refresh_styles'):
                tab_widget.refresh_styles()
    
    def _apply_legacy_theme(self):
        """Legacy метод применения темы через старую систему"""
        # Получаем цвета текущей темы
        colors = theme_manager.get_current_theme()['colors']
        
        # Применяем стили к главному окну
        self.setStyleSheet(theme_manager.generate_stylesheet())
        
        # Обновляем стиль для статусной строки
        if hasattr(self, 'status_bar') and self.status_bar is not None:
            self.status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: {colors['surface']};
                    color: {colors['text_secondary']};
                    border-top: 1px solid {colors['border']};
                }}
            """)
        
        # Обновляем стиль для вкладок только если они существуют
        if hasattr(self, 'tab_widget') and self.tab_widget is not None:
            self.tab_widget.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid {colors['border']};
                    background-color: {colors['surface']};
                    border-radius: 8px;
                }}
                QTabBar::tab {{
                    background-color: {colors['card']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border']};
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }}
                QTabBar::tab:selected {{
                    background-color: {colors['primary']};
                    color: white;
                }}
            """)
    
    def show_success_notification(self, message: str):
        """Показать уведомление об успехе"""
        notification_manager.show_success(message, parent_widget=self)
    
    def show_error_notification(self, message: str):
        """Показать уведомление об ошибке"""
        notification_manager.show_error(message, parent_widget=self)
    
    def show_warning_notification(self, message: str):
        """Показать предупреждение"""
        notification_manager.show_warning(message, parent_widget=self)
    
    def show_info_notification(self, message: str):
        """Показать информационное уведомление"""
        notification_manager.show_info(message, parent_widget=self)
    
    def toggle_notifications(self):
        """Переключение видимости панели уведомлений"""
        if hasattr(self, 'notification_panel'):
            if self.notification_panel.isVisible():
                self.notification_panel.hide()
                self.notifications_action.setText("Показать уведомления")
                notification_manager.show_info("Панель уведомлений скрыта", parent_widget=self)
            else:
                self.notification_panel.show()
                self.notifications_action.setText("Скрыть уведомления")
                notification_manager.show_info("Панель уведомлений показана", parent_widget=self)

from datetime import datetime