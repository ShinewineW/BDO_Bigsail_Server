#!/bin/bash

# 删除卡密脚本
# 使用方法: ./delete_card.sh <卡密>

# 检查参数
if [ $# -ne 1 ]; then
    echo "使用方法: $0 <卡密>"
    echo "例如: $0 5f6c91d49b104e7fb9e1b38e39a6b85a  # 删除指定卡密"
    exit 1
fi

CARD_KEY=$1

# 创建卡密记录目录
CARDS_DIR="/home/shinewine/card_records"
mkdir -p $CARDS_DIR

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${CARDS_DIR}/deleted_cards_${TIMESTAMP}.txt"

echo "开始删除卡密: $CARD_KEY..."

# 创建临时Python脚本
cat > /tmp/delete_card.py << 'EOF'
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
EOF

# 复制脚本到容器
docker cp /tmp/delete_card.py $(docker ps -qf "name=web"):/app/scripts/

# 在容器中执行脚本并捕获输出
OUTPUT=$(docker exec -it $(docker ps -qf "name=web") python -m scripts.delete_card $CARD_KEY)

# 检查执行结果
if echo "$OUTPUT" | grep -q "已删除卡密"; then
    echo "卡密删除成功！"
    
    # 提取JSON数据
    DELETED_DATA=$(echo "$OUTPUT" | sed -n '/DELETED_DATA_BEGIN/,/DELETED_DATA_END/p' | grep -v "DELETED_DATA_BEGIN" | grep -v "DELETED_DATA_END")
    
    # 保存删除记录到本地文件
    echo "删除时间: $(date)" > $LOG_FILE
    echo "卡密: $CARD_KEY" >> $LOG_FILE
    echo "----------------------------------------" >> $LOG_FILE
    
    # 格式化输出删除信息
    echo "$DELETED_DATA" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    if 'card' in data:
        card = data['card']
        print(f\"卡密信息:\")
        print(f\"  卡密: {card.get('card_key', '未知')}\")
        print(f\"  有效期: {card.get('validity_period', '未知')}天\")
        print(f\"  激活状态: {'已激活' if card.get('is_active') else '未激活'}\")
        print(f\"  激活日期: {card.get('activation_date', '未激活')}\")
        print(f\"  过期日期: {card.get('expiry_date', '未设置')}\")
        print(f\"  创建时间: {card.get('created_at', '未知')}\")
        print(f\"  删除时间: {card.get('deleted_at', '未知')}\")
        
    if 'users' in data and data['users']:
        print(f\"\n已删除的关联用户信息:\")
        for i, user in enumerate(data['users'], 1):
            print(f\"  用户 {i}:\")
            print(f\"    用户ID: {user.get('user_id', '未知')}\")
            print(f\"    硬件信息: {user.get('hardware_info', '未知')}\")
            print(f\"    最后IP: {user.get('last_ip', '未知')}\")
            print(f\"    最后功能: {user.get('last_feature', '未知')}\")
            print(f\"    最后请求时间: {user.get('last_request', '未知')}\")
            print(f\"    创建时间: {user.get('created_at', '未知')}\")
            print(f\"    使用记录数: {user.get('usage_count', 0)}条\")
    else:
        print(f\"\n无关联用户\")
        
    if 'total_usage_count' in data:
        print(f\"\n总计删除使用记录: {data['total_usage_count']}条\")
except Exception as e:
    print(f\"解析数据错误: {e}\")
" >> $LOG_FILE
    
    echo "----------------------------------------" >> $LOG_FILE
    
    echo "删除记录已保存到文件: $LOG_FILE"
    echo "----------------------------------------"
    echo "删除记录预览:"
    cat $LOG_FILE
    echo "----------------------------------------"
else
    echo "卡密删除失败！"
    echo "$OUTPUT"
fi

# 清理临时文件
rm /tmp/delete_card.py