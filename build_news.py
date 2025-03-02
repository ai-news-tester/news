import os
import re
import shutil
import requests
from datetime import datetime
from newspaper import Article  # Ensure newspaper3k is installed
from bs4 import BeautifulSoup  # Ensure beautifulsoup4 is installed

def get_full_article(article_url):
    """
    For Biztoc URLs: Attempt to extract the original article URL from the Biztoc page by
    looking for an anchor tag with text such as "this story appeared on" or "original article."
    Then, use newspaper3k to fetch the full article text from that URL.
    For all other URLs, simply attempt to fetch the full article text.
    """
    if "biztoc.com" in article_url:
        try:
            res = requests.get(article_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            original_link = None
            # Look for an anchor tag with typical Biztoc wording.
            for a in soup.find_all('a', href=True):
                text = a.get_text().strip().lower()
                if "this story appeared on" in text or "original article" in text:
                    original_link = a['href']
                    break
            if original_link:
                print(f"Extracted original link from Biztoc: {original_link}")
                article_url = original_link
            else:
                print("No original link found on Biztoc page.")
                return f'This story appeared on <a href="{article_url}" target="_blank">original source</a>.'
        except Exception as e:
            print(f"Error processing Biztoc link {article_url}: {e}")
            return f'This story appeared on <a href="{article_url}" target="_blank">original source</a>.'
    try:
        art = Article(article_url)
        art.download()
        art.parse()
        return art.text
    except Exception as e:
        print(f"Error fetching full article from {article_url}: {e}")
        return "Full article not available. Please click 'Visit Original Article'."

def fetch_ai_news():
    """
    Fetch articles from NewsAPI using a broad query for AI-related topics.
    """
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Please set the NEWS_API_KEY environment variable!")
    url = "https://newsapi.org/v2/everything"
    query = '("Artificial Intelligence" OR "machine learning" OR "deep learning" OR "neural network" OR "AI")'
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 20,
        "language": "en",
        "apiKey": api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    return articles

def filter_ai_articles(articles):
    """
    Filter articles as follows:
      1. Skip any article from blocked domains (for example, "economictimes.indiatimes.com").
      2. For every article (regardless of whether it's from Biztoc or not), require that
         at least one key AI-related phrase appears in its title, description, or content.
         This prevents non-AI Biztoc articles from being allowed.
    """
    required_terms = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network"
    ]
    blocked_domains = [
        "economictimes.indiatimes.com"
    ]
    filtered = []
    for article in articles:
        url = article.get("url", "").lower()
        # Skip any article from a blocked domain.
        if any(blocked in url for blocked in blocked_domains):
            continue
        # Combine title, description, and content (as available).
        text = " ".join([
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", "")
        ]).lower()
        # Accept the article only if at least one required term is found.
        if any(term in text for term in required_terms):
            filtered.append(article)
    return filtered

def generate_html(articles):
    """
    Generate an HTML page listing the filtered articles. Each article card includes:
      - An image (if available)
      - The title and description
      - A "Read
