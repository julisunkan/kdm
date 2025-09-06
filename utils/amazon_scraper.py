import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from urllib.parse import quote_plus
import json

class AmazonScraper:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_keyword_competition(self, keyword):
        """Get Amazon competition data for a keyword"""
        try:
            # Search Amazon for books with the keyword
            search_url = f"https://www.amazon.com/s?k={quote_plus(keyword)}&i=stripbooks"
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract result count
            result_count = self.extract_result_count(soup)
            
            # Extract book data from first page
            books_data = self.extract_books_data(soup)
            
            # Calculate competition metrics
            competition_data = self.calculate_competition_metrics(books_data, result_count)
            competition_data['keyword'] = keyword
            
            return competition_data
            
        except Exception as e:
            logging.error(f"Error scraping Amazon for '{keyword}': {e}")
            return {
                'keyword': keyword,
                'result_count': 0,
                'avg_price': 0.0,
                'avg_reviews': 0,
                'category': 'Unknown',
                'competition_level': 'Unknown',
                'error': str(e)
            }
    
    def extract_result_count(self, soup):
        """Extract the number of search results"""
        try:
            # Look for result count in various possible locations
            result_text_selectors = [
                'span[data-component-type="s-result-info-bar"] span',
                '.s-result-info-bar span',
                '[data-component-type="s-result-info-bar"]',
                '.sg-col-inner span'
            ]
            
            for selector in result_text_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if 'results' in text.lower():
                        # Extract number from text like "1-16 of over 40,000 results"
                        numbers = re.findall(r'[\d,]+', text)
                        if numbers:
                            # Take the largest number found
                            max_num = max([int(num.replace(',', '')) for num in numbers])
                            return max_num
            
            # If no result count found, count visible products
            products = soup.select('[data-component-type="s-search-result"]')
            return len(products) * 20  # Estimate based on visible products
            
        except Exception as e:
            logging.error(f"Error extracting result count: {e}")
            return 0
    
    def extract_books_data(self, soup):
        """Extract book data from search results"""
        books = []
        
        try:
            # Find all product containers
            product_containers = soup.select('[data-component-type="s-search-result"]')
            
            for container in product_containers[:10]:  # Limit to first 10 results
                try:
                    book_data = {}
                    
                    # Extract title
                    title_elem = container.select_one('h2 a span, .s-title-instructions-style span')
                    if title_elem:
                        book_data['title'] = title_elem.get_text().strip()
                    
                    # Extract price
                    price_elem = container.select_one('.a-price-whole, .a-offscreen')
                    if price_elem:
                        price_text = price_elem.get_text().strip()
                        price_match = re.search(r'[\d.]+', price_text)
                        if price_match:
                            book_data['price'] = float(price_match.group())
                    
                    # Extract rating and review count
                    rating_elem = container.select_one('.a-icon-alt')
                    if rating_elem:
                        rating_text = rating_elem.get('title', '')
                        rating_match = re.search(r'([\d.]+) out of', rating_text)
                        if rating_match:
                            book_data['rating'] = float(rating_match.group(1))
                    
                    review_elem = container.select_one('.a-size-base')
                    if review_elem:
                        review_text = review_elem.get_text().strip()
                        review_match = re.search(r'([\d,]+)', review_text)
                        if review_match:
                            book_data['review_count'] = int(review_match.group(1).replace(',', ''))
                    
                    # Extract author
                    author_elem = container.select_one('.a-size-base+ .a-size-base, .s-size-mini')
                    if author_elem:
                        book_data['author'] = author_elem.get_text().strip()
                    
                    if book_data:  # Only add if we extracted some data
                        books.append(book_data)
                        
                except Exception as e:
                    logging.warning(f"Error extracting individual book data: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error extracting books data: {e}")
        
        return books
    
    def calculate_competition_metrics(self, books_data, result_count):
        """Calculate competition metrics from book data"""
        if not books_data:
            return {
                'result_count': result_count,
                'avg_price': 0.0,
                'avg_reviews': 0,
                'category': 'Books',
                'competition_level': 'High' if result_count > 10000 else 'Medium' if result_count > 1000 else 'Low'
            }
        
        # Calculate averages
        prices = [book.get('price', 0) for book in books_data if book.get('price')]
        reviews = [book.get('review_count', 0) for book in books_data if book.get('review_count')]
        ratings = [book.get('rating', 0) for book in books_data if book.get('rating')]
        
        avg_price = sum(prices) / len(prices) if prices else 0.0
        avg_reviews = sum(reviews) / len(reviews) if reviews else 0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Determine competition level
        competition_level = 'Low'
        if result_count > 50000:
            competition_level = 'Very High'
        elif result_count > 10000:
            competition_level = 'High'
        elif result_count > 1000:
            competition_level = 'Medium'
        
        return {
            'result_count': result_count,
            'avg_price': round(avg_price, 2),
            'avg_reviews': int(avg_reviews),
            'avg_rating': round(avg_rating, 1),
            'category': 'Books',
            'competition_level': competition_level,
            'total_books_analyzed': len(books_data)
        }
    
    def get_category_bestsellers(self, category_url):
        """Get bestseller data for a specific category"""
        try:
            response = self.session.get(category_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            bestsellers = []
            
            # Extract bestseller information
            book_containers = soup.select('.zg-item-immersion')
            
            for container in book_containers[:20]:  # Top 20 bestsellers
                try:
                    book_data = {}
                    
                    # Extract title
                    title_elem = container.select_one('.p13n-sc-truncate')
                    if title_elem:
                        book_data['title'] = title_elem.get_text().strip()
                    
                    # Extract rank
                    rank_elem = container.select_one('.zg-badge-text')
                    if rank_elem:
                        rank_text = rank_elem.get_text().strip()
                        rank_match = re.search(r'#(\d+)', rank_text)
                        if rank_match:
                            book_data['rank'] = int(rank_match.group(1))
                    
                    if book_data:
                        bestsellers.append(book_data)
                        
                except Exception as e:
                    logging.warning(f"Error extracting bestseller data: {e}")
                    continue
            
            return bestsellers
            
        except Exception as e:
            logging.error(f"Error getting bestsellers: {e}")
            return []
    
    def bulk_analyze_keywords(self, keywords_list):
        """Analyze multiple keywords with rate limiting"""
        results = {}
        
        for i, keyword in enumerate(keywords_list):
            try:
                results[keyword] = self.get_keyword_competition(keyword)
                
                # Rate limiting to avoid being blocked
                delay = random.uniform(2, 5)
                time.sleep(delay)
                
                if i % 10 == 0 and i > 0:
                    logging.info(f"Processed {i} keywords...")
                    
            except Exception as e:
                logging.error(f"Error analyzing keyword '{keyword}': {e}")
                results[keyword] = {
                    'keyword': keyword,
                    'result_count': 0,
                    'error': str(e)
                }
        
        return results
