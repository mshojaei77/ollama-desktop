import requests
from bs4 import BeautifulSoup
import json

# Generic fetcher that accepts query parameters and returns parsed model JSON
def fetch_models(params=""):
    url = f"https://ollama.com/search{params}"
    resp = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; model-scraper/1.0)"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    models = []
    for li in soup.find_all("li", attrs={"x-test-model": True}):
        name_tag = li.find("span", attrs={"x-test-search-response-title": True})
        info_tag = li.find("p", class_="max-w-lg break-words text-neutral-800 text-md")

        # new: collect all tags (capabilities) and sizes
        tags = [span.get_text(strip=True)
                for span in li.find_all("span", attrs={"x-test-capability": True})]
        sizes = [span.get_text(strip=True)
                 for span in li.find_all("span", attrs={"x-test-size": True})]

        if name_tag and info_tag:
            models.append({
                "name": name_tag.get_text(strip=True),
                "info": info_tag.get_text(strip=True),
                "tags": tags,
                "sizes": sizes
            })

    return models

# Wrappers for specific queries
def fetch_popular_models():
    return fetch_models()

def fetch_vision_models():
    return fetch_models("?c=vision")

def fetch_tools_models():
    return fetch_models("?c=tools")

def fetch_newest_models():
    return fetch_models("?o=newest")

def fetch_embedding_models():
    return fetch_models("?c=embedding")

if __name__ == "__main__":
    data = fetch_embedding_models()
    print(json.dumps(data, indent=2, ensure_ascii=False))