from enum import Enum
from datetime import datetime
from .. import db

class TransactionStatus(Enum):
    DONE = 'done'
    FAILED = 'failed'
    ONGOING = 'ongoing'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    nature = db.Column(db.String)
    service = db.Column(db.String, nullable=False)
    service_provider = db.Column(db.String, nullable=False)
    related_transaction_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.Date, default=datetime.utcnow)
    currency = db.Column(db.String, default='XOF')
    wallet_id = db.Column(db.ForeignKey('wallets.id'))
    user_id = db.Column(db.ForeignKey('users.id'))
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.ONGOING)