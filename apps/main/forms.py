from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Optional
from datetime import datetime
from flask_babel import _

class UserSettingsForm(FlaskForm):
    first_name = StringField(_('Prénom'), validators=[Optional()])
    last_name = StringField(_('Nom'), validators=[Optional()])
    phone_number = StringField(_('Numéro de téléphone'), validators=[Optional()])
    email = StringField(_('Email'), validators=[Optional(), Email()])
    gender = SelectField(_('Genre'), choices=[('male', _('Homme')), ('female', _('Femme')), ('other', _('Autre'))], validators=[Optional()])
    date_of_birth = DateField(_('Date de naissance'), format='%Y-%m-%d', validators=[Optional()])
    profile_picture = FileField(_('Photo de profil'), validators=[Optional()])
    submit = SubmitField(_('Continuer'))