"""
Модуль для генерации уникальных кодов образцов
Формат: [Номер запроса]-[Плавка]-[Порядковый номер]
Например: 001-ПЛ123456-01
"""
from database.connection import SessionLocal
from models.models import Sample, SampleRequest
from sqlalchemy import func

class SampleCodeGenerator:
    @staticmethod
    def generate_sample_code(sample_request_id: int, sample_number: int = None) -> str:
        """
        Генерирует уникальный код образца
        
        Args:
            sample_request_id: ID запроса на пробы
            sample_number: Порядковый номер образца (если None, берется следующий)
        
        Returns:
            Уникальный код образца в формате XXX-ПЛXXXXXX-YY
        """
        db = SessionLocal()
        try:
            # Получаем информацию о запросе
            sample_request = db.query(SampleRequest).filter(
                SampleRequest.id == sample_request_id
            ).first()
            
            if not sample_request:
                raise ValueError(f"Запрос на пробы #{sample_request_id} не найден")
            
            # Получаем информацию о материале
            material = sample_request.material_entry
            if not material:
                raise ValueError(f"Материал для запроса #{sample_request_id} не найден")
            
            # Форматируем номер запроса (3 цифры с ведущими нулями)
            request_number = f"{sample_request_id:03d}"
            
            # Получаем номер плавки
            melt_number = material.melt_number or "БП"  # БП - без плавки
            
            # Если номер образца не указан, вычисляем следующий
            if sample_number is None:
                # Считаем количество существующих образцов для этого запроса
                existing_samples_count = db.query(func.count(Sample.id)).filter(
                    Sample.sample_request_id == sample_request_id,
                    Sample.is_deleted == False
                ).scalar()
                sample_number = existing_samples_count + 1
            
            # Форматируем порядковый номер (2 цифры с ведущими нулями)
            sample_suffix = f"{sample_number:02d}"
            
            # Собираем код образца
            sample_code = f"{request_number}-{melt_number}-{sample_suffix}"
            
            # Проверяем уникальность
            existing = db.query(Sample).filter(
                Sample.sample_code == sample_code,
                Sample.is_deleted == False
            ).first()
            
            if existing:
                # Если код уже существует, пробуем следующий номер
                return SampleCodeGenerator.generate_sample_code(
                    sample_request_id, 
                    sample_number + 1
                )
            
            return sample_code
            
        finally:
            db.close()
    
    @staticmethod
    def generate_batch_codes(sample_request_id: int, count: int) -> list:
        """
        Генерирует несколько кодов образцов для одного запроса
        
        Args:
            sample_request_id: ID запроса на пробы
            count: Количество кодов для генерации
        
        Returns:
            Список уникальных кодов образцов
        """
        codes = []
        for i in range(1, count + 1):
            code = SampleCodeGenerator.generate_sample_code(sample_request_id, i)
            codes.append(code)
        return codes
    
    @staticmethod
    def parse_sample_code(sample_code: str) -> dict:
        """
        Парсит код образца и возвращает его составляющие
        
        Args:
            sample_code: Код образца (например, "001-ПЛ123456-01")
        
        Returns:
            Словарь с компонентами кода:
            {
                'request_id': int,
                'melt_number': str,
                'sample_number': int
            }
        """
        try:
            parts = sample_code.split('-')
            if len(parts) < 3:
                raise ValueError(f"Неверный формат кода образца: {sample_code}")
            
            return {
                'request_id': int(parts[0]),
                'melt_number': '-'.join(parts[1:-1]),  # Плавка может содержать дефисы
                'sample_number': int(parts[-1])
            }
        except (ValueError, IndexError) as e:
            raise ValueError(f"Не удалось распарсить код образца '{sample_code}': {str(e)}") 