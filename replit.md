# Overview

The KDP Keyword Research Tool is a comprehensive Flask web application designed to help Amazon KDP authors and publishers discover profitable book keywords and trending topics. The application provides keyword expansion, competitor analysis, trend discovery, and comprehensive scoring systems to identify high-potential, low-competition keywords for book publishing success.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture

**Framework**: Flask web application with SQLAlchemy ORM for database operations. The application follows a modular structure with separation of concerns:

- **App Configuration**: Centralized Flask app setup with SQLite database configuration, session management, and ProxyFix middleware for deployment compatibility
- **Models Layer**: Three main data models using SQLAlchemy declarative base:
  - `SearchSession`: Stores keyword research sessions with JSON serialization for complex data
  - `Favorite`: Manages user's favorited keywords with scoring metrics
  - `TrendingTopic`: Tracks daily trending topics from various sources
- **Routes Layer**: RESTful endpoint handlers for web pages and API interactions
- **Utils Layer**: Modular utility classes for core functionality:
  - `KeywordResearcher`: Handles keyword expansion using multiple sources
  - `TrendsAnalyzer`: Integrates with Google Trends via pytrends library
  - `AmazonScraper`: Web scraping for Amazon competition analysis
  - `KeywordScorer`: Calculates comprehensive keyword scoring metrics
  - `ExportUtils`: Handles data export to CSV, Excel, and PDF formats

## Frontend Architecture

**UI Framework**: Bootstrap 5 with custom CSS for responsive design and dark/light theme support. The frontend uses:

- **Template System**: Jinja2 templating with base template inheritance
- **Interactive Components**: Chart.js for data visualization, vanilla JavaScript for dynamic interactions
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Theme System**: CSS custom properties for seamless dark/light mode switching

## Data Storage

**Database**: SQLite for local development and deployment simplicity. Database design includes:
- Session persistence for keyword research workflows
- Favorites management with full keyword metadata
- Trending topics cache with date-based filtering
- JSON serialization for complex data structures within SQLite constraints

## Scoring and Analysis System

**Multi-factor Scoring**: Comprehensive keyword evaluation using:
- Search volume estimation from trend data
- Competition analysis from Amazon result counts and reviews
- Trend momentum calculations from historical data
- Profitability scoring combining multiple weighted factors
- Difficulty scoring for competition assessment

# External Dependencies

## APIs and Web Services

- **Google Trends**: pytrends library for accessing Google Trends data without API keys
- **Google Autocomplete**: Direct HTTP requests to Google's suggestion endpoint
- **Amazon Web Scraping**: BeautifulSoup-based scraping of Amazon search results for competition analysis
- **DuckDuckGo**: Alternative search suggestions for keyword expansion
- **Wikipedia**: Content analysis for related term discovery

## Python Libraries

- **Flask Ecosystem**: Flask, Flask-SQLAlchemy for web framework and ORM
- **Data Processing**: pandas for data manipulation, nltk for natural language processing
- **Web Scraping**: requests, BeautifulSoup4 for HTML parsing
- **Document Generation**: reportlab for PDF report creation
- **Trends Analysis**: pytrends for Google Trends integration
- **Database**: SQLite (built-in) with SQLAlchemy abstraction

## Frontend Libraries

- **Bootstrap 5**: CSS framework for responsive UI components
- **Font Awesome**: Icon library for consistent iconography
- **Chart.js**: JavaScript charting library for data visualization
- **Custom JavaScript**: Vanilla JS for application logic and theme management

## Development and Deployment

- **WSGI**: Werkzeug ProxyFix middleware for proper deployment behind proxies
- **Logging**: Python's built-in logging module for debugging and monitoring
- **Session Management**: Flask's session handling with configurable secret keys
- **File Handling**: Built-in Python libraries for CSV/Excel export functionality