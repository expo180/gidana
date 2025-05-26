
import re

def validate_email(email):
    """Check if an email is valid using regex."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email)

def validate_phone(phone):
    """Validate phone number in strict E.164 format (must start with +, allow spaces)."""
    # Remove all spaces for validation
    phone = phone.replace(" ", "")
    
    # E.164: Must start with +, followed by 1-15 digits (no leading zero after +)
    phone_regex = r"^\+[1-9]\d{1,14}$"
    
    return re.match(phone_regex, phone)

def validate_identifier(identifier):
    identifier = identifier.strip()
    if validate_email(identifier):
        return 'email', identifier
    elif validate_phone(identifier):
        return 'phone_number', identifier
    else:
        raise ValueError(_('Identifiant invalide. Veuillez entrer un email ou un numéro de téléphone valide.'))
