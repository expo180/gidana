from flask_wtf import FlaskForm
from flask_babel import _
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    identifier = StringField(_('N° de Téléphone ou Adresse E-mail'), validators=[DataRequired()])
    password = PasswordField(_('Mot de Passe'), validators=[DataRequired()])
    remember_me = BooleanField(_('Se souvenir de moi'))
    submit = SubmitField(_('Se connecter'))


class RegisterForm(FlaskForm):
    identifier = StringField(_('N° de Téléphone ou Adresse E-mail'), validators=[DataRequired()])
    password = PasswordField(_('Mot de Passe'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(_('Confirmer le mot de passe'), validators=[DataRequired()])
    accept_terms = BooleanField(_('J’accepte les'), validators=[DataRequired()])
    submit = SubmitField(_('Continuer'))