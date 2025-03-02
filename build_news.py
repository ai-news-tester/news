import os
import re
import shutil
import requests
from datetime import datetime
from newspaper import Article  # Ensure newspaper3k is installed
from bs4 import BeautifulSoup  # Ensure beautifulsoup4 is installed

def get_full_article(article_url):
    """
    For Biztoc URLs: Look within the Biztoc page for an anchor tag whose text includes 
    "this story appeared on" or "original article." If found, use that URL as the source.
    For all other URLs, try to fetch the full article using newspaper3k.
    """
    if "biztoc.com" in article_url:
        try:
            res = requests.get(article_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            original_link = None
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
    Fetch articles from NewsAPI using a broad AI-related query.
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
      - If the article comes from a blocked domain (e.g. "economictimes.indiatimes.com"), skip it.
      - If the article's URL contains "biztoc.com", allow it (Biztoc often provides only preview text).
      - For all other articles, require that at least one key phrase is present in their
        title, description, or content.
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
        # Skip articles from blocked domains.
        if any(blocked in url for blocked in blocked_domains):
            continue
        # Allow Biztoc articles regardless of text.
        if "biztoc.com" in url:
            filtered.append(article)
            continue
        text = " ".join([
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", "")
        ]).lower()
        if any(term in text for term in required_terms):
            filtered.append(article)
    return filtered

def generate_html(articles):
    """
    Generate an HTML page listing articles. Each article card includes:
      - An image (if available)
      - Title and description
      - A "Read More" button that expands to show full article text (via get_full_article)
      - Publication date metadata (used by a client-side script to insert a red divider)
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Strict AI News Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <style>
    .divider {
      border-top: 2px solid red;
      margin: 20px 0;
      padding-top: 10px;
      text-align: center;
      color: red;
      font-weight: bold;
    }
  </style>
</head>
<body>
<div class="container mt-5">
  <h1 class="mb-4">Latest AI News</h1>
"""
    for index, article in enumerate(articles):
        try:
            pub_dt = datetime.fromisoformat(article.get("publishedAt").replace("Z", "+00:00"))
            pub_date = pub_dt.strftime('%Y-%m-%d %H:%M')
            pub_date_iso = article.get("publishedAt")
        except Exception:
            pub_date = article.get("publishedAt", "Unknown Date")
            pub_date_iso = ""
        image_html = (f'<img src="{article.get("urlToImage")}" class="card-img-top" alt="{article.get("title")}">'
                      if article.get("urlToImage") else "")
        full_article_text = get_full_article(article.get("url"))
        collapse_id = f"collapse{index}"
        
        html_content += f"""
  <div class="card mb-3">
    {image_html}
    <div class="card-body">
      <h5 class="card-title">{article.get("title")}</h5>
      <p class="card-text">{article.get("description", "")}</p>
      <button class="btn btn-primary" type="button" data-bs-toggle="collapse" data-bs-target="#{collapse_id}" aria-expanded="false" aria-controls="{collapse_id}">
        Read More
      </button>
      <div class="collapse mt-2" id="{collapse_id}">
        <div class="card card-body">
          <p>{full_article_text}</p>
          <a href="{article.get("url")}" target="_blank">Visit Original Article</a>
        </div>
      </div>
      <p class="card-text pub-date" data-pub-date="{pub_date_iso}">
        <small class="text-muted">Published at: {pub_date}</small>
      </p>
    </div>
  </div>
"""
    if not articles:
        html_content += "<p>No strictly AI-related articles found.</p>\n"
    html_content += """
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  const lastSeen = localStorage.getItem('lastSeen');
  const cards = document.querySelectorAll('.card.mb-3');
  let dividerInserted = false;
  if (lastSeen) {
    cards.forEach(card => {
      const pubDateElem = card.querySelector('.pub-date');
      if (pubDateElem) {
        const pubDate = new Date(pubDateElem.getAttribute('data-pub-date'));
        if (pubDate < new Date(lastSeen) && !dividerInserted) {
          const divider = document.createElement('div');
          divider.className = 'divider';
          divider.innerText = 'Previously Seen Articles';
          card.parentNode.insertBefore(divider, card);
          dividerInserted = true;
        }
      }
    });
  }
  if (cards.length > 0) {
    const firstPubDate = cards[0].querySelector('.pub-date').getAttribute('data-pub-date');
    localStorage.setItem('lastSeen', firstPubDate);
  }
});
</script>
</body>
</html>
"""
    return html_content

def clean_site_folder(site_dir="site"):
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir)

def main():
    try:
        articles = fetch_ai_news()
    except Exception as e:
        print("Error fetching news:", e)
        articles = []
    filtered_articles = filter_ai_articles(articles)
    html = generate_html(filtered_articles)
    clean_site_folder("site")
    try:
        with open(os.path.join("site", "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("Site generated at 'site/index.html'.")
    except Exception as e:
        print("Error writing HTML file:", e)

if __name__ == "__main__":
    main()
