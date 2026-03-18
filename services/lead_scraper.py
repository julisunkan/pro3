import requests
from bs4 import BeautifulSoup


def scrape_website(url: str, max_paragraphs: int = 3) -> str:
    """
    Scrape the homepage of a company website and return the first few paragraphs.
    Returns an empty string on any error.
    """
    if not url:
        return ''

    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (compatible; ColdEmailBot/1.0; '
                '+https://github.com/cold-email-generator)'
            )
        }
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove unwanted tags
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        paragraphs = soup.find_all('p')
        texts = []
        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            if len(text) > 40:  # Skip very short snippets
                texts.append(text)
            if len(texts) >= max_paragraphs:
                break

        return ' '.join(texts)

    except Exception:
        # Silently fail — scraping is best-effort
        return ''
