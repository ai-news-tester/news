import os
import re
import shutil
import requests
from datetime import datetime

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
    
    Each article shows a "Read More" button which toggles an inline collapsible
    section containing additional content. Also, each article includes a data attribute for
    its publishedAt date.
    
    Later, client-side JavaScript compares the published times against a stored
    "lastSeen" timestamp and inserts a red divider just before the first article that is older.
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
    # List all articles (without removing any).
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
        # Each article gets a collapse section for "Read More"
        html_content += f"""
  <div class="card mb-3">
    {image_html}
    <div class="card-body">
      <h5 class="card-title">{article.get("title")}</h5>
      <p class="card-text">{article.get("description", "")}</p>
      <button class="btn btn-primary" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{index}" aria-expanded="false" aria-controls="collapse{index}">
        Read More
      </button>
      <div class="collapse mt-2" id="collapse{index}">
        <div class="card card-body">
          <p>{article.get("content") or "Full content not available."}</p>
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
    
    # Insert the inline script to add a red divider based on localStorage.
    html_content += """
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Retrieve the last seen date from localStorage
  const lastSeen = localStorage.getItem('lastSeen');
  // Get all article cards (each with class "card mb-3")
  const cards = document.querySelectorAll('.card.mb-3');
  let dividerInserted = false;
  if (lastSeen) {
    cards.forEach(card => {
      const pubDateElem = card.querySelector('.pub-date');
      if (pubDateElem) {
        const pubDate = new Date(pubDateElem.getAttribute('data-pub-date'));
        // If this article is older than the last seen article and we haven't inserted a divider yet,
        // insert a red divider above this card.
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
  // Update the lastSeen value with the published date of the newest article.
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
    Remove the site folder if it exists and then recreate it.
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
