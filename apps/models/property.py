from .. import db
from datetime import datetime

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    neighborhood = db.Column(db.String(50), nullable=False)  # Quartier
    property_type = db.Column(db.String(50), nullable=False)  # Villa, Appartement, etc.
    rooms = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(50), nullable=False)  # Pays
    bathrooms = db.Column(db.Integer, nullable=False)
    shower_type = db.Column(db.String(20))  # Interne/Externe
    transaction_type = db.Column(db.String(20), nullable=False)  # Location/Vente
    surface = db.Column(db.Float)  # Superficie en m²
    has_courtyard = db.Column(db.Boolean, default=False)
    has_water = db.Column(db.Boolean, default=False)
    has_electricity = db.Column(db.Boolean, default=False)
    exact_address = db.Column(db.String(200))
    whatsapp_contact = db.Column(db.String(20))
    phone_contact = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='XOF')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    images = db.relationship(
        'PropertyImage',
        backref='property',
        lazy=True,
        cascade='all, delete-orphan'
    )

    rentals = db.relationship(
        'Rental',
        backref='property',
        lazy=True,
        cascade='all, delete-orphan'
    )

    favorites = db.relationship(
        'Favorite',
        backref='property',
        lazy=True,
        cascade='all, delete-orphan'
    )

    reviews = db.relationship(
        'Review',
        backref='property',
        lazy=True,
        cascade='all, delete-orphan'
    )
    

    
    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        total = sum(review.rating for review in self.reviews)
        return round(total / len(self.reviews), 1)
    
    @property
    def review_count(self):
        return len(self.reviews)
    
    def has_user_reviewed(self, user_id):
        return any(review.user_id == user_id for review in self.reviews)

    def __repr__(self):
        return f"<Property {self.title} in {self.neighborhood}>"