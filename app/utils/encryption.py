"""
File: encryption.py
Description: 用于加密和解密传输数据

Date: 2025-03-25
Version: 1.0

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-25: 更新内容
"""
from flask import current_app
import hashlib
from cryptography.fernet import Fernet
import json
import base64

def encrypt_data(data):
    """
    加密数据
    
    Args:
        data: 要加密的数据(字典或字符串)
        key_name: 密钥名称，默认使用主密钥
        
    Returns:
        加密后的base64字符串
    """
    key = current_app.config['ENCRYPTION_KEY']
    
    # 确保密钥长度为32字节
    key_bytes = hashlib.sha256(key.encode()).digest()
    
    # 创建Fernet对象
    fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    # 如果是字典，先转为JSON字符串
    if isinstance(data, dict):
        data = json.dumps(data)
    
    # 加密数据
    encrypted_data = fernet.encrypt(data.encode())
    
    # 返回base64编码的加密数据
    return base64.urlsafe_b64encode(encrypted_data).decode()

def decrypt_data(encrypted_data):
    """
    解密数据
    
    Args:
        encrypted_data: 加密的base64字符串
        key_name: 密钥名称，默认使用主密钥
        
    Returns:
        解密后的原始数据
    """
    key = current_app.config['ENCRYPTION_KEY']
    
    # 确保密钥长度为32字节
    key_bytes = hashlib.sha256(key.encode()).digest()
    
    # 创建Fernet对象
    fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    # 解码base64
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
    
    # 解密数据
    decrypted_data = fernet.decrypt(encrypted_bytes).decode()
    
    # 尝试解析JSON
    try:
        return json.loads(decrypted_data)
    except:
        return decrypted_data