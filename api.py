from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from database.connection import SessionLocal
from models.models import MaterialEntry, SampleRequest
from utils.reports import ReportGenerator
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import io

app = FastAPI(
    title="PPSD API",
    description="API для системы контроля качества металлопродукции",
    version="1.0.0"
)

def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/materials", response_model=List[Dict[str, Any]])
async def get_materials(db: Session = Depends(get_db)):
    """Получить список всех материалов"""
    try:
        materials = db.query(MaterialEntry).filter(
            MaterialEntry.is_deleted == False
        ).all()
        
        result = []
        for material in materials:
            result.append({
                "id": material.id,
                "material_grade": material.material_grade,
                "material_type": material.material_type,
                "batch_number": material.batch_number,
                "melt_number": material.melt_number,
                "supplier_id": material.supplier_id,
                "status": material.status,
                "created_at": material.created_at.isoformat(),
                "updated_at": material.updated_at.isoformat() if material.updated_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/materials/{material_id}")
async def get_material(material_id: int, db: Session = Depends(get_db)):
    """Получить конкретный материал по ID"""
    try:
        material = db.query(MaterialEntry).filter(
            MaterialEntry.id == material_id,
            MaterialEntry.is_deleted == False
        ).first()
        
        if not material:
            raise HTTPException(status_code=404, detail="Материал не найден")
        
        return {
            "id": material.id,
            "material_grade": material.material_grade,
            "material_type": material.material_type,
            "batch_number": material.batch_number,
            "melt_number": material.melt_number,
            "supplier_id": material.supplier_id,
            "status": material.status,
            "created_at": material.created_at.isoformat(),
            "updated_at": material.updated_at.isoformat() if material.updated_at else None,
            "edit_requested": material.edit_requested,
            "edit_comment": material.edit_comment
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/samples")
async def get_samples(db: Session = Depends(get_db)):
    """Получить список всех образцов"""
    try:
        samples = db.query(SampleRequest).all()
        
        result = []
        for sample in samples:
            result.append({
                "id": sample.id,
                "material_id": sample.material_id,
                "requested_by": sample.requested_by,
                "test_types": sample.test_types,
                "created_at": sample.created_at.isoformat(),
                "sample_code": sample.sample_code,
                "status": sample.status
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample_report/{sample_id}")
async def get_sample_report(sample_id: int, db: Session = Depends(get_db)):
    """Получить PDF-отчет по образцу с QR-кодом"""
    try:
        sample = db.query(SampleRequest).filter(SampleRequest.id == sample_id).first()
        if not sample:
            raise HTTPException(status_code=404, detail="Образец не найден")
        
        # Генерируем PDF-отчет с QR-кодом
        report_generator = ReportGenerator()
        pdf_buffer = report_generator.generate_sample_report_with_qr(sample_id)
        
        # Возвращаем PDF как поток
        pdf_buffer.seek(0)
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=sample_report_{sample_id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qr_code/{sample_code}")
async def generate_qr_code(sample_code: str):
    """Генерировать QR-код для образца"""
    try:
        from utils.qr import generate_qr_code
        import tempfile
        import os
        from fastapi.responses import FileResponse
        
        # Генерируем QR-код
        qr_image = generate_qr_code(sample_code)
        
        # Сохраняем во временный файл
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        qr_image.save(temp_file.name)
        temp_file.close()
        
        # Возвращаем как файл
        return FileResponse(
            temp_file.name,
            media_type="image/png",
            filename=f"qr_code_{sample_code.replace('/', '_')}.png",
            background=lambda: os.unlink(temp_file.name)  # Удаляем файл после отправки
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Получить статистику по материалам"""
    try:
        from models.models import MaterialStatus
        from sqlalchemy import func
        
        # Общее количество материалов
        total_materials = db.query(MaterialEntry).filter(
            MaterialEntry.is_deleted == False
        ).count()
        
        # Статистика по статусам
        status_stats = db.query(
            MaterialEntry.status,
            func.count(MaterialEntry.id).label('count')
        ).filter(
            MaterialEntry.is_deleted == False
        ).group_by(MaterialEntry.status).all()
        
        status_distribution = {}
        for status, count in status_stats:
            status_distribution[status] = count
        
        # Материалы по типам
        type_stats = db.query(
            MaterialEntry.material_type,
            func.count(MaterialEntry.id).label('count')
        ).filter(
            MaterialEntry.is_deleted == False
        ).group_by(MaterialEntry.material_type).all()
        
        type_distribution = {}
        for material_type, count in type_stats:
            type_distribution[material_type] = count
        
        # Количество образцов
        total_samples = db.query(SampleRequest).count()
        
        return {
            "total_materials": total_materials,
            "total_samples": total_samples,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/materials/{material_id}/status")
async def update_material_status(
    material_id: int, 
    new_status: str, 
    user_id: int,
    comment: str = None,
    db: Session = Depends(get_db)
):
    """Обновить статус материала (требует аутентификации в реальном приложении)"""
    try:
        from utils.status_manager import StatusManager
        from models.models import User
        
        # Получаем пользователя (в реальном приложении это будет из токена аутентификации)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Выполняем переход статуса
        success, message = StatusManager.transition_material(
            material_id=material_id,
            target_status=new_status,
            user_id=user_id,
            user_role=user.role,
            comment=comment
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем CORS middleware для веб-интерфейсов
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 