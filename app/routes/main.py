# import requests
import requests
from flask import Blueprint, render_template


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def base():

    response = requests.get(
        "http://api.weatherapi.com/v1/current.json?key=3ca3bfa286b842afb4242203252304&q=San Francisco&aqi=no")
    data = response.json()
    weather = {
        "location": data['location']['name'],
        "temp": data['current']['temp_c'],
        "condition": data['current']['condition']['text'],
        "icon": data['current']['condition']['icon'],
    }

    return render_template('base.html', weather=weather)
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



@main_bp.route('/contact')
def contact():
    print("🔁 / contac route called")

    return render_template('contact.html')

@main_bp.route('/monitoring')
def monitoring():
    print("🔁 / monitoring route called")

    return render_template('monitoring.html')