from flask import Flask, session, request, redirect, g, send_from_directory, current_app
import requests
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel, _
from datetime import datetime
import os

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
babel = Babel()


from .models.user import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(development=True, template_folder='templates', static_folder='static'):
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.from_object(config['development'])
    config['development'].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .property import property as property_blueprint
    app.register_blueprint(property_blueprint, url_prefix='/property')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    def get_locale():
        user = getattr(g, 'user', None)
        if user and user.locale in app.config['BABEL_SUPPORTED_LOCALES']:
            return user.locale
        return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

    def get_timezone():
        user = getattr(g, 'user', None)
        if user is not None:
            return user.timezone

    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)

    @app.context_processor
    def inject_get_locale():
        return {'get_locale': get_locale}

    @app.route('/set_language', methods=['POST'])
    def set_language():
        language = request.form['language']
        response = redirect(request.referrer)
        response.set_cookie('language', language)
        return response

    @app.route('/local_files/<path:folder>/<filename>')
    def local_files(folder, filename):
        """
        Serves uploaded files from a local directory.
        The folder path should be relative to your storage root.
        """
        directory = os.path.join(current_app.root_path, 'static', folder)
        return send_from_directory(directory, filename)
    
    @app.route('/sw.js')
    def serve_sw():
        return send_from_directory(current_app.root_path, 'sw.js', mimetype='application/javascript')


    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    def check_internet_connection():
        url = "https://www.google.com"
        timeout = 8
        try:
            response = requests.get(url, timeout=timeout)
            return True if response.status_code == 200 else False
        except requests.ConnectionError:
            return False

    @app.context_processor
    def inject_internet_status():
        return {'is_connected': check_internet_connection()}
    

    @app.template_filter('format_currency')
    def format_currency(value, currency):
        symbols = {
            'XOF': 'FCFA',
            'EUR': '€',
            'USD': '$',
            'GBP': '£'
        }
        symbol = symbols.get(currency.upper(), currency)
        return f"{int(value):,} {symbol}".replace(",", " ")

    @app.template_filter('transaction_suffix')
    def transaction_suffix(transaction_type):
        if transaction_type.lower() == _('À louer'):
            return "/mois"
        return ""




    @app.template_filter('strftime')
    def _jinja2_filter_strftime(dt, fmt=None):
        if dt:
            return dt.strftime(fmt)
        else:
            return None
        
    with app.app_context():
        db.create_all()

    return app