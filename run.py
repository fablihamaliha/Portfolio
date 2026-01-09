from flask import Flask
from app.routes.main import main_bp  # this assumes `app/` is a package

def create_app():
    app = Flask(__name__, template_folder='app/templates')
    app.static_folder = 'app/static'
    app.register_blueprint(main_bp)
    return app

# Optional but helpful for wsgi.py
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
