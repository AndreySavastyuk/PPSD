"""
Модуль для управления статусами материалов
"""

from models.models import MaterialStatus, UserRole
from database.connection import SessionLocal
from datetime import datetime

class StatusManager:
    """Менеджер статусов материалов"""
    
    @staticmethod
    def get_available_transitions(current_status, user_role):
        """
        Получить доступные переходы статусов для текущего статуса и роли пользователя
        
        Args:
            current_status (str): Текущий статус материала
            user_role (str): Роль пользователя
            
        Returns:
            list: Список доступных статусов для перехода
        """
        # Карта разрешенных переходов для каждого статуса
        transitions = {
            # От полученного материала
            MaterialStatus.RECEIVED.value: {
                UserRole.WAREHOUSE.value: [
                    MaterialStatus.PENDING_QC.value,  # Отправить на проверку ОТК
                ],
                UserRole.QC.value: [
                    MaterialStatus.PENDING_QC.value,  # Взять на проверку ОТК
                    MaterialStatus.QC_PASSED.value,   # Проверка пройдена
                    MaterialStatus.QC_FAILED.value,   # Проверка не пройдена
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала, ожидающего проверки ОТК
            MaterialStatus.PENDING_QC.value: {
                UserRole.QC.value: [
                    MaterialStatus.QC_PASSED.value,   # Проверка пройдена
                    MaterialStatus.QC_FAILED.value,   # Проверка не пройдена
                    MaterialStatus.LAB_TESTING.value, # Отправить на лабораторные испытания
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала, прошедшего проверку ОТК
            MaterialStatus.QC_PASSED.value: {
                UserRole.QC.value: [
                    MaterialStatus.LAB_TESTING.value, # Отправить на лабораторные испытания
                    MaterialStatus.READY_FOR_USE.value, # Одобрить для использования
                ],
                UserRole.LAB.value: [
                    MaterialStatus.LAB_TESTING.value, # Взять на лабораторные испытания
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала, не прошедшего проверку ОТК
            MaterialStatus.QC_FAILED.value: {
                UserRole.QC.value: [
                    MaterialStatus.REJECTED.value,    # Окончательный брак
                    MaterialStatus.RECEIVED.value,    # Вернуть на склад (например, для замены)
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала на лабораторных испытаниях
            MaterialStatus.LAB_TESTING.value: {
                UserRole.LAB.value: [
                    MaterialStatus.QC_PASSED.value,   # Испытания успешны, вернуть на ОТК
                    MaterialStatus.QC_FAILED.value,   # Испытания не пройдены, вернуть на ОТК с браком
                    MaterialStatus.READY_FOR_USE.value, # Одобрить для использования
                    MaterialStatus.REJECTED.value,    # Забраковать
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала, готового к использованию
            MaterialStatus.READY_FOR_USE.value: {
                UserRole.PRODUCTION.value: [
                    MaterialStatus.IN_USE.value,      # Взять в производство
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.IN_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для материала в использовании
            MaterialStatus.IN_USE.value: {
                UserRole.PRODUCTION.value: [
                    MaterialStatus.READY_FOR_USE.value, # Вернуть на склад
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.READY_FOR_USE.value,
                    MaterialStatus.REJECTED.value,
                ],
            },
            # Для отклоненного материала
            MaterialStatus.REJECTED.value: {
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                ],
            },
            # Для запроса на редактирование
            MaterialStatus.EDIT_REQUESTED.value: {
                UserRole.QC.value: [
                    MaterialStatus.RECEIVED.value,    # Разрешить редактирование
                ],
                UserRole.ADMIN.value: [
                    MaterialStatus.RECEIVED.value,
                    MaterialStatus.PENDING_QC.value,
                    MaterialStatus.QC_PASSED.value,
                    MaterialStatus.QC_FAILED.value,
                    MaterialStatus.LAB_TESTING.value,
                    MaterialStatus.READY_FOR_USE.value,
                ],
            }
        }
        
        # Администратор может переводить в любые статусы
        if user_role == UserRole.ADMIN.value:
            return list(set([
                MaterialStatus.RECEIVED.value,
                MaterialStatus.PENDING_QC.value,
                MaterialStatus.QC_PASSED.value,
                MaterialStatus.QC_FAILED.value,
                MaterialStatus.LAB_TESTING.value,
                MaterialStatus.READY_FOR_USE.value,
                MaterialStatus.IN_USE.value,
                MaterialStatus.REJECTED.value,
                MaterialStatus.EDIT_REQUESTED.value,
            ]))
        
        # Возвращаем доступные переходы или пустой список
        status_transitions = transitions.get(current_status, {})
        return status_transitions.get(user_role, [])
    
    @staticmethod
    def get_status_description(status):
        """
        Получить описание статуса
        
        Args:
            status (str): Код статуса
            
        Returns:
            str: Описание статуса
        """
        descriptions = {
            MaterialStatus.RECEIVED.value: "Материал принят на склад и ожидает проверки ОТК",
            MaterialStatus.PENDING_QC.value: "Материал находится в очереди на проверку ОТК",
            MaterialStatus.QC_PASSED.value: "Материал успешно прошел проверку ОТК",
            MaterialStatus.QC_FAILED.value: "Материал не прошел проверку ОТК из-за несоответствий",
            MaterialStatus.QC_CHECKED.value: "Материал проверен ОТК",
            MaterialStatus.LAB_TESTING.value: "Материал находится на лабораторных испытаниях в ЦЗЛ",
            MaterialStatus.LAB_CHECK_PENDING.value: "Материал ожидает проверки в лаборатории",
            MaterialStatus.READY_FOR_USE.value: "Материал полностью проверен и готов к использованию",
            MaterialStatus.IN_USE.value: "Материал находится в производстве",
            MaterialStatus.REJECTED.value: "Материал окончательно забракован и не может быть использован",
            MaterialStatus.EDIT_REQUESTED.value: "Запрошено редактирование данных материала"
        }
        
        return descriptions.get(status, "Нет описания для данного статуса") 