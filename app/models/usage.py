"""
File: usage.py
Description: 数据库模型，用于记录用户使用情况

Date: 2025-03-24
Version: 1.0

Author: ShineWine
Email: xxx@example.com
Copyright: @Netfahter Copyright Reserved

Update Log:
    - 2025-03-24: 更新内容
    - 2025-03-25: 添加记录数量限制功能
"""
from app import db
from datetime import datetime
from sqlalchemy import func

class Usage(db.Model):
    __tablename__ = 'usages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feature = db.Column(db.String(100), nullable=False)  # 使用的功能
    ip_address = db.Column(db.String(45))  # 请求IP地址
    used_at = db.Column(db.DateTime, default=datetime.utcnow)  # 使用时间
    
    def __repr__(self):
        return f'<Usage {self.id}: {self.feature}>'
    
    @classmethod
    def record_usage(cls, user_id, feature, ip_address):
        """
        记录用户使用情况，并限制记录数量不超过10,000条
        
        Args:
            user_id: 用户ID
            feature: 使用的功能
            ip_address: IP地址
            
        Returns:
            新创建的Usage对象
        """
        # 创建新记录
        usage = cls(
            user_id=user_id,
            feature=feature,
            ip_address=ip_address
        )
        db.session.add(usage)
        
        # 检查记录总数
        cls.limit_records(max_records=10000)
        
        return usage
    
    @classmethod
    def limit_records(cls, max_records=10000):
        """
        限制记录数量，当超过指定数量时删除最旧的记录
        
        Args:
            max_records: 最大记录数量，默认10000
        """
        try:
            # 获取当前记录总数
            record_count = db.session.query(func.count(cls.id)).scalar()
            
            # 如果超过最大记录数，删除多余的最旧记录
            if record_count > max_records:
                # 计算需要删除的记录数
                records_to_delete = record_count - max_records
                
                # 获取最旧的N条记录的ID
                oldest_records = db.session.query(cls.id).order_by(cls.used_at.asc()).limit(records_to_delete).all()
                oldest_ids = [record[0] for record in oldest_records]
                
                # 删除这些记录
                if oldest_ids:
                    db.session.query(cls).filter(cls.id.in_(oldest_ids)).delete(synchronize_session=False)
                    
                    # 记录日志（可选）
                    print(f"已删除 {len(oldest_ids)} 条最旧的使用记录，保持记录总数不超过 {max_records}")
        except Exception as e:
            # 出错时记录日志但不影响主要功能
            print(f"限制记录数量时出错: {str(e)}")
            db.session.rollback()