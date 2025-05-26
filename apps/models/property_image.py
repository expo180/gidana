from .. import db

class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Image {self.filename} for Property {self.property_id}>"