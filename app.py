import os
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
logging.basicConfig(level=logging.INFO if IS_VERCEL else logging.DEBUG)

CONFIG_ERROR = None


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
elif IS_VERCEL:
    CONFIG_ERROR = (
        'DATABASE_URL is not set. Add your Neon PostgreSQL connection string '
        'in Vercel → Settings → Environment Variables, then redeploy.'
    )
    logging.error(CONFIG_ERROR)
    database_url = 'sqlite:////tmp/ida-fallback.db'
else:
    database_url = 'sqlite:///ida.db'
    logging.info('No DATABASE_URL found, using SQLite for local development')

if database_url.startswith('sqlite'):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False},
    }
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'sslmode': 'require'},
    }

db.init_app(app)

_db_ready = False
_db_error = None

SETUP_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IIDA Display — Setup Required</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 48px auto; padding: 0 20px; line-height: 1.6; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
    .box { background: #fff3cd; border: 1px solid #ffecb5; padding: 16px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>IIDA Display — setup required</h1>
  <div class="box">
    <p><strong>{{ message }}</strong></p>
    <p>Add these in <strong>Vercel → Settings → Environment Variables</strong>, then redeploy:</p>
    <ul>
      <li><code>DATABASE_URL</code> — Neon PostgreSQL URL with <code>?sslmode=require</code></li>
      <li><code>SESSION_SECRET</code> — long random string</li>
      <li><code>GEMINI_API_KEY</code> — Google Gemini API key (optional, for AI features)</li>
    </ul>
  </div>
  <p><a href="/health">Check /health</a> · <a href="/status">Check /status</a></p>
</body>
</html>
"""


def ensure_database():
    global _db_ready, _db_error
    if _db_ready or CONFIG_ERROR:
        return
    try:
        with app.app_context():
            db.create_all()
        logging.info('Database tables ready')
        _db_ready = True
    except Exception as e:
        _db_error = str(e)
        logging.error(f'Database initialization failed: {e}')


@app.before_request
def _guard_and_init():
    if request.path in ('/health', '/status'):
        return
    if CONFIG_ERROR:
        return render_template_string(SETUP_TEMPLATE, message=CONFIG_ERROR), 503
    ensure_database()
    if _db_error and request.path != '/health':
        return render_template_string(
            SETUP_TEMPLATE,
            message=f'Database connection failed: {_db_error}',
        ), 503


with app.app_context():
    import models  # noqa: F401
    import routes  # noqa: F401


@app.route('/health')
def health():
    return {'status': 'ok'}, 200


@app.route('/status')
def status():
    return jsonify({
        'status': 'ok' if not CONFIG_ERROR and not _db_error else 'degraded',
        'vercel': IS_VERCEL,
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'session_secret_set': bool(os.environ.get('SESSION_SECRET')),
        'gemini_key_set': bool(os.environ.get('GEMINI_API_KEY')),
        'config_error': CONFIG_ERROR,
        'database_error': _db_error,
    }), 200


if __name__ == '__main__':
    ensure_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
