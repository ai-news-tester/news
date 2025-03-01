import os
import shutil
import requests

def fetch_ai_news():
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Please set the NEWS_API_KEY environment variable!")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "AI",  # simple query that worked before
        "sortBy": "publishedAt",
        "pageSize": 20,
        "language": "en",
        "apiKey": api_key,
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()  # will raise an error if something goes wrong
    data = response.json()
    articles = data.get("articles", [])
    return articles

def filter_ai_articles(articles):
    """
    Perform a light filtering: Only keep articles where the title or description
    contains "ai" or "artificial intelligence" (case-insensitive). If filtering returns
    an empty list, fallback to the original list so you see something.
    """
    filtered = []
    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        
        if "ai" in title or "artificial intelligence" in title or \
           "ai" in description or "artificial intelligence" in description:
            filtered.append(article)
    
    # If filtering has dropped everything, fall back to the original list.
    return filtered if filtered else articles

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
        <small class="text-muted">Published at: {article.get("publishedAt")}</small>
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
    
    if articles:
        filtered_articles = filter_ai_articles(articles)
    else:
        filtered_articles = []
    
    html = generate_html(filtered_articles)
    
    clean_site_folder("site")
    
    try:
        with open("site/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Site generated at site/index.html.")
    except Exception as e:
        print("Error writing HTML file:", e)

if __name__ == "__main__":
    main()
