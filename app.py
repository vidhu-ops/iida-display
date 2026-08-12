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
DATABASE_URL_SOURCE = None

DATABASE_URL_SUFFIXES = (
    'DATABASE_URL',
    'POSTGRES_URL',
    'DATABASE_URL_UNPOOLED',
    'POSTGRES_URL_NON_POOLING',
)


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


def collect_database_url_candidates():
    """Return ordered (env_key, url) candidates from Vercel/Neon env vars."""
    candidates = []
    seen_urls = set()

    def add(key, raw):
        if not raw or not is_valid_database_url(raw):
            return
        url = normalize_database_url(raw)
        if url in seen_urls:
            return
        seen_urls.add(url)
        candidates.append((key, url))

    add('DATABASE_URL', os.environ.get('DATABASE_URL'))

    for suffix in DATABASE_URL_SUFFIXES:
        for key, value in sorted(os.environ.items()):
            if key == 'DATABASE_URL' or not key.endswith(suffix):
                continue
            add(key, value)

    return candidates


def probe_database_url(url):
    """Return True when a Postgres URL accepts connections."""
    from sqlalchemy import create_engine, text

    engine = create_engine(
        url,
        connect_args={'sslmode': 'require'},
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True
    except Exception as exc:
        logging.warning('Database probe failed for %s: %s', url.split('@')[-1], exc)
        return False
    finally:
        engine.dispose()


def select_database_url():
    """Pick the first reachable Postgres URL on Vercel; prefer env order locally."""
    global DATABASE_URL_SOURCE

    candidates = collect_database_url_candidates()
    if not candidates:
        DATABASE_URL_SOURCE = None
        return None

    if IS_VERCEL:
        for key, url in candidates:
            if probe_database_url(url):
                DATABASE_URL_SOURCE = key
                logging.info('Using database URL from environment key: %s', key)
                return url
        logging.error(
            'No reachable database URL found among: %s',
            ', '.join(key for key, _ in candidates),
        )
        DATABASE_URL_SOURCE = None
        return None

    DATABASE_URL_SOURCE = candidates[0][0]
    logging.info('Using database URL from environment key: %s', DATABASE_URL_SOURCE)
    return candidates[0][1]


database_url = select_database_url()
DB_WARNING = None
if database_url and is_valid_database_url(database_url):
    logging.info('Database URL configured')
elif IS_VERCEL:
    DB_WARNING = (
        'No working DATABASE_URL found. Using temporary SQLite storage on this instance. '
        'Add Neon via Vercel Storage for persistent data.'
    )
    logging.warning(DB_WARNING)
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
    code, pre { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
    pre { padding: 12px; overflow-x: auto; }
    .box { background: #fff3cd; border: 1px solid #ffecb5; padding: 16px; border-radius: 8px; }
    ol { padding-left: 1.25rem; }
  </style>
</head>
<body>
  <h1>IIDA Display — setup required</h1>
  <div class="box">
    <p><strong>{{ message }}</strong></p>
    <p><strong>Fastest fix</strong> (from this repo on your machine):</p>
    <pre>npx vercel login
npx vercel link
./scripts/provision_vercel_neon.sh
npx vercel --prod</pre>
    <p>Or in the Vercel dashboard:</p>
    <ol>
      <li>Storage → Add → <strong>Neon</strong> (creates a fresh <code>DATABASE_URL</code>)</li>
      <li>Delete any old/broken <code>DATABASE_URL</code> first if Neon says endpoint disabled</li>
      <li>Set <code>SESSION_SECRET</code> and <code>GROQ_API_KEY</code></li>
      <li>Redeploy</li>
    </ol>
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
    candidates = collect_database_url_candidates()
    using_postgres = str(app.config.get('SQLALCHEMY_DATABASE_URI', '')).startswith('postgresql')

    db_ping = None
    db_ping_error = None
    if not CONFIG_ERROR:
        try:
            from sqlalchemy import text
            with app.app_context():
                db.session.execute(text('SELECT 1'))
            db_ping = True
        except Exception as e:
            db_ping = False
            db_ping_error = str(e)

    return jsonify({
        'status': 'ok' if not CONFIG_ERROR and not _db_error and db_ping else 'degraded',
        'vercel': IS_VERCEL,
        'database_url_set': bool(candidates),
        'database_url_source': DATABASE_URL_SOURCE,
        'database_url_candidates': [key for key, _ in candidates],
        'using_postgres': using_postgres,
        'database_ping': db_ping,
        'database_ping_error': db_ping_error,
        'session_secret_set': bool(os.environ.get('SESSION_SECRET')),
        'groq_key_set': bool(os.environ.get('GROQ_API_KEY')),
        'groq_model': os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile'),
        'config_error': CONFIG_ERROR,
        'database_warning': DB_WARNING,
        'database_error': _db_error,
        'fix': 'Add Neon via Vercel Storage for persistent DATABASE_URL' if DB_WARNING or not db_ping else None,
        'required_env': [
            'DATABASE_URL',
            'SESSION_SECRET',
            'GROQ_API_KEY',
        ],
    }), 200


if __name__ == '__main__':
    ensure_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
