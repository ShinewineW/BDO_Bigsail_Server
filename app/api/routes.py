from flask import Blueprint, request, jsonify, current_app, send_from_directory
from app import db
from app.models.card import Card
from app.models.user import User
from app.models.usage import Usage
from app.utils.auth import verify_card_and_user
from app.utils.encryption import decrypt_data, encrypt_data
from app.utils.file_handler import save_uploaded_file, get_file
import os
from datetime import datetime
import uuid

api = Blueprint('api', __name__)

@api.route('/verify', methods=['POST'])
def verify():
    # 检查是否有加密数据
    encrypted_data = request.json.get('encrypted_data')
    
    if encrypted_data:
        try:
            # 解密数据
            data = decrypt_data(encrypted_data)
        except Exception as e:
            current_app.logger.error(f"解密错误: {str(e)}")
            return jsonify({'status': 'error'}), 400
    else:
        current_app.logger.error("未加密的请求")
        return jsonify({'status': 'error'}), 400

    if not data:
        return jsonify({'status': 'error'}), 400
    
    card_key = data.get('card_key')
    ip = request.remote_addr
    hardware_info = data.get('hardware_info')
    feature = data.get('feature')
    
    if not all([card_key, hardware_info, feature]):
        return jsonify({'status': 'error'}), 401
    
    # 验证卡密和用户
    success, message, card, user = verify_card_and_user(card_key, hardware_info, ip, feature)
    
    if not success:
        # 加密错误响应
        error_response = {'status': 'error', 'message': message}
        encrypted_error = {'encrypted_data': encrypt_data(error_response)}
        return jsonify(encrypted_error), 401
    
    # 记录使用情况
    usage = Usage(user_id=user.id, feature=feature, ip_address=ip)
    db.session.add(usage)
    
    try:
        db.session.commit()
        
        # 如果功能是"打开程序"，返回解密密钥
        response_data = {
            'status': 'success',
            'message': message,
            'expiry_date': card.expiry_date.isoformat() if card.expiry_date else None
        }
        
        if feature == "打开程序":
            response_data['DATA_SAFE_KEY'] = current_app.config['DATA_SAFE_KEY']
        
        # 加密响应数据
        encrypted_response = {
            'encrypted_data': encrypt_data(response_data)
        }
        return jsonify(encrypted_response), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"数据库错误: {str(e)}")
        # 加密错误响应
        error_response = {'status': 'error', 'message': '服务器错误'}
        encrypted_error = {'encrypted_data': encrypt_data(error_response)}
        return jsonify(encrypted_error), 500


# 后续路由暂时不处理
# @api.route('/get_key', methods=['POST'])
# def get_key():
#     data = request.json
#     if not data:
#         return jsonify({'status': 'error', 'message': '无效的请求数据'}), 400
    
#     card_key = data.get('card_key')
#     key_name = data.get('key_name')
    
#     if not all([card_key, key_name]):
#         return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
#     # 验证卡密
#     card = verify_card(card_key)
#     if not card:
#         return jsonify({'status': 'error', 'message': '无效的卡密或已过期'}), 401
    
#     # 获取加密密钥
#     encryption_key = get_encryption_key(key_name)
#     if not encryption_key:
#         return jsonify({'status': 'error', 'message': '请求的密钥不存在'}), 404
    
#     return jsonify({
#         'status': 'success',
#         'key': encryption_key
#     })

# @api.route('/upload_file', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'status': 'error', 'message': '没有文件部分'}), 400
    
#     file = request.files['file']
#     card_key = request.form.get('card_key')
    
#     if not card_key:
#         return jsonify({'status': 'error', 'message': '缺少卡密'}), 400
    
#     if file.filename == '':
#         return jsonify({'status': 'error', 'message': '没有选择文件'}), 400
    
#     # 验证卡密
#     card = verify_card(card_key)
#     if not card:
#         return jsonify({'status': 'error', 'message': '无效的卡密或已过期'}), 401
    
#     # 保存文件
#     try:
#         filename = save_uploaded_file(file)
#         return jsonify({
#             'status': 'success',
#             'message': '文件上传成功',
#             'filename': filename
#         })
#     except Exception as e:
#         current_app.logger.error(f"文件上传错误: {str(e)}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# @api.route('/get_file/<filename>', methods=['GET'])
# def download_file(filename):
#     card_key = request.args.get('card_key')
    
#     if not card_key:
#         return jsonify({'status': 'error', 'message': '缺少卡密'}), 400
    
#     # 验证卡密
#     card = verify_card(card_key)
#     if not card:
#         return jsonify({'status': 'error', 'message': '无效的卡密或已过期'}), 401
    
#     try:
#         return get_file(filename)
#     except Exception as e:
#         current_app.logger.error(f"文件下载错误: {str(e)}")
#         return jsonify({'status': 'error', 'message': str(e)}), 404

# @api.route('/execute', methods=['POST'])
# def execute_function():
#     data = request.json
#     if not data:
#         return jsonify({'status': 'error', 'message': '无效的请求数据'}), 400
    
#     card_key = data.get('card_key')
#     function_name = data.get('function')
#     params = data.get('params', {})
    
#     if not all([card_key, function_name]):
#         return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
#     # 验证卡密
#     card = verify_card(card_key)
#     if not card:
#         return jsonify({'status': 'error', 'message': '无效的卡密或已过期'}), 401
    
#     # 这里应该有一个函数映射表或动态导入机制
#     # 简化示例:
#     try:
#         # 假设函数返回结果
#         result = {"message": f"执行了函数 {function_name} 与参数 {params}"}
#         return jsonify({
#             'status': 'success',
#             'result': result
#         })
#     except Exception as e:
#         current_app.logger.error(f"函数执行错误: {str(e)}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500
