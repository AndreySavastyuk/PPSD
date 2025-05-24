"""
Диалоговое окно для просмотра и поиска сертификатов
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QComboBox, QPushButton, QFrame,
                              QDateEdit, QTreeWidget, QTreeWidgetItem, QSplitter,
                              QTextEdit, QFileDialog, QMessageBox, QCheckBox,
                              QMenu, QHeaderView, QTableWidget, QTableWidgetItem,
                              QInputDialog, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDate, QDateTime, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap, QImage

import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from ui.themes import theme_manager
from ui.icons.icon_provider import IconProvider
from utils.certificate_manager import CertificateManager, open_certificate
from utils.material_utils import clean_material_grade
from database.connection import SessionLocal
from models.models import MaterialEntry

class CertificateBrowserDialog(QDialog):
    """Диалог для просмотра и поиска сертификатов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Обзор сертификатов")
        self.setWindowIcon(IconProvider.create_certificate_icon())
        self.setMinimumSize(900, 600)
        
        self.init_ui()
        self.load_material_grades()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("Просмотр и поиск сертификатов материалов")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {theme_manager.get_color('primary')};")
        layout.addWidget(title_label)
        
        # Верхняя панель поиска - убираем черный фон
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 12, 12, 12)
        
        # Строка 1: Поиск по тексту и фильтр по марке
        search_row1 = QHBoxLayout()
        
        # Поиск по тексту
        search_label = QLabel("Поиск:")
        search_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('text_primary')};")
        search_row1.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.setStyleSheet(theme_manager.get_input_style())
        self.search_input.textChanged.connect(self.filter_certificates)
        search_row1.addWidget(self.search_input, 2)
        
        # Фильтр по марке
        grade_label = QLabel("Марка:")
        grade_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('text_primary')};")
        search_row1.addWidget(grade_label)
        
        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(theme_manager.get_input_style())
        self.grade_combo.currentIndexChanged.connect(self.filter_certificates)
        search_row1.addWidget(self.grade_combo, 1)
        
        search_layout.addLayout(search_row1)
        
        # Строка 2: Дополнительные фильтры
        search_row2 = QHBoxLayout()
        
        # Фильтр по типу продукции
        type_label = QLabel("Тип:")
        type_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('text_primary')};")
        search_row2.addWidget(type_label)
        
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItem("Все типы", "")
        self.product_type_combo.addItem("Круг", "rod")
        self.product_type_combo.addItem("Лист", "sheet")
        self.product_type_combo.addItem("Труба", "pipe")
        self.product_type_combo.addItem("Уголок", "angle")
        self.product_type_combo.addItem("Швеллер", "channel")
        self.product_type_combo.addItem("Другое", "other")
        self.product_type_combo.setStyleSheet(theme_manager.get_input_style())
        self.product_type_combo.currentIndexChanged.connect(self.filter_certificates)
        search_row2.addWidget(self.product_type_combo, 1)
        
        # Фильтр по заказу
        order_label = QLabel("Заказ №:")
        order_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('text_primary')};")
        search_row2.addWidget(order_label)
        
        self.order_input = QLineEdit()
        self.order_input.setPlaceholderText("Номер заказа...")
        self.order_input.setStyleSheet(theme_manager.get_input_style())
        self.order_input.textChanged.connect(self.filter_certificates)
        search_row2.addWidget(self.order_input, 1)
        
        # Фильтр по номеру плавки
        melt_label = QLabel("Плавка:")
        melt_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('text_primary')};")
        search_row2.addWidget(melt_label)
        
        self.melt_input = QLineEdit()
        self.melt_input.setPlaceholderText("Номер плавки...")
        self.melt_input.setStyleSheet(theme_manager.get_input_style())
        self.melt_input.textChanged.connect(self.filter_certificates)
        search_row2.addWidget(self.melt_input, 1)
        
        search_layout.addLayout(search_row2)
        
        # Строка 3: Кнопки и флажки
        search_row3 = QHBoxLayout()
        search_row3.setSpacing(10)  # Увеличиваем расстояние между элементами
        
        # Флажок поиска в подпапках
        self.search_subfolder_cb = QCheckBox("Искать в подпапках")
        self.search_subfolder_cb.setChecked(True)
        self.search_subfolder_cb.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        search_row3.addWidget(self.search_subfolder_cb)
        
        # Флажок поиска только по имени файла
        self.search_filename_cb = QCheckBox("Только имя файла")
        self.search_filename_cb.setChecked(True)
        self.search_filename_cb.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        search_row3.addWidget(self.search_filename_cb)
        
        # Растягивающийся элемент
        search_row3.addStretch()
        
        # Кнопка поиска
        self.search_btn = QPushButton("Искать")
        self.search_btn.setIcon(IconProvider.create_search_icon())
        self.search_btn.setStyleSheet(theme_manager.get_button_style("primary"))
        self.search_btn.setMinimumWidth(100)
        self.search_btn.clicked.connect(self.filter_certificates)
        search_row3.addWidget(self.search_btn)
        
        # Кнопка очистки фильтров
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setIcon(IconProvider.create_filter_icon())
        self.clear_btn.setStyleSheet(theme_manager.get_button_style("neutral"))
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.clicked.connect(self.clear_filters)
        search_row3.addWidget(self.clear_btn)
        
        search_layout.addLayout(search_row3)
        
        layout.addWidget(search_frame)
        
        # Основная область с результатами и предпросмотром
        main_layout = QHBoxLayout()
        
        # Левая панель с деревом и таблицей
        left_panel = QVBoxLayout()
        
        # Дерево с марками материалов и размерами - улучшаем стиль
        tree_frame = QFrame()
        tree_frame.setFrameShape(QFrame.Shape.StyledPanel)
        tree_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        
        tree_title = QLabel("Категории")
        tree_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme_manager.get_color('text_primary')};")
        tree_layout.addWidget(tree_title)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Марки и типоразмеры"])
        self.tree_widget.setColumnCount(1)
        self.tree_widget.itemClicked.connect(self.tree_item_clicked)
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {theme_manager.get_color('card')};
                border: none;
            }}
            QTreeWidget::item {{
                height: 24px;
                color: {theme_manager.get_color('text_primary')};
            }}
            QTreeWidget::item:hover {{
                background-color: {theme_manager.get_color('hover')};
            }}
            QTreeWidget::item:selected {{
                background-color: {theme_manager.get_color('primary')};
                color: white;
            }}
        """)
        tree_layout.addWidget(self.tree_widget)
        
        left_panel.addWidget(tree_frame)
        
        # Таблица с сертификатами - улучшаем стиль
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Shape.StyledPanel)
        table_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(8, 8, 8, 8)
        
        table_title = QLabel("Список сертификатов")
        table_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme_manager.get_color('text_primary')};")
        table_layout.addWidget(table_title)
        
        self.cert_table = QTableWidget()
        self.cert_table.setColumnCount(4)
        self.cert_table.setHorizontalHeaderLabels(["Имя файла", "Размер", "Дата", "Путь"])
        self.cert_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cert_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cert_table.setStyleSheet(f"""
            {theme_manager.get_table_style()}
            QTableWidget {{
                gridline-color: {theme_manager.get_color('border')};
                border: 1px solid {theme_manager.get_color('border')};
                padding: 5px;
            }}
            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {theme_manager.get_color('border')};
            }}
            QTableWidget::item:selected {{
                background-color: {theme_manager.get_color('primary')};
                color: white;
            }}
            QTableWidget::item:hover:!selected {{
                background-color: {theme_manager.get_color('hover')};
            }}
            QHeaderView::section {{
                background-color: {theme_manager.get_color('header')};
                color: {theme_manager.get_color('text_primary')};
                font-weight: bold;
                padding: 6px;
                border: 1px solid {theme_manager.get_color('border')};
            }}
        """)
        
        # Настройка ширины колонок
        header = self.cert_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Устанавливаем автоматическую высоту строк с минимальным значением
        self.cert_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.cert_table.verticalHeader().setMinimumSectionSize(30)  # Минимальная высота строки
        
        # Улучшаем внешний вид таблицы
        self.cert_table.setAlternatingRowColors(True)
        self.cert_table.setShowGrid(True)
        self.cert_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.cert_table.verticalHeader().setVisible(False)
        
        # Двойной клик для открытия сертификата
        self.cert_table.cellDoubleClicked.connect(self.open_selected_certificate)
        
        # Выбор строки для предпросмотра
        self.cert_table.selectionModel().selectionChanged.connect(self.update_preview)
        
        # Контекстное меню для таблицы
        self.cert_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cert_table.customContextMenuRequested.connect(self.show_context_menu)
        
        table_layout.addWidget(self.cert_table)
        
        left_panel.addWidget(table_frame)
        
        # Правая панель для предпросмотра
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        preview_title = QLabel("Предпросмотр")
        preview_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme_manager.get_color('text_primary')};")
        preview_layout.addWidget(preview_title)
        
        # Область для предпросмотра
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumWidth(300)
        self.preview_scroll.setStyleSheet(f"background-color: {theme_manager.get_color('background')};")
        
        self.preview_label = QLabel("Выберите сертификат для предпросмотра")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        self.preview_label.setWordWrap(True)
        
        self.preview_scroll.setWidget(self.preview_label)
        preview_layout.addWidget(self.preview_scroll)
        
        # Добавляем панели в основной лейаут
        main_layout.addLayout(left_panel, 7)  # 70% ширины
        main_layout.addWidget(preview_frame, 3)  # 30% ширины
        
        layout.addLayout(main_layout, 1)  # 1 - растягивается
        
        # Нижняя панель с информацией - улучшаем стиль
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card')};
                border: 1px solid {theme_manager.get_color('border')};
                border-radius: 8px;
            }}
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        
        self.status_label = QLabel("Готово к поиску сертификатов")
        self.status_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        info_layout.addWidget(self.status_label, 1)
        
        self.count_label = QLabel("Найдено: 0")
        self.count_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.get_color('primary')};")
        info_layout.addWidget(self.count_label)
        
        layout.addWidget(info_frame)
        
        # Панель кнопок
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)  # Увеличиваем расстояние между кнопками
        
        # Кнопка открытия сертификата
        self.open_btn = QPushButton("Открыть")
        self.open_btn.setIcon(IconProvider.create_certificate_icon())
        self.open_btn.setStyleSheet(theme_manager.get_button_style("primary"))
        self.open_btn.setMinimumWidth(120)
        self.open_btn.clicked.connect(self.open_selected_certificate)
        buttons_layout.addWidget(self.open_btn)
        
        # Кнопка копирования сертификата
        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setIcon(IconProvider.create_copy_icon())
        self.copy_btn.setStyleSheet(theme_manager.get_button_style("secondary"))
        self.copy_btn.setMinimumWidth(120)
        self.copy_btn.clicked.connect(self.copy_selected_certificate)
        buttons_layout.addWidget(self.copy_btn)
        
        # Кнопка прикрепления сертификата к материалу
        self.attach_btn = QPushButton("Прикрепить к материалу")
        self.attach_btn.setIcon(IconProvider.create_material_entry_icon())
        self.attach_btn.setStyleSheet(theme_manager.get_button_style("special"))
        self.attach_btn.setMinimumWidth(180)
        self.attach_btn.clicked.connect(self.attach_to_material)
        buttons_layout.addWidget(self.attach_btn)
        
        # Растягивающийся элемент
        buttons_layout.addStretch()
        
        # Кнопка закрытия
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setStyleSheet(theme_manager.get_button_style("neutral"))
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_material_grades(self):
        """Загрузка марок материалов из директории сертификатов"""
        self.grade_combo.clear()
        self.grade_combo.addItem("Все марки", "")
        
        certificates_by_grade = CertificateManager.list_certificates_by_material_grade()
        
        # Обновляем выпадающий список марок
        for grade, count in certificates_by_grade.items():
            self.grade_combo.addItem(f"{grade} ({count})", grade)
        
        # Обновляем дерево марок и типоразмеров
        self.update_tree_widget()
    
    def update_tree_widget(self):
        """Обновление дерева марок и типоразмеров"""
        self.tree_widget.clear()
        
        # Создаем корневой элемент
        root_item = QTreeWidgetItem(self.tree_widget, ["Все сертификаты"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, "")
        root_item.setExpanded(True)
        
        # Корневая директория сертификатов
        certs_dir = CertificateManager.ALL_CERTS_DIR
        
        if os.path.exists(certs_dir):
            # Проходим по всем маркам материалов
            for grade_dir in os.listdir(certs_dir):
                grade_path = os.path.join(certs_dir, grade_dir)
                if not os.path.isdir(grade_path):
                    continue
                
                # Считаем количество файлов для марки
                grade_count = 0
                for root, _, files in os.walk(grade_path):
                    grade_count += len([f for f in files if f.lower().endswith('.pdf')])
                
                # Создаем элемент для марки материала
                grade_item = QTreeWidgetItem(root_item, [f"{grade_dir} ({grade_count})"])
                grade_item.setData(0, Qt.ItemDataRole.UserRole, grade_path)
                
                # Проходим по всем типоразмерам внутри марки
                for size_type_dir in os.listdir(grade_path):
                    size_type_path = os.path.join(grade_path, size_type_dir)
                    if not os.path.isdir(size_type_path):
                        continue
                    
                    # Считаем количество файлов для типоразмера
                    size_type_count = 0
                    for root, _, files in os.walk(size_type_path):
                        size_type_count += len([f for f in files if f.lower().endswith('.pdf')])
                    
                    # Создаем элемент для типоразмера
                    size_type_item = QTreeWidgetItem(grade_item, [f"{size_type_dir} ({size_type_count})"])
                    size_type_item.setData(0, Qt.ItemDataRole.UserRole, size_type_path)
        
        # Добавляем элемент для заказов
        orders_item = QTreeWidgetItem(self.tree_widget, ["Заказы"])
        orders_item.setData(0, Qt.ItemDataRole.UserRole, CertificateManager.ORDERS_DIR)
        
        # Добавляем элемент для приемки
        reception_item = QTreeWidgetItem(self.tree_widget, ["На приемке"])
        reception_item.setData(0, Qt.ItemDataRole.UserRole, CertificateManager.RECEPTION_DIR)
    
    def tree_item_clicked(self, item, column):
        """Обработка клика по элементу дерева"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.load_certificates_from_path(path)
    
    def load_certificates_from_path(self, path):
        """Загрузка сертификатов из указанного пути"""
        self.cert_table.setRowCount(0)
        
        if not os.path.exists(path):
            return
        
        # Получаем файлы из директории
        certificates = []
        
        if os.path.isdir(path):
            # Если выбрана поддиректория, поиск файлов в ней
            if self.search_subfolder_cb.isChecked():
                # Рекурсивный поиск
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            certificates.append(os.path.join(root, file))
            else:
                # Только в текущей директории
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path) and file.lower().endswith('.pdf'):
                        certificates.append(file_path)
        
        # Добавляем в таблицу
        self.add_certificates_to_table(certificates)
    
    def add_certificates_to_table(self, certificates):
        """Добавление сертификатов в таблицу"""
        self.cert_table.setRowCount(0)
        
        for row, cert_path in enumerate(certificates):
            file_info = Path(cert_path)
            file_name = file_info.name
            file_size = file_info.stat().st_size / 1024  # KB
            file_date = datetime.fromtimestamp(file_info.stat().st_mtime)
            
            self.cert_table.insertRow(row)
            
            # Имя файла
            name_item = QTableWidgetItem(file_name)
            # Устанавливаем подсказку с полным именем файла
            name_item.setToolTip(file_name)
            self.cert_table.setItem(row, 0, name_item)
            
            # Размер
            size_str = f"{file_size:.1f} KB" if file_size < 1024 else f"{file_size/1024:.1f} MB"
            self.cert_table.setItem(row, 1, QTableWidgetItem(size_str))
            
            # Дата
            self.cert_table.setItem(row, 2, QTableWidgetItem(file_date.strftime("%d.%m.%Y %H:%M")))
            
            # Путь (скрытый)
            path_item = QTableWidgetItem(cert_path)
            path_item.setData(Qt.ItemDataRole.UserRole, cert_path)  # Сохраняем полный путь
            path_item.setToolTip(cert_path)  # Подсказка с полным путем
            self.cert_table.setItem(row, 3, path_item)
        
        # Обновляем счетчик
        self.count_label.setText(f"Найдено: {len(certificates)}")
        
        # Сортируем по дате (новые сверху)
        self.cert_table.sortItems(2, Qt.SortOrder.DescendingOrder)
    
    def filter_certificates(self):
        """Фильтрация сертификатов по заданным критериям"""
        # Получаем значения фильтров
        search_text = self.search_input.text().strip()
        material_grade = self.grade_combo.currentData()
        product_type = self.product_type_combo.currentData()
        order_number = self.order_input.text().strip()
        melt_number = self.melt_input.text().strip()
        
        # Ищем сертификаты
        certificates = CertificateManager.search_certificates(
            search_text=search_text,
            material_grade=material_grade,
            supplier=None,  # TODO: Добавить фильтр по поставщику
            melt_number=melt_number,
            order_number=order_number,
            product_type=product_type
        )
        
        # Добавляем результаты в таблицу
        self.add_certificates_to_table(certificates)
        
        # Обновляем статус
        self.status_label.setText(f"Поиск выполнен, применено фильтров: {sum(1 for f in [search_text, material_grade, product_type, order_number, melt_number] if f)}")
    
    def clear_filters(self):
        """Очистка всех фильтров"""
        self.search_input.clear()
        self.grade_combo.setCurrentIndex(0)
        self.product_type_combo.setCurrentIndex(0)
        self.order_input.clear()
        self.melt_input.clear()
        
        # Обновляем результаты
        self.filter_certificates()
    
    def get_selected_certificate_path(self):
        """Получение пути к выбранному сертификату"""
        selected_rows = self.cert_table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        return self.cert_table.item(row, 3).data(Qt.ItemDataRole.UserRole)
    
    def open_selected_certificate(self):
        """Открытие выбранного сертификата"""
        cert_path = self.get_selected_certificate_path()
        if not cert_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите сертификат для открытия")
            return
        
        if not os.path.exists(cert_path):
            QMessageBox.warning(self, "Предупреждение", f"Файл не найден:\n{cert_path}")
            return
        
        # Открываем сертификат
        if not open_certificate(cert_path):
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть файл сертификата")
    
    def copy_selected_certificate(self):
        """Копирование выбранного сертификата"""
        cert_path = self.get_selected_certificate_path()
        if not cert_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите сертификат для копирования")
            return
        
        if not os.path.exists(cert_path):
            QMessageBox.warning(self, "Предупреждение", f"Файл не найден:\n{cert_path}")
            return
        
        # Выбор пути для сохранения
        file_name = os.path.basename(cert_path)
        target_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить сертификат", file_name, "PDF files (*.pdf)"
        )
        
        if not target_path:
            return  # Пользователь отменил сохранение
        
        try:
            import shutil
            shutil.copy2(cert_path, target_path)
            QMessageBox.information(self, "Успешно", f"Сертификат скопирован в:\n{target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать файл:\n{str(e)}")
    
    def show_context_menu(self, position):
        """Показ контекстного меню для таблицы сертификатов"""
        menu = QMenu(self)
        
        open_action = QAction("Открыть", self)
        open_action.triggered.connect(self.open_selected_certificate)
        menu.addAction(open_action)
        
        copy_action = QAction("Копировать", self)
        copy_action.triggered.connect(self.copy_selected_certificate)
        menu.addAction(copy_action)
        
        # Добавляем действие прикрепления к материалу
        attach_action = QAction("Прикрепить к материалу", self)
        attach_action.triggered.connect(self.attach_to_material)
        menu.addAction(attach_action)
        
        # Показываем меню на позиции курсора
        menu.exec(self.cert_table.mapToGlobal(position))
    
    def attach_to_material(self):
        """Прикрепление сертификата к существующему материалу"""
        cert_path = self.get_selected_certificate_path()
        if not cert_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите сертификат для прикрепления")
            return
            
        if not os.path.exists(cert_path):
            QMessageBox.warning(self, "Предупреждение", f"Файл не найден:\n{cert_path}")
            return
            
        # Запрашиваем ID материала, к которому нужно прикрепить сертификат
        material_id, ok = QInputDialog.getInt(
            self, 
            "Прикрепление сертификата", 
            "Введите ID материала:",
            1, 1, 9999, 1
        )
        
        if not ok:
            return
            
        # Проверяем существование материала и обновляем путь к сертификату
        db = SessionLocal()
        try:
            material = db.query(MaterialEntry).filter(MaterialEntry.id == material_id).first()
            
            if not material:
                QMessageBox.warning(self, "Ошибка", f"Материал с ID {material_id} не найден")
                return
                
            # Обновляем путь к сертификату
            material.certificate_file_path = cert_path
            db.commit()
            
            QMessageBox.information(
                self, 
                "Успешно", 
                f"Сертификат прикреплен к материалу #{material_id} ({material.material_grade})"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить сертификат: {str(e)}")
        finally:
            db.close()

    def update_preview(self):
        """Обновление предпросмотра выбранного сертификата"""
        cert_path = self.get_selected_certificate_path()
        if not cert_path or not os.path.exists(cert_path):
            self.preview_label = QLabel("Выберите сертификат для предпросмотра")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
            self.preview_label.setWordWrap(True)
            self.preview_scroll.setWidget(self.preview_label)
            return
            
        try:
            # Показываем иконку PDF как базовый вариант
            preview_icon = IconProvider.create_certificate_icon(64)
            
            self.preview_label = QLabel()
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setPixmap(preview_icon.pixmap(64, 64))
            self.preview_label.setWordWrap(True)
            
            # Добавляем информацию о файле
            file_info = Path(cert_path)
            file_name = file_info.name
            file_size = file_info.stat().st_size / 1024  # KB
            file_date = datetime.fromtimestamp(file_info.stat().st_mtime)
            
            info_text = f"\n\nИмя файла: {file_name}\n"
            info_text += f"Размер: {file_size:.1f} KB\n"
            info_text += f"Дата: {file_date.strftime('%d.%m.%Y %H:%M')}\n"
            info_text += f"Путь: {cert_path}"
            
            self.preview_label.setText(info_text)
            self.preview_scroll.setWidget(self.preview_label)
                
        except Exception as e:
            self.preview_label = QLabel(f"Ошибка предпросмотра:\n{str(e)}")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setStyleSheet(f"color: {theme_manager.get_color('error')};")
            self.preview_label.setWordWrap(True)
            self.preview_scroll.setWidget(self.preview_label) 