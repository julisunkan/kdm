import requests
import nltk
from nltk.corpus import wordnet
from nltk.util import ngrams
import logging
import re
from urllib.parse import quote_plus
import time
import random

class KeywordResearcher:
    def __init__(self):
        self.setup_nltk()
        
    def setup_nltk(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
        
        try:
            nltk.data.find('corpora/omw-1.4')
        except LookupError:
            nltk.download('omw-1.4')
    
    def expand_keyword(self, keyword):
        """Expand a keyword using multiple methods"""
        expansions = {
            'original': keyword,
            'autocomplete': self.get_google_autocomplete(keyword),
            'synonyms': self.get_wordnet_synonyms(keyword),
            'ngrams': self.generate_ngrams(keyword),
            'related_questions': self.get_related_questions(keyword)
        }
        
        return expansions
    
    def get_google_autocomplete(self, keyword):
        """Get Google autocomplete suggestions"""
        try:
            # Using Google's autocomplete API
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': keyword
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                suggestions = response.json()[1]
                return suggestions[:10]  # Return top 10 suggestions
        except Exception as e:
            logging.error(f"Error getting Google autocomplete: {e}")
        
        return []
    
    def get_wordnet_synonyms(self, keyword):
        """Get synonyms using WordNet"""
        synonyms = set()
        
        try:
            # Split keyword into words
            words = keyword.lower().split()
            
            for word in words:
                # Get synsets for each word
                synsets = wordnet.synsets(word)
                
                for synset in synsets[:3]:  # Limit to first 3 synsets
                    if synset and hasattr(synset, 'lemmas'):
                        for lemma in synset.lemmas():
                            if lemma and hasattr(lemma, 'name'):
                                synonym = lemma.name().replace('_', ' ')
                                if synonym != word and len(synonym) > 2:
                                    synonyms.add(synonym)
            
            return list(synonyms)[:15]  # Return top 15 synonyms
            
        except Exception as e:
            logging.error(f"Error getting WordNet synonyms: {e}")
            return []
    
    def generate_ngrams(self, keyword, n=2):
        """Generate n-grams and related phrases"""
        try:
            words = keyword.lower().split()
            
            # Common book-related prefixes and suffixes
            prefixes = [
                'how to', 'guide to', 'complete guide', 'beginner guide',
                'step by step', 'ultimate guide', 'easy', 'simple',
                'advanced', 'best practices', 'tips for', 'secrets of'
            ]
            
            suffixes = [
                'for beginners', 'guide', 'handbook', 'manual', 'tips',
                'strategies', 'techniques', 'methods', 'workbook',
                'step by step', 'made easy', 'for dummies'
            ]
            
            variations = []
            
            # Add prefixes
            for prefix in prefixes[:8]:
                variations.append(f"{prefix} {keyword}")
            
            # Add suffixes
            for suffix in suffixes[:8]:
                variations.append(f"{keyword} {suffix}")
            
            # Generate bigrams if keyword has multiple words
            if len(words) > 1:
                bigrams = list(ngrams(words, 2))
                for bigram in bigrams:
                    variations.append(' '.join(bigram))
            
            return variations[:20]  # Return top 20 variations
            
        except Exception as e:
            logging.error(f"Error generating n-grams: {e}")
            return []
    
    def get_related_questions(self, keyword):
        """Get related questions from various sources"""
        questions = []
        
        # Common question patterns for books
        question_patterns = [
            f"How to {keyword}?",
            f"What is {keyword}?",
            f"Why {keyword}?",
            f"When to {keyword}?",
            f"Where to {keyword}?",
            f"Best {keyword} methods?",
            f"Common {keyword} mistakes?",
            f"{keyword} for beginners?",
            f"Advanced {keyword} techniques?",
            f"{keyword} step by step?"
        ]
        
        return question_patterns
    
    def get_duckduckgo_suggestions(self, keyword):
        """Get suggestions from DuckDuckGo"""
        try:
            url = "https://duckduckgo.com/ac/"
            params = {'q': keyword}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                suggestions = [item['phrase'] for item in data if 'phrase' in item]
                return suggestions[:10]
                
        except Exception as e:
            logging.error(f"Error getting DuckDuckGo suggestions: {e}")
        
        return []
    
    def bulk_expand_keywords(self, keywords_list):
        """Expand multiple keywords with rate limiting"""
        results = {}
        
        for i, keyword in enumerate(keywords_list):
            try:
                results[keyword] = self.expand_keyword(keyword)
                
                # Add delay to avoid rate limiting
                if i % 5 == 0 and i > 0:
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error expanding keyword '{keyword}': {e}")
                results[keyword] = {'original': keyword}
        
        return results
