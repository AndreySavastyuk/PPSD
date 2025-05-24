from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QDialog, QFormLayout, 
                             QLineEdit, QMessageBox, QHeaderView, QTextEdit, QLabel,
                             QPlainTextEdit, QComboBox, QGroupBox, QDateEdit, QFrame,
                             QFileDialog, QCheckBox, QTabWidget)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QDateTime, Signal
import os
import datetime
from database.connection import SessionLocal
from models.models import LabTest, MaterialEntry, TestType, User, MaterialStatus
from ui.reference.base_reference_dialog import BaseReferenceDialog

class LabTestDetailDialog(BaseReferenceDialog):
    test_updated = Signal()  # Сигнал об обновлении теста
    
    def __init__(self, parent=None, test_id=None, material_entry_id=None):
        super().__init__(parent)
        self.test_id = test_id
        self.material_entry_id = material_entry_id
        self.test = None
        self.material_entry = None
        self.original_status = None
        
        # Загрузка данных
        self.load_data()
        self.init_ui()
        
    def load_data(self):
        """Загрузка данных о тесте и материале"""
        session = SessionLocal()
        try:
            if self.test_id:
                # Режим редактирования
                self.test = session.query(LabTest).get(self.test_id)
                if self.test:
                    self.material_entry_id = self.test.material_entry_id
                    self.material_entry = session.query(MaterialEntry).get(self.material_entry_id)
                    self.original_status = self.material_entry.status
            elif self.material_entry_id:
                # Режим создания
                self.material_entry = session.query(MaterialEntry).get(self.material_entry_id)
                self.original_status = self.material_entry.status
        finally:
            session.close()
            
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Отчет об испытании")
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Информация о материале
        material_group = QGroupBox("Информация о материале")
        material_layout = QFormLayout()
        material_group.setLayout(material_layout)
        
        self.material_label = QLabel()
        material_layout.addRow("Материал:", self.material_label)
        
        self.certificate_label = QLabel()
        material_layout.addRow("Сертификат №:", self.certificate_label)
        
        self.batch_label = QLabel()
        material_layout.addRow("Партия №:", self.batch_label)
        
        self.melt_label = QLabel()
        material_layout.addRow("Плавка №:", self.melt_label)
        
        if self.material_entry:
            self.material_label.setText(f"{self.material_entry.material_grade} ({self.material_entry.material_type})")
            self.certificate_label.setText(self.material_entry.certificate_number)
            self.batch_label.setText(self.material_entry.batch_number)
            self.melt_label.setText(self.material_entry.melt_number)
        
        main_layout.addWidget(material_group)
        
        # Вкладки для разных типов информации
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Вкладка общей информации
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # Тип испытания
        self.test_type_combo = QComboBox()
        general_layout.addRow("Тип испытания:", self.test_type_combo)
        
        # Загрузка типов испытаний
        session = SessionLocal()
        try:
            test_types = session.query(TestType).filter(TestType.is_deleted == False).all()
            for tt in test_types:
                self.test_type_combo.addItem(f"{tt.name} ({tt.code})", tt.id)
                
            # Загрузка инженеров ЦЗЛ для выбора исполнителя
            lab_engineers = session.query(User).filter(User.role == "lab", User.is_active == True).all()
            self.engineer_combo = QComboBox()
            for engineer in lab_engineers:
                self.engineer_combo.addItem(engineer.full_name, engineer.id)
                
            if self.test and self.test.test_type_id:
                # Найти индекс выбранного типа испытания
                for i in range(self.test_type_combo.count()):
                    if self.test_type_combo.itemData(i) == self.test.test_type_id:
                        self.test_type_combo.setCurrentIndex(i)
                        break
            
            if self.test and self.test.performed_by_id:
                # Найти индекс выбранного исполнителя
                for i in range(self.engineer_combo.count()):
                    if self.engineer_combo.itemData(i) == self.test.performed_by_id:
                        self.engineer_combo.setCurrentIndex(i)
                        break
        finally:
            session.close()
            
        general_layout.addRow("Испытание выполнил:", self.engineer_combo)
        
        # Дата выполнения
        self.performed_date = QDateEdit()
        self.performed_date.setCalendarPopup(True)
        self.performed_date.setDate(datetime.datetime.now().date())
        if self.test and self.test.performed_at:
            self.performed_date.setDate(self.test.performed_at.date())
        general_layout.addRow("Дата выполнения:", self.performed_date)
        
        # Дата завершения
        self.completed_date = QDateEdit()
        self.completed_date.setCalendarPopup(True)
        self.completed_date.setDate(datetime.datetime.now().date())
        if self.test and self.test.completed_at:
            self.completed_date.setDate(self.test.completed_at.date())
        general_layout.addRow("Дата завершения:", self.completed_date)
        
        # Результат испытания
        self.is_passed_combo = QComboBox()
        self.is_passed_combo.addItem("Не завершено", None)
        self.is_passed_combo.addItem("Соответствует", True)
        self.is_passed_combo.addItem("Не соответствует", False)
        if self.test and self.test.is_passed is not None:
            self.is_passed_combo.setCurrentIndex(1 if self.test.is_passed else 2)
        else:
            self.is_passed_combo.setCurrentIndex(0)
        # Цветовая индикация и иконка
        self.result_icon_label = QLabel()
        self.update_result_icon()
        self.is_passed_combo.currentIndexChanged.connect(self.update_result_icon)
        result_row = QHBoxLayout()
        result_row.addWidget(self.is_passed_combo)
        result_row.addWidget(self.result_icon_label)
        general_layout.addRow("Результат:", result_row)
        
        # Изменение статуса материала
        self.update_status_check = QCheckBox("Обновить статус материала")
        self.update_status_check.setChecked(True)
        general_layout.addRow("", self.update_status_check)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem("На испытаниях", MaterialStatus.TESTING.value)
        self.status_combo.addItem("Испытания завершены", MaterialStatus.TESTING_COMPLETED.value)
        self.status_combo.addItem("Одобрен", MaterialStatus.APPROVED.value)
        self.status_combo.addItem("Отклонен", MaterialStatus.REJECTED.value)
        
        # Установим текущий статус
        if self.material_entry:
            for i in range(self.status_combo.count()):
                if self.status_combo.itemData(i) == self.material_entry.status:
                    self.status_combo.setCurrentIndex(i)
                    break
                    
        general_layout.addRow("Новый статус:", self.status_combo)
        
        # Вкладка для результатов
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        results_label = QLabel("Результаты испытания:")
        results_layout.addWidget(results_label)
        
        self.results_text = QPlainTextEdit()
        if self.test and self.test.results:
            self.results_text.setPlainText(self.test.results)
        results_layout.addWidget(self.results_text)
        
        # Вкладка для отчета
        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        
        report_path_layout = QHBoxLayout()
        report_path_label = QLabel("Файл отчета:")
        self.report_path_edit = QLineEdit()
        self.report_path_edit.setReadOnly(True)
        if self.test and self.test.report_file_path:
            self.report_path_edit.setText(self.test.report_file_path)
            
        browse_button = QPushButton("Обзор...")
        browse_button.clicked.connect(self.browse_report)
        view_report_button = QPushButton("Просмотр")
        view_report_button.clicked.connect(self.view_report)
        
        report_path_layout.addWidget(report_path_label)
        report_path_layout.addWidget(self.report_path_edit)
        report_path_layout.addWidget(browse_button)
        report_path_layout.addWidget(view_report_button)
        
        report_layout.addLayout(report_path_layout)
        
        # Вкладка для комментариев (чат)
        comments_tab = QWidget()
        comments_layout = QVBoxLayout(comments_tab)
        self.comments_display = QTextEdit()
        self.comments_display.setReadOnly(True)
        comments_layout.addWidget(self.comments_display)
        self.new_comment_edit = QLineEdit()
        self.new_comment_edit.setPlaceholderText("Введите комментарий...")
        comments_layout.addWidget(self.new_comment_edit)
        add_comment_btn = QPushButton("Добавить комментарий")
        add_comment_btn.clicked.connect(self.add_comment)
        comments_layout.addWidget(add_comment_btn)
        self.tab_widget.addTab(comments_tab, "Комментарии")

        # Вкладка для истории изменений
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        history_layout.addWidget(self.history_display)
        self.tab_widget.addTab(history_tab, "История изменений")
        
        # Вкладка для графика результатов
        try:
            import matplotlib
            matplotlib.use('Agg')
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            import re
            graph_tab = QWidget()
            graph_layout = QVBoxLayout(graph_tab)
            self.figure = Figure(figsize=(4,2))
            self.canvas = FigureCanvas(self.figure)
            graph_layout.addWidget(self.canvas)
            self.tab_widget.addTab(graph_tab, "График")
            self.plot_results_graph()
        except Exception as e:
            pass
        
        # Добавление вкладок
        self.tab_widget.addTab(general_tab, "Общая информация")
        self.tab_widget.addTab(results_tab, "Результаты")
        self.tab_widget.addTab(report_tab, "Отчет")
        
        # Кнопки внизу формы
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_test)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
        
        # После инициализации UI, загрузить комментарии и историю
        self.load_comments_and_history()
    
    def browse_report(self):
        """Выбор файла отчета"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выбрать отчет",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            # Сохраняем файл в целевую директорию
            target_dir = os.path.join("docs_storage", "test_reports")
            os.makedirs(target_dir, exist_ok=True)
            
            # Имя файла: test_<material_id>_<date>_<test_type>.pdf
            test_type_id = self.test_type_combo.currentData()
            session = SessionLocal()
            try:
                test_type = session.query(TestType).get(test_type_id)
                test_code = test_type.code if test_type else "test"
            finally:
                session.close()
                
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            filename = f"test_{self.material_entry_id}_{date_str}_{test_code}.pdf"
            target_path = os.path.join(target_dir, filename)
            
            # Копируем файл
            import shutil
            shutil.copy2(file_path, target_path)
            
            # Обновляем путь
            self.report_path_edit.setText(target_path)
            
    def view_report(self):
        """Просмотр файла отчета"""
        report_path = self.report_path_edit.text()
        if not report_path or not os.path.exists(report_path):
            QMessageBox.warning(self, "Ошибка", "Файл отчета не найден")
            return
            
        # Открываем файл с помощью системного просмотрщика
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Windows':
                os.startfile(report_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', report_path))
            else:  # Linux
                subprocess.call(('xdg-open', report_path))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
            
    def save_test(self):
        """Сохранение испытания"""
        # Проверка данных
        test_type_id = self.test_type_combo.currentData()
        if not test_type_id:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать тип испытания")
            return
            
        performed_by_id = self.engineer_combo.currentData()
        if not performed_by_id:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать исполнителя")
            return
            
        session = SessionLocal()
        try:
            # Тип испытания для определения test_type (строки)
            test_type_obj = session.query(TestType).get(test_type_id)
            test_type_str = test_type_obj.code if test_type_obj else "other"
            
            # Получаем значение результата (True/False/None)
            is_passed_index = self.is_passed_combo.currentIndex()
            is_passed_value = None
            if is_passed_index == 1:
                is_passed_value = True
            elif is_passed_index == 2:
                is_passed_value = False
                
            performed_date = self.performed_date.date().toPython()
            performed_datetime = datetime.datetime.combine(
                performed_date, 
                datetime.datetime.now().time()
            )
            
            completed_date = None
            if is_passed_value is not None:  # Если есть результат, то есть и дата завершения
                completed_date = self.completed_date.date().toPython()
                completed_datetime = datetime.datetime.combine(
                    completed_date, 
                    datetime.datetime.now().time()
                )
            else:
                completed_datetime = None
                
            if self.test:
                # Обновляем существующий тест
                self.test.test_type = test_type_str
                self.test.test_type_id = test_type_id
                self.test.performed_by_id = performed_by_id
                self.test.performed_at = performed_datetime
                self.test.completed_at = completed_datetime
                self.test.is_passed = is_passed_value
                self.test.results = self.results_text.toPlainText() or None
                self.test.report_file_path = self.report_path_edit.text() or None
                
                session.add(self.test)
            else:
                # Создаем новый тест
                new_test = LabTest(
                    material_entry_id=self.material_entry_id,
                    test_type=test_type_str,
                    test_type_id=test_type_id,
                    performed_by_id=performed_by_id,
                    performed_at=performed_datetime,
                    completed_at=completed_datetime,
                    is_passed=is_passed_value,
                    results=self.results_text.toPlainText() or None,
                    report_file_path=self.report_path_edit.text() or None
                )
                session.add(new_test)
                self.test = new_test
                
            # Обновляем статус материала, если выбрано
            if self.update_status_check.isChecked() and self.material_entry:
                new_status = self.status_combo.currentData()
                if new_status != self.original_status:
                    self.material_entry.status = new_status
                    session.add(self.material_entry)
                    
            session.commit()
            self.test_updated.emit()
            self.accept()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")
        finally:
            session.close()

    def load_comments_and_history(self):
        session = SessionLocal()
        try:
            if self.test_id:
                test = session.query(LabTest).get(self.test_id)
                # Комментарии
                if hasattr(test, 'comments') and test.comments:
                    self.comments_display.setPlainText(test.comments)
                else:
                    self.comments_display.setPlainText("Комментариев нет.")
                # История изменений (пример: статус, результат, даты)
                history = []
                if test:
                    if test.performed_at:
                        history.append(f"Создано: {test.performed_at.strftime('%d.%m.%Y %H:%M')}")
                    if test.completed_at:
                        history.append(f"Завершено: {test.completed_at.strftime('%d.%m.%Y %H:%M')}")
                    if test.is_passed is not None:
                        res = "Годен" if test.is_passed else "Брак"
                        history.append(f"Результат испытания: {res}")
                    if test.report_file_path:
                        history.append(f"Файл отчета: {os.path.basename(test.report_file_path)}")
                self.history_display.setPlainText("\n".join(history) if history else "Нет истории изменений.")
        finally:
            session.close()

    def add_comment(self):
        comment = self.new_comment_edit.text().strip()
        if not comment:
            QMessageBox.warning(self, "Ошибка", "Введите текст комментария")
            return
        session = SessionLocal()
        try:
            test = session.query(LabTest).get(self.test_id)
            user = session.query(User).get(self.parent.user.id) if hasattr(self.parent, 'user') else None
            author = user.full_name if user else "Пользователь"
            timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            new_comment = f"[{timestamp}] {author}: {comment}\n"
            if hasattr(test, 'comments') and test.comments:
                test.comments += new_comment
            else:
                test.comments = new_comment
            session.commit()
            self.comments_display.append(new_comment)
            self.new_comment_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении комментария: {str(e)}")
        finally:
            session.close()

    def update_result_icon(self):
        idx = self.is_passed_combo.currentIndex()
        if idx == 1:
            self.result_icon_label.setText("✔")
            self.result_icon_label.setStyleSheet("color: green; font-size: 18px;")
            self.setStyleSheet("QDialog { border: 2px solid #6c6; }")
        elif idx == 2:
            self.result_icon_label.setText("✖")
            self.result_icon_label.setStyleSheet("color: red; font-size: 18px;")
            self.setStyleSheet("QDialog { border: 2px solid #c66; }")
        else:
            self.result_icon_label.setText("⏳")
            self.result_icon_label.setStyleSheet("color: orange; font-size: 18px;")
            self.setStyleSheet("QDialog { border: 2px solid #cc6; }")

    def plot_results_graph(self):
        try:
            from matplotlib.figure import Figure
            import re
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            # Парсим числовые значения из results
            results_text = self.results_text.toPlainText() if hasattr(self, 'results_text') else ""
            pattern = r"([A-Za-zА-Яа-яёЁ]+)\s*[=:]\s*([\d\.]+)"
            matches = re.findall(pattern, results_text)
            if matches:
                labels = [k for k, v in matches]
                values = [float(v) for k, v in matches]
                ax.bar(labels, values, color='#4a90e2')
                ax.set_ylabel('Значение')
                ax.set_title('Результаты испытания')
                self.canvas.draw()
            else:
                ax.text(0.5, 0.5, 'Нет числовых данных для графика', ha='center', va='center', fontsize=12)
                self.canvas.draw()
        except Exception:
            pass 