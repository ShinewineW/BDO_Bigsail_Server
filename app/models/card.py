"""
File: card.py
Description: 建立本地数据和数据库的数据模型的连接，如下文件定义了一个卡密的数据类型，
             卡密ID: 自增主键，用于唯一标识卡密
             卡密: 32位字符串，用于唯一标识卡密
             有效期: 整型，用于表示卡密有效期天数
             是否激活: 布尔型，用于表示卡密是否激活
             激活日期: 日期型，用于表示卡密激活日期
             过期时间: 日期型，用于表示卡密过期时间
             创建时间: 日期型，用于表示卡密创建时间
             

Date: 2025-03-24
Version: 1.0

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-24: 更新内容
"""
from app import db
from datetime import datetime, timedelta

class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    card_key = db.Column(db.String(32), unique=True, nullable=False, index=True)
    validity_period = db.Column(db.Integer, nullable=False)  # 有效期天数
    is_active = db.Column(db.Boolean, default=False)  # 默认未激活
    activation_date = db.Column(db.DateTime, nullable=True)  # 激活日期
    expiry_date = db.Column(db.DateTime, nullable=True)  # 过期时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='card', lazy='dynamic')
    
    def __repr__(self):
        return f'<Card {self.card_key}>'
    
    def is_valid(self):
        if not self.is_active or not self.expiry_date:
            return False
        return self.expiry_date > datetime.utcnow()
    
    def activate(self):
        """激活卡密并设置过期时间"""
        if not self.is_active:
            self.is_active = True
            self.activation_date = datetime.utcnow()
            self.expiry_date = self.activation_date + timedelta(days=self.validity_period)
            return True
        return False
