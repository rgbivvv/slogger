#!venv/bin/python
import logging, requests, re, shutil
from pathlib import Path
import mistune
import config
from datetime import datetime, timezone

def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(exist_ok=True)
    return path

def wipe_dir_files_only(root_dir):
    root = Path(root_dir)
    for path in root.rglob("*"):
        if path.is_file():
            path.unlink()

def download_file(url: Path, dest_path: Path):
    logger.info(f'Downloading file {url} to {dest_path} ')
    response = requests.get(str(url), stream=True, timeout=10, headers={'User-Agent': 'curl/8.2.1'})
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)

def process_remote_files(text: str, public_dir: Path) -> str:
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
        subdir = 'audio' if ext in ('.mp3', '.wav', '.ogg') else 'img'
        dest_dir = ensure_dir(public_dir / subdir)
        fname = Path(url).name
        dest_path = dest_dir / fname

        # Download the file if we do not already have it locally
        if not dest_path.exists():
            try:
                download_file(url, dest_path)
            except Exception as e:
                logger.error(f'Failed to fetch {url}: {e}')
                continue
        
        # Replace the link in the original text
        text = text.replace(url, f'{dest_dir}/{fname}')
    return text


def parse_pages(src_dir: Path, public_dir: Path) -> list[dict]:
    logger.info(f'Parsing Markdown files from "{src_dir}"')
    pages = []
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
        title = ' '.join(fname_parts[2:])
        slug = '_'.join(title.split(' '))
        if len(title) < 1: # If no title was provided...
            title = date
            slug = date

        # Parse Markdown contents
        content = file.read_text(encoding='utf-8')
        content = process_remote_files(content, public_dir)
        page = {
            'fname': file.name,
            'fstem': file.stem,
            'fslug': slug,
            'title': title,
            'epoch': epoch,
            'date': date,
            'content': content,
            'html_content': mistune.html(content),
        }
        pages.append(page)
    return pages

def get_rss_feed(posts: list[dict]) -> str:
    logger.info("Generating RSS feed")
    rss_posts = ''
    for post in posts:
        post['permalink'] = f'{config.SITE_URL}/{post['fslug']}.html'
        post_datetime = datetime.fromtimestamp(post['epoch'], tz=timezone.utc)
        rss_post = f"""
            <item>
                <title>{post['title']}</title>
                <link>{post['permalink']}</link>
                <description>{' '.join(post['content'].split()[:15]) + '...'}</description>
                <pubDate>{post_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
                <guid isPermaLink="true">{post['permalink']}</guid>
            </item>
        """
        rss_posts += rss_post
        
    feed = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>{config.SITE_NAME}</title>
            <link>{config.SITE_URL}/</link>
            <description>{config.SITE_DESCRIPTION}</description>

            {rss_posts}
            
        </channel>
    </rss>
    """
    return feed

def main():
    # Declare paths
    md_dir = ensure_dir(config.MD_DIR)
    build_dir = ensure_dir(config.BUILD_DIR)
    assets_dir = ensure_dir(config.ASSETS_DIR)
    # assets_dir_out = ensure_dir(build_dir / assets_dir)

    # Temp dirs for in-process builds
    build_temp_dir = ensure_dir('build.temp')

    # Parse our Markdown pages and store essential information
    pages = parse_pages(md_dir, assets_dir)

    # Copy assets dir to build directory
    shutil.copytree(assets_dir, build_temp_dir / assets_dir, dirs_exist_ok=True)
    # shutil.copytree(assets_dir, assets_dir_out, dirs_exist_ok=True)

    # Read header/footer templates
    header_content = Path('header.html').read_text(encoding='utf-8')
    footer_content= Path('footer.html').read_text(encoding='utf-8')

    # Sort our pages in reverse order for correct file naming
    pages.sort(key=lambda x: x['epoch'])

    # Render/write our HTML pages
    written_count = 0
    for page in pages:
        # Write the rendered HTML file
        fpath = build_temp_dir / f'{page['fslug']}.html'
        fsuffix = 1
        # TODO: break this logic out into its own function
        if fpath.exists():
            new_slug = ''
            while fpath.exists():
                new_slug = f'{page['title']}_{fsuffix}'
                fpath = build_temp_dir / f'{new_slug}.html'    
                fsuffix += 1
            page['title'] = new_slug
            page['fslug'] = new_slug

        with open(fpath, 'w') as f:
            rendered_pieces = [
                header_content.replace('{{title}}', page['title']).replace('{{site_name}}', config.SITE_NAME),
                # header_content,
                page['html_content'],
                '<p><a href="/">&larr; Back to index</a></p>',
                footer_content.replace('{{copyright_name}}', config.COPYRIGHT_NAME),
            ]
            rendered = '\n\n'.join(rendered_pieces)
            f.write(rendered)
            written_count += 1
    logger.info(f'Wrote {written_count} HTML pages')

    # Create the post list HTML
    pages.sort(key=lambda x: x['epoch'], reverse=True)
    post_list = '<ul>'
    for page in pages:
        # Add a link to the post on our post list
        post_list += f'<li><a href="{page['fslug']}.html">{page['title']}</a></li>'
    post_list += '</ul>'

    # Create the feed HTML
    feed_content = ''
    for page in pages:
        post_link = f'<small><b><a href="{page['fslug']}.html">{page['title']}</a></b><small> ( at {page['epoch']} )</small></small>'
        post_content = page['html_content']
        feed_content += '\n<br><br>\n' + post_link + '\n<br>' + post_content

    # Generate and write index.html
    index_md = Path('index.md').read_text(encoding='utf-8')
    index_pieces = [
        header_content.replace('{{title}}', config.SITE_NAME).replace('{{site_name}}', config.SITE_NAME),
        mistune.html(index_md),
        feed_content,
        footer_content.replace('{{copyright_name}}', config.COPYRIGHT_NAME)
    ]
    index_content = '\n\n'.join(index_pieces)
    (build_temp_dir / 'index.html').write_text(index_content, encoding='utf-8')

    # Generate and write RSS feed
    feed = get_rss_feed(pages)
    (build_temp_dir / 'feed.xml').write_text(feed, encoding='utf-8')

    # Copy the temp build dir to the atomic build dir, clean up temp build dir
    wipe_dir_files_only(build_dir)
    shutil.copytree(build_temp_dir, build_dir, dirs_exist_ok=True)
    shutil.rmtree(build_temp_dir)



if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    global logger
    logger = logging.getLogger(__name__)
    main()
