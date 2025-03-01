import os
import re
import shutil
import requests

def fetch_ai_news():
    """
    Fetch articles from NewsAPI using a query that returns AI-related topics.
    """
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Please set the NEWS_API_KEY environment variable!")
    
    url = "https://newsapi.org/v2/everything"
    # Use a broad query that includes several AI-related terms in a boolean OR
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
    several key AI-related terms in the title, description, or content are kept.
    """
    # Define a regular expression that matches any of the AI-related keywords.
    # \b ensures whole-word matches.
    pattern = re.compile(
        r"\b(artificial intelligence|machine learning|deep learning|neural network|ai)\b",
        re.IGNORECASE
    )
    
    filtered = []
    for article in articles:
        # Get the article text from title, description, and content.
        title = article.get("title", "") or ""
        description = article.get("description", "") or ""
        content = article.get("content", "") or ""
        # Combine the text fields.
        combined = " ".join([title, description, content])
        
        if pattern.search(combined):
            filtered.append(article)
    
    return filtered

def generate_html(articles):
    """
    Generate an HTML page displaying the given articles.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Strict AI News Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" 
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body>
<div class="container mt-5">
  <h1 class="mb-4">Latest AI News</h1>
"""
    if articles:
        for article in articles:
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
        <small class="text-muted">
          Published at: {article.get("publishedAt")}
        </small>
      </p>
    </div>
  </div>
"""
    else:
        html_content += "<p>No strictly AI-related articles found.</p>\n"
    
    html_content += """
</div>
</body>
</html>
"""
    return html_content

def clean_site_folder(site_dir="site"):
    """
    Remove the site folder, if it exists, and then recreate it.
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
