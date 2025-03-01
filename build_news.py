import os
import re
import shutil
import requests
from datetime import datetime, timedelta

def fetch_ai_news():
    """
    Fetch articles from NewsAPI using a broad query that includes several AI-related keywords.
    """
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Please set the NEWS_API_KEY environment variable!")
    
    url = "https://newsapi.org/v2/everything"
    # A broad query that should return AI-related topics
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
    Apply a strict filter so that only articles mentioning at least one of the key terms in
    their title, description, or content are kept.
    """
    # Regular expression that matches any of the key phrases.
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
    A divider is inserted if the time difference between consecutive articles exceeds the threshold.
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
      margin: 2rem 0;
      text-align: center;
      color: #6c757d;
      font-style: italic;
    }
  </style>
</head>
<body>
<div class="container mt-5">
  <h1 class="mb-4">Latest AI News</h1>
"""
    # Set a threshold for time gap (e.g., 60 minutes)
    threshold = timedelta(minutes=60)
    
    # Assume articles are already sorted by publishedAt in descending order.
    # If not, you could sort them here.
    for index, article in enumerate(articles):
        # Insert a divider if (and only if) the gap between the previous article
        # and current article exceeds the threshold.
        if index > 0:
            try:
                current_date = datetime.fromisoformat(
                    article.get("publishedAt").replace("Z", "+00:00")
                )
                previous_date = datetime.fromisoformat(
                    articles[index - 1].get("publishedAt").replace("Z", "+00:00")
                )
                if (previous_date - current_date) > threshold:
                    html_content += (
                        '<hr>'
                        '<div class="divider">Earlier Articles</div>'
                        '<hr>'
                    )
            except Exception as e:
                # In case of a parsing error, we simply continue without adding a divider.
                print("Error parsing dates:", e)
        
        # Optional: Format the publication time for display.
        try:
            pub_date = datetime.fromisoformat(
                article.get("publishedAt").replace("Z", "+00:00")
            ).strftime('%Y-%m-%d %H:%M')
        except Exception:
            pub_date = article.get("publishedAt", "Unknown Date")
        
        image_html = (
            f'<img src="{article.get("urlToImage")}" class="card-img-top" alt="{article.get("title")}">'
            if article.get("urlToImage") else ""
        )
        html_content += f"""
  <div class="card mb-3">
    {image_html}
    <div class="card-body">
      <h5 class="card-title">{article.get("title")}</h5>
      <p class="card-text">{article.get("description", "")}</p>
      <a href="{article.get("url")}" target="_blank" class="btn btn-primary">
        Read More
      </a>
      <p class="card-text">
        <small class="text-muted">Published at: {pub_date}</small>
      </p>
    </div>
  </div>
"""
    if not articles:
        html_content += "<p>No strictly AI-related articles found.</p>\n"
    
    html_content += """
</div>
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
    
    # Apply strict filtering
    strict_articles = filter_ai_articles(articles)
    
    # Generate HTML using the strictly filtered articles with dividers
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
