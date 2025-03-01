import os
import re
import shutil
import requests

def fetch_technology_sources(api_key):
    """
    Fetch a comma-separated list of source IDs for technology-related news.
    """
    url = "https://newsapi.org/v2/sources"
    params = {
        "category": "technology",
        "language": "en",
        "apiKey": api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    sources = data.get("sources", [])
    return ",".join([source["id"] for source in sources if "id" in source])

def fetch_ai_news_filtered():
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Please set the NEWS_API_KEY environment variable!")
    
    # Get IDs for technology sources.
    tech_sources = fetch_technology_sources(api_key)
    
    url = "https://newsapi.org/v2/everything"
    params = {
        # Search only in titles for "ai" or "Artificial Intelligence"
        "qInTitle": 'ai OR "Artificial Intelligence"',
        "sources": tech_sources,
        "sortBy": "publishedAt",
        "pageSize": 20,
        "language": "en",
        "apiKey": api_key,
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    
    # Debug: Print all obtained titles.
    print("Fetched articles:")
    for art in articles:
        print(" -", art.get("title"))
    
    # Optional: further filter articles with regex.
    pattern = re.compile(r"\b(ai|artificial intelligence)\b", re.IGNORECASE)
    filtered_articles = [
        art for art in articles
        if art.get("title") and pattern.search(art.get("title"))
    ]
    
    # If regex filtering removes all articles, fallback to the original list.
    if filtered_articles:
        return filtered_articles
    else:
        return articles

def generate_html(articles):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AI News Blog</title>
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
                f'<img src="{article.get("urlToImage")}" class="card-img-top" '
                f'alt="{article.get("title")}">'
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
        html_content += "<p>No AI-related articles found.</p>\n"
    
    html_content += """
</div>
</body>
</html>
"""
    return html_content

def clean_site_folder(output_dir="site"):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

def main():
    try:
        articles = fetch_ai_news_filtered()
    except Exception as e:
        print(f"Error fetching news: {e}")
        articles = []
    
    html = generate_html(articles)
    output_dir = "site"
    clean_site_folder(output_dir)
    
    try:
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("Site generated at 'site/index.html'.")
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == "__main__":
    main()
