from app import db
from datetime import datetime
import json

class SearchSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(200), nullable=False)
    keywords = db.Column(db.Text)  # JSON string of keywords and their data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_autosave = db.Column(db.Boolean, default=False)

    def set_keywords(self, keywords_data):
        self.keywords = json.dumps(keywords_data)
    
    def get_keywords(self):
        if self.keywords:
            return json.loads(self.keywords)
        return []

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(500), nullable=False)
    search_volume = db.Column(db.Integer, default=0)
    competition_score = db.Column(db.Float, default=0.0)
    difficulty_score = db.Column(db.Float, default=0.0)
    amazon_results = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class TrendingTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100))  # 'google_trends', 'youtube', 'twitter'
    trend_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date_trending = db.Column(db.Date, default=datetime.utcnow().date())
