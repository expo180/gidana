from flask_login import UserMixin
from .. import db
from .rental import Rental
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    phone_number = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String, nullable=False)
    profile_picture = db.Column(db.String)
    gender = db.Column(db.String)
    date_of_birth = db.Column(db.Date, default=datetime.utcnow)
    member_since = db.Column(db.Date, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    wallets = db.relationship('Wallet', backref='user', lazy=True)
    active = db.Column(db.Boolean, default=True)
    
    properties = db.relationship('Property', backref='owner', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    rentals = db.relationship('Rental', backref='tenant', lazy=True)

    def can_review_property(self, property_id):
        return Rental.query.filter_by(
            property_id=property_id,
            tenant_id=self.id,
            status='completed'
        ).count() > 0

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.email}>"