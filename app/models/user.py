
"""
File: user.py
Description: 用户信息数据模型，存储了:
             1. 用户id，唯一标志用户，仅暴露给数据表用于方便查询
             2. 客户id，32位客户ID，这个ID是可以暴露给客户看的
             3. 卡id，用于关联卡信息
             4. 硬件信息，用于关联客户硬件信息
             5. 最后请求ip，用于关联客户最后请求ip
             6. 最后请求时间，用于关联客户最后请求时间
             7. 最后请求功能，用于关联客户最后请求功能
             7. 创建时间，用于关联客户创建时间
             

Date: 2025-03-24
Version: 1.0

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-24: 更新内容
"""
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), unique=True, nullable=False)  # 客户ID
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False, unique=True)  # 一对一关系
    hardware_info = db.Column(db.Text, nullable=False)
    last_ip = db.Column(db.String(45))
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    last_feature = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    usages = db.relationship('Usage', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.user_id}>'
    
    def update_request_info(self, ip, hardware_info, feature):
        """更新用户请求信息"""
        self.last_ip = ip
        self.hardware_info = hardware_info
        self.last_feature = feature
        self.last_request = datetime.utcnow()
    
    def update_feature(self, feature):
        """更新用户请求功能"""
        self.last_feature = feature