from flask import render_template, redirect, url_for, flash, session, request
from .forms import LoginForm, RegisterForm
from flask_babel import _
from datetime import datetime, timedelta
from .utils import validate_email, validate_phone
from flask_login import login_user, current_user, logout_user
from ..models.user import User
from werkzeug.security import check_password_hash, generate_password_hash
from . import auth
from .. import db

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    next_page = request.args.get('next')

    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        password = form.password.data
        remember = form.remember_me.data

        # Check if identifier is an email
        if validate_email(identifier):
            user = User.query.filter_by(email=identifier).first()
        else:
            # Normalize phone number: remove spaces
            normalized_phone = identifier.replace(" ", "")

            # Validate phone number with required "+" format
            if validate_phone(normalized_phone):
                user = User.query.filter_by(phone_number=normalized_phone).first()
            else:
                flash(_('Veuillez entrer un numéro de téléphone valide au format international, avec "+" (ex: +14155552671).'), 'danger')
                return redirect(url_for('auth.login', next=next_page))

        # Check credentials
        if user is None or not check_password_hash(user.password_hash, password):
            flash(_('Identifiants incorrects. Veuillez réessayer.'), 'danger')
            return redirect(url_for('auth.login', next=next_page))

        login_user(user, remember=remember)

        if remember:
            session.permanent = True
            session.modified = True
            auth.app.permanent_session_lifetime = timedelta(days=30)

        flash(_('Connexion réussie!'), 'success')
        return redirect(next_page or url_for('main.home'))

    return render_template(
        'auth/login.html',
        form=form,
        title=_('Se Connecter'),
        year=datetime.now().year
    )


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()

    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        password = form.password.data
        confirm_password = form.confirm_password.data
        print(identifier, password, confirm_password)

        if password != confirm_password:
            flash(_('Les mots de passe ne correspondent pas. Veuillez réessayer.'), 'danger')
            return redirect(url_for('auth.register'))


        if validate_email(identifier):
            # Email is valid, check if already registered
            if User.query.filter_by(email=identifier).first():
                flash(_('Un compte avec cet e-mail existe déjà.'), 'danger')
                return redirect(url_for('auth.register'))
            email = identifier
            phone_number = None
        else:
            # Normalize and validate phone
            normalized_phone = identifier.replace(" ", "")
            if validate_phone(normalized_phone):
                if User.query.filter_by(phone_number=normalized_phone).first():
                    flash(_('Un compte avec ce numéro existe déjà.'), 'danger')
                    return redirect(url_for('auth.register'))
                phone_number = normalized_phone
                email = None
            else:
                flash(_('Identifiant invalide. Veuillez entrer un e-mail ou un numéro de téléphone valide au format international avec "+" (ex: +33612345678).'), 'danger')
                return redirect(url_for('auth.register'))


        new_user = User(
            email=email,
            phone_number=phone_number,
            password_hash=generate_password_hash(password),
            member_since=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        flash(_('Compte créé avec succès! Connectez-vous maintenant.'), 'success')
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/register.html',
        form=form,
        title=_('Nouveau Compte'),
        year=datetime.now().year
    )


@auth.route('/forgot-password')
def forgot_password():
    return 'Forgot Password'
    

@auth.route('/reset-password')
def reset_password():
    return 'Reset Password'    

@auth.route('/logout')
def logout():
    logout_user()
    flash(_('Vous avez été déconnecté.'), 'success')
    return redirect(url_for('main.home'))



