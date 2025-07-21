# app/models/stock_model.py

import uuid
from datetime import datetime
from app.extensions import db

class Stock(db.Model):
    __tablename__ = 'stock'

    stock_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment='UUID'
    )
    stock_code = db.Column(
        db.String(10),
        nullable=False,
        unique=True,
        comment='종목 코드'
    )
    stock_name = db.Column(
        db.Text,
        nullable=False,
        comment='종목 이름'
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='레코드 생성 시각'
    )

    def to_dict(self):
        return {
            'stock_id': self.stock_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
