"""
File: auth.py
Description: 用于验证卡密，并处理用户绑定。

Date: 2025-03-24
Version: 1.0

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-24: 更新内容
"""
from app.models.card import Card
from app.models.user import User
from app import db
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

def verify_card_and_user(card_key, hardware_info, ip_address, feature):
    """
    验证卡密并处理用户绑定
    
    Args:
        card_key: 卡密字符串
        hardware_info: 硬件信息
        ip_address: IP地址
        feature: 使用的功能
        
    Returns:
        (状态, 消息, 卡对象, 用户对象)
    """
    # 查找卡密
    card = Card.query.filter_by(card_key=card_key).first()
    
    if not card:
        return False, "无效的卡密", None, None
    
    # 查找与此卡密关联的用户
    user = User.query.filter_by(card_id=card.id).first()

    # 如果卡密未激活
    if not card.is_active:
        # 激活卡密
        card.activate()
        
        # 如果没有用户，创建新用户
        if not user:
            user_id = uuid.uuid4().hex
            user = User(
                user_id=user_id,
                card_id=card.id,
                hardware_info=hardware_info,
                last_ip=ip_address,
                last_feature=feature
            )
            db.session.add(user)
            try:
                db.session.commit()
                return True, "卡密激活成功", card, user
            except Exception as e:
                db.session.rollback()
                logger.error(f"数据库错误: {str(e)}")
                return False, "服务器错误", None, None
        else:
            # 更新用户信息
            user.update_request_info(ip_address, hardware_info, feature)
            db.session.commit()
            return True, "卡密激活成功", card, user

    # 如果卡密已激活
    if not card.is_valid():
        return False, "卡密已过期", None, None
    
    # 如果有用户绑定
    if user:
        # 检查硬件信息和IP是否匹配
        hardware_match = user.hardware_info == hardware_info
        ip_match = user.last_ip == ip_address
        
        if not hardware_match and not ip_match:
            logger.warning(f"可能的盗用尝试: 卡密={card_key}, 原硬件={user.hardware_info}, 新硬件={hardware_info}, 原IP={user.last_ip}, 新IP={ip_address}")
            return False, "硬件信息和IP地址不匹配", None, None
        
        # 更新用户信息
        user.update_request_info(ip_address, hardware_info, feature)
        db.session.commit()
        return True, "验证成功", card, user
    
    # 不应该到达这里，但以防万一
    return False, "未知错误", None, None
