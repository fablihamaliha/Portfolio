from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    print("🔁 / route called")

    return render_template('home.html')


@main_bp.route('/journey')
def journey():
    print("🔁 / journey route called")

    return render_template('journey.html')

@main_bp.route('/portfolio')
def portfolio():
    print("🔁 / port route called")

    return render_template('portfolio.html')

@main_bp.route('/certifications')
def certifications():
    print("🔁 / cert route called")

    return render_template('certifications.html')