"""
Simple DuckDuckGo text search client implementation.

This module provides a simple client for searching DuckDuckGo and parsing the results.
It supports text search with various parameters and returns structured results.
"""
from typing import Dict, List, Any, Optional
import random
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup


class DDGO:
    """DuckDuckGo search client.

    This class provides methods to search DuckDuckGo and parse the results.
    It supports text search with various parameters and returns structured results.
    """

    # List of user agents to rotate through to avoid rate limiting
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    ]

    def __init__(self, base_url: str = "https://duckduckgo.com/html/", timeout: int = 10, max_retries: int = 3):
        """Initialize the DDGO client.

        Args:
            base_url: The base URL for DuckDuckGo searches. Default is the HTML version.
            timeout: Timeout for HTTP requests in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list.

        Returns:
            A random user agent string.
        """
        return random.choice(self.USER_AGENTS)

    def search(self, query: str, region: str = "wt-wt", safe_search: str = "moderate",
               time_limit: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search DuckDuckGo for the given query.

        Args:
            query: The search query.
            region: Region code (e.g., 'wt-wt', 'us-en', 'uk-en'). Default is 'wt-wt' (no region).
            safe_search: Safe search setting ('on', 'moderate', 'off'). Default is 'moderate'.
            time_limit: Time limit for results ('d' for day, 'w' for week, 'm' for month, 'y' for year).
            max_results: Maximum number of results to return. If None, returns all results from the first page.

        Returns:
            A list of dictionaries containing search results with 'title', 'href', and 'body' keys.

        Raises:
            requests.RequestException: If the request fails after max_retries.
        """
        # Construct the search URL with parameters
        params = {
            'q': query,
            'kl': region,
            'kp': self._safe_search_to_param(safe_search),
        }

        # Add time limit parameter if specified
        if time_limit:
            params['df'] = time_limit

        # Encode the parameters
        encoded_params = urllib.parse.urlencode(params)
        search_url = f"{self.base_url}?{encoded_params}"

        # Set up headers with a random user agent
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://duckduckgo.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Make the request with retries
        response = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(search_url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                break
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1)  # Wait before retrying

        # Parse the results
        results = self._parse_results(response.text)

        # Limit the number of results if specified
        if max_results and len(results) > max_results:
            results = results[:max_results]

        return results

    def _safe_search_to_param(self, safe_search: str) -> str:
        """Convert safe search setting to DuckDuckGo parameter.

        Args:
            safe_search: Safe search setting ('on', 'moderate', 'off').

        Returns:
            The corresponding DuckDuckGo parameter value.
        """
        safe_search = safe_search.lower()
        if safe_search == 'on':
            return '1'
        elif safe_search == 'moderate':
            return '-1'
        elif safe_search == 'off':
            return '-2'
        else:
            return '-1'  # Default to moderate

    def _parse_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse the HTML content of the search results.

        Args:
            html_content: The HTML content of the search results page.

        Returns:
            A list of dictionaries containing search results.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        # Find all result elements
        result_elements = soup.select('.result')

        for element in result_elements:
            # Extract the title and URL
            title_element = element.select_one('.result__title')
            if not title_element:
                continue

            link_element = title_element.select_one('a')
            if not link_element:
                continue

            title = link_element.get_text(strip=True)
            href = link_element.get('href', '')

            # Extract the URL from DuckDuckGo's redirect URL
            if href.startswith('/'):
                parsed_url = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'uddg' in query_params:
                    href = query_params['uddg'][0]

            # Extract the snippet/body text
            snippet_element = element.select_one('.result__snippet')
            body = snippet_element.get_text(strip=True) if snippet_element else ''

            results.append({
                'title': title,
                'href': href,
                'body': body
            })

        return results

    def news(self, query: str, region: str = "wt-wt", safe_search: str = "moderate",
             time_limit: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search DuckDuckGo News for the given query.

        Args:
            query: The search query.
            region: Region code (e.g., 'wt-wt', 'us-en', 'uk-en'). Default is 'wt-wt' (no region).
            safe_search: Safe search setting ('on', 'moderate', 'off'). Default is 'moderate'.
            time_limit: Time limit for results ('d' for day, 'w' for week, 'm' for month).
            max_results: Maximum number of results to return. If None, returns all results from the first page.

        Returns:
            A list of dictionaries containing news search results.

        Raises:
            requests.RequestException: If the request fails after max_retries.
        """
        # Add news search parameter to the query
        news_query = f"{query} site:news"

        # Use the regular search method with the modified query
        return self.search(news_query, region, safe_search, time_limit, max_results)


if __name__ == "__main__":
    # Simple demonstration of the DDGO class when run directly
    client = DDGO()

    print("DuckDuckGo Search Example")
    query = "python"

    print(f"\nSearching for '{query}'...")
    results = client.search(query, max_results=5)

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {result['title']}")
        print(f"URL: {result['href']}")
        print(f"Snippet: {result['body']}")