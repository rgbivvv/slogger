import mistune
import bleach

ALLOWED_TAGS = (
    bleach.sanitizer.ALLOWED_TAGS |
    {
        'img', 
        'audio', 
        'video', 
        'source', 
        'pre', 
        'code', 
        'br',
        'small'
        'hr',
        'table',
        'p'
    }
)

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title"],
    "img": ["src", "alt"],
    "audio": ["src", "controls"],
    "video": ["src", "controls"],
    "source": ["src", "type"],
}

def sanitize_html(html_str: str) -> str:
    """Sanitize a given HTML string."""
    return bleach.clean(
        html_str,
        tags = ALLOWED_TAGS,
        attributes = ALLOWED_ATTRIBUTES,
        protocols = ["http", "https"],
        strip=True,
        strip_comments=True
    )