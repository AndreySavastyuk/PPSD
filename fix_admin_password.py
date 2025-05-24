#!/usr/bin/env python3
"""
Скрипт для исправления пароля пользователя admin
"""
import sys
import os
import bcrypt

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.abspath('.'))

from database.connection import SessionLocal
from models.models import User

def fix_admin_password():
    """Исправляем пароль пользователя admin"""
    db = SessionLocal()
    try:
        # Получаем пользователя admin
        admin_user = db.query(User).filter(User.username == 'admin').first()
        
        if not admin_user:
            print("❌ Пользователь admin не найден в базе данных")
            return
        
        print(f"✅ Пользователь admin найден: {admin_user.full_name}")
        print(f"📝 Текущий hash: {admin_user.password_hash[:50]}...")
        
        # Создаем новый правильный hash для пароля 'admin'
        new_password = 'admin'
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        print(f"🔧 Генерируем новый hash для пароля '{new_password}': {new_hash}")
        
        # Проверяем новый hash
        verification = bcrypt.checkpw(new_password.encode('utf-8'), new_hash.encode('utf-8'))
        print(f"✅ Проверка нового hash: {'Успех' if verification else 'Ошибка'}")
        
        # Обновляем пароль в базе данных
        admin_user.password_hash = new_hash
        db.commit()
        
        print(f"💾 Пароль пользователя admin успешно обновлен")
        
        # Проверяем вход
        from utils.auth import authenticate_user
        test_user = authenticate_user(db, 'admin', 'admin')
        print(f"🔐 Тест входа admin/admin: {'✅ Успех' if test_user else '❌ Неудача'}")
        
        # Создаем также пользователей для всех ролей, если их нет
        print(f"\n👥 Проверяем пользователей для всех ролей...")
        
        roles_to_create = [
            {'username': 'warehouse', 'password': 'warehouse', 'full_name': 'Кладовщик', 'role': 'warehouse'},
            {'username': 'qc', 'password': 'qc', 'full_name': 'Сотрудник ОТК', 'role': 'qc'},
            {'username': 'lab', 'password': 'lab', 'full_name': 'Инженер ЦЗЛ', 'role': 'lab'},
            {'username': 'production', 'password': 'production', 'full_name': 'Производство', 'role': 'production'}
        ]
        
        for user_data in roles_to_create:
            existing_user = db.query(User).filter(User.username == user_data['username']).first()
            if not existing_user:
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                new_user = User(
                    username=user_data['username'],
                    password_hash=password_hash,
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    can_edit=True,
                    can_view=True,
                    is_active=True
                )
                db.add(new_user)
                print(f"➕ Создан пользователь {user_data['username']}")
            else:
                print(f"✅ Пользователь {user_data['username']} уже существует")
        
        db.commit()
        print(f"\n🎉 Все пользователи готовы!")
        
        # Выводим итоговую информацию
        all_users = db.query(User).all()
        print(f"\n📊 Всего пользователей в системе: {len(all_users)}")
        for user in all_users:
            print(f"   - {user.username} ({user.role}) - {user.full_name}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin_password() 