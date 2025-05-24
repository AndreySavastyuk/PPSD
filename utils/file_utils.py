import os
import shutil
import datetime
import qrcode
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Arial Unicode font for Cyrillic support
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
except:
    # Fallback to default font if Arial not available
    pass

def save_uploaded_file(uploaded_file, destination_folder, new_filename=None):
    """
    Save an uploaded file to the specified destination.
    
    Args:
        uploaded_file: File-like object with read() method
        destination_folder (str): Folder to save the file
        new_filename (str, optional): New filename. If None, use original name
        
    Returns:
        str: Path to the saved file
    """
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)
    
    if new_filename:
        destination_path = os.path.join(destination_folder, new_filename)
    else:
        destination_path = os.path.join(destination_folder, uploaded_file.name)
    
    # Save file
    with open(destination_path, 'wb') as dest_file:
        shutil.copyfileobj(uploaded_file, dest_file)
    
    return destination_path

def rename_certificate_file(original_path, material_data):
    """
    Rename certificate file according to standard format.
    
    Format: SUPPLIER_MATERIALGRAGE_BATCHNUMBER_DATEYYYYMMDD.pdf
    
    Args:
        original_path (str): Original file path
        material_data (dict): Material data with supplier, material_grade, batch_number
        
    Returns:
        str: New file path
    """
    supplier = material_data.get('supplier_name', 'Unknown')
    material_grade = material_data.get('material_grade', 'Unknown')
    batch_number = material_data.get('batch_number', 'Unknown')
    
    # Format current date
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    
    # Create new filename
    new_filename = f"{supplier}_{material_grade}_{batch_number}_{current_date}.pdf"
    
    # Replace invalid characters
    new_filename = new_filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    # Get directory and file extension
    directory = os.path.dirname(original_path)
    
    # Create new path
    new_path = os.path.join(directory, new_filename)
    
    # Rename file
    if os.path.exists(original_path):
        shutil.move(original_path, new_path)
    
    return new_path

def generate_qr_code(data, size=10):
    """
    Generate a QR code for the given data.
    
    Args:
        data (str): Data to encode in the QR code
        size (int): Size of the QR code in units
        
    Returns:
        BytesIO: QR code image in memory
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to BytesIO
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    
    return byte_io

def generate_sample_request_pdf(sample_request, material, supplier, user, output_path):
    """
    Generate a PDF for sample request.
    
    Args:
        sample_request: Sample request data
        material: Material data
        supplier: Supplier data
        user: User who created the request
        output_path (str): Path to save the PDF
        
    Returns:
        str: Path to the generated PDF
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont("Arial", 14)
    
    # Title
    c.drawString(20*mm, 280*mm, "ЗАЯВКА НА ПРОБЫ")
    c.setFont("Arial", 10)
    
    # Date and number
    c.drawString(20*mm, 270*mm, f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}")
    c.drawString(20*mm, 265*mm, f"Номер заявки: {sample_request.id}")
    
    # Material info
    c.drawString(20*mm, 255*mm, "Информация о материале:")
    c.drawString(25*mm, 250*mm, f"Поставщик: {supplier.name}")
    c.drawString(25*mm, 245*mm, f"Марка материала: {material.material_grade}")
    c.drawString(25*mm, 240*mm, f"Вид проката: {material.material_type}")
    
    # Certificate info
    c.drawString(25*mm, 235*mm, f"Номер сертификата: {material.certificate_number}")
    c.drawString(25*mm, 230*mm, f"Номер партии: {material.batch_number}")
    c.drawString(25*mm, 225*mm, f"Номер плавки: {material.melt_number}")
    
    # Sample info
    c.drawString(20*mm, 215*mm, "Информация о пробах:")
    c.drawString(25*mm, 210*mm, f"Размер пробы: {sample_request.sample_size} {sample_request.sample_unit}")
    c.drawString(25*mm, 205*mm, f"Описание: {sample_request.sample_description}")
    
    # Tests to perform
    c.drawString(20*mm, 195*mm, "Требуемые испытания:")
    y_pos = 190
    if sample_request.mechanical_test:
        c.drawString(25*mm, y_pos*mm, "☑ Механические испытания")
        y_pos -= 5
    else:
        c.drawString(25*mm, y_pos*mm, "☐ Механические испытания")
        y_pos -= 5
        
    if sample_request.chemical_test:
        c.drawString(25*mm, y_pos*mm, "☑ Химический анализ")
        y_pos -= 5
    else:
        c.drawString(25*mm, y_pos*mm, "☐ Химический анализ")
        y_pos -= 5
        
    if sample_request.metallographic_test:
        c.drawString(25*mm, y_pos*mm, "☑ Металлографический анализ")
        y_pos -= 5
    else:
        c.drawString(25*mm, y_pos*mm, "☐ Металлографический анализ")
        y_pos -= 5
    
    # Signatures
    c.drawString(20*mm, 155*mm, "Подписи:")
    c.drawString(25*mm, 150*mm, f"Инженер ЦЗЛ: {user.full_name} ___________________")
    c.drawString(25*mm, 145*mm, "Сотрудник ОТК: ___________________")
    c.drawString(25*mm, 140*mm, "Мастер: ___________________")
    
    # QR code with information
    qr_data = f"Заявка №{sample_request.id}; Материал: {material.material_grade}; Партия: {material.batch_number}; Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}"
    qr_code = generate_qr_code(qr_data)
    qr_img = Image.open(qr_code)
    
    # Put QR code in the upper right corner
    c.drawInlineImage(qr_img, 160*mm, 245*mm, width=30*mm, height=30*mm)
    
    # Footer
    c.setFont("Arial", 8)
    c.drawString(20*mm, 20*mm, "ППСД - Система проверки сертификатных данных")
    
    # Save PDF
    c.save()
    
    return output_path

def generate_label_pdf(material, output_path):
    """
    Generate a label PDF for material.
    
    Args:
        material: Material data
        output_path (str): Path to save the PDF
        
    Returns:
        str: Path to the generated PDF
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=(100*mm, 60*mm))
    c.setFont("Arial", 12)
    
    # Title
    c.drawString(5*mm, 50*mm, "МАТЕРИАЛ")
    
    # Material info
    c.setFont("Arial", 10)
    c.drawString(5*mm, 45*mm, f"Марка: {material.material_grade}")
    c.drawString(5*mm, 40*mm, f"Тип: {material.material_type}")
    c.drawString(5*mm, 35*mm, f"Партия: {material.batch_number}")
    c.drawString(5*mm, 30*mm, f"ID: {material.id}")
    
    # Status
    c.setFont("Arial", 10)
    if material.status == "approved":
        c.setFillColorRGB(0, 0.5, 0)  # Green
        c.drawString(5*mm, 20*mm, "СТАТУС: ГОДЕН")
    elif material.status == "rejected":
        c.setFillColorRGB(0.8, 0, 0)  # Red
        c.drawString(5*mm, 20*mm, "СТАТУС: БРАК")
    else:
        c.setFillColorRGB(0.5, 0.5, 0)  # Yellow
        c.drawString(5*mm, 20*mm, "СТАТУС: В ПРОЦЕССЕ")
    
    # QR code with material ID
    qr_data = f"ID:{material.id}; Марка:{material.material_grade}; Партия:{material.batch_number}"
    qr_code = generate_qr_code(qr_data, size=3)
    qr_img = Image.open(qr_code)
    
    # Put QR code on the right
    c.drawInlineImage(qr_img, 70*mm, 30*mm, width=25*mm, height=25*mm)
    
    # Save PDF
    c.save()
    
    return output_path 