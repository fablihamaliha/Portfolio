from flask import Flask
from app.routes.main import main_bp  # this assumes `app/` is a package
from app.routes.metrics_api import metrics_api_bp  # Metrics API for monitoring dashboard
from telemetry_middleware import setup_telemetry
import os
import logging

def create_app():
    app = Flask(__name__, template_folder='app/templates')
    app.static_folder = 'app/static'
    app.register_blueprint(main_bp)
    app.register_blueprint(metrics_api_bp)  # Register metrics API

    # Persist logs to file for Promtail ingestion.
    logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs'))
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, 'app.log')
    root_logger = logging.getLogger()
    if not any(getattr(h, 'baseFilename', None) == log_path for h in root_logger.handlers):
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(file_handler)

    # Add telemetry
    setup_telemetry(app, app_name='portfolio')

    return app

# Optional but helpful for wsgi.py
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
