from flask import render_template, request, jsonify, redirect, url_for, flash, session, make_response, send_from_directory
from app import app, db
from models import SearchSession, Favorite, TrendingTopic
from utils.keyword_research import KeywordResearcher
from utils.trends_analysis import TrendsAnalyzer
from utils.amazon_scraper import AmazonScraper
from utils.keyword_scoring import KeywordScorer
from utils.export_utils import ExportUtils
from datetime import datetime, date
import json
import logging

# Initialize utility classes
keyword_researcher = KeywordResearcher()
trends_analyzer = TrendsAnalyzer()
amazon_scraper = AmazonScraper()
keyword_scorer = KeywordScorer()
export_utils = ExportUtils()

# Template helper functions
@app.template_filter('abbreviate_number')
def abbreviate_number(value):
    if not value or value == 0:
        return "0"
    
    try:
        num = float(value)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(int(num))
    except:
        return str(value)

@app.template_global('get_difficulty_color')
def get_difficulty_color(score):
    if not score:
        return 'secondary'
    if score <= 30:
        return 'success'
    elif score <= 60:
        return 'warning'
    else:
        return 'danger'

@app.template_global('get_competition_color')
def get_competition_color(score):
    if not score:
        return 'secondary'
    if score <= 30:
        return 'success'
    elif score <= 60:
        return 'warning'
    else:
        return 'danger'

@app.route('/')
def index():
    # Get daily trending topics
    today = date.today()
    trending_topics = TrendingTopic.query.filter_by(date_trending=today).limit(10).all()
    
    # If no trending topics for today, fetch them
    if not trending_topics:
        try:
            topics = trends_analyzer.get_daily_trending_topics()
            for topic_data in topics[:10]:
                topic = TrendingTopic()
                topic.topic = topic_data['topic']
                topic.source = topic_data['source']
                topic.trend_score = topic_data.get('score', 0.0)
                topic.date_trending = today
                db.session.add(topic)
            db.session.commit()
            trending_topics = TrendingTopic.query.filter_by(date_trending=today).limit(10).all()
        except Exception as e:
            logging.error(f"Error fetching trending topics: {e}")
            trending_topics = []
    
    return render_template('index.html', trending_topics=trending_topics)

@app.route('/dashboard')
def dashboard():
    # Get recent sessions
    recent_sessions = SearchSession.query.order_by(SearchSession.updated_at.desc()).limit(5).all()
    return render_template('dashboard.html', recent_sessions=recent_sessions)

@app.route('/search_keywords', methods=['POST'])
def search_keywords():
    try:
        data = request.get_json()
        keywords_input = data.get('keywords', '').strip()
        bulk_mode = data.get('bulk_mode', False)
        
        if not keywords_input:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Parse keywords
        if bulk_mode:
            keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
        else:
            keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        results = []
        
        for keyword in keywords[:50]:  # Limit to 50 keywords
            try:
                # Get keyword expansions
                expansions = keyword_researcher.expand_keyword(keyword)
                
                # Get trends data
                trends_data = trends_analyzer.get_keyword_trends(keyword)
                
                # Get Amazon competition data
                amazon_data = amazon_scraper.get_keyword_competition(keyword)
                
                # Calculate keyword scores
                scores = keyword_scorer.calculate_scores(
                    keyword, trends_data, amazon_data, expansions
                )
                
                result = {
                    'keyword': keyword,
                    'expansions': expansions,
                    'search_volume': trends_data.get('search_volume', 0),
                    'trend_score': trends_data.get('trend_score', 0.0),
                    'amazon_results': amazon_data.get('result_count', 0),
                    'competition_score': scores['competition_score'],
                    'difficulty_score': scores['difficulty_score'],
                    'profitability_score': scores['profitability_score'],
                    'category': amazon_data.get('category', 'Unknown'),
                    'avg_price': amazon_data.get('avg_price', 0.0),
                    'avg_reviews': amazon_data.get('avg_reviews', 0)
                }
                
                results.append(result)
                
            except Exception as e:
                logging.error(f"Error processing keyword '{keyword}': {e}")
                continue
        
        # Auto-save session
        autosave_session = SearchSession.query.filter_by(is_autosave=True).first()
        if autosave_session:
            autosave_session.set_keywords(results)
            autosave_session.updated_at = datetime.utcnow()
        else:
            autosave_session = SearchSession()
            autosave_session.session_name = "Auto-saved Session"
            autosave_session.is_autosave = True
            autosave_session.set_keywords(results)
            db.session.add(autosave_session)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': results,
            'total_keywords': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error in search_keywords: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_session', methods=['POST'])
def save_session():
    try:
        data = request.get_json()
        session_name = data.get('session_name', '').strip()
        keywords_data = data.get('keywords_data', [])
        
        if not session_name:
            return jsonify({'error': 'Session name is required'}), 400
        
        # Check if session name already exists
        existing_session = SearchSession.query.filter_by(
            session_name=session_name, is_autosave=False
        ).first()
        
        if existing_session:
            existing_session.set_keywords(keywords_data)
            existing_session.updated_at = datetime.utcnow()
        else:
            new_session = SearchSession()
            new_session.session_name = session_name
            new_session.is_autosave = False
            new_session.set_keywords(keywords_data)
            db.session.add(new_session)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Session saved successfully'})
        
    except Exception as e:
        logging.error(f"Error saving session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/load_session/<int:session_id>')
def load_session(session_id):
    try:
        # Handle autosave session (ID 0)
        if session_id == 0:
            session_data = SearchSession.query.filter_by(is_autosave=True).first()
            if not session_data:
                return jsonify({
                    'success': True,
                    'session_name': 'Autosave',
                    'keywords_data': [],
                    'created_at': '',
                    'updated_at': ''
                })
        else:
            session_data = SearchSession.query.get_or_404(session_id)
        
        keywords_data = session_data.get_keywords()
        
        return jsonify({
            'success': True,
            'session_name': session_data.session_name,
            'keywords_data': keywords_data,
            'created_at': session_data.created_at.isoformat(),
            'updated_at': session_data.updated_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error loading session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400
        
        # Check if already in favorites
        existing_favorite = Favorite.query.filter_by(keyword=keyword).first()
        if existing_favorite:
            return jsonify({'error': 'Keyword already in favorites'}), 400
        
        favorite = Favorite()
        favorite.keyword = keyword
        favorite.search_volume = data.get('search_volume', 0)
        favorite.competition_score = data.get('competition_score', 0.0)
        favorite.difficulty_score = data.get('difficulty_score', 0.0)
        favorite.amazon_results = data.get('amazon_results', 0)
        favorite.notes = data.get('notes', '')
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Added to favorites'})
        
    except Exception as e:
        logging.error(f"Error adding favorite: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        favorite = Favorite.query.filter_by(keyword=keyword).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Removed from favorites'})
        else:
            return jsonify({'error': 'Keyword not found in favorites'}), 404
            
    except Exception as e:
        logging.error(f"Error removing favorite: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/favorites')
def favorites():
    favorites_list = Favorite.query.order_by(Favorite.created_at.desc()).all()
    return render_template('favorites.html', favorites=favorites_list)

@app.route('/export_favorites')
def export_favorites():
    try:
        favorites_list = Favorite.query.order_by(Favorite.created_at.desc()).all()
        
        # Convert favorites to the format expected by export_utils
        favorites_data = []
        for favorite in favorites_list:
            favorites_data.append({
                'keyword': favorite.keyword,
                'search_volume': favorite.search_volume,
                'competition_score': favorite.competition_score,
                'difficulty_score': favorite.difficulty_score,
                'amazon_results': favorite.amazon_results,
                'created_at': favorite.created_at.isoformat() if favorite.created_at else '',
                'notes': favorite.notes or ''
            })
        
        # Use export_utils to create CSV response
        response = export_utils.export_to_csv(favorites_data)
        
        # Update filename to indicate this is favorites export
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'attachment; filename=' in content_disposition:
            response.headers['Content-Disposition'] = f'attachment; filename=kdp_favorites_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting favorites: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export/<format>')
def export_data(format):
    try:
        # Get current session data from request args or use autosave
        session_id = request.args.get('session_id')
        
        if session_id:
            session_data = SearchSession.query.get_or_404(session_id)
            keywords_data = session_data.get_keywords()
        else:
            # Use autosave session
            autosave_session = SearchSession.query.filter_by(is_autosave=True).first()
            keywords_data = autosave_session.get_keywords() if autosave_session else []
        
        if format.lower() == 'csv':
            response = export_utils.export_to_csv(keywords_data)
        elif format.lower() == 'excel':
            response = export_utils.export_to_excel(keywords_data)
        elif format.lower() == 'pdf':
            response = export_utils.export_to_pdf(keywords_data)
        else:
            return jsonify({'error': 'Invalid export format'}), 400
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/get_sessions')
def get_sessions():
    sessions = SearchSession.query.filter_by(is_autosave=False).order_by(
        SearchSession.updated_at.desc()
    ).all()
    
    session_list = []
    for session in sessions:
        session_list.append({
            'id': session.id,
            'name': session.session_name,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'keyword_count': len(session.get_keywords())
        })
    
    return jsonify({'sessions': session_list})

@app.route('/backup_sessions')
def backup_sessions():
    try:
        sessions = SearchSession.query.filter_by(is_autosave=False).order_by(
            SearchSession.updated_at.desc()
        ).all()
        
        session_list = []
        for session in sessions:
            # Include full session data with keywords for backup
            session_list.append({
                'id': session.id,
                'name': session.session_name,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'keyword_count': len(session.get_keywords()),
                'keywords_data': session.get_keywords()  # Include actual keywords data
            })
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'sessions': session_list
        }
        
        # Create JSON response for download
        response = make_response(json.dumps(backup_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=kdp_sessions_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        logging.error(f"Error creating sessions backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        session_data = SearchSession.query.get_or_404(session_id)
        if session_data.is_autosave:
            return jsonify({'error': 'Cannot delete autosave session'}), 400
        
        db.session.delete(session_data)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Session deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting session: {e}")
        return jsonify({'error': str(e)}), 500

# PWA Routes
@app.route('/static/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/static/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')
