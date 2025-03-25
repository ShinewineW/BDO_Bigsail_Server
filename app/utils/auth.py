"""
File: auth.py
Description: 用于验证卡密，并处理用户绑定。

Date: 2025-03-24
Version: 1.1

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-24: 更新内容
    - 2025-03-26: 改进错误处理、日志记录和时间处理
"""
from app.models.card import Card
from app.models.user import User
from app import db
from datetime import datetime, timezone
import uuid
import logging
import traceback

# 配置日志记录器
logger = logging.getLogger(__name__)

def get_utc_now():
    """
    获取当前UTC时间
    
    Returns:
        datetime: 当前UTC时间
    """
    return datetime.now(timezone.utc)

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
    try:
        # 记录验证请求
        logger.info(f"验证请求: 卡密={card_key}, IP={ip_address}, 功能={feature}")
        
        # 参数验证
        if not all([card_key, hardware_info, ip_address, feature]):
            logger.warning(f"参数不完整: 卡密={card_key}, 硬件={hardware_info}, IP={ip_address}, 功能={feature}")
            return False, "请求参数不完整", None, None
        
        # 查找卡密
        card = Card.query.filter_by(card_key=card_key).first()
        
        if not card:
            logger.warning(f"无效卡密: {card_key}")
            return False, "无效的卡密", None, None
        
        # 查找与此卡密关联的用户
        user = User.query.filter_by(card_id=card.id).first()

        # 开始事务
        db_transaction = db.session.begin_nested()
        
        try:
            # 如果卡密未激活
            if not card.is_active:
                logger.info(f"激活卡密: {card_key}")
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
                    db.session.flush()  # 确保用户ID已生成
                    logger.info(f"创建新用户: 卡密={card_key}, 用户ID={user.id}, 硬件={hardware_info}")
                    db.session.commit()
                    return True, "卡密激活成功", card, user
                else:
                    # 更新用户信息
                    user.update_request_info(ip_address, hardware_info, feature)
                    logger.info(f"更新用户信息: 卡密={card_key}, 用户ID={user.id}")
                    db.session.commit()
                    return True, "卡密激活成功", card, user

            # 如果卡密已激活
            if not card.is_valid():
                expiry = card.expiry_date.strftime('%Y-%m-%d %H:%M:%S') if card.expiry_date else "未知"
                logger.warning(f"卡密已过期: 卡密={card_key}, 过期时间={expiry}")
                return False, "卡密已过期", None, None
            
            # 如果有用户绑定
            if user:
                # 检查硬件信息和IP是否匹配
                hardware_match = user.hardware_info == hardware_info
                ip_match = user.last_ip == ip_address
                
                if not hardware_match and not ip_match:
                    logger.warning(f"验证失败: 卡密={card_key}, 原硬件={user.hardware_info}, 新硬件={hardware_info}, 原IP={user.last_ip}, 新IP={ip_address}")
                    return False, "硬件信息和IP地址不匹配", None, None
                
                # 更新用户信息
                user.update_request_info(ip_address, hardware_info, feature)
                logger.info(f"验证成功: 卡密={card_key}, 用户ID={user.id}")
                db.session.commit()
                return True, "验证成功", card, user
            else:
                # 卡密已激活但没有关联用户（可能是被解绑过）
                # 创建新用户
                logger.info(f"卡密已激活但无关联用户，重新绑定: 卡密={card_key}")
                user_id = uuid.uuid4().hex
                user = User(
                    user_id=user_id,
                    card_id=card.id,
                    hardware_info=hardware_info,
                    last_ip=ip_address,
                    last_feature=feature
                )
                db.session.add(user)
                db.session.flush()  # 确保用户ID已生成
                logger.info(f"重新绑定成功: 卡密={card_key}, 新用户ID={user.id}")
                db.session.commit()
                return True, "重新绑定成功", card, user
                
        except Exception as e:
            # 回滚事务
            db_transaction.rollback()
            # 记录详细错误信息
            error_details = traceback.format_exc()
            logger.error(f"数据库操作错误: 卡密={card_key}, 错误={str(e)}\n{error_details}")
            return False, "服务器错误", None, None
            
    except Exception as e:
        # 记录详细错误信息
        error_details = traceback.format_exc()
        logger.error(f"验证过程中发生未处理异常: {str(e)}\n{error_details}")
        return False, "服务器内部错误", None, None
    
    # 不应该到达这里，但以防万一
    logger.error(f"验证过程到达了不应该到达的代码路径: 卡密={card_key}")
    return False, "未知错误", None, None
