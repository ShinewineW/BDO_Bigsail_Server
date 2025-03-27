from app import create_app, db
from app.models.card import Card
from app.models.user import User
from app.models.usage import Usage
import sys
import json
import traceback
from datetime import datetime

def delete_card(card_key):
    """删除指定的卡密及其关联的用户记录和使用记录"""
    app = create_app()
    with app.app_context():
        try:
            # 查找卡密
            card = Card.query.filter_by(card_key=card_key).first()
            
            if not card:
                print(f"错误: 卡密 {card_key} 不存在")
                return False, {}
            
            # 收集卡密信息用于记录
            card_info = {
                "card_key": card.card_key,
                "validity_period": card.validity_period,
                "is_active": card.is_active,
                "activation_date": card.activation_date.isoformat() if card.activation_date else None,
                "expiry_date": card.expiry_date.isoformat() if card.expiry_date else None,
                "created_at": card.created_at.isoformat(),
                "deleted_at": datetime.utcnow().isoformat()
            }
            
            # 查找关联的用户
            users = User.query.filter_by(card_id=card.id).all()
            
            # 记录用户信息和使用记录
            user_info = []
            usage_count = 0
            
            for user in users:
                # 收集用户信息
                user_data = {
                    "user_id": user.user_id,
                    "hardware_info": user.hardware_info,
                    "last_ip": user.last_ip,
                    "last_feature": user.last_feature,
                    "last_request": user.last_request.isoformat() if user.last_request else None,
                    "created_at": user.created_at.isoformat()
                }
                
                # 计算该用户的使用记录数量
                user_usage_count = Usage.query.filter_by(user_id=user.id).count()
                user_data["usage_count"] = user_usage_count
                usage_count += user_usage_count
                
                user_info.append(user_data)
            
            # 开始删除操作
            try:
                # 先删除所有关联的使用记录
                for user in users:
                    # 删除该用户的所有使用记录
                    Usage.query.filter_by(user_id=user.id).delete()
                
                # 再删除所有关联的用户
                for user in users:
                    db.session.delete(user)
                
                # 最后删除卡密
                db.session.delete(card)
                
                # 提交事务
                db.session.commit()
                
                print(f"已删除卡密: {card_key}")
                print(f"已删除关联的用户记录: {len(users)}个")
                print(f"已删除关联的使用记录: {usage_count}条")
                
                # 返回删除的信息用于记录
                return True, {
                    "card": card_info,
                    "users": user_info,
                    "total_usage_count": usage_count
                }
            except Exception as e:
                db.session.rollback()
                raise e
            
        except Exception as e:
            print(f"删除卡密时发生错误: {str(e)}")
            traceback.print_exc()
            return False, {}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("使用方法: python delete_card.py <卡密>")
        sys.exit(1)
    
    card_key = sys.argv[1]
    success, deleted_data = delete_card(card_key)
    
    # 输出JSON格式的删除数据，供shell脚本捕获
    print("DELETED_DATA_BEGIN")
    print(json.dumps(deleted_data))
    print("DELETED_DATA_END")
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
