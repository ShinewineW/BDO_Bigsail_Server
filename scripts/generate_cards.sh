#!/bin/bash

# 生成卡密脚本
# 使用方法: ./generate_cards.sh <数量> <有效期天数>

# 检查参数
if [ $# -ne 2 ]; then
    echo "使用方法: $0 <数量> <有效期天数>"
    echo "例如: $0 10 30  # 生成10张30天有效期的卡密"
    exit 1
fi

COUNT=$1
VALIDITY=$2

# 创建卡密记录目录
CARDS_DIR="/home/shinewine/card_records"
mkdir -p $CARDS_DIR

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${CARDS_DIR}/cards_${COUNT}_${VALIDITY}days_${TIMESTAMP}.txt"

echo "开始生成 $COUNT 张 $VALIDITY 天有效期的卡密..."

# 创建临时Python脚本
cat > /tmp/generate_cards.py << 'EOF'
from app import create_app, db
from app.models.card import Card
import uuid
import sys
import json

def generate_cards(count, validity_days):
    """生成指定数量和有效期的卡密"""
    app = create_app()
    with app.app_context():
        cards = []
        card_data = []
        
        for _ in range(count):
            card_key = uuid.uuid4().hex  # 生成32位卡密
            card = Card(
                card_key=card_key,
                validity_period=validity_days,
                is_active=False
            )
            cards.append(card)
            card_data.append({
                "card_key": card_key,
                "validity_period": validity_days
            })
        
        db.session.add_all(cards)
        db.session.commit()
        
        print(f"已生成 {count} 张卡密:")
        for card in cards:
            print(f"卡密: {card.card_key}, 有效期: {card.validity_period}天")
            
        # 返回卡密数据用于保存到文件
        return card_data

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("使用方法: python generate_cards.py <数量> <有效期天数>")
        sys.exit(1)
    
    count = int(sys.argv[1])
    validity = int(sys.argv[2])
    card_data = generate_cards(count, validity)
    
    # 输出JSON格式的卡密数据，供shell脚本捕获
    print("CARD_DATA_BEGIN")
    print(json.dumps(card_data))
    print("CARD_DATA_END")
EOF

# 复制脚本到容器
docker cp /tmp/generate_cards.py $(docker ps -qf "name=web"):/app/scripts/

# 在容器中执行脚本并捕获输出
OUTPUT=$(docker exec -it $(docker ps -qf "name=web") python -m scripts.generate_cards $COUNT $VALIDITY)

# 提取JSON数据
CARD_DATA=$(echo "$OUTPUT" | sed -n '/CARD_DATA_BEGIN/,/CARD_DATA_END/p' | grep -v "CARD_DATA_BEGIN" | grep -v "CARD_DATA_END")

# 保存卡密到本地文件
echo "生成时间: $(date)" > $OUTPUT_FILE
echo "数量: $COUNT" >> $OUTPUT_FILE
echo "有效期: $VALIDITY 天" >> $OUTPUT_FILE
echo "----------------------------------------" >> $OUTPUT_FILE

# 格式化输出卡密列表
echo "$CARD_DATA" | python3 -c "
import json, sys
cards = json.loads(sys.stdin.read())
for i, card in enumerate(cards, 1):
    print(f\"{i}. 卡密: {card['card_key']}, 有效期: {card['validity_period']}天\")
" >> $OUTPUT_FILE

# 清理临时文件
rm /tmp/generate_cards.py

echo "卡密生成完成！"
echo "卡密已保存到文件: $OUTPUT_FILE"

# 显示文件内容
echo "----------------------------------------"
echo "文件内容预览:"
cat $OUTPUT_FILE
echo "----------------------------------------"