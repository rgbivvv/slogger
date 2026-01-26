#!venv/bin/python

import logging, shutil
from pathlib import Path
import mistune
import lib.config as config
from datetime import datetime, timezone

from lib.process_files import parse_posts, write_post_pages
from lib.utils import ensure_dir, wipe_dir_files_only
from lib.pages import render_write_page
from lib.sanitize import sanitize_html

logger = logging.getLogger(__name__)

def get_rss_feed(posts: list[dict]) -> str:
    logger.info("Generating RSS feed")
    rss_posts = ''
    for post in posts:
        post['permalink'] = f'{config.SITE_URL}/{post['slug']}.html'
        post_datetime = datetime.fromtimestamp(post['epoch'], tz=timezone.utc)
        rss_post = f"""
        <item>
            <title>{post['title']}</title>
            <link>{post['permalink']}</link>
            <description><![CDATA[{post['html_content']}]]></description>
            <pubDate>{post_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
            <guid isPermaLink="true">{post['permalink']}</guid>
        </item>
        """
        rss_posts += rss_post
        
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
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
    build_temp_dir = ensure_dir('build.temp') # For in-process builds
    assets_dir = ensure_dir(config.ASSETS_DIR)

    # Parse our Markdown pages to store essential information
    logger.info(f'Parsing Markdown files from "{(md_dir.resolve())}"')
    posts = parse_posts(md_dir, assets_dir)
    
    # Copy assets dir to build directory (necessary so we don't download existing assets twice)
    shutil.copytree(assets_dir, build_temp_dir / assets_dir, dirs_exist_ok=True)

    # Write our individual post pages
    written_count = write_post_pages(posts, build_temp_dir)
    logger.info(f'Wrote a total of {written_count} posts')

    # Create the post list component
    posts.sort(key=lambda x: x['epoch'], reverse=True)
    post_list = '<ul>'
    for post in posts:
        # Add a link to the post on our post list
        post_list += f'<li><span class="post-list-link"><a href="{post['permalink']}">{post['title']}</a></span></li>'
    post_list += '</ul>'

    # Create the feed component
    feed_content = ''
    for post in posts:
        post_link = f'<span class="post-link"><small><b><a href="{post['permalink']}">{post['title']}</a></b><small> ( at {post['epoch']} )</small></small></span>'
        post_content = post['html_content']
        feed_content += '\n<br><br>\n' + post_link + '\n<br>' + post_content

    # Render and write index.html
    index_md = Path('index.md').read_text(encoding='utf-8')
    render_write_page([
        sanitize_html(str(mistune.html(index_md))),
        post_list,
        feed_content
    ], build_temp_dir / 'index.html')

    # Generate and write RSS feed
    feed = get_rss_feed(posts)
    (build_temp_dir / 'feed.xml').write_text(feed, encoding='utf-8')

    # Copy the temp build dir to the atomic build dir, clean up temp build dir
    wipe_dir_files_only(build_dir)
    shutil.copytree(build_temp_dir, build_dir, dirs_exist_ok=True)
    shutil.rmtree(build_temp_dir)

    logger.info('Done.')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
