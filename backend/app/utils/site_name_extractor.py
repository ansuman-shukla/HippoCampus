from urllib.parse import urlparse

async def extract_site_name(url: str) -> str:
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    
    parsed = urlparse(url)
    domain = parsed.netloc  # This gives everything between // and the next /
    
    # Remove www prefix if present
    if domain.startswith("www."):
        domain = domain[4:]
    
    return domain