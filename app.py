import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kdp-keyword-research-tool-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kdp_keywords.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models
    import routes
    
    # Create all tables
    db.create_all()

# Template filters
@app.template_filter('abbreviate_number')
def abbreviate_number_filter(value):
    """Abbreviate large numbers"""
    if not value:
        return '0'
    
    value = int(value)
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"
    else:
        return str(value)

@app.template_filter('get_difficulty_color')
def get_difficulty_color(score):
    """Get Bootstrap color class for difficulty score"""
    if not score:
        return 'secondary'
    if score <= 30:
        return 'success'
    elif score <= 60:
        return 'warning'
    else:
        return 'danger'

@app.template_filter('get_competition_color')
def get_competition_color(score):
    """Get Bootstrap color class for competition score"""
    if not score:
        return 'secondary'
    if score <= 30:
        return 'success'
    elif score <= 60:
        return 'warning'
    else:
        return 'danger'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
