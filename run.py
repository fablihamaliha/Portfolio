from app.routes.main import main_bp  # adjust if needed
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='app/templates')
    app.static_folder = 'app/static'
    app.register_blueprint(main_bp)
    return app

# 👇 This is the key fix: expose app at module level
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
