import os
from flask import url_for, current_app
from werkzeug.utils import secure_filename
from firebase_admin import storage, initialize_app, credentials
from dotenv import load_dotenv
import socket

load_dotenv()

firebase_config = {
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
}

cred = credentials.Certificate(firebase_config)
default_app = initialize_app(cred, {'storageBucket': 'afrilog-797e8.appspot.com'})


def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """Check if internet is available."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def save_property_images(files, folder_name):
    """
    Saves image files for a property either to Firebase or locally.
    
    Returns a list of public URLs (Firebase or local).
    """
    if check_internet_connection():
        return save_images_to_firebase(files, folder_name)
    else:
        return save_images_locally(files, folder_name)

def save_images_to_firebase(files, folder):
    saved_urls = []
    bucket = storage.bucket()

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            blob = bucket.blob(f"{folder}/{filename}")
            blob.upload_from_file(file)
            blob.make_public()
            saved_urls.append(blob.public_url)

    return saved_urls

def save_images_locally(files, folder_name):
    """
    Saves image files locally and returns list of public URLs for the frontend.
    """
    saved_urls = []
    base_path = os.path.join(get_app_data_path(), folder_name)
    os.makedirs(base_path, exist_ok=True)

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            full_path = os.path.join(base_path, filename)
            file.save(full_path)
            file_url = url_for('local_files', folder=folder_name, filename=filename, _external=True)
            saved_urls.append(file_url)

    return saved_urls

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_app_data_path():
    """Helper for local storage root directory."""
    return os.path.join(current_app.root_path, 'static')


def delete_property_image(image_url_or_path):
    """
    Deletes a property image from either Firebase Storage or local storage.
    
    Args:
        image_url_or_path: The public URL (for Firebase) or local path of the image to delete
    """
    try:
        # Check if this is a Firebase URL
        if 'firebasestorage.googleapis.com' in image_url_or_path:
            # Extract the blob path from the Firebase URL
            bucket_name = 'afrilog-797e8.appspot.com'  # Your Firebase bucket name
            start_index = image_url_or_path.find(bucket_name) + len(bucket_name) + 1
            blob_path = image_url_or_path[start_index:].split('?')[0]
            
            # Delete from Firebase
            bucket = storage.bucket()
            blob = bucket.blob(blob_path)
            blob.delete()
            return True
        
        else:
            # Handle local file deletion
            # Extract the relative path from the URL (assuming format like '/static/property_images/1/filename.jpg')
            if url_for('local_files') in image_url_or_path:
                # Remove the base URL part to get the relative path
                static_path = url_for('static', filename='').lstrip('/')
                relative_path = image_url_or_path.split(static_path)[-1]
                full_path = os.path.join(get_app_data_path(), relative_path)
                
                # Delete the file if it exists
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
                
    except Exception as e:
        current_app.logger.error(f"Error deleting image: {str(e)}")
        return False
    
    return False