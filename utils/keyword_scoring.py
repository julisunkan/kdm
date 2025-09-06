import math
import logging
from datetime import datetime

class KeywordScorer:
    def __init__(self):
        # Scoring weights
        self.weights = {
            'search_volume': 0.3,
            'competition': 0.4,
            'trend': 0.2,
            'amazon_results': 0.1
        }
    
    def calculate_scores(self, keyword, trends_data, amazon_data, expansions):
        """Calculate comprehensive keyword scores"""
        try:
            # Extract data points
            search_volume = trends_data.get('search_volume', 0)
            trend_score = trends_data.get('trend_score', 0.0)
            amazon_results = amazon_data.get('result_count', 0)
            avg_reviews = amazon_data.get('avg_reviews', 0)
            
            # Calculate individual scores (0-100 scale)
            volume_score = self.calculate_volume_score(search_volume)
            competition_score = self.calculate_competition_score(amazon_results, avg_reviews)
            trend_score_normalized = self.normalize_trend_score(trend_score)
            expansion_score = self.calculate_expansion_score(expansions)
            
            # Calculate difficulty score (lower is better)
            difficulty_score = self.calculate_difficulty_score(
                competition_score, amazon_results, avg_reviews
            )
            
            # Calculate profitability score (higher is better)
            profitability_score = self.calculate_profitability_score(
                volume_score, competition_score, trend_score_normalized, expansion_score
            )
            
            # Calculate overall opportunity score
            opportunity_score = self.calculate_opportunity_score(
                profitability_score, difficulty_score
            )
            
            return {
                'volume_score': round(volume_score, 2),
                'competition_score': round(competition_score, 2),
                'trend_score': round(trend_score_normalized, 2),
                'expansion_score': round(expansion_score, 2),
                'difficulty_score': round(difficulty_score, 2),
                'profitability_score': round(profitability_score, 2),
                'opportunity_score': round(opportunity_score, 2),
                'recommendation': self.get_recommendation(opportunity_score, difficulty_score)
            }
            
        except Exception as e:
            logging.error(f"Error calculating scores for '{keyword}': {e}")
            return {
                'volume_score': 0,
                'competition_score': 0,
                'trend_score': 0,
                'expansion_score': 0,
                'difficulty_score': 100,
                'profitability_score': 0,
                'opportunity_score': 0,
                'recommendation': 'Analysis failed'
            }
    
    def calculate_volume_score(self, search_volume):
        """Calculate search volume score (0-100)"""
        if search_volume <= 0:
            return 0
        
        # Logarithmic scaling for search volume
        # Volumes: 0-100 = 0-20, 100-1000 = 20-50, 1000-10000 = 50-80, 10000+ = 80-100
        if search_volume < 100:
            return min(20, search_volume * 0.2)
        elif search_volume < 1000:
            return 20 + ((search_volume - 100) / 900) * 30
        elif search_volume < 10000:
            return 50 + ((search_volume - 1000) / 9000) * 30
        else:
            return min(100, 80 + math.log10(search_volume / 10000) * 10)
    
    def calculate_competition_score(self, amazon_results, avg_reviews):
        """Calculate competition score (0-100, higher = more competitive)"""
        if amazon_results <= 0:
            return 0
        
        # Base competition from result count
        if amazon_results < 100:
            base_score = 10
        elif amazon_results < 1000:
            base_score = 25
        elif amazon_results < 10000:
            base_score = 50
        elif amazon_results < 100000:
            base_score = 75
        else:
            base_score = 90
        
        # Adjust based on average reviews (more reviews = more established competition)
        review_modifier = 0
        if avg_reviews > 100:
            review_modifier = 10
        elif avg_reviews > 50:
            review_modifier = 5
        
        return min(100, base_score + review_modifier)
    
    def normalize_trend_score(self, trend_score):
        """Normalize trend score to 0-100 scale"""
        # Trend scores typically range from 0-3, normalize to 0-100
        normalized = min(100, max(0, trend_score * 33.33))
        return normalized
    
    def calculate_expansion_score(self, expansions):
        """Calculate score based on keyword expansion potential"""
        try:
            total_expansions = 0
            
            # Count expansions from different sources
            if expansions.get('autocomplete'):
                total_expansions += len(expansions['autocomplete'])
            
            if expansions.get('synonyms'):
                total_expansions += len(expansions['synonyms'])
            
            if expansions.get('ngrams'):
                total_expansions += len(expansions['ngrams'])
            
            if expansions.get('related_questions'):
                total_expansions += len(expansions['related_questions'])
            
            # Normalize to 0-100 scale
            # More expansions = higher potential for content creation
            expansion_score = min(100, (total_expansions / 50) * 100)
            return expansion_score
            
        except Exception as e:
            logging.error(f"Error calculating expansion score: {e}")
            return 0
    
    def calculate_difficulty_score(self, competition_score, amazon_results, avg_reviews):
        """Calculate keyword difficulty (0-100, lower is easier)"""
        # Base difficulty from competition
        base_difficulty = competition_score
        
        # Additional factors
        result_factor = 0
        if amazon_results > 100000:
            result_factor = 20
        elif amazon_results > 10000:
            result_factor = 10
        elif amazon_results > 1000:
            result_factor = 5
        
        review_factor = 0
        if avg_reviews > 500:
            review_factor = 15
        elif avg_reviews > 100:
            review_factor = 8
        elif avg_reviews > 50:
            review_factor = 3
        
        difficulty = min(100, base_difficulty + result_factor + review_factor)
        return difficulty
    
    def calculate_profitability_score(self, volume_score, competition_score, trend_score, expansion_score):
        """Calculate profitability potential (0-100, higher is better)"""
        # Profitability is good volume + good trends + low competition + good expansion potential
        profitability = (
            volume_score * 0.4 +
            trend_score * 0.2 +
            (100 - competition_score) * 0.3 +  # Invert competition score
            expansion_score * 0.1
        )
        
        return min(100, profitability)
    
    def calculate_opportunity_score(self, profitability_score, difficulty_score):
        """Calculate overall opportunity score"""
        # Good opportunity = high profitability + low difficulty
        opportunity = (profitability_score * 0.7) + ((100 - difficulty_score) * 0.3)
        return min(100, opportunity)
    
    def get_recommendation(self, opportunity_score, difficulty_score):
        """Get recommendation based on scores"""
        if opportunity_score >= 80 and difficulty_score <= 30:
            return "Excellent - High opportunity, low competition"
        elif opportunity_score >= 70 and difficulty_score <= 50:
            return "Very Good - Strong potential with manageable competition"
        elif opportunity_score >= 60 and difficulty_score <= 60:
            return "Good - Decent opportunity, moderate effort required"
        elif opportunity_score >= 50:
            return "Moderate - Some potential, higher effort needed"
        elif difficulty_score <= 30:
            return "Low Competition - Easy to rank but limited volume"
        else:
            return "Challenging - High competition or low opportunity"
    
    def get_color_code(self, opportunity_score, difficulty_score):
        """Get color code for UI display"""
        if opportunity_score >= 70 and difficulty_score <= 40:
            return "success"  # Green
        elif opportunity_score >= 50 and difficulty_score <= 60:
            return "warning"  # Yellow
        else:
            return "danger"   # Red
    
    def batch_score_keywords(self, keywords_data):
        """Score multiple keywords at once"""
        scored_keywords = []
        
        for keyword_data in keywords_data:
            try:
                keyword = keyword_data.get('keyword', '')
                trends_data = keyword_data.get('trends_data', {})
                amazon_data = keyword_data.get('amazon_data', {})
                expansions = keyword_data.get('expansions', {})
                
                scores = self.calculate_scores(keyword, trends_data, amazon_data, expansions)
                
                # Combine original data with scores
                keyword_result = {
                    **keyword_data,
                    **scores,
                    'color_code': self.get_color_code(scores['opportunity_score'], scores['difficulty_score'])
                }
                
                scored_keywords.append(keyword_result)
                
            except Exception as e:
                logging.error(f"Error scoring keyword data: {e}")
                continue
        
        # Sort by opportunity score (descending)
        scored_keywords.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
        
        return scored_keywords
