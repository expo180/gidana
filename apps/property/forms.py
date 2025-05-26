from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_babel import _

class PropertyForm(FlaskForm):
    title = StringField(_('Titre'), validators=[DataRequired(), Length(max=100)])
    description = TextAreaField(_('Description'))
    neighborhood = StringField(
        _('Quartier'), 
        validators=[DataRequired(), Length(max=50)],
        render_kw={
            'autocomplete': 'off'
        }
    )
    country = StringField(
        _('Pays'), 
        validators=[DataRequired(), Length(max=50)],
        render_kw={
            'autocomplete': 'off'
        }
    )
    property_type = SelectField(_('Type de propriété'), choices=[
        (_('Maison'), _('Maison')),
        (_('Appartement'), _('Appartement')),
        (_('Villa'), _('Villa')),
        (_('Terrain'), _('Terrain'))
    ], validators=[DataRequired()])
    transaction_type = SelectField(_('Transaction'), choices=[
        (_('À louer'), _('À louer')),
        (_('À vendre'), _('À vendre'))
    ], validators=[DataRequired()])
    rooms = IntegerField(_('Nombre de chambres'), validators=[DataRequired(), NumberRange(min=1)])
    bathrooms = IntegerField(_('Nombre de salles de bain'), validators=[DataRequired(), NumberRange(min=1)])
    shower_type = SelectField(_('Type de douche'), choices=[
        (_('interne'), _('Interne')),
        (_('externe'), _('Externe'))
    ])
    surface = FloatField(_('Superficie (m²)'), validators=[Optional(), NumberRange(min=1)])  # <- FIXED
    price = FloatField(_('Prix/mois'), validators=[DataRequired(), NumberRange(min=0)])  # required
    currency = SelectField(_('Devise'), choices=[
        ('XOF', _('FCFA')),
        ('EUR', _('Euro')),
        ('USD', _('Dollar'))
    ], validators=[DataRequired()], default='XOF')
    is_available = BooleanField(_('Disponible'), default=True)
    has_courtyard = BooleanField(_('Avec cour'))
    has_water = BooleanField(_('Eau disponible'))
    has_electricity = BooleanField(_('Électricité disponible'))
    exact_address = StringField(
        _('Adresse exacte'), 
        validators=[Length(max=200)],
        render_kw={
            'autocomplete': 'off',
            'data-autocomplete': 'address'
        }
    )
    whatsapp_contact = StringField(_('Contact WhatsApp'), validators=[DataRequired(), Length(max=20)])
    phone_contact = StringField(_('Téléphone'), validators=[Length(max=20)])
