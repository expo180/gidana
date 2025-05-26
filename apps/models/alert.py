from .. import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    neighborhood = db.Column(db.String(50))
    property_type = db.Column(db.String(50))
    min_rooms = db.Column(db.Integer)
    max_price = db.Column(db.Float)
    transaction_type = db.Column(db.String(20))  # Location/Vente
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)