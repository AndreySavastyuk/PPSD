#!/usr/bin/env python3
"""
Расширенный API для аналитики системы ППСД
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

# Добавляем корневую директорию в путь
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.connection import SessionLocal
from models.models import MaterialEntry, User, Supplier, MaterialType, MaterialStatus, UserRole

app = FastAPI(title="ППСД Analytics API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic модели для ответов
class StatisticsResponse(BaseModel):
    total_materials: int
    approved: int
    rejected: int
    pending_qc: int
    pending_lab: int
    in_testing: int
    received: int
    qc_check: int
    lab_testing: int

class MaterialDistribution(BaseModel):
    status: str
    count: int
    percentage: float

class SupplierStats(BaseModel):
    supplier_name: str
    total_materials: int
    approved_count: int
    rejected_count: int
    approval_rate: float

class TimelineData(BaseModel):
    date: str
    materials_count: int
    approved_count: int
    rejected_count: int

class ProcessingTimeStats(BaseModel):
    stage: str
    avg_processing_time_hours: float
    avg_processing_time_days: float

class MaterialGradeStats(BaseModel):
    grade: str
    count: int
    latest_date: str

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "ППСД Analytics API v1.0.0", "status": "ok"}

@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    days: int = Query(30, description="Количество дней для анализа"),
    supplier_id: Optional[int] = Query(None, description="ID поставщика для фильтрации"),
    material_grade: Optional[str] = Query(None, description="Марка материала для фильтрации"),
    db: Session = Depends(get_db)
):
    """Получение общей статистики системы"""
    
    # Базовый запрос
    query = db.query(MaterialEntry).filter(MaterialEntry.is_deleted == False)
    
    # Фильтрация по дате
    if days > 0:
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(MaterialEntry.created_at >= start_date)
    
    # Дополнительные фильтры
    if supplier_id:
        query = query.filter(MaterialEntry.supplier_id == supplier_id)
    
    if material_grade:
        query = query.filter(MaterialEntry.material_grade.ilike(f"%{material_grade}%"))
    
    # Подсчет по статусам
    total_materials = query.count()
    
    stats = {
        'total_materials': total_materials,
        'approved': query.filter(MaterialEntry.status == MaterialStatus.APPROVED.value).count(),
        'rejected': query.filter(MaterialEntry.status == MaterialStatus.REJECTED.value).count(),
        'pending_qc': query.filter(MaterialEntry.status == MaterialStatus.QC_CHECK_PENDING.value).count(),
        'pending_lab': query.filter(MaterialEntry.status == MaterialStatus.LAB_CHECK_PENDING.value).count(),
        'in_testing': query.filter(MaterialEntry.status == MaterialStatus.TESTING.value).count(),
        'received': query.filter(MaterialEntry.status == MaterialStatus.RECEIVED.value).count(),
        'qc_check': query.filter(MaterialEntry.status == MaterialStatus.QC_CHECKED.value).count(),
        'lab_testing': query.filter(MaterialEntry.status.in_([
            MaterialStatus.SAMPLES_REQUESTED.value,
            MaterialStatus.SAMPLES_COLLECTED.value,
            MaterialStatus.TESTING.value
        ])).count()
    }
    
    return StatisticsResponse(**stats)

@app.get("/materials/distribution", response_model=List[MaterialDistribution])
async def get_materials_distribution(
    days: int = Query(30, description="Количество дней для анализа"),
    db: Session = Depends(get_db)
):
    """Получение распределения материалов по статусам"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Подсчет материалов по статусам
    status_counts = db.query(
        MaterialEntry.status,
        func.count(MaterialEntry.id).label('count')
    ).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    ).group_by(MaterialEntry.status).all()
    
    total = sum(item.count for item in status_counts)
    
    distribution = []
    for status, count in status_counts:
        percentage = (count / total * 100) if total > 0 else 0
        distribution.append(MaterialDistribution(
            status=status,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    return distribution

@app.get("/suppliers/stats", response_model=List[SupplierStats])
async def get_suppliers_stats(
    days: int = Query(90, description="Количество дней для анализа"),
    limit: int = Query(10, description="Количество топ поставщиков"),
    db: Session = Depends(get_db)
):
    """Получение статистики по поставщикам"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Запрос статистики по поставщикам
    supplier_stats = db.query(
        Supplier.name,
        func.count(MaterialEntry.id).label('total_materials'),
        func.sum(func.case(
            (MaterialEntry.status == MaterialStatus.APPROVED.value, 1),
            else_=0
        )).label('approved_count'),
        func.sum(func.case(
            (MaterialEntry.status == MaterialStatus.REJECTED.value, 1),
            else_=0
        )).label('rejected_count')
    ).join(
        MaterialEntry, Supplier.id == MaterialEntry.supplier_id
    ).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    ).group_by(
        Supplier.id, Supplier.name
    ).order_by(
        desc('total_materials')
    ).limit(limit).all()
    
    stats = []
    for name, total, approved, rejected in supplier_stats:
        approved = approved or 0
        rejected = rejected or 0
        approval_rate = (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0
        
        stats.append(SupplierStats(
            supplier_name=name,
            total_materials=total,
            approved_count=approved,
            rejected_count=rejected,
            approval_rate=round(approval_rate, 2)
        ))
    
    return stats

@app.get("/materials/timeline", response_model=List[TimelineData])
async def get_materials_timeline(
    days: int = Query(30, description="Количество дней для анализа"),
    db: Session = Depends(get_db)
):
    """Получение временной линии поступления материалов"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Группировка по дням
    timeline_data = db.query(
        func.date(MaterialEntry.created_at).label('date'),
        func.count(MaterialEntry.id).label('materials_count'),
        func.sum(func.case(
            (MaterialEntry.status == MaterialStatus.APPROVED.value, 1),
            else_=0
        )).label('approved_count'),
        func.sum(func.case(
            (MaterialEntry.status == MaterialStatus.REJECTED.value, 1),
            else_=0
        )).label('rejected_count')
    ).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    ).group_by(
        func.date(MaterialEntry.created_at)
    ).order_by('date').all()
    
    timeline = []
    for date, materials_count, approved_count, rejected_count in timeline_data:
        timeline.append(TimelineData(
            date=date.strftime('%Y-%m-%d'),
            materials_count=materials_count,
            approved_count=approved_count or 0,
            rejected_count=rejected_count or 0
        ))
    
    return timeline

@app.get("/processing/time-stats", response_model=List[ProcessingTimeStats])
async def get_processing_time_stats(
    days: int = Query(90, description="Количество дней для анализа"),
    db: Session = Depends(get_db)
):
    """Получение статистики времени обработки по этапам"""
    
    # Это упрощенная версия - в реальности нужно отслеживать время перехода между статусами
    # Пока возвращаем тестовые данные
    
    stats = [
        ProcessingTimeStats(
            stage="ОТК проверка",
            avg_processing_time_hours=48.5,
            avg_processing_time_days=2.0
        ),
        ProcessingTimeStats(
            stage="Лабораторные испытания",
            avg_processing_time_hours=120.0,
            avg_processing_time_days=5.0
        ),
        ProcessingTimeStats(
            stage="Окончательное утверждение",
            avg_processing_time_hours=24.0,
            avg_processing_time_days=1.0
        )
    ]
    
    return stats

@app.get("/materials/grades", response_model=List[MaterialGradeStats])
async def get_material_grades_stats(
    days: int = Query(90, description="Количество дней для анализа"),
    limit: int = Query(15, description="Количество топ марок"),
    db: Session = Depends(get_db)
):
    """Получение статистики по маркам материалов"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    grade_stats = db.query(
        MaterialEntry.material_grade,
        func.count(MaterialEntry.id).label('count'),
        func.max(MaterialEntry.created_at).label('latest_date')
    ).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    ).group_by(
        MaterialEntry.material_grade
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    stats = []
    for grade, count, latest_date in grade_stats:
        stats.append(MaterialGradeStats(
            grade=grade,
            count=count,
            latest_date=latest_date.strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    return stats

@app.get("/kpi/dashboard")
async def get_kpi_dashboard(
    days: int = Query(30, description="Количество дней для анализа"),
    db: Session = Depends(get_db)
):
    """Получение KPI для дашборда"""
    
    start_date = datetime.now() - timedelta(days=days)
    prev_start_date = start_date - timedelta(days=days)
    
    # Текущий период
    current_stats = db.query(MaterialEntry).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    )
    
    # Предыдущий период для сравнения
    prev_stats = db.query(MaterialEntry).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= prev_start_date,
        MaterialEntry.created_at < start_date
    )
    
    current_total = current_stats.count()
    prev_total = prev_stats.count()
    
    current_approved = current_stats.filter(MaterialEntry.status == MaterialStatus.APPROVED.value).count()
    prev_approved = prev_stats.filter(MaterialEntry.status == MaterialStatus.APPROVED.value).count()
    
    current_rejected = current_stats.filter(MaterialEntry.status == MaterialStatus.REJECTED.value).count()
    prev_rejected = prev_stats.filter(MaterialEntry.status == MaterialStatus.REJECTED.value).count()
    
    # Вычисление изменений в процентах
    def calculate_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    
    total_change = calculate_change(current_total, prev_total)
    approved_change = calculate_change(current_approved, prev_approved)
    rejected_change = calculate_change(current_rejected, prev_rejected)
    
    # Коэффициент одобрения
    approval_rate = (current_approved / (current_approved + current_rejected) * 100) if (current_approved + current_rejected) > 0 else 0
    prev_approval_rate = (prev_approved / (prev_approved + prev_rejected) * 100) if (prev_approved + prev_rejected) > 0 else 0
    approval_rate_change = approval_rate - prev_approval_rate
    
    return {
        "period_days": days,
        "current_period": {
            "total_materials": current_total,
            "approved": current_approved,
            "rejected": current_rejected,
            "approval_rate": round(approval_rate, 2)
        },
        "changes": {
            "total_materials_change": round(total_change, 2),
            "approved_change": round(approved_change, 2),
            "rejected_change": round(rejected_change, 2),
            "approval_rate_change": round(approval_rate_change, 2)
        },
        "trend": {
            "materials_trend": "up" if total_change > 0 else "down" if total_change < 0 else "stable",
            "approval_trend": "up" if approval_rate_change > 0 else "down" if approval_rate_change < 0 else "stable"
        }
    }

@app.get("/export/analytics-report")
async def export_analytics_report(
    days: int = Query(30, description="Количество дней для анализа"),
    format: str = Query("json", description="Формат экспорта: json, csv"),
    db: Session = Depends(get_db)
):
    """Экспорт аналитического отчета"""
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Поддерживаемые форматы: json, csv")
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Получаем детальные данные
    materials = db.query(MaterialEntry).filter(
        MaterialEntry.is_deleted == False,
        MaterialEntry.created_at >= start_date
    ).all()
    
    # Формируем данные для экспорта
    export_data = []
    for material in materials:
        supplier = db.query(Supplier).filter(Supplier.id == material.supplier_id).first()
        
        export_data.append({
            "id": material.id,
            "material_grade": material.material_grade,
            "material_type": material.material_type,
            "melt_number": material.melt_number,
            "batch_number": material.batch_number,
            "supplier_name": supplier.name if supplier else "Неизвестно",
            "status": material.status,
            "created_at": material.created_at.isoformat(),
            "updated_at": material.updated_at.isoformat() if material.updated_at else None
        })
    
    if format == "csv":
        # Возвращаем CSV
        import io
        from fastapi.responses import StreamingResponse
        
        df = pd.DataFrame(export_data)
        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding='utf-8')
        response = StreamingResponse(
            io.BytesIO(stream.getvalue().encode('utf-8')),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return response
    
    return {
        "report_date": datetime.now().isoformat(),
        "period_days": days,
        "total_records": len(export_data),
        "data": export_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 