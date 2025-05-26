from flask import render_template, request, flash, url_for, redirect, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from ..models.user import User
from ..models.property import Property
from ..models.transaction import Transaction
from ..models.review import Review
from ..models.favorite import Favorite
from ..models.search_history import SearchHistory
from sqlalchemy import func, select, or_, and_
import os
from ..models.wallet import Wallet
from flask_babel import _
from .utils import fetch_nita_balance, fetch_mastercard_balance, fetch_mpesa_balance, fetch_paypal_balance, fetch_visa_balance
from . import main
from .. import db
from datetime import datetime
from werkzeug.utils import secure_filename
from .. import db
from .forms import UserSettingsForm
from .utils import save_profile_image, delete_profile_image
import time
try:
    from unidecode import unidecode
    has_unidecode = True
except ImportError:
    has_unidecode = False

@main.route('/')
def home():
    
    avg_rating_subquery = select(
        Review.property_id,
        func.avg(Review.rating).label('avg_rating')
    ).group_by(Review.property_id).subquery()
    
    # Recommandations (best ratings + availability)
    recommended_properties = db.session.query(Property)\
    .options(
        joinedload(Property.favorites).joinedload(Favorite.user)
    )\
    .outerjoin(avg_rating_subquery, Property.id == avg_rating_subquery.c.property_id)\
    .filter(Property.is_available == True)\
    .order_by(avg_rating_subquery.c.avg_rating.desc())\
    .limit(4)\
    .all()
    
    return render_template(
        'main/home.html',
        title=_('Accueil'),
        recommended_properties=recommended_properties
    )



@main.route('/explore')
def explore():
    query = Property.query.options(
        joinedload(Property.favorites).joinedload(Favorite.user)
    ).filter_by(is_available=True)

    property_type = request.args.get('type')
    if property_type and property_type != 'all':
        if property_type == _('À louer'):
            query = query.filter_by(transaction_type=_('À louer'))
        elif property_type == _('À vendre'):
            query = query.filter_by(transaction_type=_('À vendre'))
        else:
            query = query.filter_by(property_type=property_type)

    search_term = request.args.get('q')
    if search_term:
        search_cleaned = ' '.join(search_term.split()).lower()
        search_normalized = unidecode(search_cleaned) if has_unidecode else search_cleaned
        
        components = [comp.strip() for comp in search_normalized.split(',') if comp.strip()]
        conditions = []
        for component in components:
            words = component.split()
            component_conditions = []
            for word in words:
                if len(word) > 2:
                    word_pattern = f'%{word}%'
                    component_conditions.append(
                        or_(
                            func.lower(Property.neighborhood).ilike(word_pattern),
                            func.lower(Property.country).ilike(word_pattern),
                            func.lower(Property.exact_address).ilike(word_pattern)
                        )
                    )
            if component_conditions:
                conditions.append(and_(*component_conditions))
        
        if conditions:
            query = query.filter(or_(*conditions))
        
        if current_user.is_authenticated:
            search = SearchHistory(
                user_id=current_user.id,
                query=search_term
            )
            db.session.add(search)
            db.session.commit()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    properties = pagination.items

    recent_searches = []
    if current_user.is_authenticated:
        recent_searches = SearchHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(
            SearchHistory.created_at.desc()
        ).limit(5).all()

    return render_template(
        'main/explore.html',
        title=_('Explorer'),
        properties=properties,
        pagination=pagination,
        recent_searches=recent_searches
    )


@main.route('/save-search-history', methods=['POST'])
def save_search_history():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'status': 'error', 'message': 'No query provided'}), 400
    
    # Check if this exact search already exists recently
    existing = SearchHistory.query.filter_by(
        user_id=current_user.id,
        search_term=query
    ).order_by(SearchHistory.created_at.desc()).first()
    
    # Don't save duplicate searches within 1 hour
    if existing and (datetime.utcnow() - existing.created_at).total_seconds() < 3600:
        return jsonify({'status': 'success', 'message': 'Duplicate ignored'})
    
    # Save new search
    search = SearchHistory(
        user_id=current_user.id,
        query=query
    )
    db.session.add(search)
    db.session.commit()
    
    return jsonify({'status': 'success'})


@main.route('/local-suggestions')
def local_suggestions():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 3:
        return jsonify({'results': []})
    
    # Search for matching neighborhoods, cities, etc. in your database
    suggestions = db.session.query(
        Property.neighborhood,
        Property.country,
        Property.exact_address
    ).filter(
        or_(
            func.lower(Property.neighborhood).contains(query),
            func.lower(Property.country).contains(query),
            func.lower(Property.exact_address).contains(query)
        )
    ).distinct().limit(5).all()
    
    results = []
    for neighborhood, country, address in suggestions:
        display_text = ', '.join(filter(None, [neighborhood, country]))
        if address and address.lower() not in display_text.lower():
            display_text = f"{address}, {display_text}" if display_text else address
        
        results.append({
            'formatted': display_text,
            'components': {
                'neighbourhood': neighborhood,
                'country': country,
                'address': address
            }
        })
    
    return jsonify({'results': results})


@main.route('/favoris')
@login_required
def favourites():
    page = request.args.get('page', 1, type=int)
    per_page = 10 
    
    favorites_query = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(Favorite.created_at.desc())
    
    pagination = favorites_query.paginate(page=page, per_page=per_page, error_out=False)
    favorites = pagination.items
    
    return render_template(
        'main/favourites.html',
        title=_('Favoris'),
        favorites=favorites,
        pagination=pagination
    )


@main.route('/refresh_wallet_balance', methods=['POST'])
def refresh_wallet_balance():
    if not current_user.is_authenticated:
        flash(_('Vous devez être connecté pour effectuer cette action'), 'danger')
        return redirect(url_for('auth.login'))

    wallet = Wallet.query.filter_by(
        user_id=current_user.id,
        selected=True
    ).first()

    if not wallet:
        flash(_('Aucun portefeuille sélectionné'), 'danger')
        return redirect(request.referrer or url_for('main.index'))

    try:
        if wallet.provider == 'Nita':
            new_balance = fetch_nita_balance(wallet.phone_number, wallet.password)
        elif wallet.provider == 'MPesa':
            new_balance = fetch_mpesa_balance(wallet)
        elif wallet.provider == 'Visa':
            new_balance = fetch_visa_balance(wallet)
        elif wallet.provider == 'Mastercard':
            new_balance = fetch_mastercard_balance(wallet)
        elif wallet.provider == 'PayPal':
            new_balance = fetch_paypal_balance(wallet.email, wallet.password)
        else:
            flash(_('Fournisseur non supporté'), 'danger')
            return redirect(request.referrer or url_for('main.home'))

        wallet.balance = new_balance
        db.session.commit()
        
        flash(_(f'Solde {wallet.provider} actualisée'), 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(_(f'Erreur lors de la mise à jour du solde: {str(e)}'), 'danger')
    
    return redirect(request.referrer or url_for('main.index'))

@main.route('/wallet')
@login_required
def wallet():
    wallets = Wallet.query.filter_by(user_id=current_user.id).all()
    selected_wallet = Wallet.query.filter_by(selected=True).first()
    return render_template(
        'main/wallet.html',
        wallets=wallets,
        selected_wallet=selected_wallet,
        title=_('Portefeuilles'),
        year=datetime.now().year
    )

@main.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    transactions_pagination = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page)

    return render_template(
        'main/transactions.html',
        title=_('Transactions'),
        transactions=transactions_pagination,
        year=datetime.now().year
    )

@main.route('/user-settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    form = UserSettingsForm()

    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone_number.data = current_user.phone_number
        form.email.data = current_user.email
        form.gender.data = current_user.gender
        form.date_of_birth.data = current_user.date_of_birth

    if form.validate_on_submit():
        try:
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone_number = form.phone_number.data
            current_user.email = form.email.data
            current_user.gender = form.gender.data
            current_user.date_of_birth = form.date_of_birth.data

            if form.profile_picture.data:
                profile_picture = form.profile_picture.data
                print(profile_picture)

                profile_picture.seek(0, os.SEEK_END)
                size = profile_picture.tell()
                profile_picture.seek(0)

                if size > current_app.config['MAX_IMAGE_SIZE']:
                    flash(_('L\'image dépasse la taille maximale autorisée (5MB)'), 'danger')
                    return render_template('main/user_settings.html', form=form)

                try:
                    new_url = save_profile_image(profile_picture, current_user.id)

                    # Delete old one if it's not remote
                    if current_user.profile_picture and not current_user.profile_picture.startswith(('http://', 'https://')):
                        delete_profile_image(current_user.profile_picture)

                    current_user.profile_picture = new_url

                except ValueError as ve:
                    flash(str(ve), 'danger')
                    return render_template('main/user_settings.html', form=form)

            db.session.commit()
            flash(_('Vos paramètres ont été mis à jour!'), 'success')
            return redirect(url_for('main.user_settings'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user settings: {str(e)}", exc_info=True)
            flash(_('Une erreur est survenue lors de la mise à jour de vos paramètres'), 'danger')

    return render_template(
        'main/user_settings.html',
        title=_('Paramètres'),
        form=form
    )



@main.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('main/terms_and_conditions.html', title=_('Termes et Conditions'))
