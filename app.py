import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.INFO if os.environ.get('VERCEL') else logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-for-ida')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


def is_valid_database_url(url):
    if not url:
        return False
    valid_schemes = ['postgresql://', 'postgres://', 'sqlite://', 'mysql://', 'mariadb://']
    return any(url.startswith(scheme) for scheme in valid_schemes)


def normalize_database_url(url):
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


database_url = os.environ.get('DATABASE_URL')
if database_url and is_valid_database_url(database_url):
    database_url = normalize_database_url(database_url)
    logging.info('Using DATABASE_URL from environment')
else:
    database_url = 'sqlite:///ida.db'
    logging.info('No valid DATABASE_URL found, using SQLite for local development')

if database_url.startswith('sqlite'):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False},
    }
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    engine_options = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    if 'neon.tech' in database_url or os.environ.get('VERCEL'):
        engine_options['connect_args'] = {'sslmode': 'require'}
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

db.init_app(app)

with app.app_context():
    import models  # noqa: F401
    import routes  # noqa: F401

    try:
        db.create_all()
        logging.info('Database tables created successfully')
    except Exception as e:
        logging.error(f'Failed to create database tables: {e}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
