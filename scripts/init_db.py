from app import create_app, db
from app.models.card import Card
from app.models.user import User
from app.models.usage import Usage
from datetime import datetime, timedelta
import uuid

def init_db():
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库初始化完成")
        
        # # 检查是否已有卡密
        # if Card.query.count() == 0:
        #     # 创建一些测试卡密
        #     cards = [
        #         Card(
        #             card_key=str(uuid.uuid4()),
        #             expiry_date=datetime.utcnow() + timedelta(days=30),
        #             is_active=True
        #         ),
        #         Card(
        #             card_key=str(uuid.uuid4()),
        #             expiry_date=datetime.utcnow() + timedelta(days=90),
        #             is_active=True
        #         ),
        #         Card(
        #             card_key=str(uuid.uuid4()),
        #             expiry_date=datetime.utcnow() + timedelta(days=365),
        #             is_active=True
        #         )
        #     ]
            
        #     db.session.add_all(cards)
        #     db.session.commit()
            
        #     print("已创建测试卡密:")
        #     for card in cards:
        #         print(f"卡密: {card.card_key}, 过期时间: {card.expiry_date}")

if __name__ == '__main__':
    init_db()
