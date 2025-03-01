import os
import re
import shutil
import requests
from datetime import datetime
from newspaper import Article  # Make sure to install newspaper3k

def get_full_article(article_url):
    """
    Scrape the full article text from the URL using newspaper3k.
    If unsuccessful, return a fallback message.
    """
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
    Fetch articles from NewsAPI using a broad query that includes several AI-related keywords.
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
    Apply a strict filter so that only articles which mention at least one of
    the key AI-related terms in their title, description, or content are kept.
    """
    pattern = re.compile(
        r"\b(artificial intelligence|machine learning|deep learning|neural network|ai)\b",
        re.IGNORECASE
    )
    
    filtered = []
    for article in articles:
        title = article.get("title", "") or ""
        description = article.get("description", "") or ""
        content = article.get("content", "") or ""
        combined = " ".join([title, description, content])
        if pattern.search(combined):
            filtered.append(article)
    
    return filtered

def generate_html(articles):
    """
    Generate an HTML page displaying the articles.
    
    Each article has a "Read More" button that expands a collapsible area. In the collapsible area,
    the full article is loaded using newspaper3k.
    
    A red divider is inserted as a reminder of previously seen articles using client-side localStorage.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Strict AI News Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
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
        image_html = (
            f'<img src="{article.get("urlToImage")}" class="card-img-top" alt="{article.get("title")}">'
            if article.get("urlToImage") else ""
        )
        # Instead of using the truncated content from NewsAPI, fetch full content.
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
    """
    Remove the site folder if it exists, then recreate it.
    """
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)
    os.makedirs(site_dir)

def main():
    try:
        articles = fetch_ai_news()
    except Exception as e:
        print("Error fetching news:", e)
        articles = []
    
    strict_articles = filter_ai_articles(articles)
    html = generate_html(strict_articles)
    clean_site_folder("site")
    
    try:
        with open(os.path.join("site", "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("Site generated at 'site/index.html'.")
    except Exception as e:
        print("Error writing HTML file:", e)

if __name__ == "__main__":
    main()
