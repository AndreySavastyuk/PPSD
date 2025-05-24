# Миграция с PyQt5 на PySide6 (Qt6)

## Преимущества перехода на Qt6

1. **Современный стек технологий**:
   - Qt6 использует современные функции C++17
   - Лучшая поддержка высоких разрешений экрана (HiDPI)
   - Улучшенная производительность и меньший размер приложения

2. **Улучшенная совместимость**:
   - Лучшая поддержка последних версий Windows, macOS и Linux
   - Более гладкая интеграция с современными ОС

3. **Долгосрочная поддержка**:
   - Qt5 постепенно устаревает, Qt6 будет поддерживаться долгое время
   - Новые функции добавляются в основном в Qt6

4. **PySide6 вместо PyQt**:
   - PySide6 - это официальная Python библиотека от Qt (The Qt Company)
   - Лицензия LGPL более гибкая, чем GPL у PyQt
   - Тот же API, но с некоторыми улучшениями

## Процесс миграции

### 1. Установка зависимостей

Заменить PyQt5 на PySide6 в requirements.txt:

```
pyside6==6.5.2
# другие зависимости
```

### 2. Изменение импортов

Основные изменения в импортах:

| PyQt5                    | PySide6                   |
|--------------------------|---------------------------|
| `from PyQt5.QtWidgets import *` | `from PySide6.QtWidgets import *` |
| `from PyQt5.QtCore import *`    | `from PySide6.QtCore import *`    |
| `from PyQt5.QtGui import *`     | `from PySide6.QtGui import *`     |

### 3. Основные изменения API

#### Сигналы и слоты

**PyQt5**:
```python
self.button.clicked.connect(self.handle_click)
```

**PySide6**:
```python
self.button.clicked.connect(self.handle_click)
```
(Синтаксис одинаковый, но внутренняя реализация другая)

#### QAction

**PyQt5**:
```python
action = QAction("Текст", self)
action.triggered.connect(self.handle_action)
```

**PySide6**:
```python
action = QAction("Текст", self)
action.triggered.connect(self.handle_action)
```
(Синтаксис одинаковый)

#### Диалоги с кнопками

**PyQt5**:
```python
reply = QMessageBox.question(self, "Заголовок", "Сообщение",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No)
if reply == QMessageBox.Yes:
    # действие при Yes
```

**PySide6**:
```python
reply = QMessageBox.question(self, "Заголовок", "Сообщение",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No)
if reply == QMessageBox.StandardButton.Yes:
    # действие при Yes
```

### 4. Изменения для QPainter

В нашем приложении в `ui/icons/icon_provider.py` потребуются изменения для QPainter:

**PyQt5**:
```python
painter.setPen(QPen(QColor(80, 80, 80), 2))
```

**PySide6**:
```python
painter.setPen(QPen(QColor(80, 80, 80), 2))
```
(Синтаксис тот же, но могут быть небольшие различия в обработке)

### 5. Константы в Qt

В Qt6 некоторые константы перемещены в пространства имен:

**PyQt5**:
```python
Qt.AlignCenter
Qt.transparent
```

**PySide6**:
```python
Qt.AlignmentFlag.AlignCenter
Qt.GlobalColor.transparent
```

### 6. Тестирование и отладка

После замены всех импортов и адаптации кода:

1. Запустите приложение и проверьте все функции
2. Обратите внимание на консольные ошибки и предупреждения
3. Проверьте каждую форму и диалог
4. Протестируйте на разных размерах экрана

## План миграции для ППСД

1. Создать ветку в системе контроля версий для миграции
2. Обновить requirements.txt и настроить среду разработки
3. Изменить импорты во всех файлах
4. Адаптировать константы Qt и специфичные API
5. Обновить модуль icon_provider.py для работы с Qt6
6. Провести полное тестирование
7. Документировать все изменения

## Примерное время на миграцию

- Обновление зависимостей и настройка: 1 час
- Изменение импортов: 1-2 часа
- Адаптация кода: 2-4 часа
- Тестирование и отладка: 3-5 часов

Всего: примерно 7-12 часов работы 