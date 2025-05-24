import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTabWidget, QPushButton, 
                             QMessageBox, QFrame, QStatusBar, QAction, QMenu,
                             QToolBar)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

from database.connection import SessionLocal
from models.models import UserRole
from ui.tabs.warehouse_tab import WarehouseTab
from ui.tabs.qc_tab import QCTab
from ui.tabs.lab_tab import LabTab
from ui.tabs.admin_tab import AdminTab
from ui.reference.material_grade_reference import MaterialGradeReference
from ui.reference.product_type_reference import ProductTypeReference
from ui.reference.supplier_reference import SupplierReference
from ui.icons.icon_provider import IconProvider

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
        self.setMinimumSize(1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Add header with user info
        header_layout = QHBoxLayout()
        
        logo_label = QLabel("ППСД")
        logo_font = QFont("Arial", 16)
        logo_font.setBold(True)
        logo_label.setFont(logo_font)
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch()
        
        user_label = QLabel(f"Пользователь: {self.user.full_name}")
        user_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(user_label)
        
        role_label = QLabel(f"Роль: {self.get_role_display_name(self.user.role)}")
        role_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(role_label)
        
        main_layout.addLayout(header_layout)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs based on user role
        self.add_tabs_for_user()
        
        # Установка сообщения в статусную строку
        self.status_bar.showMessage("Готово")
        
        # Create menu bar
        self.create_menu_bar()
    
    def add_tabs_for_user(self):
        """Add tabs based on user role and permissions"""
        # Everyone can see the materials tab if they can view
        if self.user.can_view:
            # Add tabs based on role
            if self.user.role == UserRole.WAREHOUSE.value:
                # Warehouse interface
                self.warehouse_tab = WarehouseTab(self.user, self)
                self.tab_widget.addTab(self.warehouse_tab, "Склад")
            
            if self.user.role == UserRole.QC.value:
                # QC interface
                self.qc_tab = QCTab(self.user, self)
                self.tab_widget.addTab(self.qc_tab, "ОТК")
            
            if self.user.role == UserRole.LAB.value:
                # Lab interface
                self.lab_tab = LabTab(self.user, self)
                self.tab_widget.addTab(self.lab_tab, "Лаборатория")
            
            # Admin can see all tabs
            if self.user.role == UserRole.ADMIN.value:
                self.warehouse_tab = WarehouseTab(self.user, self)
                self.tab_widget.addTab(self.warehouse_tab, "Склад")
                
                self.qc_tab = QCTab(self.user, self)
                self.tab_widget.addTab(self.qc_tab, "ОТК")
                
                self.lab_tab = LabTab(self.user, self)
                self.tab_widget.addTab(self.lab_tab, "Лаборатория")
                
                # Admin tab is only for admins
                self.admin_tab = AdminTab(self.user, self)
                self.tab_widget.addTab(self.admin_tab, "Администрирование")
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("Файл")
        
        # Logout action
        logout_action = QAction("Выйти из системы", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        # Exit action
        exit_action = QAction("Закрыть программу", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Reference menu
        if self.user.can_edit or self.user.role == UserRole.ADMIN.value:
            ref_menu = menu_bar.addMenu("Справочники")
            
            # Material Grade Reference
            material_grade_action = QAction(IconProvider.create_material_grade_icon(), "Марки материалов", self)
            material_grade_action.triggered.connect(self.show_material_grade_reference)
            ref_menu.addAction(material_grade_action)
            
            # Product Type Reference
            product_type_action = QAction(IconProvider.create_product_type_icon(), "Виды проката", self)
            product_type_action.triggered.connect(self.show_product_type_reference)
            ref_menu.addAction(product_type_action)
            
            # Supplier Reference
            supplier_action = QAction(IconProvider.create_supplier_icon(), "Поставщики", self)
            supplier_action.triggered.connect(self.show_supplier_reference)
            ref_menu.addAction(supplier_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Справка")
        
        # About action
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_material_grade_reference(self):
        """Show material grade reference window"""
        self.material_grade_ref = MaterialGradeReference(self)
        self.material_grade_ref.setWindowTitle("Справочник: Марки материалов")
        self.material_grade_ref.setWindowIcon(IconProvider.create_material_grade_icon())
        self.material_grade_ref.show()
    
    def show_product_type_reference(self):
        """Show product type reference window"""
        self.product_type_ref = ProductTypeReference(self)
        self.product_type_ref.setWindowTitle("Справочник: Виды проката")
        self.product_type_ref.setWindowIcon(IconProvider.create_product_type_icon())
        self.product_type_ref.show()
    
    def show_supplier_reference(self):
        """Show supplier reference window"""
        self.supplier_ref = SupplierReference(self)
        self.supplier_ref.setWindowTitle("Справочник: Поставщики")
        self.supplier_ref.setWindowIcon(IconProvider.create_supplier_icon())
        self.supplier_ref.show()
    
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
        QMessageBox.about(self, "О программе", 
                         "ППСД - Система проверки сертификатных данных\n\n"
                         "Версия 1.0\n\n"
                         "Система для контроля качества и проверки сертификатных данных "
                         "материалов на металлообрабатывающем предприятии.")
    
    def get_role_display_name(self, role):
        """Convert role code to display name"""
        role_names = {
            UserRole.ADMIN.value: "Администратор",
            UserRole.WAREHOUSE.value: "Кладовщик",
            UserRole.QC.value: "Сотрудник ОТК",
            UserRole.LAB.value: "Инженер ЦЗЛ"
        }
        return role_names.get(role, role) 