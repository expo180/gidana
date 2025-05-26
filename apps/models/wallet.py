from .. import db

class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String)
    balance = db.Column(db.Float, default=0.0)
    provider = db.Column(db.String, nullable=False)  # e.g., 'Nita', 'MPesa', 'Visa', 'Mastercard'
    nature = db.Column(db.String)  # Type of wallet (e.g., 'mobile money', 'card', etc.)
    selected = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String, unique=True, nullable=True)  
    email = db.Column(db.String, unique=True, nullable=True)  
    card_number = db.Column(db.String, unique=True, nullable=True)
    cvv = db.Column(db.String, nullable=True)
    expiration_date = db.Column(db.String, nullable=True)
    currency = db.Column(db.String, default='XOF')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='wallet', lazy=True)
    

    def __repr__(self):
        return f"<Wallet {self.provider} - {self.nature}>"