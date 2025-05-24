from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QTextEdit, QMessageBox,
                              QFormLayout, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from database.connection import SessionLocal
from models.models import MaterialEntry, MaterialStatus, Supplier, User
from utils.status_manager import StatusManager
from utils.telegram_bot import (send_qc_approval_notification, send_qc_rejection_notification,
                               send_lab_test_failure_notification, send_final_acceptance_notification)
from utils.material_utils import get_status_display_name
from datetime import datetime

class StatusChangeDialog(QDialog):
    """Диалог для изменения статуса материала"""
    
    def __init__(self, material_id, user, parent=None):
        super().__init__(parent)
        self.material_id = material_id
        self.user = user
        self.material = None
        self.setWindowTitle("Изменение статуса материала")
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_material_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Изменение статуса материала")
        self.setMinimumWidth(500)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        
        # Информация о материале
        material_group = QGroupBox("Информация о материале")
        material_layout = QFormLayout()
        
        self.material_grade_label = QLabel("-")
        material_layout.addRow("Марка материала:", self.material_grade_label)
        
        self.material_type_label = QLabel("-")
        material_layout.addRow("Тип материала:", self.material_type_label)
        
        self.batch_label = QLabel("-")
        material_layout.addRow("Партия:", self.batch_label)
        
        self.melt_label = QLabel("-")
        material_layout.addRow("Плавка:", self.melt_label)
        
        self.current_status_label = QLabel("-")
        self.current_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        material_layout.addRow("Текущий статус:", self.current_status_label)
        
        material_group.setLayout(material_layout)
        main_layout.addWidget(material_group)
        
        # Новый статус
        status_group = QGroupBox("Изменение статуса")
        status_layout = QVBoxLayout()
        
        # Выбор статуса
        status_selection = QFormLayout()
        
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(200)
        self.status_combo.currentIndexChanged.connect(self.on_status_changed)
        status_selection.addRow("Новый статус:", self.status_combo)
        
        status_layout.addLayout(status_selection)
        
        # Описание статуса
        self.status_description_label = QLabel("")
        self.status_description_label.setWordWrap(True)
        status_layout.addWidget(self.status_description_label)
        
        # Информация о переходе
        self.transition_info_label = QLabel("")
        self.transition_info_label.setWordWrap(True)
        self.transition_info_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.transition_info_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Дополнительные причины брака для статуса "Отклонен" (изначально скрыты)
        self.defects_group = QGroupBox("Причины отклонения (ОТК)")
        self.defects_group.setVisible(False)
        defects_layout = QVBoxLayout()
        
        self.defect_certificate = QCheckBox("Проблемы с сертификатом")
        defects_layout.addWidget(self.defect_certificate)
        
        self.defect_dimensions = QCheckBox("Отклонения по размерам")
        defects_layout.addWidget(self.defect_dimensions)
        
        self.defect_chemical = QCheckBox("Отклонения по хим. составу")
        defects_layout.addWidget(self.defect_chemical)
        
        self.defect_visual = QCheckBox("Визуальные дефекты")
        defects_layout.addWidget(self.defect_visual)
        
        self.defect_other = QCheckBox("Другие причины")
        defects_layout.addWidget(self.defect_other)
        
        self.defects_group.setLayout(defects_layout)
        main_layout.addWidget(self.defects_group)
        
        # Дополнительные причины брака для результатов лабораторных испытаний
        self.lab_issues_group = QGroupBox("Результаты испытаний (ЦЗЛ)")
        self.lab_issues_group.setVisible(False)
        lab_issues_layout = QVBoxLayout()
        
        self.lab_issue_hardness = QCheckBox("Не соответствует по твердости")
        lab_issues_layout.addWidget(self.lab_issue_hardness)
        
        self.lab_issue_tensile = QCheckBox("Не соответствует по прочности")
        lab_issues_layout.addWidget(self.lab_issue_tensile)
        
        self.lab_issue_impact = QCheckBox("Не соответствует по ударной вязкости")
        lab_issues_layout.addWidget(self.lab_issue_impact)
        
        self.lab_issue_chemical = QCheckBox("Не соответствует по хим. составу")
        lab_issues_layout.addWidget(self.lab_issue_chemical)
        
        self.lab_issue_other = QCheckBox("Другие причины")
        lab_issues_layout.addWidget(self.lab_issue_other)
        
        self.lab_issues_group.setLayout(lab_issues_layout)
        main_layout.addWidget(self.lab_issues_group)
        
        # Комментарий
        comment_group = QGroupBox("Комментарий")
        comment_layout = QVBoxLayout()
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Введите комментарий к изменению статуса (опционально)...")
        self.comment_edit.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_edit)
        
        comment_group.setLayout(comment_layout)
        main_layout.addWidget(comment_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        buttons_layout.addStretch()
        
        self.ok_btn = QPushButton("Изменить статус")
        self.ok_btn.setMinimumWidth(120)
        self.ok_btn.clicked.connect(self.change_status)
        buttons_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def load_material_data(self):
        """Загрузка данных о материале"""
        db = SessionLocal()
        try:
            # Получение материала по ID
            self.material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
            
            if not self.material:
                QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                self.reject()
                return
            
            # Заполнение данных
            self.material_grade_label.setText(self.material.material_grade)
            
            # Отображение типа материала
            material_types = {
                "rod": "Круг",
                "sheet": "Лист",
                "pipe": "Труба",
                "angle": "Уголок",
                "channel": "Швеллер",
                "other": "Другое"
            }
            material_type = material_types.get(self.material.material_type, self.material.material_type)
            self.material_type_label.setText(material_type)
            
            self.batch_label.setText(self.material.batch_number or "Нет")
            self.melt_label.setText(self.material.melt_number)
            self.current_status_label.setText(
                get_status_display_name(self.material.status)
            )
            
            # Определение доступных переходов статуса в зависимости от роли пользователя
            available_statuses = StatusManager.get_available_transitions(
                self.material.status, 
                self.user.role
            )
            
            # Очищаем комбобокс
            self.status_combo.clear()
            
            if not available_statuses:
                self.status_combo.addItem("Нет доступных переходов", None)
                self.transition_info_label.setText(
                    "❌ Нет доступных переходов статуса для вашей роли или текущий статус является финальным."
                )
                self.ok_btn.setEnabled(False)
                return
            
            # Добавляем доступные статусы
            for status in available_statuses:
                display_name = get_status_display_name(status)
                self.status_combo.addItem(display_name, status)
            
            self.transition_info_label.setText(
                f"✓ Доступны {len(available_statuses)} вариантов перехода статуса для вашей роли."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
            self.reject()
        finally:
            db.close()
    
    def on_status_changed(self):
        """Обработка изменения выбранного статуса"""
        selected_status = self.status_combo.currentData()
        if selected_status:
            description = StatusManager.get_status_description(selected_status)
            self.status_description_label.setText(description)
            
            # Показываем соответствующие поля в зависимости от статуса
            self.defects_group.setVisible(False)
            self.lab_issues_group.setVisible(False)
            
            # Если статус "Отклонен" - показываем поля для замечаний ОТК
            if selected_status == MaterialStatus.REJECTED.value:
                self.defects_group.setVisible(True)
                
            # Если статус связан с лабораторными испытаниями
            if selected_status == MaterialStatus.LAB_TESTING.value:
                self.lab_issues_group.setVisible(True)
                
        else:
            self.status_description_label.setText("")
            self.defects_group.setVisible(False)
            self.lab_issues_group.setVisible(False)
    
    def change_status(self):
        """Выполнение изменения статуса"""
        selected_status = self.status_combo.currentData()
        if not selected_status:
            QMessageBox.warning(self, "Предупреждение", "Выберите новый статус!")
            return
        
        comment = self.comment_edit.toPlainText().strip()
        
        # Подтверждение изменения
        current_display = get_status_display_name(self.material.status)
        new_display = get_status_display_name(selected_status)
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение изменения", 
            f"Вы уверены, что хотите изменить статус материала?\n\n"
            f"С: {current_display}\n"
            f"На: {new_display}",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                # Обновление статуса материала
                material = db.query(MaterialEntry).filter(MaterialEntry.id == self.material_id).first()
                if not material:
                    QMessageBox.critical(self, "Ошибка", "Материал не найден!")
                    return
                
                # Устанавливаем новый статус
                prev_status = material.status
                material.status = selected_status
                material.last_status_change = datetime.now()
                material.last_status_change_by_id = self.user.id
                
                # Сохраняем комментарий
                if comment:
                    # Если есть предыдущие комментарии, добавляем новый
                    if material.status_comment:
                        material.status_comment = (
                            f"{material.status_comment}\n"
                            f"[{datetime.now().strftime('%d.%m.%Y %H:%M')} - {self.user.full_name}]: {comment}"
                        )
                    else:
                        material.status_comment = (
                            f"[{datetime.now().strftime('%d.%m.%Y %H:%M')} - {self.user.full_name}]: {comment}"
                        )
                
                # Обработка дополнительных полей в зависимости от статуса
                if selected_status == MaterialStatus.REJECTED.value:
                    # Собираем причины отклонения
                    rejection_reasons = []
                    if self.defect_certificate.isChecked():
                        rejection_reasons.append("Проблемы с сертификатом")
                    if self.defect_dimensions.isChecked():
                        rejection_reasons.append("Отклонения по размерам")
                    if self.defect_chemical.isChecked():
                        rejection_reasons.append("Отклонения по хим. составу")
                    if self.defect_visual.isChecked():
                        rejection_reasons.append("Визуальные дефекты")
                    if self.defect_other.isChecked():
                        rejection_reasons.append("Другие причины")
                    
                    if rejection_reasons:
                        rejection_text = ", ".join(rejection_reasons)
                        material.rejection_reasons = rejection_text
                        
                        # Добавляем в комментарий
                        material.status_comment = (
                            f"{material.status_comment or ''}\n"
                            f"Причины отклонения: {rejection_text}"
                        )
                
                elif selected_status == MaterialStatus.LAB_TESTING.value:
                    # Собираем результаты лабораторных испытаний
                    lab_issues = []
                    if self.lab_issue_hardness.isChecked():
                        lab_issues.append("Не соответствует по твердости")
                    if self.lab_issue_tensile.isChecked():
                        lab_issues.append("Не соответствует по прочности")
                    if self.lab_issue_impact.isChecked():
                        lab_issues.append("Не соответствует по ударной вязкости")
                    if self.lab_issue_chemical.isChecked():
                        lab_issues.append("Не соответствует по хим. составу")
                    if self.lab_issue_other.isChecked():
                        lab_issues.append("Другие причины")
                    
                    if lab_issues:
                        lab_issues_text = ", ".join(lab_issues)
                        material.lab_issues = lab_issues_text
                        
                        # Добавляем в комментарий
                        material.status_comment = (
                            f"{material.status_comment or ''}\n"
                            f"Результаты испытаний: {lab_issues_text}"
                        )
                
                # Сохраняем изменения
                db.commit()
                
                # Отправляем уведомления (если настроены)
                try:
                    # Обрабатываем ключевые переходы статусов
                    if prev_status == MaterialStatus.PENDING_QC.value and selected_status == MaterialStatus.QC_PASSED.value:
                        # Уведомление об успешной проверке ОТК
                        send_qc_approval_notification(material)
                    
                    elif prev_status == MaterialStatus.PENDING_QC.value and selected_status == MaterialStatus.QC_FAILED.value:
                        # Уведомление о непрохождении проверки ОТК
                        send_qc_rejection_notification(material, comment)
                    
                    elif prev_status == MaterialStatus.LAB_TESTING.value:
                        # Проверяем есть ли замечания лаборатории в комментарии
                        comment = self.comment_edit.toPlainText().strip().lower()
                        if any(word in comment for word in ['брак', 'не соответств', 'отклон', 'дефект']):
                            # Брак лаборатории
                            send_lab_test_failure_notification(material, comment)
                    
                    elif selected_status == MaterialStatus.READY_FOR_USE.value:
                        # Финальное одобрение
                        send_final_acceptance_notification(material)
                        
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")
                
                QMessageBox.information(
                    self, 
                    "Статус изменен", 
                    f"Статус материала успешно изменен на \"{new_display}\"."
                )
                self.accept()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")
            finally:
                db.close()
    
    def exec(self):
        """Запуск диалога с проверкой доступности материала"""
        if not self.material:
            return QDialog.Rejected
        return super().exec() 