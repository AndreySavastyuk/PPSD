"""
Модуль для генерации отчетов
Поддерживает различные типы отчетов: сводные, статистические, по поставщикам
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import func, and_, or_

from database.connection import SessionLocal
from models.models import MaterialEntry, Supplier, QCCheck, LabTest, MaterialStatus, UserRole, Sample
from utils.qr import generate_qr_code

# Регистрируем русские шрифты (нужно будет добавить файлы шрифтов)
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    DEFAULT_FONT = 'DejaVuSans'
except:
    DEFAULT_FONT = 'Helvetica'

class ReportGenerator:
    """Генератор отчетов для системы PPSD"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        ))
    
    def generate_material_summary_report(self, start_date: datetime = None, end_date: datetime = None) -> BytesIO:
        """
        Генерация сводного отчета по материалам
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
        
        Returns:
            BytesIO объект с PDF документом
        """
        # Устанавливаем период по умолчанию - последний месяц
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Создаем буфер для PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        # Элементы документа
        elements = []
        
        # Заголовок
        title = Paragraph(
            f"Сводный отчет по материалам<br/>за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        db = SessionLocal()
        try:
            # Получаем материалы за период
            materials = db.query(MaterialEntry).filter(
                MaterialEntry.created_at.between(start_date, end_date),
                MaterialEntry.is_deleted == False
            ).all()
            
            # Статистика по статусам
            status_stats = {}
            for material in materials:
                status = material.status
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            # Таблица статистики по статусам
            elements.append(Paragraph("Статистика по статусам", self.styles['CustomHeading']))
            
            status_data = [['Статус', 'Количество']]
            for status, count in status_stats.items():
                status_name = self._get_status_name(status)
                status_data.append([status_name, str(count)])
            
            status_table = Table(status_data, colWidths=[10*cm, 3*cm])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(status_table)
            elements.append(Spacer(1, 1*cm))
            
            # Статистика по поставщикам
            supplier_stats = {}
            for material in materials:
                supplier_name = material.supplier.name
                if supplier_name not in supplier_stats:
                    supplier_stats[supplier_name] = {'total': 0, 'approved': 0, 'rejected': 0}
                supplier_stats[supplier_name]['total'] += 1
                if material.status == MaterialStatus.APPROVED.value:
                    supplier_stats[supplier_name]['approved'] += 1
                elif material.status == MaterialStatus.REJECTED.value:
                    supplier_stats[supplier_name]['rejected'] += 1
            
            # Таблица статистики по поставщикам
            elements.append(Paragraph("Статистика по поставщикам", self.styles['CustomHeading']))
            
            supplier_data = [['Поставщик', 'Всего', 'Одобрено', 'Отклонено', '% брака']]
            for supplier, stats in supplier_stats.items():
                reject_rate = (stats['rejected'] / stats['total'] * 100) if stats['total'] > 0 else 0
                supplier_data.append([
                    supplier,
                    str(stats['total']),
                    str(stats['approved']),
                    str(stats['rejected']),
                    f"{reject_rate:.1f}%"
                ])
            
            supplier_table = Table(supplier_data, colWidths=[7*cm, 2*cm, 2*cm, 2*cm, 2*cm])
            supplier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(supplier_table)
            
        finally:
            db.close()
        
        # Строим документ
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_lab_performance_report(self, start_date: datetime = None, end_date: datetime = None) -> BytesIO:
        """
        Генерация отчета по работе лаборатории
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
        
        Returns:
            BytesIO объект с PDF документом
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        # Заголовок
        title = Paragraph(
            f"Отчет по работе лаборатории<br/>за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        db = SessionLocal()
        try:
            # Получаем испытания за период
            tests = db.query(LabTest).filter(
                LabTest.performed_at.between(start_date, end_date),
                LabTest.is_deleted == False
            ).all()
            
            # Статистика по типам испытаний
            test_stats = {
                'mechanical': {'total': 0, 'passed': 0, 'failed': 0, 'pending': 0},
                'chemical': {'total': 0, 'passed': 0, 'failed': 0, 'pending': 0},
                'metallographic': {'total': 0, 'passed': 0, 'failed': 0, 'pending': 0}
            }
            
            for test in tests:
                if test.test_type in test_stats:
                    test_stats[test.test_type]['total'] += 1
                    if test.is_passed is None:
                        test_stats[test.test_type]['pending'] += 1
                    elif test.is_passed:
                        test_stats[test.test_type]['passed'] += 1
                    else:
                        test_stats[test.test_type]['failed'] += 1
            
            # Таблица статистики по испытаниям
            elements.append(Paragraph("Статистика по типам испытаний", self.styles['CustomHeading']))
            
            test_data = [['Тип испытания', 'Всего', 'Годен', 'Брак', 'В процессе', '% брака']]
            test_names = {
                'mechanical': 'Механические испытания',
                'chemical': 'Химический анализ',
                'metallographic': 'Металлография'
            }
            
            for test_type, stats in test_stats.items():
                if stats['total'] > 0:
                    completed = stats['passed'] + stats['failed']
                    reject_rate = (stats['failed'] / completed * 100) if completed > 0 else 0
                    test_data.append([
                        test_names.get(test_type, test_type),
                        str(stats['total']),
                        str(stats['passed']),
                        str(stats['failed']),
                        str(stats['pending']),
                        f"{reject_rate:.1f}%"
                    ])
            
            test_table = Table(test_data, colWidths=[6*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(test_table)
            elements.append(Spacer(1, 1*cm))
            
            # Время обработки
            processing_times = []
            for test in tests:
                if test.completed_at:
                    processing_time = (test.completed_at - test.performed_at).total_seconds() / 3600  # в часах
                    processing_times.append(processing_time)
            
            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                min_time = min(processing_times)
                max_time = max(processing_times)
                
                elements.append(Paragraph("Время обработки испытаний", self.styles['CustomHeading']))
                time_info = Paragraph(
                    f"Среднее время: {avg_time:.1f} часов<br/>"
                    f"Минимальное: {min_time:.1f} часов<br/>"
                    f"Максимальное: {max_time:.1f} часов",
                    self.styles['Normal']
                )
                elements.append(time_info)
            
        finally:
            db.close()
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_supplier_analysis_report(self, supplier_id: int) -> BytesIO:
        """
        Генерация детального отчета по поставщику
        
        Args:
            supplier_id: ID поставщика
        
        Returns:
            BytesIO объект с PDF документом
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        
        db = SessionLocal()
        try:
            # Получаем информацию о поставщике
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                raise ValueError(f"Поставщик с ID {supplier_id} не найден")
            
            # Заголовок
            title = Paragraph(
                f"Анализ поставщика: {supplier.name}",
                self.styles['CustomTitle']
            )
            elements.append(title)
            elements.append(Spacer(1, 0.5*cm))
            
            # Информация о поставщике
            supplier_info = Paragraph(
                f"<b>Тип:</b> {'Прямой поставщик' if supplier.is_direct else 'Непрямой поставщик'}<br/>"
                f"<b>Адрес:</b> {supplier.address or 'Не указан'}<br/>"
                f"<b>Контакты:</b> {supplier.contact_info or 'Не указаны'}",
                self.styles['Normal']
            )
            elements.append(supplier_info)
            elements.append(Spacer(1, 1*cm))
            
            # Получаем все материалы поставщика
            materials = db.query(MaterialEntry).filter(
                MaterialEntry.supplier_id == supplier_id,
                MaterialEntry.is_deleted == False
            ).all()
            
            # Статистика по материалам
            total_materials = len(materials)
            approved = sum(1 for m in materials if m.status == MaterialStatus.APPROVED.value)
            rejected = sum(1 for m in materials if m.status == MaterialStatus.REJECTED.value)
            in_process = sum(1 for m in materials if m.status not in [
                MaterialStatus.APPROVED.value, 
                MaterialStatus.REJECTED.value,
                MaterialStatus.ARCHIVED.value
            ])
            
            elements.append(Paragraph("Общая статистика", self.styles['CustomHeading']))
            
            stats_data = [
                ['Показатель', 'Значение'],
                ['Всего поставок', str(total_materials)],
                ['Одобрено', f"{approved} ({approved/total_materials*100:.1f}%)" if total_materials > 0 else "0"],
                ['Отклонено', f"{rejected} ({rejected/total_materials*100:.1f}%)" if total_materials > 0 else "0"],
                ['В процессе', str(in_process)]
            ]
            
            stats_table = Table(stats_data, colWidths=[8*cm, 5*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 1*cm))
            
            # Анализ причин брака
            if rejected > 0:
                elements.append(Paragraph("Анализ причин брака", self.styles['CustomHeading']))
                
                # Получаем проверки ОТК для отклоненных материалов
                rejected_materials = [m for m in materials if m.status == MaterialStatus.REJECTED.value]
                rejection_reasons = {}
                
                for material in rejected_materials:
                    qc_check = material.qc_check
                    if qc_check:
                        # Анализируем причины
                        if qc_check.issue_repurchase:
                            rejection_reasons['Перекуп'] = rejection_reasons.get('Перекуп', 0) + 1
                        if qc_check.issue_poor_quality:
                            rejection_reasons['Плохое качество сертификата'] = rejection_reasons.get('Плохое качество сертификата', 0) + 1
                        if qc_check.issue_no_stamp:
                            rejection_reasons['Нет печати'] = rejection_reasons.get('Нет печати', 0) + 1
                        if qc_check.issue_diameter_deviation:
                            rejection_reasons['Отклонение по диаметру'] = rejection_reasons.get('Отклонение по диаметру', 0) + 1
                        if qc_check.issue_cracks:
                            rejection_reasons['Трещины'] = rejection_reasons.get('Трещины', 0) + 1
                        if qc_check.issue_no_melt:
                            rejection_reasons['Не набита плавка'] = rejection_reasons.get('Не набита плавка', 0) + 1
                        if qc_check.issue_no_certificate:
                            rejection_reasons['Нет сертификата'] = rejection_reasons.get('Нет сертификата', 0) + 1
                        if qc_check.issue_copy:
                            rejection_reasons['Копия без синей печати'] = rejection_reasons.get('Копия без синей печати', 0) + 1
                
                if rejection_reasons:
                    reason_data = [['Причина брака', 'Количество случаев']]
                    for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                        reason_data.append([reason, str(count)])
                    
                    reason_table = Table(reason_data, colWidths=[10*cm, 3*cm])
                    reason_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(reason_table)
            
        finally:
            db.close()
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_sample_report_with_qr(self, sample_id: int) -> BytesIO:
        """
        Генерирует PDF-отчет по образцу с QR-кодом
        Args:
            sample_id: ID образца
        Returns:
            BytesIO объект с PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        db = SessionLocal()
        try:
            sample = db.query(Sample).filter(Sample.id == sample_id, Sample.is_deleted == False).first()
            if not sample:
                raise ValueError(f"Образец с ID {sample_id} не найден")
            # Генерируем QR-код
            qr_img = generate_qr_code(sample.sample_code, box_size=6)
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            rl_qr = RLImage(qr_buffer, width=3*cm, height=3*cm)
            # Заголовок и QR
            elements.append(Paragraph(f"Отчет по образцу: <b>{sample.sample_code}</b>", self.styles['CustomTitle']))
            elements.append(rl_qr)
            elements.append(Spacer(1, 0.5*cm))
            # Основная информация
            info = f"""
            <b>Материал:</b> {sample.material_entry.material_grade if sample.material_entry else '-'}<br/>
            <b>Плавка:</b> {sample.material_entry.melt_number if sample.material_entry else '-'}<br/>
            <b>Тип испытания:</b> {sample.test_type or '-'}<br/>
            <b>Дата создания:</b> {sample.created_at.strftime('%d.%m.%Y') if sample.created_at else '-'}<br/>
            """
            elements.append(Paragraph(info, self.styles['Normal']))
            # TODO: добавить результаты испытаний, статусы и т.д.
        finally:
            db.close()
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
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