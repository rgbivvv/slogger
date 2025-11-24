from pathlib import Path
from typing import Any

import config

# Declare global template variables
TEMPLATE_VARS = {
    'title': config.SITE_NAME,
    'site_name': config.SITE_NAME,
    'copyright_name': config.COPYRIGHT_NAME
}

def _render_page(page_components: list[str], template_vars: dict[str, Any]) -> str:
    """Render a page from a list of HTML page components, as well as replace template variables with the desire values.

    Args:
        page_components (list[str]): A list of HTML strings that make up elements of the page.
        template_vars (dict[str, Any]): A dictionary mapping template variable names to their values.

    Returns:
        str: The complete, rendered HTML page.
    """
    page_content = '\n\n'.join(page_components)
    for template_var, value in template_vars.items():
        page_content = page_content.replace(f'{{{{{template_var}}}}}', str(value))
    return page_content

def render_page(page_components: list[str]) -> str:
    """An "overloaded" version of `_render_page` that automatically reads a header and footer from the source directory of the repo and appends them to the page components.

    Args:
        page_components (list[str]): A list of HTML strings that make up the elemnts of the page. These will be wrapped by the contents of `header.html` and `footer.html`

    Returns:
        str: The complete, rendered HTML page.
    """
    header_content = Path('header.html').read_text(encoding='utf-8')
    footer_content = Path('footer.html').read_text(encoding='utf-8')
    page_components = [header_content] + page_components + [footer_content]
    return _render_page(page_components, TEMPLATE_VARS)

def render_write_page(page_components: list[str], dest_path: Path):
    rendered = render_page(page_components)
    dest_path.write_text(rendered, encoding='utf-8')