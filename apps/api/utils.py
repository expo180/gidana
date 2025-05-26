import json
from flask import current_app

def mask_phone_number(phone_number):
    """Mask a phone number, showing only the last 3 digits."""
    if not phone_number or len(phone_number) < 3:
        return phone_number
    return f"******{phone_number[-3:]}"

def mask_email(email):
    """Mask an email, showing only the first 2 characters and the domain."""
    if not email or '@' not in email:
        return email
    username, domain = email.split('@', 1)
    return f"{username[:2]}*****@{domain}"


def mask_card_number(card_number):
    """Mask a card number, showing only the last 4 digits."""
    if not card_number or len(card_number) < 4:
        return card_number
    return f"**** **** **** {card_number[-4:]}"


def load_service_prices():
    with open(current_app.config['SERVICES_PRICES_PATH'], 'r') as file:
        return json.load(file)