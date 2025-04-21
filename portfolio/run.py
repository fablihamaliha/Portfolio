from flask import Flask
from app.routes.main import main_bp  # adjust this import if needed

def create_app():
    app = Flask(__name__, template_folder='app/templates')  # 👈 tell Flask where templates live
    app.static_folder = 'app/static'  # optional, for CSS/JS
    app.register_blueprint(main_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
