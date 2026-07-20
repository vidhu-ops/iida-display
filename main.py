from app import app

# Vercel expects a WSGI `app` object in this module.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
