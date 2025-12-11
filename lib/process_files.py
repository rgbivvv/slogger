import logging
from pathlib import Path
import mistune

import lib.config as config
from lib.sanitize import sanitize_html
from lib.pages import render_write_page
from lib.fetch_remote_assets import localize_remote_assets

logger = logging.getLogger(__name__)

def parse_posts(src_dir: Path, assets_dir: Path) -> list[dict]:
    """Read and parse Markdown files, or "posts".

    Args:
        src_dir (Path): The directory of Markdown files to parse.
        assets_dir (Path): Remote assets will be downloaded and stored here if not present in the directory already.

    Returns:
        list[dict]: A list of dictionaries containing data on all of the posts.
    """
    posts = []
    for file in src_dir.iterdir():
        # Skip if what we have is not a file
        if not file.is_file():
            continue

        # Delete the file if it is empty
        if file.stat().st_size <= 1:
            file.unlink(missing_ok=True)
            continue

        # Extract epoch and title
        fname_parts = file.stem.split('_')
        date = fname_parts[0]
        epoch = int(fname_parts[1])
        title = ' '.join([date] + fname_parts[2:])
        slug = '_'.join(title.split(' '))
        if len(title) < 1: # If no title was provided...
            title = date
            slug = date

        # Parse Markdown files
        fcontent = file.read_text(encoding='utf-8')
        fcontent = localize_remote_assets(fcontent, assets_dir)
        html_content = sanitize_html(str(mistune.html(fcontent)))
        post = {
            'fname_src': file.name,           # The name of the Markdown file
            'fname': slug + '.html',          # The name of the rendered HTML file
            'slug': slug,                     # The slugified post title
            'title': title,                   # The string post title
            'epoch': epoch,                   # The UNIX timestamp of the post
            'date': date,                     # The ISO 8601 date of the post
            'fcontent': fcontent,             # The original content of the file
            'html_content': html_content,     # Rendered HTML of the file
            'permalink': f'{config.SITE_URL}/{slug}.html' # Post permalink
        }
        posts.append(post)

    # Sort our pages in reverse order for correct file naming
    posts.sort(key=lambda x: x['epoch'])
    return posts

def write_post_pages(posts: list[dict], dest_dir: Path) -> int:
    """Write a list of posts to a directory.

    Args:
        posts (list[dict]): The list of posts to write.
        dest_dir (Path): The destination path of the posts.

    Returns:
        int: The number of posts written.
    """
    written_count = 0
    for post in posts:
        # Check to see if a post with this title/slug already exists.
        # If it does, append a suffix to differentiate the files
        fpath = dest_dir / post['fname']
        fsuffix = 1
        if fpath.exists():
            new_slug = post['slug']
            while fpath.exists():
                new_slug = f'{post['title']}_{fsuffix}'
                fpath = dest_dir / f'{new_slug}.html'    
                fsuffix += 1
            # Correct the data containing the old slug
            post['title'] = new_slug
            post['slug'] = new_slug
            post['permalink'] = f'{config.SITE_URL}/{new_slug}.html'

        # A couple of small components to put on the individual post pages
        post_header = f'<table><tbody><tr><td>https://<a href="{config.SITE_URL}">{config.SITE_NAME}</a>/{post['fname']}</td></tr></tbody></table>'
        back_link = '<p><a href="/">&#8604; Back to index</a></p>'

        # Render the page and write it
        render_write_page([
            post_header,
            post['html_content'],
            back_link
        ], fpath)
        written_count += 1

    return written_count