from flask import render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from ..models.wallet import Wallet
from ..models.transaction import Transaction
from datetime import datetime
from . import api
from .. import db
from flask_babel import _
from .utils import mask_email, mask_phone_number, mask_card_number, load_service_prices
from ..main.utils import fetch_nita_balance, fetch_paypal_balance
from werkzeug.security import generate_password_hash
from ..models.transaction import TransactionStatus
from ..auth.utils import validate_email, validate_phone

@api.route('/create_new_wallet', methods=['GET', 'POST'])
@login_required
def add_wallet():
    if request.method == 'POST':
        provider = request.form.get('provider')
        phone_number = request.form.get('phone_number')
        card_number = request.form.get('card_number')
        cvv = request.form.get('cvv')
        expiration_date = request.form.get('expiration_date')
        email = request.form.get('email')
        password = request.form.get('password')
        selected = request.form.get('selected') == 'on'
        currency = request.form.get('currency')

        if provider == "Nita":
            if not phone_number or not password:
                flash(_("Le numéro de téléphone et le mot de passe sont requis pour Nita."), "error")
                return redirect(url_for('api.add_wallet'))
            hashed_password = generate_password_hash(password)
            balance = fetch_nita_balance(phone_number, password)
        elif provider == "PayPal":
            if not email or not password:
                flash(_("L'adresse e-mail et le mot de passe sont requis pour PayPal."), "error")
                return redirect(url_for('api.add_wallet'))
            hashed_password = generate_password_hash(password)
            balance = fetch_paypal_balance(email, password)
        elif provider in ["Visa", "Mastercard"]:
            if not card_number or not cvv or not expiration_date:
                flash(_("Tous les champs sont requis pour Visa/Mastercard."), "error")
                return redirect(url_for('api.add_wallet'))
            hashed_password = None
            balance = 0.0 

        if selected:
            Wallet.query.filter_by(user_id=current_user.id, selected=True).update({'selected': False})
            db.session.commit()

        new_wallet = Wallet(
            user_id=current_user.id,
            provider=provider,
            phone_number=phone_number,
            card_number=card_number,
            cvv=cvv,
            expiration_date=expiration_date,
            email=email,
            password=hashed_password,
            selected=selected,
            currency=currency,
            balance=balance
        )
        db.session.add(new_wallet)
        db.session.commit()

        flash(_("Portefeuille créé avec succès!"), "success")
        return redirect(url_for('main.wallet'))

    return render_template(
        'api/create_new_wallet.html',
        year=datetime.now().year
    )

@api.route('/edit_wallet/<int:wallet_id>', methods=['GET', 'POST'])
@login_required
def edit_wallet(wallet_id):
    wallet = Wallet.query.filter_by(id=wallet_id, user_id=current_user.id).first()
    if not wallet:
        flash("Portefeuille introuvable.", "error")
        return redirect(url_for('api.add_wallet'))

    if request.method == 'POST':
        provider = request.form.get('provider')
        phone_number = request.form.get('phone_number')
        card_number = request.form.get('card_number')
        cvv = request.form.get('cvv')
        expiration_date = request.form.get('expiration_date')
        email = request.form.get('email')
        currency = request.form.get('currency')
        selected = request.form.get('selected') == 'on'

        if provider == "Nita":
            if not phone_number:
                flash(_("Le numéro de téléphone est requis pour Nita."), "error")
                return redirect(url_for('api.edit_wallet', wallet_id=wallet_id))
        elif provider in ["Visa", "Mastercard"]:
            if not card_number or not cvv or not expiration_date:
                flash(_("Tous les champs sont requis pour Visa/Mastercard."), "error")
                return redirect(url_for('api.edit_wallet', wallet_id=wallet_id))
        elif provider == "PayPal":
            if not email:
                flash(_("L'adresse e-mail est requise pour PayPal."), "error")
                return redirect(url_for('api.edit_wallet', wallet_id=wallet_id))

        wallet.provider = provider
        wallet.phone_number = phone_number
        wallet.card_number = card_number
        wallet.cvv = cvv
        wallet.expiration_date = expiration_date
        wallet.email = email
        wallet.currency = currency

        if selected:
            Wallet.query.filter_by(user_id=current_user.id, selected=True).update({'selected': False})
            wallet.selected = True
        else:
            wallet.selected = False

        db.session.commit()

        flash(_("Portefeuille mis à jour avec succès!"), "success")
        return redirect(url_for('main.wallet'))

    return render_template('api/edit_wallet.html', wallet=wallet)

@api.route('/delete_wallet/<int:wallet_id>', methods=['GET'])
@login_required
def delete_wallet(wallet_id):
    wallet = Wallet.query.filter_by(id=wallet_id, user_id=current_user.id).first()
    if not wallet:
        flash(_("Portefeuille introuvable."), "error")
        return redirect(url_for('api.add_wallet'))

    db.session.delete(wallet)
    db.session.commit()

    flash(_("Portefeuille supprimé avec succès!"), "success")
    return redirect(url_for('api.add_wallet'))


@api.route('/pay-a-service', methods=['GET','POST'])
@login_required
def pay_service():
    if request.method == 'GET':
        # Fetch the selected wallet (default wallet)
        selected_wallet = Wallet.query.filter_by(selected=True).first()
        
        # Fetch all wallets for the dropdown (if needed)
        wallets = Wallet.query.filter_by(user_id=current_user.id).all()
        
        return render_template(
            'api/pay_a_service.html',
            title=_('Payer un service'),
            selected_wallet=selected_wallet,
            wallets=wallets,
            mask_phone_number=mask_phone_number,
            mask_email=mask_email,
            mask_card_number=mask_card_number
        )
    
    if request.method == 'POST':
        wallet_id = request.form.get('walletProvider')
        service_type = request.form.get('serviceType')
        provider = request.form.get('provider')
        plan = request.form.get('starlinkPlan', None)
        starlink_email = request.form.get('starlinkEmail', None)
        starlink_password = request.form.get('starlinkPassword', None)
        tv_account_number = request.form.get('tvAccountNumber', None)
        tv_pin = request.form.get('tvPin', None)

        if not wallet_id:
            flash(_('Please select a wallet'), 'error')
            return redirect(url_for('api.pay_service'))

        if not service_type or not provider:
            flash(_('Veuillez sélectionner un service et un fournisseur'), 'error')
            return redirect(url_for('api.pay_service'))

        # Validate Starlink-specific fields
        if service_type == 'network' and provider == 'starlink':
            if not plan:
                flash(_('Veuillez sélectionner un plan'), 'error')
                return redirect(url_for('api.pay_service'))
            if not starlink_email or not starlink_password:
                flash(_('Veuillez fournir votre mot de passe et identifiants Starlink'), 'error')
                return redirect(url_for('api.pay_service'))

        # Validate TV-specific fields
        if service_type == 'tv':
            if not tv_account_number or not tv_pin:
                flash(_('Veuillez fournir votre N° d\'abonné et votre PIN'), 'error')
                return redirect(url_for('api.pay_service'))

        wallet = Wallet.query.filter_by(id=wallet_id, user_id=current_user.id).first()
        if not wallet:
            flash(_('Portefeuille introuvable'), 'error')
            return redirect(url_for('api.pay_service'))

        service_prices = load_service_prices()

        if service_type == 'network' and provider == 'starlink':
            service_data = service_prices.get('starlink', {}).get(plan, {})
            base_price = service_data.get('price', 0)
            currency = service_data.get('currency', 'XOF')
        elif service_type == 'tv':
            service_data = service_prices.get('tv', {}).get(provider, {})
            base_price = service_data.get('price', 0)
            currency = service_data.get('currency', 'XOF')
        else:
            flash(_('Invalid service type or provider'), 'error')
            return redirect(url_for('api.pay_service'))

        # For simplicity, we'll just add 10% of the base price as the service fee
        # Here we will need a function for converting the currency to default wallet currency
        service_fee = base_price * 0.1
        total_amount = base_price + service_fee

        session['payment_details'] = {
            'wallet_id': wallet_id,
            'service_type': service_type,
            'provider': provider,
            'plan': plan,
            'starlink_email': starlink_email,
            'starlink_password': starlink_password,
            'tv_account_number': tv_account_number,
            'tv_pin': tv_pin,
            'base_price': base_price,
            'service_fee': service_fee,
            'total_amount': total_amount,
            'currency': currency,
            'wallet_balance': wallet.balance
        }

        return redirect(url_for('api.confirm_payment'))
    
    
@api.route('/confirm_payment', methods=['GET'])
@login_required
def confirm_payment():
    payment_details = session.get('payment_details')
    if not payment_details:
        flash(_('Aucun détail de paiement trouvé'), 'error')
        return redirect(url_for('api.pay_service'))

    return render_template(
        'api/confirm_payment.html',
        title=_('Confirmer le paiement'),
        payment_details=payment_details
    )


@api.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    payment_details = session.get('payment_details')
    if not payment_details:
        flash(_('Aucun détail de paiement trouvé'), 'error')
        return redirect(url_for('api.pay_a_service'))

    wallet = Wallet.query.filter_by(id=payment_details['wallet_id'], user_id=current_user.id).first()
    if not wallet:
        flash(_('Portefeuille introuvable'), 'error')
        return redirect(url_for('api.pay_a_service'))

    if wallet.balance < payment_details['total_amount']:
        flash(_('Solde insuffisante pour effectuer le paiement'), 'error')
        return redirect(url_for('api.pay_a_service'))

    # Deduct the amount from the wallet
    wallet.balance -= payment_details['total_amount']

    # Calculate the total amount (base_price + service_fee)
    total_amount = payment_details['base_price'] + payment_details['service_fee']

    transaction = Transaction(
        wallet_id=wallet.id,
        user_id=current_user.id,
        service=payment_details['service_type'],
        service_provider=payment_details['provider'],
        amount=total_amount,
        currency=payment_details['currency'],
        status=TransactionStatus.DONE,
        nature='expense',
        created_at=datetime.utcnow()
    )

    db.session.add(transaction)
    db.session.commit()

    # Clear the payment details from the session
    session.pop('payment_details', None)

    flash(_('Paiement effectué avec succès'), 'success')
    return redirect(url_for('main.home'))


@api.route('/transfer-money', methods=['GET', 'POST'])
def transfer_money():
    if request.method == 'GET':
        default_wallet = Wallet.query.filter_by(
            user_id=current_user.id,
            selected=True
        ).first()

        if not default_wallet:
            flash(_('No default wallet found. Please set a default wallet first.'), 'error')
            return redirect(url_for('wallet.manage_wallets'))

        return render_template('api/transfer.html',
                            title=_('Transférer'),
                            mask_email=mask_email,
                            mask_phone_number=mask_phone_number,
                            selected_wallet=default_wallet)

    data = request.form

    try:
        if not all(key in data for key in ['transferMethod', 'amount']):
            flash(_("Veuillez compléter tous les champs requis"), "error")
            return redirect(url_for('api.transfer_money'))

        sender_wallet = Wallet.query.filter_by(
            user_id=current_user.id,
            selected=True
        ).first()

        if not sender_wallet:
            flash(_("Votre portefeuille est introuvable"), "error")
            return redirect(url_for('api.transfer_money'))

        try:
            amount = float(data['amount'])
            if amount <= 0:
                flash(_("Montant doit être supérieur à 0"), "error")
                return redirect(url_for('api.transfer_money'))
        except ValueError:
            flash(_("Montant invalide"), "error")
            return redirect(url_for('api.transfer_money'))

        if sender_wallet.balance < amount:
            flash(_("Solde insuffisante"), "error")
            return redirect(url_for('api.transfer_money'))

        transfer_method = data['transferMethod']
        recipient_identifier = None

        if transfer_method == 'mobile_money':
            recipient_identifier = data.get('recipientPhone')
            if not validate_phone(recipient_identifier):
                flash(_("Numéro de téléphone du destinataire invalide"), "error")
                return redirect(url_for('api.transfer_money'))

            if recipient_identifier == sender_wallet.phone_number:
                flash(_("Vous ne pouvez pas transférer à votre propre portefeuille"), "error")
                return redirect(url_for('api.transfer_money'))

            recipient_wallet = Wallet.query.filter_by(
                phone_number=recipient_identifier,
                provider='Nita'
            ).first()

        elif transfer_method == 'paypal':
            recipient_identifier = data.get('recipientEmail')
            if not validate_email(recipient_identifier):
                flash(_("Adresse E-mail invalide"), "error")
                return redirect(url_for('api.transfer_money'))

            if recipient_identifier == sender_wallet.email:
                flash(_("Vous ne pouvez pas transférer à votre propre portefeuille"), "error")
                return redirect(url_for('api.transfer_money'))

            recipient_wallet = Wallet.query.filter_by(
                email=recipient_identifier,
                provider='PayPal'
            ).first()

        else:
            flash(_("Méthode de transfer invalide"), "error")
            return redirect(url_for('api.transfer_money'))

        if not recipient_wallet:
            flash(_("Destinataire non trouvé. Veuillez vérifier les informations"), "error")
            return redirect(url_for('api.transfer_money'))

        if sender_wallet.provider in ['Nita', 'PayPal'] and 'password' not in data:
            flash(_("Mot de passe requis"), "error")
            return redirect(url_for('api.transfer_money'))


        if sender_wallet.currency != recipient_wallet.currency:
            flash(_("Les devises des portefeuilles ne correspondent pas"), "error")
            return redirect(url_for('api.transfer_money'))

        sender_wallet.balance -= amount
        recipient_wallet.balance += amount

        db.session.add(sender_wallet)
        db.session.add(recipient_wallet)

        sender_transaction = Transaction(
            amount=amount,
            nature='transfer_out',
            service='peer_transfer',
            service_provider=recipient_wallet.provider,
            created_at=datetime.utcnow(),
            currency=sender_wallet.currency,
            wallet_id=sender_wallet.id,
            user_id=sender_wallet.user_id,
            status=TransactionStatus.DONE
        )

        recipient_transaction = Transaction(
            amount=amount,
            nature='transfer_in',
            service='peer_transfer',
            service_provider=sender_wallet.provider,
            created_at=datetime.utcnow(),
            currency=recipient_wallet.currency,
            wallet_id=recipient_wallet.id,
            user_id=recipient_wallet.user_id,
            status=TransactionStatus.DONE
        )

        sender_transaction.related_transaction_id = recipient_transaction.id
        recipient_transaction.related_transaction_id = sender_transaction.id

        db.session.add(sender_transaction)
        db.session.add(recipient_transaction)
        db.session.commit()

        flash(_("Transfer effectué avec succès"), "success")
        return redirect(url_for('main.home'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Transfer error: {str(e)}")
        flash(_("Une erreur s'est produite lors du transfert"), "error")
        return redirect(url_for('api.transfer_money'))