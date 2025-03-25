from flask import current_app, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

def allowed_file(filename):
    """检查文件是否允许上传"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'py', 'json', 'xml', 'yaml', 'yml'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """
    保存上传的文件
    
    Args:
        file: 文件对象
        
    Returns:
        保存后的文件名
    
    Raises:
        Exception: 如果文件类型不允许或保存失败
    """
    if not allowed_file(file.filename):
        raise Exception("不允许的文件类型")
    
    # 生成安全的文件名
    filename = secure_filename(file.filename)
    # 添加UUID前缀确保唯一性
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # 保存文件
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    return unique_filename

def get_file(filename):
    """
    获取上传的文件
    
    Args:
        filename: 文件名
        
    Returns:
        文件响应
    """
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
