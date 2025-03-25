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
