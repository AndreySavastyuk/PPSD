import qrcode
from PIL import Image
import os

def generate_qr_code(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
    """
    Генерирует QR-код для заданной строки.
    Args:
        data: Строка для кодирования (например, код образца)
        box_size: Размер одной "коробки" QR-кода
        border: Толщина рамки (в коробках)
    Returns:
        Объект PIL Image с QR-кодом
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def save_qr_code(data: str, filename: str, box_size: int = 10, border: int = 4) -> str:
    """
    Генерирует и сохраняет QR-код в PNG-файл.
    Args:
        data: Строка для кодирования
        filename: Имя файла для сохранения (PNG)
        box_size: Размер одной "коробки" QR-кода
        border: Толщина рамки
    Returns:
        Путь к сохраненному файлу
    """
    img = generate_qr_code(data, box_size, border)
    img.save(filename)
    return os.path.abspath(filename)

# Пример использования
if __name__ == "__main__":
    code = "001-ПЛ123456-01"
    out_file = "sample_qr.png"
    path = save_qr_code(code, out_file)
    print(f"QR-код сохранен: {path}") 