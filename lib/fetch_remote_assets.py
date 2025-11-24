import logging
import requests
import re
from pathlib import Path

from lib.utils import ensure_dir

logger = logging.getLogger(__name__)

def save_remote_file(url: Path, dest_path: Path):
    logger.info(f'Downloading file {url} to {dest_path} ')
    response = requests.get(str(url), stream=True, timeout=10, headers={'User-Agent': 'curl/8.2.1'})
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)

def localize_remote_assets(text: str, dest_dir: Path) -> str:
    # Matches strings like ![xyz](https://example.com/xyz.jpg)
    urls = set(re.findall(r'!\[.*?\]\((https?:\/\/[^\)]+)\)', text))
    # Matches strings like src="https://example.com/xyz.jpg"
    urls |= set(re.findall(r'src=[\'"](https?:\/\/[^\'"]+)[\'"]', text))

    for url in urls:
        if not url.startswith(("http://", "https://")):
            logger.info(f"Skipping local reference: {url}")
            continue

        # Figure out where to look for the file
        ext = Path(url).suffix.lower()
        if ext in ('.mp3', '.wav', '.ogg', '.flac'):
            subdir = 'audio'
        elif ext in ('.mp4', '.mpeg', '.mov', '.avi'):
            subdir = 'video'
        elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'):
            subdir = 'img'
        else:
            subdir = 'other'
        fname = Path(url).name
        dest_path = ensure_dir(dest_dir / subdir) / fname

        # Download the file if we do not already have it locally
        if not dest_path.exists():
            try:
                save_remote_file(url, dest_path)
            except Exception as e:
                logger.error(f'Failed to fetch {url}: {e}')
                continue
        
        # Replace the link in the original text
        text = text.replace(url, str(dest_path))
    return text