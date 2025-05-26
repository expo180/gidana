from flask import current_app
from ..property.utils import save_property_images, allowed_file, delete_property_image

def save_profile_image(file, user_id):
    """
    Saves a user's profile image either to Firebase or locally.
    
    Returns the public URL of the uploaded image or None.
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        raise ValueError("Unsupported file type")

    folder = f"profile_pictures/{user_id}"

    saved_urls = save_property_images([file], folder)
    return saved_urls[0] if saved_urls else None


def delete_profile_image(image_url):
    """
    Deletes a user's profile image from Firebase or local storage.
    """
    if not image_url:
        return

    try:
        delete_property_image(image_url)
    except Exception as e:
        current_app.logger.error(f"Error deleting profile image: {str(e)}")



def fetch_nita_balance(phone_number, password):
    # Implement logic to fetch balance from Nita provider
    return 1000.0  # Example balance


def fetch_paypal_balance(email, password):
    # Implement logic to fetch balance from Nita provider
    return 1000.0  # Example balance

def fetch_mpesa_balance(wallet):
    # Implement logic to fetch balance from MPesa provider
    return 500.0  # Example balance

def fetch_visa_balance(wallet):
    # Implement logic to fetch balance from Visa provider
    return 750.0  # Example balance

def fetch_mastercard_balance(wallet):
    # Implement logic to fetch balance from Mastercard provider
    return 600.0  # Example balance

